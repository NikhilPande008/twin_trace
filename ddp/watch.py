"""
Decision watch (T12.4 / T12.5): a recorded decision is a bet on a few facts; keep checking them.

When something changes after a decision was recorded (a registry flags or withdraws a counterparty,
a new transaction arrives, a cited rule changes), the watch:

  1. finds the standing decisions it affects,
  2. re-runs the SAME calculator of record on the decision's SAVED inputs with the change applied
     (a COMPUTE_RUNS row with PARENT_RUN_ID = the decision's run; never the current case data),
  3. compares the deterministic verdicts before and after, and
  4. appends one DECISION_EVENTS row: holds | reopened | needs_review, naming the fact that moved.

No model is involved: the same change on the same decision always gives the same outcome hash, and
the watch works without an API key. A reopen never edits the ledger; it sets the alert's working
status to REOPENED and the event row says why.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import yaml

from .compute.runner import canonical_json
from .stress.signals import evaluate_signals, level, verdict

FEED_PATH = Path(__file__).resolve().parent.parent / "domain" / "feeds" / "registry_feed.yaml"
WATCHED = ("FILE", "NOT_FILE")


def _sha(obj) -> str:
    return hashlib.sha256(canonical_json(obj).encode()).hexdigest()


@lru_cache(maxsize=None)
def load_feed() -> dict:
    data = yaml.safe_load(FEED_PATH.read_bytes())
    return {"registry": data["registry"], "items": data["items"],
            "sha256": hashlib.sha256(FEED_PATH.read_bytes()).hexdigest()}


def registry_event(item: dict, registry: str | None = None) -> dict:
    """A feed item as a watch cause."""
    return {"cause": "registry_update", "item_id": item["item_id"], "action": item["action"],
            "counterparty": item["counterparty"], "received_on": item.get("received_on"),
            "registry": registry or load_feed()["registry"], "note": item.get("note", "")}


class DecisionWatch:
    def __init__(self, store, runner):
        self.store = store
        self.runner = runner

    # ── public ───────────────────────────────────────────────────────────────
    def standing_decisions(self) -> list[dict]:
        return [d for d in self.store.latest_decisions() if d["DISPOSITION"] in WATCHED]

    def apply(self, cause: dict) -> list[dict]:
        """Apply one change to every standing decision it touches. Returns the event rows
        (newly recorded or already recorded); decisions it does not touch get no row."""
        out = []
        for d in self.standing_decisions():
            if cause["cause"] == "rule_change":
                ev = self._rule_change(d, cause)
            else:
                ev = self._recheck(d, cause)
            if ev is not None:
                out.append(ev)
        return out

    def run_feed(self, items: list[dict] | None = None) -> dict:
        """Process feed items in order, then record a watch pass on every standing decision so
        'was it re-checked?' has an answer even when nothing touched it."""
        feed = load_feed()
        items = feed["items"] if items is None else items
        events = [ev for item in items for ev in self.apply(registry_event(item, feed["registry"]))]
        passes = [self._watch_pass(d, feed, [i["item_id"] for i in items])
                  for d in self.standing_decisions()]
        return {"events": events, "passes": passes}

    # ── internals ────────────────────────────────────────────────────────────
    def _base(self, decision: dict) -> tuple[dict | None, dict | None]:
        meta = _json(decision.get("METADATA_JSON"))
        run_id = meta.get("compute_run_id")
        run = self.store.get_compute_run(run_id) if run_id else None
        if not run or not run.get("INPUT_JSON"):
            return None, None
        return run, json.loads(run["INPUT_JSON"])

    def _recheck(self, decision: dict, cause: dict) -> dict | None:
        run, inputs = self._base(decision)
        txns = (inputs or {}).get("transactions")
        if txns is None:
            txns = self.store.transactions_for(decision["ALERT_ID"])
        if not _touches(cause, decision, txns):
            return None
        if run is None:
            return self._record(decision, cause, None, None, "needs_review", {
                "reason": "the decision cites no saved calculator run, so it cannot be re-checked "
                          "deterministically; review it by hand",
                "trigger": _trigger_label(cause)})

        changed = _apply_change(txns, cause)
        rerun = self.runner.run(decision["ALERT_ID"], changed, inputs.get("params") or {},
                                parent_run_id=run["RUN_ID"],
                                hypothesis=[{"watch_cause": _cause_core(cause)}])
        before_sigs = evaluate_signals(json.loads(run["OUTPUT_JSON"]).get("facts", []))
        after_sigs = evaluate_signals(rerun["facts"])
        v0, v1 = verdict(before_sigs), verdict(after_sigs)
        disp = decision["DISPOSITION"]
        if disp == "NOT_FILE" and v1 == "HIGH" and v0 != "HIGH":
            outcome = "reopened"
        elif disp == "FILE" and level(v1) < level(v0):
            outcome = "needs_review"
        elif disp == "NOT_FILE" and level(v1) > level(v0):
            outcome = "needs_review"
        else:
            outcome = "holds"
        named = self._named_at_decision(decision, cause)
        detail = {
            "disposition": disp, "verdict_before": v0, "verdict_after": v1,
            "fired_before": [s.signal_id for s in before_sigs if s.fired],
            "fired_after": [s.signal_id for s in after_sigs if s.fired],
            "trigger": _trigger_label(cause), "named_at_decision": named,
            "reason": _reason(outcome, disp, v0, v1, cause, named),
        }
        ev = self._record(decision, cause, run["RUN_ID"], rerun["run_id"], outcome, detail)
        if outcome == "reopened" and ev.get("status") == "recorded":
            self.store.set_alert_status(decision["ALERT_ID"], "REOPENED")
        return ev

    def _rule_change(self, decision: dict, cause: dict) -> dict | None:
        cited = _json_list(decision.get("RULES_CITED"))
        if cause["rule_id"] not in cited:
            return None
        run, _ = self._base(decision)
        return self._record(decision, cause, run["RUN_ID"] if run else None, None, "needs_review", {
            "disposition": decision["DISPOSITION"], "rule_id": cause["rule_id"],
            "trigger": f"Cited rule {cause['rule_id']} changed at its source",
            "reason": f"The decision cites {cause['rule_id']}, whose source text changed. Re-read "
                      "the rule and confirm the decision still holds."})

    def _watch_pass(self, decision: dict, feed: dict, item_ids: list[str]) -> dict:
        run, _ = self._base(decision)
        cause = {"cause": "watch_pass", "feed_sha256": feed["sha256"], "items": item_ids,
                 "registry": feed["registry"]}
        touched = [e for e in self.store.events_for_decision(decision["DECISION_ID"])
                   if e["CAUSE"] != "watch_pass"]
        return self._record(decision, cause, run["RUN_ID"] if run else None, None, "holds", {
            "disposition": decision["DISPOSITION"],
            "trigger": f"Watch pass over {feed['registry']}",
            "events_so_far": len(touched),
            "reason": "Every feed item was checked against this decision."})

    def _named_at_decision(self, decision: dict, cause: dict) -> bool:
        """Was this exact change a reopen trigger in a stress test recorded before the decision?"""
        if cause.get("cause") != "registry_update" or cause.get("action") != "flag":
            return False
        hid = f"FLAG:{cause['counterparty']}"
        for ev in self.store.evidence_for_alert(decision["ALERT_ID"], "stress_test"):
            if ev["CREATED_AT"] > decision["DECISION_MADE_AT"]:
                continue
            report = _json(ev["CONTENT_JSON"])
            if any(t.get("hypotheses") == [hid] for t in report.get("reopen_triggers", [])):
                return True
        return False

    def _record(self, decision, cause, base_run_id, rerun_id, outcome, detail) -> dict:
        core = _cause_core(cause)
        cause_sha = _sha(core)
        outcome_sha = _sha({"cause": core, "outcome": outcome, "detail": detail})
        return self.store.append_event({
            "EVENT_ID": f"EVT-{uuid.uuid4().hex[:12]}",
            "DECISION_ID": decision["DECISION_ID"], "ALERT_ID": decision["ALERT_ID"],
            "CAUSE": cause["cause"], "CAUSE_JSON": cause, "CAUSE_SHA256": cause_sha,
            "BASE_RUN_ID": base_run_id, "RERUN_ID": rerun_id, "OUTCOME": outcome,
            "OUTCOME_JSON": detail, "OUTCOME_SHA256": outcome_sha,
            "CREATED_AT": datetime.now(timezone.utc).isoformat(),
        })


# ── helpers ──────────────────────────────────────────────────────────────────
def _json(v) -> dict:
    if isinstance(v, dict):
        return v
    try:
        out = json.loads(v or "{}")
        return out if isinstance(out, dict) else {}
    except (TypeError, ValueError):
        return {}


def _json_list(v) -> list:
    if isinstance(v, list):
        return v
    try:
        out = json.loads(v or "[]")
        return out if isinstance(out, list) else []
    except (TypeError, ValueError):
        return []


def _cause_core(cause: dict) -> dict:
    """The identity of a change: what changed, not when it was processed."""
    keys = {"registry_update": ("cause", "item_id", "action", "counterparty", "registry"),
            "new_transaction": ("cause", "alert_id", "transaction"),
            "rule_change": ("cause", "rule_id", "change_ref"),
            "watch_pass": ("cause", "feed_sha256", "items", "registry")}[cause["cause"]]
    return {k: cause.get(k) for k in keys}


def _touches(cause: dict, decision: dict, txns: list[dict]) -> bool:
    if cause["cause"] == "registry_update":
        return any(t.get("counterparty") == cause["counterparty"] for t in txns)
    if cause["cause"] == "new_transaction":
        return cause.get("alert_id") == decision["ALERT_ID"]
    return False


def _apply_change(txns: list[dict], cause: dict) -> list[dict]:
    if cause["cause"] == "new_transaction":
        return [dict(t) for t in txns] + [dict(cause["transaction"])]
    flag = cause["action"] == "flag"
    return [dict(t, is_flagged=flag) if t.get("counterparty") == cause["counterparty"] else dict(t)
            for t in txns]


def _trigger_label(cause: dict) -> str:
    if cause["cause"] == "registry_update":
        verb = "flagged" if cause["action"] == "flag" else "flag withdrawn"
        return f"'{cause['counterparty']}' {verb} on {cause.get('registry', 'a registry')}"
    if cause["cause"] == "new_transaction":
        t = cause["transaction"]
        return f"New transaction {t.get('txn_id')} on the account"
    return cause["cause"]


def _reason(outcome, disp, v0, v1, cause, named) -> str:
    trig = _trigger_label(cause)
    if outcome == "reopened":
        return (f"{trig}. Re-run on the recorded inputs: {v0} -> {v1}. The closure no longer "
                "holds; reopen and review." + (" This was a reopen trigger named when the "
                                                "decision was made." if named else ""))
    if outcome == "needs_review" and disp == "FILE":
        return (f"{trig}. Re-run on the recorded inputs: {v0} -> {v1}. A fact this FILE rested "
                "on has moved; check the Ground of Suspicion still stands.")
    if outcome == "needs_review":
        return (f"{trig}. Re-run on the recorded inputs: {v0} -> {v1}. The case is stronger "
                "than when it was closed, but not at HIGH; review it.")
    return f"{trig}. Re-run on the recorded inputs: {v0} -> {v1}. The decision holds."


# ── read models for the UI (pure; tested in tests/test_watch.py) ─────────────
OPEN_OUTCOMES = ("reopened", "needs_review")


def alert_reasons(store, alert_id: str) -> list[dict]:
    """Why an alert is back in front of the officer: the latest open watch outcome on its
    standing decision, and earlier closures on the same customer (a ledger count, D1)."""
    out = []
    standing = [d for d in store.latest_decisions() if d["ALERT_ID"] == alert_id]
    if standing:
        d = standing[0]
        events = [e for e in store.events_for_decision(d["DECISION_ID"]) if e["CAUSE"] != "watch_pass"]
        open_ = [e for e in events if e["OUTCOME"] in OPEN_OUTCOMES]
        if open_:
            e = open_[-1]
            detail = _json(e["OUTCOME_JSON"])
            label = "Reopened" if e["OUTCOME"] == "reopened" else "Needs review"
            out.append({"kind": e["OUTCOME"], "text": f"{label}: {detail.get('trigger', e['CAUSE'])}",
                        "event_id": e["EVENT_ID"]})
    panels = store.evidence_for_alert(alert_id, "tier_panel")
    if panels and _json(panels[-1]["CONTENT_JSON"]).get("contested"):
        # Which way the models lean is not shown here (anti-anchoring); it is in the AI section.
        out.append({"kind": "contested", "text": "Contested: needs your judgement",
                    "evidence_id": panels[-1]["EVIDENCE_ID"]})
    alert = store.get_alert(alert_id) or {}
    cust = (standing[0]["CUSTOMER_REF"] if standing else None) or alert.get("CUSTOMER_REF")
    if cust:
        closures = [c for c in store.closures_for_customer(cust) if c["ALERT_ID"] != alert_id]
        if closures:
            out.append({"kind": "repeat_closure",
                        "text": f"{len(closures)} earlier closure(s) on this customer",
                        "query": "DECISION_LEDGER where CUSTOMER_REF matches and DISPOSITION = "
                                 "NOT_FILE, other alerts"})
    return out


def timeline(store, alert_id: str) -> list[dict]:
    """Every decision on the alert and every event after it, oldest first."""
    nodes = []
    for d in store.query("SELECT * FROM DECISION_LEDGER WHERE ALERT_ID = ? ORDER BY SEQ",
                         (alert_id,)):
        nodes.append({"type": "decision", "at": d["DECISION_MADE_AT"], "id": d["DECISION_ID"],
                      "disposition": d["DISPOSITION"], "hash": d["ROW_HASH"],
                      "run_id": _json(d["METADATA_JSON"]).get("compute_run_id")})
        for e in store.events_for_decision(d["DECISION_ID"]):
            detail = _json(e["OUTCOME_JSON"])
            nodes.append({"type": "event", "at": e["CREATED_AT"], "id": e["EVENT_ID"],
                          "cause": e["CAUSE"], "outcome": e["OUTCOME"], "detail": detail,
                          "rerun_id": e["RERUN_ID"], "base_run_id": e["BASE_RUN_ID"],
                          "hash": e["ROW_HASH"]})
    return nodes


DEMO_RATIONALES = {
    "ALERT-16": ("NOT_FILE",
                 "Credits are family support and one hospital payment backed by an invoice on file; "
                 "the senders are KYC-linked family members and no counterparty is on a registry."),
    "ALERT-01": ("FILE",
                 "Debits went to the I4C-flagged handle C within days of credits from unknown UPI "
                 "handles, a pass-through pattern inconsistent with the declared salary."),
}


def scratch_twins():
    """A seeded in-memory store with the twins recorded (a stress test first, then the decision
    with its calculator run), for the guided walkthrough. Nothing touches the real ledger."""
    from .bootstrap import compute_params, open_store
    from .compute import ComputeRunner
    from .skills import POE_FACTORS, CoPilotSkills
    from .stress import StressTester

    store = open_store(":memory:")
    runner = ComputeRunner(store)
    poe = [{"factor_id": f, "factor_name": n, "assessment": "clear"} for f, n in POE_FACTORS]
    for alert_id, (disp, text) in DEMO_RATIONALES.items():
        txns, params = store.transactions_for(alert_id), compute_params(store, alert_id)
        StressTester(runner, store).run(alert_id, txns, params, disposition=disp)
        run = runner.run(alert_id, txns, params)
        a = store.get_alert(alert_id)
        CoPilotSkills(store).alert_disposition_recorder(
            alert_id=alert_id, customer_ref=a["CUSTOMER_REF"], disposition=disp,
            rationale_text=text, rules_cited=json.loads(a["RULES_CITED"]), rfi_triggers=[],
            poe_assessment=poe, compute_run_id=run["run_id"], decision_maker_id="DEMO-PO",
            decision_maker_basis="scratch walkthrough (not a real decision)")
    return store, runner
