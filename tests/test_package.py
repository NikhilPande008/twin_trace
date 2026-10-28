"""
T3: recorded inputs and programs make a decision reconstructable; the package verifies offline
and detects alteration; current data never stands in for historical inputs. Offline.
"""
from __future__ import annotations

import copy
import json

import pytest

from ddp.bootstrap import compute_params, open_store
from ddp.compute import ComputeRunner, reproduce_recorded
from ddp.package import build_package, verify_package
from ddp.skills import POE_FACTORS, CoPilotSkills
from scripts.verify_package import main as verify_cli

POE = [{"factor_id": f, "factor_name": n, "assessment": "clear"} for f, n in POE_FACTORS]


@pytest.fixture
def recorded():
    store = open_store(":memory:")
    txns = store.transactions_for("ALERT-01")
    run = ComputeRunner(store).run("ALERT-01", txns, compute_params(store, "ALERT-01"))
    res = CoPilotSkills(store).alert_disposition_recorder(
        alert_id="ALERT-01", customer_ref="CUST-01", disposition="FILE",
        rationale_text="Debits totalled ₹3,40,700 (F-TOTAL-DEBIT) to the I4C-flagged handle C; "
                       "₹1,10,000 arrived from Unknown UPI handle A.",
        rules_cited=[], rfi_triggers=[], poe_assessment=POE, compute_run_id=run["run_id"])
    return store, run, res["decision_id"]


def test_run_saves_input_and_archives_program(recorded):
    store, run, _ = recorded
    row = store.get_compute_run(run["run_id"])
    assert json.loads(row["INPUT_JSON"])["alert_id"] == "ALERT-01"
    assert store.get_program(row["CODE_SHA256"])["PROGRAM"] == "aggregations.v1"


def test_reproduce_uses_recorded_inputs_not_current_data(recorded):
    store, run, _ = recorded
    store._exec("UPDATE TRANSACTIONS SET AMOUNT_INR = 1 WHERE ALERT_ID = 'ALERT-01'")
    assert reproduce_recorded(store, run["run_id"])["status"] == "reproduced"


def test_run_without_saved_input_is_unavailable_not_success(recorded):
    store, run, _ = recorded
    legacy = dict(store.get_compute_run(run["run_id"]), RUN_ID="RUN-legacy", INPUT_JSON=None)
    store.append_compute_run(legacy)
    r = reproduce_recorded(store, "RUN-legacy")
    assert r["status"] == "unavailable" and "not saved" in r["reason"]


def test_package_verifies_offline(recorded, tmp_path):
    store, _, did = recorded
    pkg = build_package(store, did)
    assert verify_package(pkg)["ok"], verify_package(pkg)
    path = tmp_path / "pkg.json"
    path.write_text(json.dumps(pkg, default=str))
    assert verify_cli([str(path)]) == 0
    statuses = {c["raw"]: c["status"] for c in pkg["claims"]["claims"]}
    assert statuses == {"₹3,40,700": "verified_calculation", "₹1,10,000": "source_transaction"}


def test_package_ignores_later_changes_to_operational_data(recorded):
    store, _, did = recorded
    before = build_package(store, did)
    store._exec("UPDATE TRANSACTIONS SET AMOUNT_INR = 1 WHERE ALERT_ID = 'ALERT-01'")
    after = build_package(store, did)
    for s in ("decision", "compute_runs", "programs", "claims"):
        assert before["manifest"][s] == after["manifest"][s], s


@pytest.mark.parametrize("tamper", [
    lambda p: p["decision"].__setitem__("DISPOSITION", "NOT_FILE"),
    lambda p: p["compute_runs"][0].__setitem__(
        "INPUT_JSON", p["compute_runs"][0]["INPUT_JSON"].replace("110000", "110001")),
    lambda p: p["programs"].__setitem__(
        next(iter(p["programs"])), next(iter(p["programs"].values())) + "\n# edited"),
    lambda p: p["claims"]["claims"][1].__setitem__("status", "verified_calculation"),
])
def test_altered_package_fails(recorded, tamper):
    store, _, did = recorded
    pkg = copy.deepcopy(build_package(store, did))
    tamper(pkg)
    assert verify_package(pkg)["ok"] is False
