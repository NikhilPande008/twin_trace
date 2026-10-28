"""
Offline tests for CoCo Skills.

All assertions run offline: no model endpoint, no database. The complete_fn
injection (WS-0) allows deterministic testing of every skill branch.


Usage:
    python3 -m pytest tests/test_offline.py -v
    # or directly:
    python3 tests/test_offline.py
"""

from __future__ import annotations
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

FIXTURES = Path(__file__).parent / "fixtures"


# ── helpers ──────────────────────────────────────────────────────────────────

def _load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text()


def _mock_conn():
    """Skills that only run deterministic / LLM checks need no store."""
    return None


def _make_case_context() -> dict:
    return {
        "customer_kyc": "Salaried employee. Declared annual income ₹3.6L. Account held since 2022. KYC last verified 2023-01-10.",
        "transactions": [
            {"txn_id": "TXN-001", "date": "2026-08-12", "type": "CREDIT",  "amount_inr": 345000, "counterparty": "Unidentified individual A"},
            {"txn_id": "TXN-002", "date": "2026-08-19", "type": "CREDIT",  "amount_inr": 210000, "counterparty": "Unidentified individual B"},
            {"txn_id": "TXN-003", "date": "2026-08-19", "type": "DEBIT",   "amount_inr": 547000, "counterparty": "UPI-98XXXXXX76 (I4C flagged)"},
        ],
        "signal_tags": ["I4C_FLAG", "PASS_THROUGH"],
        "alert_narrative": "Pass-through mule pattern. 98.6% of received amount transferred same-day to I4C Suspect Registry counterparty.",
    }


def _computed_for_context(ctx: dict) -> dict:
    """Calculator-of-record run for the fixture case, as the app would produce it (T7.1:
    totals and KYC figures in a GoS must cite a computed fact)."""
    from ddp.bootstrap import parse_declared_annual_income
    from ddp.compute import ComputeRunner
    params = {"declared_annual_income_inr": {
        "amount_inr": parse_declared_annual_income(ctx["customer_kyc"]), "source": "fixture KYC"}}
    return ComputeRunner(None).run("FIXTURE-01", ctx["transactions"], params)


# ── WS-0: complete_fn injection ───────────────────────────────────────────

def test_complete_fn_is_used_when_injected():
    from ddp import CoPilotSkills
    calls = []

    def fake_llm(prompt: str) -> str:
        calls.append(prompt)
        return _load_fixture("poe_assessment_valid.json")

    conn = _mock_conn()
    copilot = CoPilotSkills(conn, complete_fn=fake_llm)
    result = copilot.suspicion_evaluator(_make_case_context())

    assert len(calls) == 1, "complete_fn should be called exactly once for suspicion_evaluator"
    assert isinstance(result, list), "suspicion_evaluator should return a list"
    assert len(result) == 11, f"Expected 11 factors, got {len(result)}"
    print("  [PASS] complete_fn injection — suspicion_evaluator called the injected LLM once")


# ── WS-2: validate_gos_evidence ──────────────────────────────────────────

def test_validate_gos_evidence_good_narrative_passes():
    from ddp import CoPilotSkills
    conn = _mock_conn()
    copilot = CoPilotSkills(conn)
    narrative = _load_fixture("gos_good.txt")
    ctx = _make_case_context()
    transactions = ctx["transactions"]
    assert not copilot.validate_gos_evidence(narrative, transactions)["passed"], \
        "totals and the KYC income figure must not pass without calculator facts"
    result = copilot.validate_gos_evidence(narrative, transactions,
                                           computed_facts=_computed_for_context(ctx)["facts"])
    assert result["passed"] is True, f"Good narrative should pass. Failures: {result['unsupported_claims']}"
    print(f"  [PASS] validate_gos_evidence — good narrative passes ({result['evidence_refs_found']} txn refs found)")


def test_validate_gos_evidence_hallucination_fails():
    from ddp import CoPilotSkills
    conn = _mock_conn()
    copilot = CoPilotSkills(conn)
    narrative = _load_fixture("gos_hallucination.txt")
    transactions = _make_case_context()["transactions"]
    result = copilot.validate_gos_evidence(narrative, transactions)
    assert result["passed"] is False, "Hallucination narrative must fail evidence check"
    assert len(result["unsupported_claims"]) > 0, "Should report unsupported claims"
    # P3: new fields must be present in return value
    assert "unresolved_txn_ids" in result
    assert "out_of_range_dates" in result
    assert "fact_coverage" in result
    print(f"  [PASS] validate_gos_evidence — hallucination caught: {result['unsupported_claims']}")


