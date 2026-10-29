"""
Item 4 measurement tooling (2026-10-28): the agent on the holdout, and agent-only dev runs that
must not replace a full report on the Measured Results page.
"""

from __future__ import annotations

import json
from pathlib import Path

from ddp.bootstrap import open_store
from ddp.evidence_view import live_eval_reports
from scripts.run_agent_holdout import HOLDOUT, load_cases, main, summarise


def test_holdout_cases_load_without_their_labels():
    store = open_store(":memory:")
    cases = json.loads(HOLDOUT.read_text())["cases"]
    load_cases(store, cases)
    for c in cases:
        alert = store.get_alert(c["id"])
        assert alert["GOLD_DISPOSITION"] == "UNSET (holdout)", c["id"]
        assert len(store.transactions_for(c["id"])) == len(c["transactions"])


def test_summary_counts_contested_filings():
    rows = [{"expected": "FILE", "agent": "submitted", "agent_disp": "FILE", "agent_rejections": 1},
            {"expected": "NOT_FILE", "agent": "submitted", "agent_disp": "FILE", "agent_rejections": 0},
            {"expected": "CONTESTED", "agent": "submitted", "agent_disp": "FILE", "agent_rejections": 2},
            {"expected": "CONTESTED", "agent": "submitted", "agent_disp": "NEEDS_MORE_INFO",
             "agent_rejections": 0}]
    s = summarise(rows)
    assert (s["clear_agree"], s["clear_cases"], s["contested_filed"], s["contested"]) == (1, 2, 1, 2)
    assert s["contested_dispositions"]["NEEDS_MORE_INFO"] == 1 and s["rejections"] == 3


def test_mock_run_writes_a_report_with_the_prompt_hash(tmp_path):
    assert main(["--mock", "--out", str(tmp_path)]) == 0
    out = json.loads(next(tmp_path.glob("AGENT-HOLDOUT-*-mock.json")).read_text())
    assert out["mode"] == "mock" and len(out["agent_prompt_sha256"]) == 64
    assert out["summary"]["cases"] == 6


def test_agent_only_dev_run_is_not_shown_as_the_live_result(tmp_path: Path):
    rows = [{"alert_id": "ALERT-01", "gold": "FILE", "verdict": "HIGH", "agent": "submitted",
             "agent_disp": "FILE", "agent_rejections": 0}]
    (tmp_path / "REPORT-2026-10-28-live.json").write_text(
        json.dumps({"mode": "live", "started_utc": "2026-10-28T20:00:00", "rows": rows}))
    assert live_eval_reports(tmp_path) == []
    rows[0].update(assess="success")
    (tmp_path / "REPORT-2026-10-28-live.json").write_text(
        json.dumps({"mode": "live", "started_utc": "2026-10-28T20:00:00", "rows": rows}))
    assert len(live_eval_reports(tmp_path)) == 1
