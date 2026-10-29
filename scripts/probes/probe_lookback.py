"""
Live probe of the rule-change lookback (T12.12): Tavily Extract on a rule's source page, a
Nemotron clause proposal, and the verbatim check. Writes evals/LOOKBACK-<date>-live.md/.json.

    python -m scripts.probes.probe_lookback [--rules SB-004,STR-002,INS-002]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ddp.bootstrap import open_store  # noqa: E402
from ddp.config import get_settings  # noqa: E402
from ddp.llm import TokenFactoryClient  # noqa: E402
from ddp.lookback import check_rule  # noqa: E402
from ddp.skills import CoPilotSkills  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default="SB-004,STR-002,INS-002")
    args = ap.parse_args(argv)
    s = get_settings()
    if not (s.llm_configured and s.tavily_api_key):
        print("Needs NEBIUS_API_KEY and TAVILY_API_KEY.")
        return 2
    store = open_store(":memory:")
    skills = CoPilotSkills(store, llm=TokenFactoryClient(s))
    rows = []
    for rid in args.rules.split(","):
        r = check_rule(store, skills, rid, tavily_key=s.tavily_api_key)
        rows.append({k: r.get(k) for k in ("status", "detail", "RULE_ID", "SOURCE_URL",
                                           "PAGE_SHA256", "QUOTE", "QUOTE_VERIFIED", "CHANGED",
                                           "SUMMARY", "STATUS")} | {"rule": rid})
        print(rid, r.get("status"), r.get("STATUS"), flush=True)
    now = datetime.now(timezone.utc)
    stem = ROOT / "evals" / f"LOOKBACK-{now:%Y-%m-%d}-live"
    stem.with_suffix(".json").write_text(json.dumps({"generated_at": now.isoformat(timespec="seconds"),
                                                     "model": s.models["reasoning"], "rows": rows},
                                                    indent=1))
    lines = [f"# Rule-change lookback probe — {now.isoformat(timespec='seconds')} (LIVE)", "",
             f"Tavily Extract + `{s.models['reasoning']}` on Token Factory. A proposal is kept only "
             "if its passage appears word for word on the fetched page.", "",
             "| Rule | Fetch | Proposal | Changed | Passage (first 160 chars) |", "|---|---|---|---|---|"]
    for r in rows:
        q = (r.get("QUOTE") or "").replace("|", "/")[:160]
        lines.append(f"| {r['rule']} | {r['status']} {r.get('detail') or ''} | {r.get('STATUS') or '—'} "
                     f"| {r.get('CHANGED')} | {q} |")
    lines += ["", "Summaries:"] + [f"- {r['rule']}: {r.get('SUMMARY') or r.get('detail') or ''}"
                                   for r in rows]
    stem.with_suffix(".md").write_text("\n".join(lines) + "\n")
    print(f"wrote {stem}.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
