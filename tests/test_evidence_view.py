"""The Measured Results numbers are computed from committed reports and match what the README says (T9.10)."""

from __future__ import annotations

import json
from pathlib import Path

from ddp.evidence_view import (EVALS, latest_live_holdout, live_eval_reports, summarise_holdout,
                               summarise_live, holdout_runs)

RERUN = EVALS / "rerun-2026-10-21" / "REPORT-2026-10-21-live.json"


def test_committed_live_report_numbers_match_the_readme():
    s = summarise_live(json.loads(RERUN.read_text()), RERUN)
    assert s["alerts"] == 16 and s["assess_model_valid"] == 16
    assert s["assess_outcomes"] == {"success": 12, "repaired": 4}
    assert (s["clear_agree"], s["clear_cases"], s["clear_gold_file"]) == (12, 12, 9)
    assert (s["contested"], s["contested_filed"]) == (4, 4)
    assert s["agent_rejections"] == 19 and s["agent_alerts_with_rejection"] == 12


def test_withdrawn_report_is_never_listed():
    sources = [str(p) for p, _ in live_eval_reports()]
    assert not any(p.endswith("evals/REPORT-2026-10-21-live.json") for p in sources)
    for _, d in live_eval_reports():
        assert all(r.get("assess") != "valid" for r in d["rows"])


def test_mock_runs_are_never_listed(tmp_path):
    (tmp_path / "REPORT-2026-01-01-mock.json").write_text(json.dumps({"mode": "mock", "rows": []}))
    (tmp_path / "REPORT-2026-01-02-live.json").write_text(
        json.dumps({"mode": "mock", "rows": [{"assess": "success"}]}))
    assert live_eval_reports(tmp_path) == []


def test_holdout_numbers_match_the_readme():
    h = latest_live_holdout()
    assert (h["caught"], h["faults_total"]) == (10, 15)
    assert (h["caught_designed"], h["designed_total"]) == (10, 12)
    assert (h["false_rejections"], h["supported_total"]) == (0, 11)
    c = h["conditions"]
    assert (c["C2_baseline_no_controls"]["drafts_with_unsupported"], c["C2_baseline_no_controls"]["drafts"]) == (6, 6)
    assert c["C3_full_product"]["drafts_with_unsupported"] == 3
    assert c["C3_full_product"]["accepted_by_gate"] == 3 and c["C3_full_product"]["unsupported_in_accepted"] == 0
    assert h["label_provenance"] and "NOT expert ground truth" in h["label_provenance"]


def test_missing_or_corrupt_files_do_not_crash(tmp_path):
    assert live_eval_reports(tmp_path / "nope") == []
    assert latest_live_holdout(tmp_path) is None
    run = tmp_path / "RUN-x"
    run.mkdir()
    (run / "config.json").write_text("{not json")
    (run / "metrics.json").write_text("{}")
    assert holdout_runs(tmp_path) == []


FINAL = EVALS / "live-2026-10-21-final" / "REPORT-2026-10-21-live.json"


def test_readme_quotes_exactly_the_final_live_report():
    """README's live-results table must match the committed report it links to (T9.4)."""
    s = summarise_live(json.loads(FINAL.read_text()), FINAL)
    assert s["assess_outcomes"] == {"success": 14, "repaired": 2} and s["assess_model_valid"] == 16
    assert (s["clear_agree"], s["clear_cases"], s["clear_gold_file"]) == (12, 12, 9)
    assert (s["contested"], s["contested_filed"]) == (4, 4)
    assert s["agent_rejections"] == 16 and s["agent_alerts_with_rejection"] == 12
    assert (s["median_assess_s"], s["median_agent_s"]) == (26.0, 20.2)
    readme = (EVALS.parent / "README.md").read_text()
    for quoted in ("14 first try, 2 after one repair", "**16** across 12 alerts",
                   "26.0 s for the 11-factor assessment, 20.2 s for the agent",
                   "evals/live-2026-10-21-final/REPORT-2026-10-21-live.md"):
        assert quoted in readme, quoted
