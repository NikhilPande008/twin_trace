"""
T7.3: the live-eval runner must not count a fallback assessment as model success. Offline.
"""
from __future__ import annotations

import json

from ddp.skills import POE_FACTORS, CoPilotSkills
from scripts.run_live_eval import assessment_outcome

CTX = {"customer_kyc": "Salaried; Rs.28K/month declared", "transactions": [],
       "signal_tags": [], "alert_narrative": "synthetic"}


def _valid_output() -> str:
    return json.dumps({"factors": [
        {"factor_id": fid, "factor_name": name, "assessment": "clear", "evidence": "none",
         "evidence_txn_ids": [], "rules_cited": []} for fid, name in POE_FACTORS]})


def _run(responses):
    it = iter(responses)
    skills = CoPilotSkills(None, complete_fn=lambda prompt: next(it))
    out = skills.suspicion_evaluator(CTX)
    return out, assessment_outcome(skills.last_model_call)


def test_unparseable_model_is_fallback_not_success():
    out, outcome = _run(["not json", "still not json"])
    assert outcome == "fallback"
    assert all(a["assessment"] == "insufficient_data" for a in out)


def test_first_try_is_success():
    _, outcome = _run([_valid_output()])
    assert outcome == "success"


def test_one_repair_is_repaired():
    _, outcome = _run(["garbage", _valid_output()])
    assert outcome == "repaired"


def test_outcome_from_flags():
    assert assessment_outcome({}) == "success"
    assert assessment_outcome(None) == "success"
    assert assessment_outcome({"parse_failures": 1}) == "repaired"
    assert assessment_outcome({"parse_failures": 2}) == "fallback"
    assert assessment_outcome({"fallback": True}) == "fallback"
