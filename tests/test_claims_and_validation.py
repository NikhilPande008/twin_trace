"""
T2: semantic validation beyond schema shape, claim map statuses, agent rationale rules. Offline.
"""
from __future__ import annotations

import json

import pytest

from ddp import structured as S
from ddp.bootstrap import compute_params, open_store
from ddp.claims import claim_map
from ddp.compute import ComputeRunner
from ddp.skills import POE_FACTORS, CoPilotSkills


def _factors(ids):
    return {"factors": [{"factor_id": i, "factor_name": i, "assessment": "clear",
                         "evidence": "x", "evidence_txn_ids": [], "rules_cited": []} for i in ids]}


def test_duplicate_factor_fails_semantic_validation():
    ids = [f for f, _ in POE_FACTORS]
    ids[-1] = ids[0]                                   # POE-002 twice, POE-012 missing
    with pytest.raises(S.SchemaError, match="exactly once"):
        S.parse_and_validate(json.dumps(_factors(ids)), "poe_assessment")


def test_complete_factor_set_passes():
    S.parse_and_validate(json.dumps(_factors([f for f, _ in POE_FACTORS])), "poe_assessment")


def test_duplicate_checklist_item_fails():
    items = [{"item_number": n, "applies": False, "note": ""} for n in [1] * 2 + list(range(3, 11))]
    with pytest.raises(S.SchemaError, match="exactly once"):
        S.parse_and_validate(json.dumps({"items": items}), "quality_check")


def test_unknown_txn_citation_is_flagged_not_trusted():
    out = _factors([f for f, _ in POE_FACTORS])
    out["factors"][0]["evidence_txn_ids"] = ["T01-1", "T99-9"]
    skills = CoPilotSkills(None, complete_fn=lambda p: json.dumps(out))
    res = skills.suspicion_evaluator({"customer_kyc": "", "signal_tags": [], "alert_narrative": "",
                                      "transactions": [{"txn_id": "T01-1", "amount_inr": 1}]})
    assert res[0]["evidence_txn_ids"] == ["T01-1"] and res[0]["unknown_txn_ids"] == ["T99-9"]
    assert skills.last_model_call["factors_with_unknown_txn_ids"] == 1


@pytest.fixture
def alert01():
    store = open_store(":memory:")
    txns = store.transactions_for("ALERT-01")
    run = ComputeRunner(store).run("ALERT-01", txns, compute_params(store, "ALERT-01"))
    return txns, run


def test_claim_statuses(alert01):
    txns, run = alert01
    text = ("Unknown UPI handle A sent ₹1,10,000. UPI handle C received ₹1,40,000. "
            "Debits totalled ₹3,40,700. Another ₹9,99,999 arrived. About ₹3-4 lakh moved. "
            "The pattern is consistent with a mule account.")
    cm = claim_map(text, txns, run["facts"], run["run_id"])
    status = {c["raw"]: c["status"] for c in cm["claims"]}
    assert status == {"₹1,10,000": "source_transaction", "₹1,40,000": "needs_review",
                      "₹3,40,700": "verified_calculation", "₹9,99,999": "unsupported",
                      "₹3-4 lakh": "unparsed"}
    total = next(c for c in cm["claims"] if c["raw"] == "₹3,40,700")
    assert "F-TOTAL-DEBIT" in total["fact_ids"] and total["txn_ids"] == ["T01-3", "T01-5"]
    assert total["run_id"] == run["run_id"] and total["derivation"]
    assert "The pattern is consistent with a mule account." in \
        cm["coverage"]["outside_deterministic_coverage"]


def test_wrong_party_does_not_fail_gate_but_is_not_verified(alert01):
    txns, run = alert01
    res = CoPilotSkills(None).validate_gos_evidence(
        "UPI handle C received ₹1,40,000 from the customer.", txns, run["facts"])
    assert res["passed"] is True                     # the figure is real...
    assert res["needs_review"] and res["needs_review"][0]["label"] == "Context needs your review"  # ...the link is not


def test_rs_abbreviation_does_not_split_a_sentence(alert01):
    txns, run = alert01
    cm = claim_map("UPI handle B sent Rs. 1,40,000 on the same day. It looks like a mule pattern.",
                   txns, run["facts"])
    assert cm["coverage"]["sentences"] == 2
    assert cm["claims"][0]["sentence"].startswith("UPI handle B sent Rs. 1,40,000")
    assert cm["coverage"]["outside_deterministic_coverage"] == ["It looks like a mule pattern."]
