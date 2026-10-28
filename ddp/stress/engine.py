"""
Decision Stress Test — "what does this decision rest on, and what would change it?"

1. Run the calculator of record on the case (base run) and derive deterministic signals.
2. Generate counter-hypotheses (ddp.stress.hypotheses) aimed at the proposed disposition:
     FILE      -> hypotheses that could weaken it (explain a txn, unflag a counterparty)
     NOT_FILE  -> hypotheses that could strengthen the case (flag a counterparty)
3. Re-run the SAME hashed program on each hypothesis set as a branch run. Every branch is a
   full COMPUTE_RUNS row with PARENT_RUN_ID = base run and HYPOTHESIS_JSON, so each "what if"
   is as reproducible as the decision itself.
4. Search for MINIMAL flip sets (no proper subset flips), smallest first, under a run budget.

Output, all of it computed (no model arithmetic):
  * load-bearing evidence for a FILE: the facts the Ground of Suspicion must document
  * reopen triggers for a NOT_FILE: the future events that should reopen the alert
  * robustness: how many single counter-hypotheses the decision survives

An optional Nemotron memo (triage tier) turns the report into prose. Any number in it that is not
a transaction amount or a base-run fact value rejects the memo (fail closed to the
deterministic summary).
"""

from __future__ import annotations

import json
import re
import time
from itertools import combinations

from ..money import rupee_evidence, unsupported_money
from .hypotheses import Hypothesis, apply, challenges_to_close, challenges_to_file
from .signals import HEURISTICS, LEVELS, evaluate_signals, level, verdict

DEFAULT_BUDGET = 64
DEFAULT_MAX_SET = 3


