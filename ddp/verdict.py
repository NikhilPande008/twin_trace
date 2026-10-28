"""
Verdict card and Twin Cases data, built only from deterministic stress-test reports.

The stress test checks a PROPOSED disposition; it never chooses one. The card therefore shows
both readings — what a FILE would rest on, and what would reopen a closure — and leaves the choice
to the officer. Nothing here calls a model or computes a figure: every value comes from the
report, from the base run's recorded output, or from the alert row.
"""

from __future__ import annotations

import json

from .stress.headline import headline

TWIN_PAIR = ("ALERT-01", "ALERT-16")
DISPOSITIONS = ("FILE", "NOT_FILE")
MAX_CHIPS = 3


def readings(tester, store, alert_id: str, params: dict) -> dict[str, dict]:
    """Both stress-test readings for one alert, without the model memo (instant, offline)."""
    txns = store.transactions_for(alert_id)
    return {d: tester.run(alert_id, txns, params, disposition=d) for d in DISPOSITIONS}


def _chip(h: dict) -> str:
    t = h["target"]
    return {"UNFLAG": f"registry flag on {t} is correct",
            "EXPLAIN": f"no explanation for {t}",
            "FLAG": f"{t} reported to a registry"}[h["kind"]]


def reading(report: dict) -> dict:
    """One side of the card: headline, chips and any caveat notes."""
    h = headline(report)
    if report["mode"] == "weaken":
        sets = sorted(report["minimal_flip_sets"], key=len)
        chips = [" + ".join(_chip(x) for x in f) for f in sets]
        chip_label = "Rests on"
    else:
        by_id = {x["id"]: x for x in report["hypotheses"]}
        chips = [" + ".join(_chip(by_id[i]) for i in t["hypotheses"])
                 for t in report["reopen_triggers"]]
        chip_label = "Reopen if"
    return {"disposition": report["disposition_tested"], "tone": h["tone"], "title": h["title"],
            "detail": h["detail"], "chip_label": chip_label, "chips": chips[:MAX_CHIPS],
            "more": max(0, len(chips) - MAX_CHIPS), "notes": list(report["notes"])}


def card(reports: dict[str, dict]) -> dict:
    f, c = reports["FILE"], reports["NOT_FILE"]
    return {"level": f["base"]["verdict"],
            "runs": sum(r["search"]["runs_used"] + 1 for r in (f, c)),
            "file": reading(f), "close": reading(c)}


def base_facts(store, report: dict) -> dict[str, object]:
    """Fact values of the report's own base run, read back from COMPUTE_RUNS (no recompute)."""
    row = store.get_compute_run(report["base"]["run_id"])
    out = json.loads(row["OUTPUT_JSON"]) if row else {}
    facts = out.get("facts", []) if isinstance(out, dict) else out
    return {x["fact_id"]: x["value"] for x in facts}


def shared_features(alert_a: dict, alert_b: dict, facts_a: dict, facts_b: dict) -> list[dict]:
    """What the rules engine sees for each alert, and whether it is identical."""
    def rfi(a):
        try:
            return ", ".join(json.loads(str(a.get("RFI_TRIGGERS") or "[]"))) or "—"
        except ValueError:
            return "—"
    rows = [("Alert type", alert_a["ALERT_TYPE"].replace("_", " ").title(),
             alert_b["ALERT_TYPE"].replace("_", " ").title()),
            ("Signal source", alert_a["SIGNAL_SOURCE"], alert_b["SIGNAL_SOURCE"]),
            ("Red-flag codes", rfi(alert_a), rfi(alert_b)),
            ("Total credits (F-TOTAL-CREDIT)", facts_a.get("F-TOTAL-CREDIT"),
             facts_b.get("F-TOTAL-CREDIT"))]
    return [{"label": l, "a": a, "b": b, "same": a == b} for l, a, b in rows]


def signal_contrast(report_a: dict, report_b: dict) -> list[dict]:
    """Each calculator signal, fired or not, for both alerts; `differs` marks the fork."""
    b = {s["signal_id"]: s["fired"] for s in report_b["base"]["signals"]}
    return [{"signal_id": s["signal_id"], "label": s["label"], "a": s["fired"],
             "b": b.get(s["signal_id"], False), "differs": s["fired"] != b.get(s["signal_id"], False)}
            for s in report_a["base"]["signals"]]
