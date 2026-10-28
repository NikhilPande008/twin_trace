"""
Tests for the Nebius edition's proof-carrying capabilities:

  - DB-enforced append-only ledger + hash chain (tamper DETECTION)
  - calculator of record: determinism, reproducibility, regulatory aggregation
  - hard gate accepting computed facts (and only exact ones as citations)
  - retrieval guardrail: NEEDS-VERIFICATION rules are unreachable
  - Token Factory client: parsing, tiering, retry policy, fail-loud when unconfigured
  - sandbox backend is an honest stub (refuses, never pretends)

No network, no API key. Usage:
    python3 tests/test_nebius_edition.py      or      pytest -q
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ddp import CoPilotSkills  # noqa: E402
from ddp.bootstrap import compute_params, open_store  # noqa: E402
from ddp.compute import ComputeError, ComputeRunner, NebiusSandboxBackend, reproduce  # noqa: E402
from ddp.config import Settings  # noqa: E402
from ddp.llm import LLMError, LLMNotConfigured, TokenFactoryClient  # noqa: E402


def _poe(triggered=3):
    from ddp.skills import POE_FACTORS
    return [{"factor_id": fid, "factor_name": fn,
             "assessment": "triggered" if i < triggered else "clear",
             "evidence": "x", "evidence_txn_ids": []} for i, (fid, fn) in enumerate(POE_FACTORS)]


def _record(skills, alert_id="ALERT-01", disposition="FILE", **kw):
    return skills.alert_disposition_recorder(
        alert_id=alert_id, customer_ref="CUST-01", disposition=disposition,
        rationale_text="Formed suspicion on pass-through to I4C-flagged counterparty.",
        rules_cited=["STR-001"], rfi_triggers=["RFI-001"], poe_assessment=_poe(), **kw)


# ── ledger integrity ─────────────────────────────────────────────────────────

def test_ledger_rejects_update_and_delete():
    store = open_store(":memory:")
    _record(CoPilotSkills(store))
    for sql in ("UPDATE DECISION_LEDGER SET DISPOSITION = 'NOT_FILE'", "DELETE FROM DECISION_LEDGER"):
        try:
            store._exec(sql)
            assert False, f"should have been rejected: {sql}"
        except sqlite3.IntegrityError as e:
            assert "append-only" in str(e)
    print("  [PASS] ledger — UPDATE and DELETE rejected by database triggers")


def test_hash_chain_verifies_and_detects_edit_and_removal():
    store = open_store(":memory:")
    skills = CoPilotSkills(store)
    for aid in ("ALERT-01", "ALERT-02", "ALERT-03"):
        _record(skills, alert_id=aid)
    assert store.verify_ledger_chain()["ok"]

    # Simulate an attacker with raw file access: drop the guard, edit a row.
    store._conn.executescript("DROP TRIGGER LEDGER_NO_UPDATE; DROP TRIGGER LEDGER_NO_DELETE;")
    store._exec("UPDATE DECISION_LEDGER SET DISPOSITION = 'NOT_FILE' WHERE SEQ = 2")
    v = store.verify_ledger_chain()
    assert not v["ok"] and v["first_break_seq"] == 2 and "edited" in v["detail"], v

    store2 = open_store(":memory:")
    s2 = CoPilotSkills(store2)
    for aid in ("ALERT-01", "ALERT-02", "ALERT-03"):
        _record(s2, alert_id=aid)
    store2._conn.executescript("DROP TRIGGER LEDGER_NO_DELETE;")
    store2._exec("DELETE FROM DECISION_LEDGER WHERE SEQ = 2")
    v2 = store2.verify_ledger_chain()
    assert not v2["ok"] and v2["first_break_seq"] == 3 and "removed" in v2["detail"], v2
    print("  [PASS] hash chain — verifies clean; detects an edited row and a removed row")


def test_recorder_writes_provenance_and_marks_reviewed():
    store = open_store(":memory:")
    skills = CoPilotSkills(store)
    run = ComputeRunner(store).run("ALERT-01", store.transactions_for("ALERT-01"), compute_params(store))
    res = _record(skills, compute_run_id=run["run_id"], ai_recommendation="FILE",
                  model_calls=[{"tier": "disposition", "model_reported": "nvidia/x"}])
    row = store.ledger_joined()[0]
    meta = json.loads(row["METADATA_JSON"])
    assert meta["compute_run_id"] == run["run_id"] and meta["model_calls"][0]["tier"] == "disposition"
    assert row["ROW_HASH"] == res["row_hash"] and row["PREV_HASH"] == "0" * 64
    assert store.get_alert("ALERT-01")["ALERT_STATUS"] == "REVIEWED"
    print("  [PASS] recorder — provenance (compute run, model calls) in ledger; alert REVIEWED")


# ── calculator of record ─────────────────────────────────────────────────────

def _facts(run):
    return {f["fact_id"]: f["value"] for f in run["facts"]}


def test_compute_alert01_figures():
    store = open_store(":memory:")
    run = ComputeRunner(store).run("ALERT-01", store.transactions_for("ALERT-01"), compute_params(store, "ALERT-01"))
    f = _facts(run)
    assert f["F-TOTAL-CREDIT"] == 345000
    assert f["F-TOTAL-DEBIT"] == 246500 + 94200
    assert f["F-FLAGGED-AMOUNT"] == 246500 + 94200
    assert f["F-PASSTHROUGH-BP"] == round((246500 + 94200) * 10000 / 345000)
    assert f["F-FAN-IN"] == 3 and f["F-FAN-OUT"] == 1
    assert store.get_compute_run(run["run_id"])["BACKEND"] == "local"
    # F-DECLARED-INCOME: KYC-declared monthly income must appear as a computed fact (INR)
    # so the evidence gate accepts ₹28,000 in a GoS narrative without blocking it.
    assert f["F-DECLARED-INCOME"] == 28000, "declared income must be a compute fact"
    print(f"  [PASS] compute ALERT-01 — credits 345000, debits {f['F-TOTAL-DEBIT']}, "
          f"pass-through {f['F-PASSTHROUGH-BP']/100:.2f}%, income {f['F-DECLARED-INCOME']}")


def test_compute_is_deterministic_and_reproducible():
    store = open_store(":memory:")
    runner = ComputeRunner(store)
    txns, params = store.transactions_for("ALERT-04"), compute_params(store)
    a, b = runner.run("ALERT-04", txns, params), runner.run("ALERT-04", txns, params)
    assert a["provenance"]["OUTPUT_SHA256"] == b["provenance"]["OUTPUT_SHA256"]
    assert a["provenance"]["INPUT_SHA256"] == b["provenance"]["INPUT_SHA256"]
    rep = reproduce(store.get_compute_run(a["run_id"]), txns, params)
    assert rep == {"input_matches": True, "code_matches": True, "output_matches": True}, rep
    # tamper with input -> input hash no longer matches
    bad = [dict(t) for t in txns]; bad[0]["amount_inr"] += 1
    rep2 = reproduce(store.get_compute_run(a["run_id"]), bad, params)
    assert rep2["input_matches"] is False and rep2["output_matches"] is False
    try:
        store._exec("DELETE FROM COMPUTE_RUNS")
        assert False, "COMPUTE_RUNS delete should be rejected"
    except sqlite3.IntegrityError:
        pass
    print("  [PASS] compute — same input -> same output hash; reproduce() verifies; runs append-only")


def test_compute_cash_threshold_aggregation():
    """Integrally connected sub-threshold cash in one month crossing the monthly threshold."""
    txns = [{"txn_id": f"C-{i}", "date": f"2026-08-{i:02d}", "type": "CREDIT",
             "amount_inr": 95000, "channel": "CASH", "counterparty": "self"} for i in range(1, 12)]
    txns.append({"txn_id": "C-99", "date": "2026-09-01", "type": "CREDIT", "amount_inr": 95000,
                 "channel": "CASH", "counterparty": "self"})
    run = ComputeRunner(None).run("SYN-1", txns, {"cash_threshold": {"amount_inr": 1_000_000,
                                                                      "rule_id": "CTR-001"}})
    f = _facts(run)
    assert f["F-CASH-2026-08-CREDIT"] == 11 * 95000
    assert f["F-CASH-2026-08-ABOVE-THRESHOLD"] == 1 and f["F-CASH-2026-08-ALL-BELOW"] == 1
    assert f["F-CASH-2026-09-ABOVE-THRESHOLD"] == 0
    print("  [PASS] compute — 11 x ₹95,000 cash in Aug = ₹10,45,000 > CTR-001 threshold, each below it")


def test_hard_gate_accepts_computed_fact_only_with_provenance():
    txns = [
        {"txn_id": "T-1", "date": "2026-07-10", "type": "CREDIT", "amount_inr": 400000, "channel": "CASH"},
        {"txn_id": "T-2", "date": "2026-07-20", "type": "CREDIT", "amount_inr": 350000, "channel": "CASH"},
        {"txn_id": "T-3", "date": "2026-08-05", "type": "CREDIT", "amount_inr": 300000, "channel": "CASH"},
    ]
    narrative = "Cash credits in July 2026 totalled ₹7,50,000 across two deposits."
    skills = CoPilotSkills(None)
    assert not skills.validate_gos_evidence(narrative, txns)["passed"], \
        "a monthly subtotal the model computed itself must NOT pass without provenance"
    run = ComputeRunner(None).run("SYN-2", txns, {})
    res = skills.validate_gos_evidence(narrative, txns, computed_facts=run["facts"])
    assert res["passed"], res
    assert res["fact_citations"] == {"₹7,50,000": ["F-CASH-2026-07-CREDIT"]}, res["fact_citations"]
    print("  [PASS] hard gate — ₹7,50,000 rejected alone, accepted and linked to F-CASH-2026-07-CREDIT")


def test_gos_writer_receives_computed_facts():
    store = open_store(":memory:")
    run = ComputeRunner(store).run("ALERT-01", store.transactions_for("ALERT-01"), compute_params(store))
    prompts = []

    def fake(prompt):
        prompts.append(prompt)
        if "Evaluate the draft" in prompt:  # quality checker
            return json.dumps([{"item_number": i + 1, "applies": False, "note": ""} for i in range(10)])
        return "I formed suspicion because credits of ₹3,45,000 were followed by ₹3,40,700 to a flagged handle."

    out = CoPilotSkills(store, complete_fn=fake).ground_of_suspicion_writer(
        {"transactions": store.transactions_for("ALERT-01")}, _poe(), computed=run)
    assert "F-TOTAL-DEBIT" in prompts[0] and run["run_id"] in prompts[0]
    assert out["hard_gate_passed"] and out["compute_run_id"] == run["run_id"]
    assert set(out["fact_citations"]["₹3,40,700"]) == {"F-TOTAL-DEBIT", "F-FLAGGED-AMOUNT"}
    print("  [PASS] GoS writer — computed facts in prompt; figures linked to fact ids")


# ── retrieval guardrail ──────────────────────────────────────────────────────

def test_needs_verification_rules_unreachable():
    store = open_store(":memory:")
    skills = CoPilotSkills(store)
    nv = store.corpus_rows(("NEEDS-VERIFICATION",))
    assert nv, "fixture: corpus should contain NV rules"
    for r in nv:
        # query with the NV rule's own id and text — the strongest possible match
        for q in (r["RULE_ID"], r["RULE_TEXT"][:200]):
            ids = {x["rule_id"] for x in skills.regulatory_lookup(q, limit=10)}
            assert r["RULE_ID"] not in ids, f"{r['RULE_ID']} leaked for query {q[:40]!r}"
    print(f"  [PASS] retrieval — none of {len(nv)} NEEDS-VERIFICATION rules reachable, even by own text")


# ── Token Factory client ─────────────────────────────────────────────────────

class _Resp:
    def __init__(self, status, body):
        self.status_code, self._body = status, body
        self.text = json.dumps(body)

    def json(self):
        return self._body


def _settings(**kw):
    base = dict(base_url="https://example.invalid/v1/", api_key="k",
                models={"triage": "m-nano", "reasoning": "m-super", "disposition": "m-ultra"},
                request_timeout_s=5)
    base.update(kw)
    return Settings(**base)


def test_llm_client_parses_and_records_call():
    seen = {}

    def post(url, headers, json, timeout):
        seen.update(url=url, model=json["model"], auth=headers["Authorization"])
        return _Resp(200, {"model": "m-ultra", "usage": {"prompt_tokens": 10, "completion_tokens": 5},
                           "choices": [{"message": {"content": "<think>scratch</think>Final text."}}]})

    c = TokenFactoryClient(_settings(), _post=post)
    assert c.complete("hi", tier="disposition") == "Final text."
    assert seen["url"].endswith("/v1/chat/completions") and seen["model"] == "m-ultra"
    assert c.last_call["tier"] == "disposition" and c.last_call["usage"]["completion_tokens"] == 5
    assert c.last_call["reasoning_chars"] == len("<think>scratch</think>")
    print("  [PASS] llm — OpenAI-compatible call, tier->model, <think> stripped, usage recorded")


def test_llm_client_retry_policy_and_unconfigured():
    import ddp.llm as llm_mod
    llm_mod.time.sleep = lambda s: None  # no real waiting in tests
    calls = []

    def flaky(url, headers, json, timeout):
        calls.append(1)
        if len(calls) == 1:
            return _Resp(429, {"error": "rate"})
        return _Resp(200, {"choices": [{"message": {"content": "ok"}}]})

    assert TokenFactoryClient(_settings(), _post=flaky).complete("x") == "ok" and len(calls) == 2

    calls.clear()

    def unauthorized(url, headers, json, timeout):
        calls.append(1)
        return _Resp(401, {"error": "bad key"})

    try:
        TokenFactoryClient(_settings(), _post=unauthorized).complete("x")
        assert False
    except LLMError as e:
        assert "401" in str(e) and len(calls) == 1, "4xx must not be retried"

    try:
        TokenFactoryClient(_settings(api_key=None)).complete("x")
        assert False
    except LLMNotConfigured:
        pass
    print("  [PASS] llm — 429 retried, 401 not retried, missing key fails loudly")


def test_sandbox_backend_is_honest_stub():
    try:
        ComputeRunner(None, NebiusSandboxBackend()).run("A", [], {})
        assert False, "stub must refuse"
    except ComputeError as e:
        assert "T1.3" in str(e)
    print("  [PASS] sandbox backend — refuses until wired (no pretend execution)")


def test_build_passes_api_key_to_sandbox_backend():
    """T7.4: the configured key reaches the sandbox backend. Construction only; no network."""
    from ddp.bootstrap import build
    from ddp.config import Settings
    settings = Settings(api_key="test-key", compute_backend="nebius-sandbox")
    _, _, runner, _ = build(settings=settings, store=open_store(":memory:"))
    assert isinstance(runner.backend, NebiusSandboxBackend)
    assert runner.backend.api_key == "test-key"


# ── structured output: repair retry + fail-closed ────────────────────────────

def test_suspicion_evaluator_repair_retry():
    """A parse failure on the first attempt triggers a repair prompt; second response is accepted."""
    from ddp import CoPilotSkills
    from ddp.skills import POE_FACTORS
    calls = []

    valid_json = json.dumps([
        {"factor_id": fid, "factor_name": fn, "assessment": "triggered",
         "evidence": "x", "evidence_txn_ids": [], "rules_cited": []}
        for fid, fn in POE_FACTORS
    ])

    def fake(prompt: str) -> str:
        calls.append(prompt)
        if len(calls) == 1:
            return "Not valid JSON at all"
        return valid_json  # second call succeeds

    result = CoPilotSkills(None, complete_fn=fake).suspicion_evaluator({})
    assert len(calls) == 2, f"expected 2 calls (initial + repair), got {len(calls)}"
    assert result[0]["assessment"] == "triggered"
    print("  [PASS] suspicion_evaluator — parse failure triggers repair retry; second response accepted")


def test_suspicion_evaluator_double_failure_returns_insufficient():
    """Double parse failure degrades to all insufficient_data (never raises)."""
    from ddp import CoPilotSkills
    calls = []

    def fake(prompt: str) -> str:
        calls.append(prompt)
        return "still not json"

    result = CoPilotSkills(None, complete_fn=fake).suspicion_evaluator({})
    assert len(calls) == 2, f"expected 2 calls, got {len(calls)}"
    assert all(r["assessment"] == "insufficient_data" for r in result)
    print("  [PASS] suspicion_evaluator — double parse failure → all insufficient_data, no exception")


def test_str_quality_checker_fail_closed_on_double_failure():
    """str_quality_checker FAILS CLOSED on double parse failure (T3.4 fix): quality_score=0."""
    from ddp import CoPilotSkills

    def fake(_: str) -> str:
        return "not json"

    result = CoPilotSkills(None, complete_fn=fake).str_quality_checker(
        "narrative", {"transactions": [], "customer_kyc": ""})
    assert result["quality_score"] == 0, \
        f"fail-closed must give quality_score=0, got {result['quality_score']}"
    assert result["recommendation"] == "REJECT"
    assert len(result["failures"]) == 10
    print("  [PASS] str_quality_checker — double parse failure → quality_score=0 (fail closed, not fail open)")


def test_token_usage_summary():
    store = open_store(":memory:")
    skills = CoPilotSkills(store)
    # Decision without model calls
    _record(skills, alert_id="ALERT-01")
    u = store.token_usage_summary()
    assert u["total"] == 0 and u["decisions_with_model_calls"] == 0

    # Decision with two model calls across different tiers
    _record(skills, alert_id="ALERT-02", model_calls=[
        {"tier": "reasoning",    "usage": {"prompt_tokens": 1000, "completion_tokens": 200}},
        {"tier": "disposition",  "usage": {"prompt_tokens": 2000, "completion_tokens": 400}},
    ])
    u2 = store.token_usage_summary()
    assert u2["total_prompt"] == 3000
    assert u2["total_completion"] == 600
    assert u2["total"] == 3600
    assert u2["decisions_with_model_calls"] == 1
    assert u2["by_tier"]["reasoning"]["prompt"] == 1000
    assert u2["by_tier"]["disposition"]["completion"] == 400
    print("  [PASS] token_usage_summary — aggregates prompt+completion tokens by tier across decisions")


TESTS = [
    test_ledger_rejects_update_and_delete,
    test_hash_chain_verifies_and_detects_edit_and_removal,
    test_recorder_writes_provenance_and_marks_reviewed,
    test_compute_alert01_figures,
    test_compute_is_deterministic_and_reproducible,
    test_compute_cash_threshold_aggregation,
    test_hard_gate_accepts_computed_fact_only_with_provenance,
    test_gos_writer_receives_computed_facts,
    test_needs_verification_rules_unreachable,
    test_llm_client_parses_and_records_call,
    test_llm_client_retry_policy_and_unconfigured,
    test_sandbox_backend_is_honest_stub,
    test_build_passes_api_key_to_sandbox_backend,
    test_suspicion_evaluator_repair_retry,
    test_suspicion_evaluator_double_failure_returns_insufficient,
    test_str_quality_checker_fail_closed_on_double_failure,
    test_token_usage_summary,
]

if __name__ == "__main__":
    print("Running Nebius-edition tests (no network, no API key)...\n")
    passed = failed = 0
    for fn in TESTS:
        try:
            fn()
            passed += 1
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  [FAIL] {fn.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{passed}/{passed + failed} tests passed.")
    if failed:
        sys.exit(1)