class StressTester:
    def __init__(self, runner, store=None, skills=None):
        self.runner = runner
        self.store = store
        self.skills = skills  # CoPilotSkills, optional — only for the memo

    # ── public ───────────────────────────────────────────────────────────────
    def run(self, alert_id: str, transactions: list[dict], params: dict | None = None, *,
            disposition: str | None = None, max_set_size: int = DEFAULT_MAX_SET,
            budget: int = DEFAULT_BUDGET, with_memo: bool = False, on_progress=None) -> dict:
        t0 = time.monotonic()
        progress = on_progress or (lambda _msg: None)
        params = params or {}
        base = self.runner.run(alert_id, transactions, params)
        base_signals = evaluate_signals(base["facts"])
        base_verdict = verdict(base_signals)
        disposition = (disposition or ("FILE" if base_verdict == "HIGH" else "NOT_FILE")).upper()
        notes: list[str] = []

        if disposition == "FILE":
            mode, hyps = "weaken", challenges_to_file(transactions)
            flips = lambda v: level(v) < level(base_verdict)  # noqa: E731
            if base_verdict != "HIGH":
                notes.append(f"FILE proposed but calculator signals are {base_verdict}: the "
                             "Ground of Suspicion must rest on evidence outside these signals "
                             "(narrative, RFI responses) and say so.")
        else:
            mode, hyps = "strengthen", challenges_to_close(transactions)
            flips = lambda v: v == "HIGH"  # noqa: E731
            if base_verdict == "HIGH":
                notes.append("NOT_FILE proposed against HIGH calculator signals: the closure note "
                             "must document why each fired signal is explained.")
                flips = lambda v: False  # noqa: E731

        branches, flip_sets, runs_used, cache = [], [], 0, {}
        exhausted = False
        for k in range(1, max_set_size + 1):
            for combo in combinations(hyps, k):
                if any(set(f) <= set(combo) for f in flip_sets):
                    continue  # a subset already flips: this set is not minimal
                if runs_used >= budget:
                    exhausted = True
                    break
                txns2 = apply(transactions, combo)
                key = json.dumps(txns2, sort_keys=True, default=str)
                if key in cache:
                    result = cache[key]
                else:
                    run = self.runner.run(alert_id, txns2, params, parent_run_id=base["run_id"],
                                          hypothesis=[h.to_dict() for h in combo])
                    runs_used += 1
                    sigs = evaluate_signals(run["facts"])
                    result = {"run_id": run["run_id"], "verdict": verdict(sigs),
                              "fired": [s.signal_id for s in sigs if s.fired],
                              "backend_run_ref": run["provenance"].get("BACKEND_RUN_REF")}
                    cache[key] = result
                flipped = flips(result["verdict"])
                branches.append({"hypotheses": [h.hid for h in combo], **result,
                                 "flips": flipped})
                if flipped:
                    flip_sets.append(combo)
            if exhausted:
                break

        singles = [b for b in branches if len(b["hypotheses"]) == 1]
        survived = sum(1 for b in singles if not b["flips"])
        hyp_index = {h.hid: h for h in hyps}
        load_bearing = sorted({h.hid for f in flip_sets for h in f})

        report = {
            "alert_id": alert_id,
            "disposition_tested": disposition,
            "mode": mode,
            "base": {"run_id": base["run_id"], "verdict": base_verdict,
                     "signals": [s.to_dict() for s in base_signals],
                     "backend_run_ref": base["provenance"].get("BACKEND_RUN_REF")},
            "hypotheses": [h.to_dict() for h in hyps],
            "branches": branches,
            "minimal_flip_sets": [[h.to_dict() for h in f] for f in flip_sets],
            "smallest_flip_size": min((len(f) for f in flip_sets), default=None),
            # A FILE on LOW signals cannot be lowered and a closure on HIGH cannot be raised, so
            # every challenge "survives" trivially; the count then says nothing (2026-10-28).
            "robustness": {"single_hypotheses": len(singles), "survived": survived,
                           "meaningful": not ((mode == "weaken" and base_verdict == "LOW")
                                              or (mode == "strengthen" and base_verdict == "HIGH"))},
            "load_bearing": [hyp_index[i].to_dict() for i in load_bearing],
            "reopen_triggers": self._reopen_triggers(flip_sets, base_verdict)
            if mode == "strengthen" else [],
            "search": {"max_set_size": max_set_size, "budget": budget, "runs_used": runs_used,
                       "budget_exhausted": exhausted},
            "heuristics": HEURISTICS,
            "levels": LEVELS,
            "notes": notes,
            "latency_s": round(time.monotonic() - t0, 3),
        }
        report["summary"] = deterministic_summary(report)
        progress(f"{runs_used + 1} runs of the calculator of record "
                 f"({len(flip_sets)} minimal flip set(s))")
        if with_memo and self.skills is not None:
            progress("Writing the memo: Nemotron, triage tier (numbers checked after)")
            report["memo"] = self._memo(report, transactions, base["facts"])
            progress(f"Memo {report['memo']['status']}")
        if self.store is not None:
            report["evidence_id"] = self.store.record_evidence(
                alert_id, "stress_test", f"stress_test.v1:{base['run_id']}",
                {k: v for k, v in report.items() if k != "latency_s"},
                {"base_run_id": base["run_id"],
                 "branch_run_ids": sorted({b["run_id"] for b in branches}),
                 "heuristics": HEURISTICS})
        return report

    # ── helpers ──────────────────────────────────────────────────────────────
    @staticmethod
    def _reopen_triggers(flip_sets, base_verdict) -> list[dict]:
        return [{"if": [h.label() for h in f], "hypotheses": [h.hid for h in f],
                 "verdict_change": f"{base_verdict} -> HIGH"} for f in flip_sets]

    def _memo(self, report: dict, transactions: list[dict], facts: list[dict]) -> dict:
        compact = {k: report[k] for k in ("disposition_tested", "mode", "smallest_flip_size",
                                          "robustness", "load_bearing", "reopen_triggers",
                                          "notes", "summary")}
        compact["base_verdict"] = report["base"]["verdict"]
        compact["fired_signals"] = [s["label"] for s in report["base"]["signals"] if s["fired"]]
        prompt = (
            "You are assisting a bank's Principal Officer. Below is a deterministic stress-test "
            "report for an AML alert decision. Write a short memo for the case file.\n"
            "Rules: do not add any number, amount or percentage that is not in the report; do "
            "not state a legal conclusion; plain English.\n"
            'Return ONE JSON object: {"summary": str, "load_bearing_evidence": [str], '
            '"reopen_triggers": [str]}\n\nREPORT:\n' + json.dumps(compact, indent=1))
        try:
            obj, failures = self.skills._complete_structured(prompt, "triage", "stress_memo")
        except Exception as e:  # noqa: BLE001 — memo is optional; fail closed
            return {"status": "unavailable", "reason": str(e)[:200]}
        allowed = allowed_numbers(report, transactions, facts)
        text = " ".join([obj["summary"], *obj["load_bearing_evidence"], *obj["reopen_triggers"]])
        bad = sorted(n for n in numbers_in(text) if n not in allowed)
        bad += unsupported_money(text, rupee_evidence(transactions, facts))
        if bad:
            return {"status": "rejected", "reason": f"ungrounded numbers: {bad[:5]}",
                    "model_call": getattr(self.skills, "last_model_call", None)}
        return {"status": "ok", **obj, "repair_attempts": failures,
                "model_call": getattr(self.skills, "last_model_call", None)}


