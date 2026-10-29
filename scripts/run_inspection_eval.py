"""
Inspection replay evaluation (T12.9): how many inspector questions does the record answer, for a
Twin Trace record against a cursory closure of the same alert?

    python -m scripts.run_inspection_eval --deterministic   # section 1 only, no model, no key
    python -m scripts.run_inspection_eval                   # + section 2: Nemotron cross-examination

Section 1 (deterministic). For each of the 16 synthetic alerts, two records are written to two
fresh in-memory stores:
  cursory     the pattern FIU-IND's UBI 13/2024 order describes: a one-line closure, no calculator
              run, no stress test, no rules, no factor assessment
  twin trace  what the product records WITHOUT a model: stress test, calculator run, the scenario's
              gold draft (or the demo closure for ALERT-16) as the rationale, the alert's rules
The question bank is put to both. No factor assessment is recorded in either (that needs a model),
so IQ-08 is unanswered in both, and the officer is self-asserted in both.

Section 2 (live). Nemotron (reasoning tier; the Ground of Suspicion drafter is the disposition
tier) cross-examines each Twin Trace record. Reported: findings, how many it marked answered with
valid citations, and how many citations code rejected.

Writes evals/INSPECTION-<date>-<mode>.md and .json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ddp.bootstrap import compute_params, open_store  # noqa: E402
from ddp.compute import ComputeRunner  # noqa: E402
from ddp.config import get_settings  # noqa: E402
from ddp.enforcement import question_bank  # noqa: E402
from ddp.evidence_view import seed_fingerprint  # noqa: E402
from ddp.inspection import cross_examine, inspect_decision  # noqa: E402
from ddp.llm import TokenFactoryClient  # noqa: E402
from ddp.skills import CoPilotSkills  # noqa: E402
from ddp.stress import StressTester  # noqa: E402
from ddp.watch import DEMO_RATIONALES  # noqa: E402

SCENARIOS = ROOT / "domain" / "scenarios"
CURSORY = "Reviewed; activity consistent with profile. Closed."


def gold_drafts() -> dict[str, str]:
    out = {}
    for f in sorted(SCENARIOS.glob("[01][0-9]-*.md")):
        n = int(f.name[:2])
        if 1 <= n <= 15:
            m = re.search(r"^### \d+\. Draft [^\n]*\n(.*?)(?=^### |\Z)", f.read_text(), re.M | re.S)
            if m:
                out[f"ALERT-{n:02d}"] = m.group(1).strip()
    out["ALERT-16"] = DEMO_RATIONALES["ALERT-16"][1]
    return out


def _record(store, alert_id, text, *, full: bool):
    a = store.get_alert(alert_id)
    disp = {"CONTESTED": "FILE"}.get(a["GOLD_DISPOSITION"], a["GOLD_DISPOSITION"])
    run_id = None
    if full:
        runner = ComputeRunner(store)
        txns, params = store.transactions_for(alert_id), compute_params(store, alert_id)
        StressTester(runner, store).run(alert_id, txns, params, disposition=disp)
        run_id = runner.run(alert_id, txns, params)["run_id"]
    return CoPilotSkills(store).alert_disposition_recorder(
        alert_id=alert_id, customer_ref=a["CUSTOMER_REF"],
        disposition=disp if full else "NOT_FILE", rationale_text=text,
        rules_cited=json.loads(a["RULES_CITED"]) if full else [], rfi_triggers=[],
        poe_assessment=[], compute_run_id=run_id)["decision_id"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deterministic", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "evals"))
    args = ap.parse_args(argv)
    settings = get_settings()
    live = not args.deterministic
    if live and not settings.llm_configured:
        print("NEBIUS_API_KEY not set; use --deterministic.")
        return 2
    drafts, rows, t0 = gold_drafts(), [], time.monotonic()
    for alert_id, text in drafts.items():
        s_full, s_cur = open_store(":memory:"), open_store(":memory:")
        d_full = _record(s_full, alert_id, text, full=True)
        d_cur = _record(s_cur, alert_id, CURSORY, full=False)
        full = inspect_decision(s_full, d_full, record=False)
        cur = inspect_decision(s_cur, d_cur, record=False)
        row = {"alert_id": alert_id,
               "twin_trace": {"answered": full["answered"], "asked": full["asked"],
                              "status": {r["id"]: r["status"] for r in full["results"]}},
               "cursory": {"answered": cur["answered"], "asked": cur["asked"],
                           "status": {r["id"]: r["status"] for r in cur["results"]}}}
        if live:
            x = cross_examine(CoPilotSkills(s_full, llm=TokenFactoryClient(settings)), s_full,
                              d_full, full)
            row["cross_examination"] = {
                "status": x["status"], "reason": x.get("reason"),
                "findings": len(x["accepted"]) + len(x["rejected"]),
                "answered_with_valid_citations": sum(1 for f in x["accepted"] if f["answered"]),
                "not_answered": sum(1 for f in x["accepted"] if not f["answered"]),
                "rejected": len(x["rejected"]),
                "questions": [f["question"] for f in x["accepted"] if not f["answered"]][:5],
                "model": (x.get("model_call") or {}).get("model_reported")}
        rows.append(row)
        print(alert_id, row["twin_trace"]["answered"], row["cursory"]["answered"],
              row.get("cross_examination", {}).get("status", ""), flush=True)
    now = datetime.now(timezone.utc)
    mode = "live" if live else "deterministic"
    qb = question_bank()
    per_q = {q["id"]: {"twin_trace": sum(1 for r in rows if r["twin_trace"]["status"][q["id"]] == "answered"),
                       "cursory": sum(1 for r in rows if r["cursory"]["status"][q["id"]] == "answered")}
             for q in qb["questions"]}
    rep = {"mode": mode, "generated_at": now.isoformat(timespec="seconds"),
           "seed_sha256": seed_fingerprint(), "bank_sha256": qb["sha256"],
           "inspector_model": settings.models.get("reasoning") if live else None,
           "alerts": len(rows), "per_question": per_q, "rows": rows,
           "wall_seconds": round(time.monotonic() - t0, 1)}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = out / f"INSPECTION-{now:%Y-%m-%d}-{mode}"
    stem.with_suffix(".json").write_text(json.dumps(rep, indent=1, default=str))
    stem.with_suffix(".md").write_text(_markdown(rep, qb))
    print(f"wrote {stem}.md")
    return 0


def _markdown(rep, qb) -> str:
    n = rep["alerts"]
    lines = [f"# Inspection replay — {rep['generated_at']} ({rep['mode']})", "",
             f"Seed `{rep['seed_sha256'][:16]}…` · question bank `{rep['bank_sha256'][:16]}…` · "
             f"{n} synthetic alerts · {rep['wall_seconds']} s", "",
             "Questions are this project's, derived from FIU-IND Section 13 orders "
             "(`domain/enforcement/`); they are not an FIU-IND checklist. Records are synthetic. "
             "Neither record has a factor assessment (it needs a model) and both officers are "
             "self-asserted, so IQ-07 and IQ-08 are not answered in either.", "",
             "| Question | Twin Trace record answers | Cursory closure answers |", "|---|---|---|"]
    for q in qb["questions"]:
        p = rep["per_question"][q["id"]]
        lines.append(f"| {q['id']} {q['text']} | {p['twin_trace']} / {n} | {p['cursory']} / {n} |")
    tt = sum(r["twin_trace"]["answered"] for r in rep["rows"])
    cu = sum(r["cursory"]["answered"] for r in rep["rows"])
    a_tt = sum(r["twin_trace"]["asked"] for r in rep["rows"])
    a_cu = sum(r["cursory"]["asked"] for r in rep["rows"])
    lines += ["", f"Total answered: Twin Trace {tt} / {a_tt}; cursory {cu} / {a_cu} (questions "
              "that do not apply, such as IQ-03 when the reasoning cites no amount, are not "
              "counted).", ""]
    if rep["mode"] == "live":
        xs = [r["cross_examination"] for r in rep["rows"]]
        ok = [x for x in xs if x["status"] == "ok"]
        lines += [f"## Cross-examination (live, `{rep['inspector_model']}`)", "",
                  f"Ran on {len(ok)} / {n} records. Findings {sum(x['findings'] for x in ok)}; "
                  f"marked answered with valid citations "
                  f"{sum(x['answered_with_valid_citations'] for x in ok)}; not answered by the "
                  f"record {sum(x['not_answered'] for x in ok)}; rejected by the citation checker "
                  f"{sum(x['rejected'] for x in ok)}.", "",
                  "| Alert | Findings | Answered (valid cites) | Not answered | Rejected |",
                  "|---|---|---|---|---|"]
        for r in rep["rows"]:
            x = r["cross_examination"]
            lines.append(f"| {r['alert_id']} | {x['findings']} | {x['answered_with_valid_citations']}"
                         f" | {x['not_answered']} | {x['rejected']} |" if x["status"] == "ok"
                         else f"| {r['alert_id']} | {x['status']}: {x['reason']} | | | |")
        lines += ["", "Questions the model said the record does not answer (first alert with any):"]
        first = next((r for r in rep["rows"] if r["cross_examination"].get("questions")), None)
        if first:
            lines += [f"- {first['alert_id']}: {q}" for q in first["cross_examination"]["questions"]]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
