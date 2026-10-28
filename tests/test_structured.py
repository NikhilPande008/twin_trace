"""Structured output: local schema validation and the json_schema -> json_object fallback."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from ddp import structured as S  # noqa: E402
from ddp.bootstrap import open_store  # noqa: E402
from ddp.llm import LLMError  # noqa: E402
from ddp.skills import CoPilotSkills  # noqa: E402


def _factor(i, assessment="clear"):
    return {"factor_id": S.POE_IDS[i], "factor_name": "x", "assessment": assessment,
            "evidence": "e", "evidence_txn_ids": [], "rules_cited": []}


def test_wrapped_and_bare_arrays_validate():
    factors = [_factor(i) for i in range(11)]
    assert S.parse_and_validate(json.dumps({"factors": factors}), "poe_assessment")
    assert S.parse_and_validate("```json\n" + json.dumps(factors) + "\n```", "poe_assessment")


@pytest.mark.parametrize("mutate,msg", [
    (lambda f: f[:10], "10 items"),
    (lambda f: [dict(f[0], assessment="maybe")] + f[1:], "not in"),
    (lambda f: [{k: v for k, v in f[0].items() if k != "evidence"}] + f[1:], "missing"),
])
def test_schema_violations_raise(mutate, msg):
    factors = mutate([_factor(i) for i in range(11)])
    with pytest.raises(S.SchemaError, match=msg):
        S.parse_and_validate(json.dumps({"factors": factors}), "poe_assessment")


def test_prose_around_json_is_tolerated():
    raw = 'Here you go: {"summary": "s", "load_bearing_evidence": [], "reopen_triggers": []} done'
    assert S.parse_and_validate(raw, "stress_memo")["summary"] == "s"


def test_response_format_modes():
    assert S.response_format("stress_memo", "json_object") == {"type": "json_object"}
    rf = S.response_format("stress_memo", "json_schema")
    assert rf["type"] == "json_schema" and rf["json_schema"]["strict"] is True


class _LLM:
    """First json_schema call -> HTTP 400; then answers. Second reply invalid unless repaired."""

    def __init__(self, replies):
        self.replies, self.formats, self.last_call = list(replies), [], {}

    def complete(self, prompt, tier="reasoning", response_format=None, **_):
        self.formats.append(response_format)
        if response_format and response_format.get("type") == "json_schema":
            raise LLMError("Token Factory call failed. HTTP 400: json_schema unsupported")
        return self.replies.pop(0)


def test_schema_rejection_falls_back_and_repair_retry(monkeypatch):
    monkeypatch.setenv("STRUCTURED_OUTPUT_MODE", "json_schema")
    good = json.dumps({"summary": "s", "load_bearing_evidence": [], "reopen_triggers": []})
    llm = _LLM(["not json", good])
    skills = CoPilotSkills(open_store(":memory:"), llm=llm)
    obj, repairs = skills._complete_structured("p", "triage", "stress_memo")
    assert obj["summary"] == "s" and repairs == 1
    assert skills.last_model_call.get("structured_mode") == "json_object"
    # the tier is remembered: the repair call went straight to json_object
    assert [f["type"] for f in llm.formats] == ["json_schema", "json_object", "json_object"]
