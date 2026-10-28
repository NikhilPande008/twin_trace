"""
Measured results, read from the committed reports in evals/ (T9.10).

Every number the app shows on its "Measured Results" page is computed here from a dated report
file. Nothing is typed in by hand, and each summary carries the file, date and code revision it
came from, so a figure cannot outlive the evidence behind it. Mock runs are never shown as results.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from statistics import median

EVALS = Path(__file__).resolve().parent.parent / "evals"
CLEAR_GOLD = ("FILE", "NOT_FILE")          # CONTESTED cases are ambiguous by design


def seed_fingerprint() -> str:
    """SHA-256 of the seeded alerts and transactions. Reports record it (from 2026-10-28) so a
    figure from a run on an earlier seed can be labelled as such."""
    from . import seed_data
    blob = json.dumps({"alerts": seed_data.ALERTS, "transactions": seed_data.TRANSACTIONS},
                      sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def deterministic_reports(evals_dir: Path = EVALS) -> list[tuple[Path, dict]]:
    """Deterministic (calculator + stress test only, no model) 16-alert reports, newest first."""
    found = [(p, d) for p in evals_dir.rglob("REPORT-*-deterministic.json")
             if (d := _load(p)) and d.get("mode") == "deterministic"
             and isinstance(d.get("rows"), list)]
    return sorted(found, key=lambda x: x[1].get("started_utc", ""), reverse=True)


def summarise_stress(report: dict, path: Path | None = None) -> dict:
    """Gold-FILE alerts whose calculator signals are HIGH, and whether the run used this seed."""
    rows = report["rows"]
    return {"source": str(path.relative_to(EVALS.parent)) if path else "",
            "started_utc": report.get("started_utc"),
            "stress_high": sum(1 for r in rows if r.get("gold") == "FILE" and r.get("verdict") == "HIGH"),
            "gold_file": sum(1 for r in rows if r.get("gold") == "FILE"),
            "current_seed": report.get("seed_sha256") == seed_fingerprint()}


def _load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def live_eval_reports(evals_dir: Path = EVALS) -> list[tuple[Path, dict]]:
    """Live (never mock) 16-alert reports, newest first.

    Reports written before 2026-10-21 T7.3 label every assessment "valid", because fallback
    placeholders were counted as successes (DECISIONS.md, "Correction"). That figure is withdrawn,
    so such a report is never returned.
    """
    found = []
    for p in evals_dir.rglob("REPORT-*-live.json"):
        d = _load(p)
        if d and d.get("mode") == "live" and isinstance(d.get("rows"), list):
            if any(r.get("assess") == "valid" for r in d["rows"]):
                continue
            if not any("assess" in r for r in d["rows"]):
                continue                    # agent-only run (item 4 measurement), not a full run
            found.append((p, d))
    return sorted(found, key=lambda x: x[1].get("started_utc", ""), reverse=True)


def summarise_live(report: dict, path: Path | None = None) -> dict:
    rows = report["rows"]
    outcome = {}
    for r in rows:
        outcome[r.get("assess")] = outcome.get(r.get("assess"), 0) + 1
    clear = [r for r in rows if r.get("gold") in CLEAR_GOLD and r.get("agent") == "submitted"]
    agree = [r for r in clear if r.get("agent_disp") == r.get("gold")]
    contested = [r for r in rows if r.get("gold") not in CLEAR_GOLD]
    gold_file = [r for r in clear if r.get("gold") == "FILE"]
    assess_s = [r["assess_s"] for r in rows if r.get("assess_s") is not None]
    agent_s = [r["agent_s"] for r in rows if r.get("agent_s") is not None]
    return {
        "source": str(path.relative_to(EVALS.parent)) if path else None,
        "started_utc": report.get("started_utc"),
        "models": report.get("models"),
        "compute_backend": report.get("compute_backend"),
        "alerts": len(rows),
        "assess_outcomes": outcome,                       # success / repaired / fallback / failed
        "assess_model_valid": outcome.get("success", 0) + outcome.get("repaired", 0),
        "assess_truncated": sum(1 for r in rows if r.get("assess_truncated")),
        "agent_submitted": sum(1 for r in rows if r.get("agent") == "submitted"),
        "agent_rejections": sum(r.get("agent_rejections") or 0 for r in rows),
        "agent_alerts_with_rejection": sum(1 for r in rows if (r.get("agent_rejections") or 0) > 0),
        "clear_cases": len(clear),
        "clear_agree": len(agree),
        "clear_gold_file": len(gold_file),            # what an always-FILE rule would get right
        "contested": len(contested),
        "contested_filed": sum(1 for r in contested if r.get("agent_disp") == "FILE"),
        "median_assess_s": round(median(assess_s), 1) if assess_s else None,
        "median_agent_s": round(median(agent_s), 1) if agent_s else None,
        "stress_high": sum(1 for r in rows if r.get("gold") == "FILE" and r.get("verdict") == "HIGH"),
        "gold_file": sum(1 for r in rows if r.get("gold") == "FILE"),
        "current_seed": report.get("seed_sha256") == seed_fingerprint(),
    }


def holdout_runs(evals_dir: Path = EVALS) -> list[dict]:
    """Holdout comparison runs (RUN-*), newest first, each with its config and metrics."""
    runs = []
    for d in sorted(evals_dir.glob("RUN-*"), reverse=True):
        cfg, met = _load(d / "config.json"), _load(d / "metrics.json")
        if cfg and met:
            runs.append({"dir": str(d.relative_to(evals_dir.parent)), "config": cfg, "metrics": met})
    return runs


def summarise_holdout(run: dict) -> dict:
    gate = run["metrics"]["gate"]
    all_hit, all_n = gate["catch_rate_all"]
    des_hit, des_n = gate["catch_rate_in_designed_coverage"]
    bad_rej, sup_n = gate["false_rejections"]
    faults = [{"case": f["case"], "fault": f["fault"], "text": f["text"],
               "expected": f["expected"], "got": f["got"], "caught": f["caught"]}
              for f in gate["faults"]]
    return {
        "dir": run["dir"],
        "mode": run["config"].get("mode"),
        "started_utc": run["config"].get("started_utc"),
        "git_rev": run["config"].get("git_rev"),
        "dataset": run["config"].get("dataset"),
        "dataset_sha256": run["config"].get("dataset_sha256"),
        "cases": run["config"].get("cases"),
        "label_provenance": run["config"].get("label_provenance"),
        "caught": all_hit, "faults_total": all_n,
        "caught_designed": des_hit, "designed_total": des_n,
        "false_rejections": bad_rej, "supported_total": sup_n,
        "faults": faults,
        "label_mismatches": gate.get("label_mismatches", []),
        "conditions": run["metrics"].get("conditions"),
    }


def latest_live_holdout(evals_dir: Path = EVALS) -> dict | None:
    for run in holdout_runs(evals_dir):
        if run["config"].get("mode") == "live" and run["metrics"].get("conditions"):
            return summarise_holdout(run)
    return None
