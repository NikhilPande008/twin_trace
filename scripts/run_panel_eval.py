"""
Tier panel evaluation (T12.7): does disagreement between Nemotron Nano, Super and Ultra pick out the
cases labelled CONTESTED?

    python -m scripts.run_panel_eval --mock          # offline harness self-test (stamped MOCK)
    python -m scripts.run_panel_eval                 # live: 16 dev alerts + 6 holdout cases

For every case the three tiers assess the same 11-factor prompt in parallel. The panel is
"contested" when the tiers' recommendations differ (deterministic, ddp.panel). Reported as counts
against the author-assigned labels (not expert ground truth):

  contested caught      CONTESTED cases the panel marked contested
  false alarms          clear (FILE / NOT_FILE) cases the panel marked contested
  unanimous and right   clear cases where every answering tier recommended the gold disposition
  failures              tiers that did not answer

Writes evals/PANEL-<date>-<mode>.md and .json with the seed and holdout SHA-256 and the models.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ddp.bootstrap import (compute_params, open_store, parse_declared_annual_income,  # noqa: E402
                           parse_declared_monthly_income)
from ddp.compute import ComputeRunner  # noqa: E402
from ddp.config import get_settings  # noqa: E402
from ddp.evidence_view import seed_fingerprint  # noqa: E402
from ddp.llm import TokenFactoryClient  # noqa: E402
from ddp.panel import TIERS, TierPanel  # noqa: E402
from ddp.skills import CoPilotSkills  # noqa: E402
from ddp.stress import StressTester  # noqa: E402
from ddp.structured import POE_IDS  # noqa: E402

HOLDOUT = ROOT / "evals" / "holdout" / "HOLDOUT-v1.json"


class MockTierLLM:
    """Scripted for --mock: Nano triggers more factors than Super and Ultra, so some cases split.
    Says nothing about Nemotron."""

    def __init__(self):
        self.last_call = {}

    def complete(self, prompt, tier="reasoning", **_):
        self.last_call = {"provider": "mock", "tier": tier, "model_requested": f"mock-{tier}",
                          "usage": {"prompt_tokens": 0, "completion_tokens": 0}}
        n = {"triage": 3, "reasoning": 3, "disposition": 2}[tier] if "I4C" in prompt else 0
        return json.dumps({"factors": [
            {"factor_id": f, "factor_name": f, "assessment": "triggered" if i < n else "clear",
             "evidence": "mock", "evidence_txn_ids": [], "rules_cited": []}
            for i, f in enumerate(POE_IDS)]})


def _cases(store) -> list[dict]:
    out = []
    for a in store.query("SELECT * FROM ALERTS ORDER BY ALERT_ID"):
        out.append({"set": "dev", "id": a["ALERT_ID"], "gold": a["GOLD_DISPOSITION"],
                    "alert_id": a["ALERT_ID"], "transactions": store.transactions_for(a["ALERT_ID"]),
                    "params": compute_params(store, a["ALERT_ID"]),
                    "case": {"customer_kyc": a["CUSTOMER_PROFILE"],
                             "transactions": store.transactions_for(a["ALERT_ID"]),
                             "signal_tags": json.loads(a["RFI_TRIGGERS"] or "[]"),
                             "alert_narrative": a["ALERT_NARRATIVE"]}})
    hold = json.loads(HOLDOUT.read_text())
    for c in hold["cases"]:
        params = compute_params(store)
        m = parse_declared_monthly_income(c["customer_profile"])
        y = parse_declared_annual_income(c["customer_profile"])
        if m:
            params["declared_monthly_income_inr"] = {"amount_inr": m, "source": c["id"]}
        if y:
            params["declared_annual_income_inr"] = {"amount_inr": y, "source": c["id"]}
        out.append({"set": "holdout", "id": c["id"], "gold": c["expected"], "alert_id": c["id"],
                    "transactions": c["transactions"], "params": params,
                    "case": {"customer_kyc": c["customer_profile"],
                             "transactions": c["transactions"],
                             "signal_tags": [c.get("signal_source") or ""],
                             "alert_narrative": c["alert_narrative"]}})
    return out


def _summary(rows: list[dict], subset: str) -> dict:
    rs = [r for r in rows if r["set"] == subset]
    contested = [r for r in rs if r["gold"] == "CONTESTED"]
    clear = [r for r in rs if r["gold"] in ("FILE", "NOT_FILE")]
    return {
        "cases": len(rs),
        "contested_labelled": len(contested),
        "contested_caught": sum(1 for r in contested if r["contested"]),
        "clear_labelled": len(clear),
        "false_alarms": sum(1 for r in clear if r["contested"]),
        "unanimous_and_right": sum(1 for r in clear if r["unanimous"] == r["gold"]),
        "incomplete": sum(1 for r in rs if not r["complete"]),
        "tier_failures": sum(len(r["tiers_failed"]) for r in rs),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--only", default="", help="comma-separated case ids")
    ap.add_argument("--out", default=str(ROOT / "evals"))
    args = ap.parse_args(argv)
    settings = get_settings()
    if not args.mock and not settings.llm_configured:
        print("NEBIUS_API_KEY not set; use --mock for the offline self-test.")
        return 2
    store = open_store(":memory:")
    runner = ComputeRunner(store)
    tester = StressTester(runner, store)
    make = ((lambda: CoPilotSkills(store, llm=MockTierLLM())) if args.mock
            else (lambda: CoPilotSkills(store, llm=TokenFactoryClient(settings))))
    panel = TierPanel(make)
    only = {x for x in args.only.split(",") if x}
    rows, t0 = [], time.monotonic()
    for c in _cases(store):
        if only and c["id"] not in only:
            continue
        stress = tester.run(c["alert_id"], c["transactions"], c["params"])
        r = panel.run(c["case"], stress_report=stress)
        rows.append({"set": c["set"], "id": c["id"], "gold": c["gold"],
                     "recommendations": r["recommendations"], "contested": r["contested"],
                     "unanimous": r["unanimous"], "complete": r["complete"],
                     "tiers_failed": r["tiers_failed"], "split_factors": r["split_factors"],
                     "splitting_fact": r["splitting_fact"], "errors": r["errors"],
                     "seconds": r["seconds"], "calls": r["calls"]})
        print(f"{c['id']:9} gold={c['gold']:9} recs={r['recommendations']} "
              f"contested={r['contested']}", flush=True)
    now = datetime.now(timezone.utc)
    mode = "mock" if args.mock else "live"
    tokens = {t: sum(((r["calls"].get(t) or {}).get("usage") or {}).get("completion_tokens") or 0
                     for r in rows) for t in TIERS}
    report = {
        "mode": mode, "generated_at": now.isoformat(timespec="seconds"),
        "seed_sha256": seed_fingerprint(),
        "holdout_sha256": hashlib.sha256(HOLDOUT.read_bytes()).hexdigest(),
        "models": ({t: f"mock-{t}" for t in TIERS} if args.mock else settings.models),
        "tiers": list(TIERS),
        "summary": {"dev": _summary(rows, "dev"), "holdout": _summary(rows, "holdout")},
        "completion_tokens_by_tier": tokens,
        "wall_seconds": round(time.monotonic() - t0, 1),
        "rows": rows,
    }
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = out / f"PANEL-{now:%Y-%m-%d}-{mode}"
    stem.with_suffix(".json").write_text(json.dumps(report, indent=1, default=str))
    stem.with_suffix(".md").write_text(_markdown(report))
    print(f"wrote {stem}.md")
    return 0


def _markdown(rep: dict) -> str:
    lines = [f"# Tier panel evaluation — {rep['generated_at']} ({rep['mode'].upper()})", ""]
    if rep["mode"] == "mock":
        lines += ["**MOCK: scripted model. These numbers test the harness and say nothing about "
                  "Nemotron. Do not quote them.**", ""]
    lines += [f"Seed `{rep['seed_sha256'][:16]}…` · holdout `{rep['holdout_sha256'][:16]}…` · "
              f"wall time {rep['wall_seconds']} s", "",
              "Models: " + ", ".join(f"{t} `{m}`" for t, m in rep["models"].items()), "",
              "Labels are author-assigned (synthetic scenarios), not expert ground truth. "
              "Contested = the tiers' recommendations differ (deterministic count rule over each "
              "tier's 11 factor assessments).", "",
              "| Set | Cases | CONTESTED caught | False alarms on clear cases | Unanimous and "
              "matching gold (clear) | Incomplete panels |", "|---|---|---|---|---|---|"]
    for k, s in rep["summary"].items():
        lines.append(f"| {k} | {s['cases']} | {s['contested_caught']} / {s['contested_labelled']} "
                     f"| {s['false_alarms']} / {s['clear_labelled']} | {s['unanimous_and_right']} "
                     f"/ {s['clear_labelled']} | {s['incomplete']} |")
    lines += ["", "| Case | Gold | Nano | Super | Ultra | Contested | Split factors |",
              "|---|---|---|---|---|---|---|"]
    for r in rep["rows"]:
        rec = r["recommendations"]
        lines.append(f"| {r['id']} | {r['gold']} | {rec.get('triage', 'failed')} | "
                     f"{rec.get('reasoning', 'failed')} | {rec.get('disposition', 'failed')} | "
                     f"{'yes' if r['contested'] else 'no'} | {len(r['split_factors'])} |")
    lines += ["", "Completion tokens by tier: " + ", ".join(
        f"{t} {n}" for t, n in rep["completion_tokens_by_tier"].items()), ""]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
