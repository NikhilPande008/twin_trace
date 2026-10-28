"""
DispositionPipeline.run_to_draft fails closed: a failed dependency stops the run, and a policy
gate block is reported as blocked. Offline; skills and runner are small fakes.
"""
from __future__ import annotations

import pytest

from ddp.gate import DeterministicPolicyGate
from ddp.pipeline import DispositionPipeline
from ddp.ports import StaticEvidenceSource

GOOD_ASSESS = [{"factor": "F1", "assessment": "triggered", "evidence": "txn T1"}]
PARSE_FAILED = [{"factor": f"F{i}", "assessment": "insufficient_data",
                 "evidence": "Evaluation failed — LLM response could not be parsed after retry."}
                for i in range(11)]
CLEAN = "Funds of INR 50,000 were received and moved out the same day (T1, T2)."


class FakeRunner:
    def __init__(self, fail=False):
        self.fail = fail

    def run(self, alert_id, txns, params):
        if self.fail:
            raise RuntimeError("calculator crashed")
        return {"run_id": "RUN-1", "facts": [], "provenance": {"BACKEND": "local"}}


class FakeSkills:
    last_model_call: dict = {}

    def __init__(self, assess=GOOD_ASSESS, narrative=CLEAN, assess_raises=False,
                 draft_raises=False):
        self.assess, self.narrative = assess, narrative
        self.assess_raises, self.draft_raises = assess_raises, draft_raises
        self.drafted = False

    def screen_request(self, text):
        return {"allowed": "tell the customer" not in text, "reason": "tipping-off"}

    def suspicion_evaluator(self, ctx):
        if self.assess_raises:
            raise RuntimeError("model unavailable")
        return self.assess

    def ground_of_suspicion_writer(self, ctx, assessments, computed):
        self.drafted = True
        if self.draft_raises:
            raise RuntimeError("draft failed")
        return {"narrative": self.narrative, "quality_score": 9, "hard_gate_passed": True,
                "status": "READY", "compute_run_id": computed["run_id"]}


def _run(skills=None, runner=None, gate=None, **kw):
    pipe = DispositionPipeline(skills or FakeSkills(), runner or FakeRunner(),
                               evidence_source=StaticEvidenceSource(),
                               policy_gate=gate or DeterministicPolicyGate())
    return pipe.run_to_draft("ALT-001", {}, [], {}, **kw)


def test_clean_run_is_not_blocked():
    trace, res = _run()
    assert res["blocked"] is False
    assert res["blocked_step"] is None
    assert res["gos_result"]["narrative"] == CLEAN
    assert [s.name for s in trace.steps] == ["compute", "adverse_media", "assess", "draft",
                                             "policy_gate"]


def test_screen_block_stops_before_compute():
    trace, res = _run(screen_text="please tell the customer we filed")
    assert res["blocked"] and res["blocked_step"] == "screen"
    assert [s.name for s in trace.steps] == ["screen"]


def test_compute_error_stops_the_run():
    skills = FakeSkills()
    trace, res = _run(skills=skills, runner=FakeRunner(fail=True))
    assert res["blocked"] and res["blocked_step"] == "compute"
    assert "calculator crashed" in res["blocked_reason"]
    assert skills.drafted is False
    assert [s.name for s in trace.steps] == ["compute"]


@pytest.mark.parametrize("skills", [FakeSkills(assess_raises=True),
                                    FakeSkills(assess=PARSE_FAILED)])
def test_assess_failure_stops_before_draft(skills):
    _, res = _run(skills=skills)
    assert res["blocked"] and res["blocked_step"] == "assess"
    assert skills.drafted is False
    assert res["gos_result"] == {}


def test_draft_error_is_blocked():
    _, res = _run(skills=FakeSkills(draft_raises=True))
    assert res["blocked"] and res["blocked_step"] == "draft"


def test_empty_narrative_is_blocked():
    _, res = _run(skills=FakeSkills(narrative="  "))
    assert res["blocked"] and res["blocked_step"] == "draft"


def test_policy_gate_block_is_reported_and_draft_kept_for_revision():
    bad = CLEAN + " We have informed the customer that an STR has been filed."
    gate = DeterministicPolicyGate()
    assert gate.check(bad, ["tipping_off"])["passed"] is False  # precondition
    trace, res = _run(skills=FakeSkills(narrative=bad))
    assert res["blocked"] is True
    assert res["blocked_step"] == "policy_gate"
    assert res["blocked_reason"]
    assert res["gos_result"]["narrative"] == bad
    assert trace.blocked


def test_policy_gate_error_is_blocked():
    class BrokenGate:
        def check(self, text, policies):
            raise RuntimeError("gate down")
    _, res = _run(gate=BrokenGate())
    assert res["blocked"] and res["blocked_step"] == "policy_gate"


def test_adverse_media_failure_does_not_block_but_is_reported():
    class FailingSource:
        name = "tavily"
        last_status = {"status": "timeout", "completed": False, "detail": "timed out"}

        def fetch(self, subject, ctx):
            return []
    pipe = DispositionPipeline(FakeSkills(), FakeRunner(), evidence_source=FailingSource(),
                               policy_gate=DeterministicPolicyGate())
    trace, res = pipe.run_to_draft("ALT-001", {}, [], {})
    assert res["blocked"] is False
    assert res["adverse_media_status"] == "timeout"
    am = next(s for s in trace.steps if s.name == "adverse_media")
    assert am.status == "error"