_NUM = re.compile(r"(?<![A-Za-z0-9-])\d[\d,]*(?:\.\d+)?")


def numbers_in(text: str) -> set[float]:
    out = set()
    for m in _NUM.finditer(text or ""):
        try:
            out.add(float(m.group(0).replace(",", "")))
        except ValueError:
            pass
    return out


def allowed_numbers(report: dict, transactions: list[dict], facts: list[dict]) -> set[float]:
    allowed = {float(t.get("amount_inr") or 0) for t in transactions}
    for f in facts:
        if isinstance(f.get("value"), (int, float)):
            allowed.add(float(f["value"]))
    rob = report["robustness"]
    allowed |= {float(rob["single_hypotheses"]), float(rob["survived"]),
                float(report["smallest_flip_size"] or 0), float(len(report["minimal_flip_sets"]))}
    allowed |= {float(n) for n in range(0, 4)}  # list ordinals / set sizes
    # identifiers carry digits (T01-3, ALERT-01, 2026-08-15): allow every number in the report
    allowed |= numbers_in(json.dumps({k: report[k] for k in ("hypotheses", "alert_id")}))
    return allowed


def deterministic_summary(r: dict) -> str:
    base, rob = r["base"]["verdict"], r["robustness"]
    fired = [s["label"] for s in r["base"]["signals"] if s["fired"]]
    parts = [f"Calculator signals: {base}"
             + (f" ({'; '.join(fired)})." if fired else " (no signal fired).")]
    parts.extend(r["notes"])            # a disposition against the signals is said first
    if r["mode"] == "weaken":
        if r["minimal_flip_sets"]:
            sets = [" + ".join(h["label"] for h in f) for f in r["minimal_flip_sets"][:3]]
            parts.append(f"A FILE here rests on specific evidence. The verdict drops below {base} "
                         f"if: " + " | OR | ".join(sets) + ". Document these in the Ground of "
                         "Suspicion.")
        elif base == "LOW":
            parts.append("The calculator does not support this FILE: the level is already LOW, "
                         "so no counter-hypothesis can lower it.")
        else:
            parts.append(f"No combination of up to {r['search']['max_set_size']} counter-"
                         f"hypotheses lowers the verdict below {base}"
                         + (": the FILE does not hinge on one fact." if base == "HIGH" else "."))
    else:
        if r["reopen_triggers"]:
            parts.append("Reopen this alert if: " + " | OR | ".join(
                " + ".join(t["if"]) for t in r["reopen_triggers"][:3]) + ".")
        elif base == "HIGH":
            parts.append("The calculator does not support this closure: the level is already "
                         "HIGH, so no registry hit can raise it.")
        else:
            parts.append(f"No registry hit on up to {r['search']['max_set_size']} existing "
                         "counterparties would raise the verdict to HIGH.")
    if rob.get("meaningful", True):
        parts.append(f"Survives {rob['survived']} of {rob['single_hypotheses']} single "
                     f"counter-hypotheses; {r['search']['runs_used']} branch runs of the calculator.")
    else:
        parts.append(f"{r['search']['runs_used']} branch runs of the calculator; the count of "
                     "challenges survived is not meaningful here.")
    return " ".join(parts)
