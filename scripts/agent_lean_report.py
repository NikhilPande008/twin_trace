"""
Before/after comparison for the agent's filing lean (item 4, 2026-10-28), computed from the dated
run files only. Writes evals/AGENT-LEAN-2026-10-28.md.

    python -m scripts.agent_lean_report             # prompt change (item 4)
    python -m scripts.agent_lean_report --framing   # stress-summary framing fix, same prompt
                                                    # → evals/AGENT-FRAMING-2026-10-28.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
DEV = {"before": ["live-2026-10-28-seed", "agent-dev-2026-10-28-before-2"],
       "after": ["agent-dev-2026-10-28-after-1", "agent-dev-2026-10-28-after-2"]}
HOLDOUT = {"before": ["agent-holdout-2026-10-28-before-1", "agent-holdout-2026-10-28-before-2"],
           "after": ["agent-holdout-2026-10-28-after-1", "agent-holdout-2026-10-28-after-2"]}
OUT = EVALS / "AGENT-LEAN-2026-10-28.md"
# Same agent prompt as "before"; only the stress-test summary differs (ddp/stress/engine.py).
FRAMING_DEV = {"before": DEV["before"],
               "framing fix": ["agent-dev-2026-10-28-framing-1", "agent-dev-2026-10-28-framing-2"]}
FRAMING_HOLDOUT = {"before": HOLDOUT["before"],
                   "framing fix": ["agent-holdout-2026-10-28-framing-1",
                                   "agent-holdout-2026-10-28-framing-2"]}
FRAMING_OUT = EVALS / "AGENT-FRAMING-2026-10-28.md"


def dev_run(d: str) -> dict:
    rep = json.loads(next((EVALS / d).glob("REPORT-*-live.json")).read_text())
    rows = rep["rows"]
    clear = [r for r in rows if r["gold"] in ("FILE", "NOT_FILE")]
    cont = [r for r in rows if r["gold"] == "CONTESTED"]
    return {"dir": d, "prompt": rep.get("agent_prompt_sha256", "")[:12],
            "engine": (rep.get("stress_engine_sha256") or "")[:12],
            "clear": f"{sum(r.get('agent_disp') == r['gold'] for r in clear)} / {len(clear)}",
            "contested_filed": f"{sum(r.get('agent_disp') == 'FILE' for r in cont)} / {len(cont)}",
            "contested": ", ".join(f"{r['alert_id']} {r.get('agent_disp')}" for r in cont),
            "missed": ", ".join(f"{r['alert_id']} {r['gold']}→{r.get('agent_disp')}" for r in clear
                                if r.get("agent_disp") != r["gold"]) or "—",
            "rejections": sum(r.get("agent_rejections", 0) for r in rows)}


def holdout_run(d: str) -> dict:
    rep = json.loads(next((EVALS / d).glob("AGENT-HOLDOUT-*-live.json")).read_text())
    rows, s = rep["rows"], rep["summary"]
    cont = [r for r in rows if r["expected"] == "CONTESTED"]
    return {"dir": d, "prompt": rep["agent_prompt_sha256"][:12],
            "engine": (rep.get("stress_engine_sha256") or "")[:12],
            "clear": f"{s['clear_agree']} / {s['clear_cases']}",
            "contested_filed": f"{s['contested_filed']} / {s['contested']}",
            "contested": ", ".join(f"{r['case']} {r['agent_disp']}" for r in cont),
            "missed": ", ".join(f"{r['case']} {r['expected']}→{r['agent_disp']}" for r in rows
                                if r["expected"] in ("FILE", "NOT_FILE")
                                and r["agent_disp"] != r["expected"]) or "—",
            "rejections": s["rejections"]}


def table(title: str, runs: dict, fn) -> list[str]:
    lines = [f"## {title}", "",
             "| condition | run | agent prompt | clear cases agreeing | contested filed | contested dispositions | clear cases missed | rejected submissions |",
             "|---|---|---|---|---|---|---|---|"]
    for cond, dirs in runs.items():
        for d in dirs:
            r = fn(d)
            lines.append(f"| {cond} | [`{d}`]({d}/) | `{r['prompt']}…` | {r['clear']} | "
                         f"{r['contested_filed']} | {r['contested']} | {r['missed']} | {r['rejections']} |")
    return lines + [""]


def framing_table(title: str, runs: dict, fn) -> list[str]:
    lines = [f"## {title}", "",
             "| condition | run | agent prompt | stress engine | clear cases agreeing | contested filed | contested dispositions | clear cases missed | rejected submissions |",
             "|---|---|---|---|---|---|---|---|---|"]
    for cond, dirs in runs.items():
        for d in dirs:
            r = fn(d)
            lines.append(f"| {cond} | [`{d}`]({d}/) | `{r['prompt']}…` | "
                         f"{('`' + r['engine'] + '…`') if r['engine'] else 'previous (not recorded)'} | "
                         f"{r['clear']} | {r['contested_filed']} | {r['contested']} | {r['missed']} | "
                         f"{r['rejections']} |")
    return lines + [""]


def framing_main() -> int:
    lines = ["# Agent filing lean: before and after the 2026-10-28 stress-summary framing fix", "",
             "Same agent prompt in every run. The only change is the stress-test summary the agent's "
             "`stress_test` tool returns: a FILE on LOW signals (or a closure on HIGH) is no longer "
             "summarised as robust. Dev set: 16 seeded alerts, current seed. Holdout: 6 frozen cases, "
             "author-assigned labels, not expert ground truth. Two runs per condition; a change counts "
             "only if both runs show it. Numbers are read from the linked run files by "
             "`scripts/agent_lean_report.py --framing`.", ""]
    lines += framing_table("Development set (16 alerts: 12 clear, 4 contested)", FRAMING_DEV, dev_run)
    lines += framing_table("Holdout (6 cases: 4 clear, 2 contested)", FRAMING_HOLDOUT, holdout_run)
    lines += ["The disposition stays advisory and is shown last in the app; the officer decides.", ""]
    FRAMING_OUT.write_text("\n".join(lines))
    print("\n".join(lines))
    return 0


def main() -> int:
    if "--framing" in sys.argv[1:]:
        return framing_main()
    lines = ["# Agent filing lean: before and after the 2026-10-28 prompt change", "",
             "Dev set: the 16 seeded alerts on the current seed (gold labels by the scenario authors). "
             "Holdout: 6 frozen cases (`holdout/HOLDOUT-v1.json`, author-assigned labels, not expert "
             "ground truth). Agent: Nemotron reasoning tier via Token Factory, live. Two runs per "
             "condition; model output varies between runs, so a change counts only if both runs show it. "
             "Every number below is read from the linked run files by `scripts/agent_lean_report.py`.", ""]
    lines += table("Development set (16 alerts: 12 clear, 4 contested)", DEV, dev_run)
    lines += table("Holdout (6 cases: 4 clear, 2 contested)", HOLDOUT, holdout_run)
    lines += ["The disposition stays advisory and is shown last in the app; the officer decides.", ""]
    OUT.write_text("\n".join(lines))
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