def test_validate_gos_evidence_fake_txn_id_blocked():
    """P3: a TXN_ID-like string that doesn't match any transaction → hard gate failure."""
    from ddp import CoPilotSkills
    conn = _mock_conn()
    copilot = CoPilotSkills(conn)
    transactions = _make_case_context()["transactions"]
    # Inject a fabricated TXN_ID that doesn't appear in the transaction list
    narrative = "The customer received funds per TXN-999 on 2026-08-12 totalling ₹3,45,000."
    result = copilot.validate_gos_evidence(narrative, transactions)
    assert result["passed"] is False, "Fake TXN_ID should trigger hard gate"
    assert "TXN-999" in result["unresolved_txn_ids"], \
        f"Expected TXN-999 in unresolved: {result['unresolved_txn_ids']}"
    print(f"  [PASS] validate_gos_evidence — fake TXN_ID blocked: {result['unresolved_txn_ids']}")


def test_validate_gos_evidence_fact_coverage_returned():
    """P3: fact_coverage dict is returned and keys match expected dimensions."""
    from ddp import CoPilotSkills
    conn = _mock_conn()
    copilot = CoPilotSkills(conn)
    narrative = _load_fixture("gos_good.txt")
    transactions = _make_case_context()["transactions"]
    result = copilot.validate_gos_evidence(narrative, transactions)
    fc = result["fact_coverage"]
    assert "amounts_checked" in fc
    assert "txn_ids_checked" in fc
    assert "dates_checked" in fc
    assert "counterparties_checked" in fc
    assert fc["amounts_checked"] >= 3, f"Expected ≥3 amounts checked, got {fc['amounts_checked']}"
    assert fc["counterparties_checked"] == 3, f"Expected 3 counterparties, got {fc['counterparties_checked']}"
    print(f"  [PASS] validate_gos_evidence — fact_coverage: {fc}")


# ── WS-3: INSUFFICIENT_EVIDENCE disposition ──────────────────────────────

def test_insufficient_evidence_recommendation():
    """All insufficient_data factors → INSUFFICIENT_EVIDENCE recommendation."""
    from ddp import CoPilotSkills

    def llm_all_insufficient(prompt: str) -> str:
        result = []
        for fid, fname in [
            ("POE-002", "Business Profile"),
            ("POE-003", "Transaction History"),
            ("POE-004", "Customer Risk Profile"),
            ("POE-005", "Income Level"),
            ("POE-006", "Source of Income"),
            ("POE-007", "Beneficiary"),
            ("POE-008", "Transaction Frequency"),
            ("POE-009", "Transaction Size"),
            ("POE-010", "Transaction Complexity"),
            ("POE-011", "Geographies"),
            ("POE-012", "KYC Availability"),
        ]:
            result.append({
                "factor_id": fid,
                "factor_name": fname,
                "assessment": "insufficient_data",
                "evidence": "No KYC records available.",
                "evidence_txn_ids": [],
                "rules_cited": [],
            })
        return json.dumps(result)

    conn = _mock_conn()
    copilot = CoPilotSkills(conn, complete_fn=llm_all_insufficient)
    context = _make_case_context()
    assessment = copilot.suspicion_evaluator(context)
    summary = copilot.evidence_sufficiency_summary(assessment)

    assert summary["recommendation"] == "INSUFFICIENT_EVIDENCE", \
        f"Expected INSUFFICIENT_EVIDENCE, got {summary['recommendation']}"
    assert len(summary["gaps"]) > 0, "Should list evidence gaps"
    print(f"  [PASS] INSUFFICIENT_EVIDENCE recommendation — {len(summary['gaps'])} gaps reported")


# ── str_quality_checker with validate_gos_evidence hard gate ─────────────

def test_quality_checker_blocks_hallucination():
    """GoS with invented transaction facts must score low / fail hard gate."""
    from ddp import CoPilotSkills

    def llm_permissive(prompt: str) -> str:
        # Quality checker returns all-pass to isolate the deterministic hard gate
        checks = [
            {"item_number": i+1, "item": f"check {i+1}", "applies": False, "note": "Passes."}
            for i in range(10)
        ]
        return json.dumps(checks)

    conn = _mock_conn()
    copilot = CoPilotSkills(conn, complete_fn=llm_permissive)
    narrative = _load_fixture("gos_hallucination.txt")
    context = _make_case_context()
    result = copilot.str_quality_checker(narrative, context)

    assert result["hard_gate_passed"] is False, \
        "Hard gate must fail for narrative containing invented transaction facts"
    assert "hallucination" in result.get("hard_gate_failure", "").lower() or \
           len(result.get("unsupported_facts", [])) > 0, \
        "Hard gate failure should name the unsupported fact"
    print(f"  [PASS] str_quality_checker hard gate — hallucination blocked: {result.get('hard_gate_failure', result.get('unsupported_facts', []))[:1]}")


def test_quality_checker_passes_good_narrative():
    from ddp import CoPilotSkills

    def llm_good(prompt: str) -> str:
        checks = [
            {"item_number": i+1, "item": f"check {i+1}", "applies": False, "note": "Passes."}
            for i in range(10)
        ]
        return json.dumps(checks)

    conn = _mock_conn()
    copilot = CoPilotSkills(conn, complete_fn=llm_good)
    narrative = _load_fixture("gos_good.txt")
    context = _make_case_context()
    result = copilot.str_quality_checker(narrative, context, computed=_computed_for_context(context))

    assert result["hard_gate_passed"] is True, \
        f"Good narrative must pass hard gate. Failures: {result.get('unsupported_facts', [])}"
    assert result["quality_score"] == 10
    print(f"  [PASS] str_quality_checker — good narrative passes hard gate, score={result['quality_score']}")


