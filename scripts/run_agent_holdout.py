"""
The agentic investigator on the frozen holdout (evals/holdout/HOLDOUT-v1.json, 6 cases), scored
against the author-assigned expected disposition (2026-10-28, item 4).

    python -m scripts.run_agent_holdout --mock          # offline: exercises the runner
    python -m scripts.run_agent_holdout --out evals/agent-holdout-2026-10-28-before-1

Each case is loaded into an in-memory store as an alert with its transactions. The agent sees the
same tools as on the development set; the expected disposition is never stored where get_case can
return it. Writes AGENT-HOLDOUT-<date>-<mode>.{md,json} with the dataset and agent-prompt SHA-256,
so runs before and after a prompt change can be told apart from the files alone. Labels are
author-assigned, not expert ground truth: report counts, not accuracy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ddp import agent as A  # noqa: E402
from ddp.agent import Investigator  # noqa: E402
from ddp.bootstrap import compute_params, open_store  # noqa: E402
from ddp.compute import ComputeRunner  # noqa: E402
from ddp.config import get_settings  # noqa: E402
from ddp.llm import TokenFactoryClient  # noqa: E402
from ddp.skills import CoPilotSkills  # noqa: E402
from scripts.run_live_eval import MockLLM  # noqa: E402

HOLDOUT = ROOT / "evals" / "holdout" / "HOLDOUT-v1.json"


def load_cases(store, cases: list[dict]) -> None:
    """Holdout cases as alerts (no gold label in the store) plus their transactions."""
    alerts, txns = [], []
    for c in cases:
        cust = f"CUST-{c['id']}"
        dates = sorted(t["date"] for t in c["transactions"])
        alerts.append({"ALERT_ID": c["id"], "SCENARIO_ID": c["id"], "CUSTOMER_REF": cust,
                       "ALERT_DATE": dates[-1], "ALERT_TYPE": c["alert_type"],
                       "SIGNAL_SOURCE": c["signal_source"], "ACCOUNT_TYPE": "SAVINGS",
                       "CUSTOMER_PROFILE": c["customer_profile"],
                       "ALERT_AMOUNT_INR": sum(t["amount_inr"] for t in c["transactions"]
                                               if t["type"] == "CREDIT"),
                       "ALERT_NARRATIVE": c["alert_narrative"], "RFI_TRIGGERS": [],
                       "POE_FACTORS": [], "RULES_CITED": [], "GOLD_DISPOSITION": "UNSET (holdout)",
                       "ALERT_STATUS": "OPEN"})
        txns += [{"TXN_ID": t["txn_id"], "ALERT_ID": c["id"], "CUSTOMER_REF": cust,
                  "TXN_DATE": t["date"], "TXN_TYPE": t["type"], "AMOUNT_INR": t["amount_inr"],
                  "CHANNEL": t.get("channel"), "COUNTERPARTY": t.get("counterparty"),
                  "IS_FLAGGED": bool(t.get("is_flagged"))} for t in c["transactions"]]
    store.upsert_alerts(alerts)
    store.upsert_transactions(txns)


def _git_rev() -> str:
    """Short HEAD, marked when ddp/ or scripts/ have uncommitted changes (the code that ran)."""
    try:
        rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True).stdout.strip() or "unknown"
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "ddp", "scripts"], cwd=ROOT,
                               capture_output=True, text=True).stdout.strip()
        return rev + ("+uncommitted" if dirty else "")
    except OSError:
        return "unknown"


def summarise(rows: list[dict]) -> dict:
    clear = [r for r in rows if r["expected"] in ("FILE", "NOT_FILE")]
    contested = [r for r in rows if r["expected"] == "CONTESTED"]
    return {"cases": len(rows),
            "submitted": sum(1 for r in rows if r["agent"] == "submitted"),
            "clear_agree": sum(1 for r in clear if r["agent_disp"] == r["expected"]),
            "clear_cases": len(clear),
            "contested": len(contested),
            "contested_filed": sum(1 for r in contested if r["agent_disp"] == "FILE"),
            "contested_dispositions": {d: sum(1 for r in contested if r["agent_disp"] == d)
                                       for d in ("FILE", "NOT_FILE", "NEEDS_MORE_INFO", None)},
            "rejections": sum(r["agent_rejections"] for r in rows)}


def render(config: dict, rows: list[dict], s: dict) -> str:
    lines = [f"# Agent on the holdout — {config['started_utc'][:16]} UTC ({config['mode'].upper()})",
             ""]
    if config["mode"] == "mock":
        lines += ["> **MOCK RUN.** Scripted model; says nothing about Nemotron.", ""]
    lines += [f"- Dataset: `{config['dataset']}` (sha256 `{config['dataset_sha256'][:12]}…`), "
              f"{s['cases']} synthetic cases; labels author-assigned, not expert ground truth",
              f"- Agent prompt sha256 `{config['agent_prompt_sha256'][:12]}…` · code `{config['git_rev']}`",
              f"- Models: `{json.dumps(config['models'])}`", "",
              f"Clear cases agreeing with the expected disposition: **{s['clear_agree']} of "
              f"{s['clear_cases']}** · contested cases filed: **{s['contested_filed']} of "
              f"{s['contested']}** · rejected submissions: **{s['rejections']}**.", "",
              "| case | expected | status | agent | tool calls | rejected | tokens | seconds |",
              "|---|---|---|---|---|---|---|---|"]
    lines += [f"| {r['case']} | {r['expected']} | {r['agent']} | {r['agent_disp'] or '—'} | "
              f"{r['agent_steps']} | {r['agent_rejections']} | {r['agent_tokens']} | {r['agent_s']} |"
              for r in rows]
    lines += ["", "Reproduce: `python -m scripts.run_agent_holdout" + (" --mock" if config["mode"] == "mock"
                                                                      else "") + "`.", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "evals"))
    args = ap.parse_args(argv)
    settings = get_settings()
    if not args.mock and not settings.llm_configured:
        print("NEBIUS_API_KEY not set. Use --mock to exercise the runner offline.")
        return 2
    raw = HOLDOUT.read_bytes()
    cases = json.loads(raw)["cases"]
    store = open_store(":memory:")
    load_cases(store, cases)
    runner = ComputeRunner(store)
    llm = MockLLM() if args.mock else TokenFactoryClient(settings)
    skills = CoPilotSkills(store, llm=llm)
    started = datetime.now(timezone.utc)
    rows = []
    for c in cases:
        inv = Investigator(llm, store, skills, runner, lambda x: compute_params(store, x))
        t = inv.investigate(c["id"])
        rows.append({"case": c["id"], "expected": c["expected"], "agent": t["status"],
                     "agent_disp": (t.get("assessment") or {}).get("disposition"),
                     "agent_steps": len(t["steps"]), "agent_rejections": t.get("rejections", 0),
                     "agent_tokens": sum((t.get("tokens") or {}).values()),
                     "agent_s": t.get("latency_s")})
        print(json.dumps(rows[-1]))
    mode = "mock" if args.mock else "live"
    config = {"mode": mode, "started_utc": started.isoformat(), "dataset": HOLDOUT.name,
              "dataset_sha256": hashlib.sha256(raw).hexdigest(),
              "agent_prompt_sha256": hashlib.sha256(A.SYSTEM.encode()).hexdigest(),
              "stress_engine_sha256": hashlib.sha256(
                  (ROOT / "ddp" / "stress" / "engine.py").read_bytes()).hexdigest(),
              "git_rev": _git_rev(), "models": settings.models if mode == "live" else {}}
    s = summarise(rows)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = started.strftime("%Y-%m-%d")
    (out / f"AGENT-HOLDOUT-{stamp}-{mode}.json").write_text(
        json.dumps({**config, "summary": s, "rows": rows}, indent=1, default=str))
    (out / f"AGENT-HOLDOUT-{stamp}-{mode}.md").write_text(render(config, rows, s))
    print(render(config, rows, s))
    print(f"wrote {out}/AGENT-HOLDOUT-{stamp}-{mode}.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
