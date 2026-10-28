"""
The in-app package verifier (T9.5): an uploaded package is untrusted input. It must verify a
genuine package, flag an altered one, and never execute program source it does not trust.
"""

from __future__ import annotations

import copy
import json

import pytest

from ddp.bootstrap import compute_params, open_store
from ddp.compute import ComputeRunner
from ddp.compute.runner import canonical_json, sha256_bytes
from ddp.package import (MAX_PACKAGE_BYTES, build_package, check_uploaded_package, verify_package)
from ddp.skills import POE_FACTORS, CoPilotSkills

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
    return store, build_package(store, res["decision_id"])


def test_genuine_package_verifies(recorded):
    store, pkg = recorded
    out = check_uploaded_package(json.dumps(pkg, default=str).encode(), store)
    assert out["status"] == "verified", out


def test_verifies_without_the_source_database(recorded):
    """A reviewer's deployment has an empty database: the shipped program is still trusted."""
    _, pkg = recorded
    out = check_uploaded_package(json.dumps(pkg, default=str).encode(), open_store(":memory:"))
    assert out["status"] == "verified", out


def test_altered_package_fails(recorded):
    store, pkg = recorded
    bad = copy.deepcopy(pkg)
    bad["decision"]["RATIONALE_TEXT"] += " (edited)"
    out = check_uploaded_package(json.dumps(bad, default=str).encode(), store)
    assert out["status"] == "failed"


def test_untrusted_program_is_never_executed(recorded, tmp_path):
    """A package can carry any source with a matching hash. It must not be run."""
    store, pkg = recorded
    marker = tmp_path / "executed.txt"
    evil = (f"import sys\nopen({str(marker)!r}, 'w').write('ran')\n"
            "print('{\"program\":\"aggregations.v1\",\"facts\":[]}')\n")
    evil_hash = sha256_bytes(evil.encode())
    bad = copy.deepcopy(pkg)
    run = bad["compute_runs"][0]
    bad["programs"] = {evil_hash: evil}
    run["CODE_SHA256"] = evil_hash
    out = check_uploaded_package(json.dumps(bad, default=str).encode(), store)
    assert not marker.exists(), "package-supplied program was executed"
    assert out["status"] == "failed"
    skipped = [c for c in out["result"]["checks"] if c["name"].startswith("reproduce:")]
    assert skipped and "not executed" in skipped[0]["detail"]


def test_default_verifier_behaviour_is_unchanged(recorded):
    _, pkg = recorded
    assert verify_package(pkg)["ok"]


@pytest.mark.parametrize("raw", [b"not json", b"[]", b'{"package_version": "other"}', b"\xff\xfe"])
def test_garbage_is_invalid_not_a_crash(raw):
    assert check_uploaded_package(raw, None)["status"] == "invalid"


def test_malformed_sections_do_not_crash():
    raw = json.dumps({"package_version": "ddp-decision-package/1", "decision": 5,
                      "compute_runs": "x", "manifest": []}).encode()
    assert check_uploaded_package(raw, None)["status"] in ("invalid", "failed")


def test_oversize_is_refused():
    assert check_uploaded_package(b"x" * (MAX_PACKAGE_BYTES + 1), None)["status"] == "invalid"
