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
    readme = (EVALS.parent / "README.md").read_text()      # quoted as the earlier, old-seed run
    for quoted in ("14 first try, 2 after one repair", "**16** rejections across 12 alerts",
                   "26.0 s for the 11-factor assessment, 20.2 s for the agent",
                   "evals/live-2026-10-21-final/REPORT-2026-10-21-live.md"):
        assert quoted in readme, quoted


DETERMINISTIC = EVALS / "REPORT-2026-10-28-deterministic.json"


def test_old_live_report_is_labelled_as_the_old_seed():
    """The 2026-10-21 run predates the 2026-10-28 case histories; the app must say so."""
    assert summarise_live(json.loads(FINAL.read_text()), FINAL)["current_seed"] is False


def test_readme_quotes_the_deterministic_report_on_the_current_seed():
    from ddp.evidence_view import deterministic_reports, summarise_stress
    s = summarise_stress(json.loads(DETERMINISTIC.read_text()), DETERMINISTIC)
    assert (s["stress_high"], s["gold_file"], s["current_seed"]) == (3, 9, True)
    assert any(p == DETERMINISTIC for p, _ in deterministic_reports())
    readme = (EVALS.parent / "README.md").read_text()
    for quoted in ("**3 of 9** gold-FILE alerts reach a HIGH modeled level",
                   "evals/REPORT-2026-10-28-deterministic.md", "Earlier run on the old seed"):
        assert quoted in readme, quoted


SEED_RUN = EVALS / "live-2026-10-28-seed" / "REPORT-2026-10-28-live.json"


def test_readme_table_quotes_exactly_the_live_run_on_the_current_seed():
    s = summarise_live(json.loads(SEED_RUN.read_text()), SEED_RUN)
    assert s["current_seed"] is True and s["assess_outcomes"] == {"success": 16}
    assert (s["clear_agree"], s["clear_cases"], s["clear_gold_file"]) == (12, 12, 9)
    assert (s["contested"], s["contested_filed"]) == (4, 4)
    assert (s["agent_rejections"], s["agent_alerts_with_rejection"]) == (14, 9)
    assert (s["median_assess_s"], s["median_agent_s"], s["stress_high"]) == (18.1, 14.9, 3)
    readme = (EVALS.parent / "README.md").read_text()
    for quoted in ("**16 / 16**, all first try", "**14** across 9 alerts",
                   "18.1 s for the 11-factor assessment, 14.9 s for the agent",
                   "evals/live-2026-10-28-seed/REPORT-2026-10-28-live.md"):
        assert quoted in readme, quoted


def test_readme_agent_lean_sentence_matches_the_comparison_runs():
    """Item 4: only the ALERT-11 move held in both dev runs; the holdout did not move in both."""
    from scripts.agent_lean_report import DEV, HOLDOUT, dev_run, holdout_run
    after_dev = [dev_run(d) for d in DEV["after"]]
    assert all("ALERT-11 NEEDS_MORE_INFO" in r["contested"] for r in after_dev)
    assert [r["contested_filed"] for r in after_dev] == ["3 / 4", "3 / 4"]
    assert [holdout_run(d)["contested_filed"] for d in HOLDOUT["after"]] == ["1 / 2", "2 / 2"]
    assert any(r["missed"] != "—" for r in after_dev)
    readme = (EVALS.parent / "README.md").read_text()
    assert "evals/AGENT-LEAN-2026-10-28.md" in readme and "It was\n  not an improvement and was reverted" in readme


def test_readme_framing_sentence_matches_the_framing_runs():
    """The stress-summary framing fix left the lean unchanged in both runs on both sets."""
    from scripts.agent_lean_report import FRAMING_DEV, FRAMING_HOLDOUT, dev_run, holdout_run
    assert [dev_run(d)["contested_filed"] for d in FRAMING_DEV["framing fix"]] == ["4 / 4", "4 / 4"]
    assert [holdout_run(d)["contested_filed"] for d in FRAMING_HOLDOUT["framing fix"]] == ["2 / 2", "2 / 2"]
    readme = (EVALS.parent / "README.md").read_text()
    assert "evals/AGENT-FRAMING-2026-10-28.md" in readme and "FILE on 4 / 4 contested in both" in readme
