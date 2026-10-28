"""
T4: injected faults produce accurate, visible states — never a silent success. Offline.
"""
from __future__ import annotations

import json
import types

import pytest

from ddp import llm as L
from ddp.config import Settings
from ddp.llm import LLMError, TokenFactoryClient
from ddp.pipeline import DispositionPipeline
from ddp.ports import StaticEvidenceSource
from ddp.skills import POE_FACTORS, CoPilotSkills


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(L.time, "sleep", lambda s: None)


def _client(post):
    return TokenFactoryClient(Settings(api_key="test-key"), _post=post)


def _resp(status=200, content="", finish="stop", usage=None):
    r = types.SimpleNamespace(status_code=status, text=f"status {status}")
    r.json = lambda: {"model": "m", "usage": usage or {"prompt_tokens": 10, "completion_tokens": 5,
                                                       "total_tokens": 15},
                      "choices": [{"message": {"content": content}, "finish_reason": finish}]}
    return r


def _valid():
    return json.dumps({"factors": [
        {"factor_id": f, "factor_name": n, "assessment": "clear", "evidence": "none",
         "evidence_txn_ids": [], "rules_cited": []} for f, n in POE_FACTORS]})


class ReadTimeout(Exception):
    pass


@pytest.mark.parametrize("post, kind", [
    (lambda *a, **k: (_ for _ in ()).throw(ReadTimeout("read timed out")), "timeout"),
    (lambda *a, **k: _resp(429), "rate_limited"),
    (lambda *a, **k: _resp(503), "server_error"),
    (lambda *a, **k: _resp(401), "client_error"),
])
def test_transport_failures_are_classified_and_recorded(post, kind):
    c = _client(post)
    with pytest.raises(LLMError) as e:
        c.complete("hi", "triage")
    assert e.value.kind == kind
    assert c.last_call["failed"] and c.last_call["error_kind"] == kind
    expected_attempts = 1 if kind == "client_error" else 3      # no retry on a 4xx
    assert len(c.last_call["transport_errors"]) == expected_attempts


def test_success_after_429_keeps_the_failed_attempt():
    seq = iter([_resp(429), _resp(content="ok")])
    c = _client(lambda *a, **k: next(seq))
    assert c.complete("hi", "triage") == "ok"
    assert c.last_call["attempts"] == 2
    assert c.last_call["transport_errors"][0]["kind"] == "rate_limited"


def test_malformed_then_valid_counts_both_attempts():
    seq = iter([_resp(content="not json"), _resp(content=_valid())])
    skills = CoPilotSkills(None, llm=_client(lambda *a, **k: next(seq)))
    skills.suspicion_evaluator({"transactions": [], "customer_kyc": "", "signal_tags": [],
                                "alert_narrative": ""})
    mc = skills.last_model_call
    assert mc["parse_failures"] == 1 and len(mc["all_attempts"]) == 2
    assert mc["usage_all_attempts"]["total_tokens"] == 30          # both attempts, not the last


def test_truncation_is_flagged_and_falls_back_visibly():
    seq = iter([_resp(content='{"factors": [', finish="length")] * 2)
    skills = CoPilotSkills(None, llm=_client(lambda *a, **k: next(seq)))
    out = skills.suspicion_evaluator({"transactions": [], "customer_kyc": "", "signal_tags": [],
                                      "alert_narrative": ""})
    mc = skills.last_model_call
    assert mc["truncated"] and mc["fallback"]
    assert all(f["assessment"] == "insufficient_data" for f in out)


def test_provider_failure_during_structured_call_is_logged():
    skills = CoPilotSkills(None, llm=_client(lambda *a, **k: _resp(503)))
    with pytest.raises(LLMError):
        skills._complete_structured("x", "triage", "poe_assessment")
    assert skills.call_log[-1]["failed"] and skills.call_log[-1]["error_kind"] == "server_error"


def test_calculator_failure_blocks_the_pipeline():
    class Broken:
        def run(self, *a, **k):
            raise RuntimeError("calculator crashed")
    _, res = DispositionPipeline(CoPilotSkills(None), Broken(),
                                 evidence_source=StaticEvidenceSource()).run_to_draft(
        "A", {}, [], {})
    assert res["blocked"] and res["blocked_step"] == "compute"


def test_agent_tool_exception_is_returned_not_raised():
    from ddp.agent import Investigator, _CaseState
    inv = Investigator(None, None, None, None, lambda a: {})
    inv._tool_get_case = lambda s: 1 / 0
    out = inv._dispatch(_CaseState("A", {}, []), "get_case", {})
    assert "get_case failed: ZeroDivisionError" in out["error"]


def test_agent_tool_budget():
    from tests.test_agent import GOOD_SUBMIT, _inv
    inv, _, _ = _inv([{"calls": [("get_case", {})] * 5}] * 10)
    inv.max_tool_calls = 7
    t = inv.investigate("ALERT-01")
    assert t["status"] == "budget_exhausted" and t["tool_calls"] == 7
    assert t["trace_id"].startswith("AGENT-")
    assert GOOD_SUBMIT  # imported helper still valid


def test_agent_does_not_repeat_external_search():
    from tests.test_agent import _inv
    calls = []

    class Source:
        api_key, name, last_status = "k", "tavily", {"status": "no_results", "completed": True}

        def fetch(self, subject, ctx):
            calls.append(1)
            return []
    inv, _, _ = _inv([{"calls": [("get_case", {}), ("screen_adverse_media", {}),
                                 ("screen_adverse_media", {})]}])
    inv.evidence_source = Source()
    inv.investigate("ALERT-01")
    assert len(calls) == 1
