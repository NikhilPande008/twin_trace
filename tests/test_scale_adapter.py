"""Scale-test adapter (T12.15) on a hand-made fixture in the IBM/ETH dataset format."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from ddp.compute import ComputeRunner  # noqa: E402
from ddp.scale.amlworld import load_accounts  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "amlworld_sample.csv"


def test_accounts_are_grouped_with_direction_and_labels():
    acc = load_accounts(FIXTURE)
    mule = acc["20:MULE1"]
    assert mule["laundering"] is True
    types = sorted(t["type"] for t in mule["transactions"])
    assert types == ["CREDIT", "CREDIT", "CREDIT", "DEBIT"]
    assert all(t["is_flagged"] is False for t in mule["transactions"])
    assert acc["50:EMP1"]["laundering"] is False
    assert "10:8000EBD30" not in acc                 # self-transfer skipped, then too few rows


def test_calculator_runs_on_adapted_accounts():
    acc = load_accounts(FIXTURE)
    facts = {f["fact_id"]: f["value"] for f in
             ComputeRunner(None).run("20:MULE1", acc["20:MULE1"]["transactions"], {})["facts"]}
    assert facts["F-FAN-IN"] == 3 and facts["F-FAN-OUT"] == 1


def test_a_different_header_is_refused(tmp_path):
    bad = tmp_path / "x.csv"
    bad.write_text("a,b,c\n1,2,3\n")
    with pytest.raises(ValueError):
        load_accounts(bad)
