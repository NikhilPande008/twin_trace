"""
Live probe for Tavily (T2.1 / T6.3): adverse-media screening and regulator-only search.

Runs against the real Tavily API with TAVILY_API_KEY from .env, using synthetic seed alerts
only and an in-memory store (data/ddp.sqlite3 is not touched). It exercises:
  1. adverse-media screen through DispositionPipeline.step_adverse_media (ALERT-01, ALERT-16)
  2. regulator-only search via fetch_regulatory_updates (include_domains = regulator sites)
  3. the case-identifier refusal (no network call is made)
  4. forced failures: an invalid key (expect http_error) and a 1 ms timeout (expect timeout)

Writes evals/TAVILY-PROBE-<date>.md and .json. The API key is never printed or stored.

Usage:
    python3 -m scripts.probes.probe_tavily
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ddp.bootstrap import seed                                    # noqa: E402
from ddp.config import get_settings                               # noqa: E402
from ddp.evidence.tavily import TavilyEvidenceSource, fetch_regulatory_updates  # noqa: E402
from ddp.pipeline import DispositionPipeline, RunTrace            # noqa: E402
from ddp.store import Store                                       # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent
ALERTS = ["ALERT-01", "ALERT-16"]
REG_QUESTION = "RBI master direction KYC customer due diligence amendment"


def _screen(store: Store, src: TavilyEvidenceSource, alert_id: str) -> dict:
    alert = store.get_alert(alert_id)
    pipe = DispositionPipeline(object(), object(), evidence_source=src, store=store)
    t0 = time.monotonic()
    step = pipe.step_adverse_media("", {"alert_type": alert["ALERT_TYPE"]},
                                   RunTrace(alert_id=alert_id), alert_id=alert_id)
    hits = [json.loads(r["CONTENT_JSON"])
            for r in store.evidence_for_alert(alert_id, ev_type="adverse_media")]
    return {"case": f"adverse_media:{alert_id}", "step_status": step.status,
            "screen": step.outputs.get("screen"), "seconds": round(time.monotonic() - t0, 2),
            "evidence_rows": len(hits) + len(store.evidence_for_alert(
                alert_id, ev_type="adverse_media_screen")),
            "hits": [{"title": h["title"][:90], "url": h["url"]} for h in hits]}


def _regulatory(src: TavilyEvidenceSource, question: str, case_terms: list[str],
                label: str) -> dict:
    t0 = time.monotonic()
    out = fetch_regulatory_updates(src, question, case_terms=case_terms)
    return {"case": label, "screen": src.last_status, "seconds": round(time.monotonic() - t0, 2),
            "hits": [{"title": h["title"][:90], "url": h["url"], "domain": h["domain"]}
                     for h in out]}


def main() -> int:
    key = get_settings().tavily_api_key
    if not key:
        print("TAVILY_API_KEY not set in .env — nothing to probe.")
        return 2
    store = Store(":memory:")
    seed(store)
    src = TavilyEvidenceSource(key)

    rows = [_screen(store, src, a) for a in ALERTS]
    rows.append(_regulatory(src, REG_QUESTION, [], "regulator_search"))
    rows.append(_regulatory(src, "reporting rules for ALERT-01", ["ALERT-01"],
                            "regulator_search_refused"))
    for label, failing in [("forced_failure:invalid_key", TavilyEvidenceSource("tvly-invalid-probe")),
                           ("forced_failure:timeout", TavilyEvidenceSource(key, timeout_s=0.001))]:
        fresh = Store(":memory:")   # own store, so earlier hits are not counted as this run's
        seed(fresh)
        rows.append(_screen(fresh, failing, "ALERT-01") | {"case": label})

    expected = {"adverse_media:ALERT-01": {"ok", "no_results"},
                "adverse_media:ALERT-16": {"ok", "no_results"},
                "regulator_search": {"ok", "no_results"},
                "regulator_search_refused": {"refused"},
                "forced_failure:invalid_key": {"http_error"},
                "forced_failure:timeout": {"timeout", "network_error"}}
    for r in rows:
        r["expected"] = sorted(expected[r["case"]])
        r["pass"] = (r["screen"] or {}).get("status") in expected[r["case"]]

    now = datetime.now(timezone.utc)
    blob = json.dumps(rows, indent=2, default=str)
    assert key not in blob, "API key leaked into probe output"
    stem = REPO / "evals" / f"TAVILY-PROBE-{now:%Y-%m-%d}"
    stem.with_suffix(".json").write_text(blob)

    lines = [f"# Tavily live probe — {now:%Y-%m-%d %H:%M} UTC", "",
             "Synthetic seed alerts only; in-memory store. "
             "Reproduce: `python3 -m scripts.probes.probe_tavily`.", "",
             "| case | status | expected | HTTP | results | seconds | pass |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        s = r["screen"] or {}
        lines.append(f"| {r['case']} | {s.get('status')} | {'/'.join(r['expected'])} | "
                     f"{s.get('http_status') or '—'} | {s.get('result_count', 0)} | "
                     f"{r['seconds']} | {'✓' if r['pass'] else '✗'} |")
    lines += ["", "## Queries sent", ""]
    for r in rows:
        q = (r["screen"] or {}).get("query")
        lines.append(f"- **{r['case']}**: `{q}`" if q else f"- **{r['case']}**: (none sent)")
    lines += ["", "## Results returned", ""]
    for r in rows:
        for h in r["hits"]:
            lines.append(f"- {r['case']}: [{h['title']}]({h['url']})")
    stem.with_suffix(".md").write_text("\n".join(lines) + "\n")

    print("\n".join(lines))
    ok = all(r["pass"] for r in rows)
    print(f"\nPROBE {'PASSED' if ok else 'FAILED'} → {stem.with_suffix('.md').relative_to(REPO)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