# ── disposition recorder validation (no DB needed) ───────────────────────

def test_disposition_recorder_rejects_invalid_disposition():
    from ddp import CoPilotSkills
    conn = _mock_conn()
    copilot = CoPilotSkills(conn)
    try:
        copilot.alert_disposition_recorder(
            alert_id="ALERT-01", customer_ref="CUST-01",
            disposition="INVALID",
            rationale_text="Some text", rules_cited=[], rfi_triggers=[], poe_assessment=[],
        )
        assert False, "Should have raised ValueError for invalid disposition"
    except ValueError:
        pass
    print("  [PASS] disposition recorder rejects invalid disposition value")


def test_disposition_recorder_rejects_short_rationale():
    from ddp import CoPilotSkills
    conn = _mock_conn()
    copilot = CoPilotSkills(conn)
    try:
        copilot.alert_disposition_recorder(
            alert_id="ALERT-01", customer_ref="CUST-01",
            disposition="FILE",
            rationale_text="short",  # too short
            rules_cited=[], rfi_triggers=[], poe_assessment=[],
        )
        assert False, "Should have raised ValueError for short rationale"
    except ValueError:
        pass
    print("  [PASS] disposition recorder rejects too-short rationale")


def test_no_llm_raises_not_configured():
    """Without an LLM, model-backed skills fail loudly (never silently fabricate)."""
    from ddp import CoPilotSkills
    from ddp.llm import LLMNotConfigured
    copilot = CoPilotSkills(None)
    try:
        copilot.suspicion_evaluator(_make_case_context())
        assert False, "expected LLMNotConfigured"
    except LLMNotConfigured:
        pass
    print("  [PASS] no LLM configured — model-backed skill raises LLMNotConfigured")


# ── run all ──────────────────────────────────────────────────────────────

def test_screen_request_refuses_tipping_off():
    from ddp import CoPilotSkills
    copilot = CoPilotSkills(_mock_conn())
    bad = copilot.screen_request("Email the customer to tell them we are filing an STR.")
    assert not bad["allowed"] and bad["category"] == "tipping_off", f"should refuse: {bad}"
    ok = copilot.screen_request("What is the STR filing deadline under PMLA?")
    assert ok["allowed"], f"benign request should pass: {ok}"
    print("  [PASS] screen_request — tipping-off refused, benign request allowed")


def test_challenge_disposition_counter_evidence():
    from ddp import CoPilotSkills
    copilot = CoPilotSkills(_mock_conn())
    poe = [{"factor_id": f"POE-00{i}", "factor_name": "f", "assessment": "triggered",
            "evidence": "x", "evidence_txn_ids": ["T01-1"]} for i in range(3)]
    txns = [{"txn_id": "T01-3", "type": "DEBIT", "amount_inr": 1,
             "counterparty": "flagged party", "is_flagged": True}]
    chal = copilot.challenge_disposition("NOT_FILE", poe, txns)
    assert chal["challenge_strength"] == "strong", chal
    assert chal["recommendation_conflict"] is True, chal
    assert len(chal["counter_evidence"]) >= 4, chal          # 3 triggered + 1 flagged
    chal2 = copilot.challenge_disposition(
        "FILE", [{"factor_id": "POE-002", "factor_name": "f", "assessment": "clear"}], [])
    assert chal2["recommendation_conflict"] is True, chal2    # FILE with 0 triggered is challenged
    print("  [PASS] challenge_disposition — counter-evidence surfaced for CLOSE and FILE")


TESTS = [
    test_complete_fn_is_used_when_injected,
    test_validate_gos_evidence_good_narrative_passes,
    test_validate_gos_evidence_hallucination_fails,
    test_validate_gos_evidence_fake_txn_id_blocked,
    test_validate_gos_evidence_fact_coverage_returned,
    test_insufficient_evidence_recommendation,
    test_quality_checker_blocks_hallucination,
    test_quality_checker_passes_good_narrative,
    test_disposition_recorder_rejects_invalid_disposition,
    test_disposition_recorder_rejects_short_rationale,
    test_no_llm_raises_not_configured,
    test_screen_request_refuses_tipping_off,
    test_challenge_disposition_counter_evidence,
]

if __name__ == "__main__":
    print("Running offline tests (no network, no database)...\n")
    passed = 0
    failed = 0
    for test_fn in TESTS:
        try:
            test_fn()
            passed += 1
        except Exception as exc:
            failed += 1
            print(f"  [FAIL] {test_fn.__name__}: {exc}")
    print(f"\n{passed}/{passed+failed} tests passed.")
    if failed:
        sys.exit(1)
