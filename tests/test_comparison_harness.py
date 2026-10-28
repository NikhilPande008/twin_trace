"""T5: the holdout/comparison harness runs offline and reports honestly. Offline."""
from __future__ import annotations

import json

from scripts.run_comparison import main


def test_mock_run_writes_all_artifacts(tmp_path):
    assert main(["--mock", "--out", str(tmp_path)]) == 0
    run = next(tmp_path.glob("RUN-*-mock"))
    for f in ("config.json", "outputs.jsonl", "metrics.json", "REPORT.md"):
        assert (run / f).exists(), f
    cfg = json.loads((run / "config.json").read_text())
    assert len(cfg["dataset_sha256"]) == 64
    assert "NOT expert ground truth" in cfg["label_provenance"]
    report = (run / "REPORT.md").read_text()
    assert "MOCK RUN" in report and "Not measured" in report
    m = json.loads((run / "metrics.json").read_text())
    assert m["conditions"]["C2_baseline_no_controls"]["unsupported_figures_total"] > 0
    assert m["conditions"]["C3_full_product"]["unsupported_in_accepted"] == 0


def test_gate_measurement_reports_mismatches_not_hides_them(tmp_path):
    assert main(["--gate-only", "--out", str(tmp_path)]) == 0
    m = json.loads((next(tmp_path.glob("RUN-*-gate-only")) / "metrics.json").read_text())
    caught, total = m["gate"]["catch_rate_all"]
    assert total == len(m["gate"]["faults"]) and caught < total   # known limits stay visible
    assert m["gate"]["false_rejections"][0] == 0
    assert m["gate"]["label_mismatches"]
