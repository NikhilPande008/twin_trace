"""Agentic investigator — offline tests with a scripted tool-calling model."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ddp.agent import Investigator  # noqa: E402
from ddp.bootstrap import compute_params, open_store  # noqa: E402
from ddp.compute import ComputeRunner  # noqa: E402
from ddp.llm import normalise_tool_calls  # noqa: E402
from ddp.skills import CoPilotSkills  # noqa: E402


class ScriptedLLM:
    """Plays back a fixed list of assistant turns; records the messages it was sent."""

    def __init__(self, turns):
        self.turns, self.sent, self.last_call = list(turns), [], {}

    def chat(self, messages, tier, tools=None, **_):
        self.sent.append([dict(m) for m in messages])
        self.last_call = {"provider": "scripted", "tier": tier,
                          "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
        turn = self.turns.pop(0) if self.turns else {"content": "done"}
        return {"role": "assistant", "content": turn.get("content", ""),
                "tool_calls": [{"id": f"c{i}", "name": n, "arguments": a}
                               for i, (n, a) in enumerate(turn.get("calls", []))]}


def _inv(turns):
    store = open_store(":memory:")
    skills = CoPilotSkills(store)
    llm = ScriptedLLM(turns)
    inv = Investigator(llm, store, skills, ComputeRunner(store),
                       lambda a: compute_params(store, a))
    return inv, store, llm


GOOD_SUBMIT = {"disposition": "FILE",
               "rationale": "Debits T01-3 (246500) and T01-5 (94200) went to an I4C-flagged "
                            "handle; flagged outflow is 98.75% of credits (F-FLAGGED-SHARE-BP); "
                            "credits are 12.3x declared income.",
               "cited_fact_ids": ["F-FLAGGED-SHARE-BP", "F-INCOME-MULTIPLE-X10"],
               "cited_txn_ids": ["T01-3", "T01-5"], "cited_rule_ids": []}


def test_full_loop_submits_and_logs_every_step():
    inv, store, llm = _inv([
        {"calls": [("get_case", {}), ("run_calculator", {})]},
        {"calls": [("stress_test", {"disposition": "FILE"})]},
        {"calls": [("submit_assessment", GOOD_SUBMIT)]},
    ])
    t = inv.investigate("ALERT-01")
    assert t["status"] == "submitted", t
    assert t["assessment"]["disposition"] == "FILE" and t["assessment"]["advisory"]
    steps = store.evidence_for_alert("ALERT-01", "agent_step")
    assert len(steps) == len(t["steps"]) == 4
    assert t["tokens"] == {"prompt": 30, "completion": 15}
    # tool results are fed back with the matching tool_call_id
    assert any(m["role"] == "tool" and m["tool_call_id"] == "c0" for m in llm.sent[1])


def test_invented_number_is_rejected_then_fixed():
    bad = dict(GOOD_SUBMIT, rationale="About 3,41,000 left the account within days.")
    inv, _, _ = _inv([
        {"calls": [("get_case", {}), ("run_calculator", {}),
                   ("stress_test", {"disposition": "FILE"})]},
        {"calls": [("submit_assessment", bad)]},
        {"calls": [("submit_assessment", GOOD_SUBMIT)]},
    ])
    t = inv.investigate("ALERT-01")
    assert t["status"] == "submitted" and t["rejections"] == 1
    rejected = [s for s in t["steps"] if s["tool"] == "submit_assessment"][0]
    assert "341000" in rejected["result_preview"]


def test_lakh_and_crore_figures_are_checked_as_amounts():
    """'₹3 lakh' is 3,00,000, not the ordinal 3; it must match a tool figure exactly."""
    bad = dict(GOOD_SUBMIT, rationale=GOOD_SUBMIT["rationale"] + " Roughly ₹3 lakh moved out.")
    inv, _, _ = _inv([
        {"calls": [("get_case", {}), ("run_calculator", {}),
                   ("stress_test", {"disposition": "FILE"})]},
        {"calls": [("submit_assessment", bad)]},
        {"calls": [("submit_assessment", GOOD_SUBMIT)]},
    ])
    t = inv.investigate("ALERT-01")
    assert t["status"] == "submitted" and t["rejections"] == 1
    rejected = [s for s in t["steps"] if s["tool"] == "submit_assessment"][0]
    assert "rupee amounts not equal" in rejected["result_preview"]


def _rejection_for(submit):
    inv, _, _ = _inv([
        {"calls": [("get_case", {}), ("run_calculator", {}),
                   ("stress_test", {"disposition": "FILE"})]},
        {"calls": [("submit_assessment", submit)]},
        {"calls": [("submit_assessment", GOOD_SUBMIT)]},
    ])
    t = inv.investigate("ALERT-01")
    assert t["status"] == "submitted" and t["rejections"] == 1
    return [s for s in t["steps"] if s["tool"] == "submit_assessment"][0]["result_preview"]


def test_thin_rationale_is_rejected():
    assert "substantive" in _rejection_for(dict(GOOD_SUBMIT, rationale="File it."))


def test_rationale_without_citations_is_rejected():
    assert "substantive" in _rejection_for(dict(GOOD_SUBMIT, cited_fact_ids=[], cited_txn_ids=[]))


def test_customer_disclosure_in_agent_rationale_is_rejected():
    bad = dict(GOOD_SUBMIT, rationale=GOOD_SUBMIT["rationale"]
               + " We will inform the customer that an STR is being prepared.")
    assert "policy gate" in _rejection_for(bad)


def test_submission_without_reading_the_case_is_rejected():
    inv, _, _ = _inv([
        {"calls": [("run_calculator", {}), ("stress_test", {"disposition": "FILE"})]},
        {"calls": [("submit_assessment", GOOD_SUBMIT)]},
        {"calls": [("get_case", {})]},
        {"calls": [("submit_assessment", GOOD_SUBMIT)]},
    ])
    t = inv.investigate("ALERT-01")
    first = [s for s in t["steps"] if s["tool"] == "submit_assessment"][0]
    assert "get_case" in first["result_preview"] and t["status"] == "submitted"


def test_unknown_citations_and_missing_stress_test_are_rejected():
    inv, _, _ = _inv([
        {"calls": [("run_calculator", {})]},
        {"calls": [("submit_assessment", dict(GOOD_SUBMIT, cited_fact_ids=["F-MADE-UP"],
                                              cited_rule_ids=["STR-001"]))]},
    ])
    t = inv.investigate("ALERT-01")
    assert t["status"] == "max_steps" or t["status"] == "no_submission"
    preview = [s for s in t["steps"] if s["tool"] == "submit_assessment"][0]["result_preview"]
    assert "F-MADE-UP" in preview and "STR-001" in preview and "stress_test" in preview


def test_tipping_off_refused_before_any_model_call():
    inv, _, llm = _inv([{"calls": [("get_case", {})]}])
    t = inv.investigate("ALERT-01", "Draft a message to tell the customer we filed an STR")
    assert t["status"] == "refused" and llm.sent == []


def test_regulator_search_refuses_case_identifiers():
    inv, _, _ = _inv([
        {"calls": [("check_regulator_updates", {"topic": "UPI handle C (I4C-flagged) rules"})]},
    ])
    t = inv.investigate("ALERT-01")
    assert "case identifiers" in t["steps"][0]["result_preview"]


def test_bounded_loop():
    inv, _, _ = _inv([{"calls": [("get_case", {})]}] * 50)
    inv.max_steps = 4
    t = inv.investigate("ALERT-01")
    assert t["status"] == "max_steps" and len(t["steps"]) == 4


def test_empty_tool_arguments_normalised():
    calls = normalise_tool_calls([{"id": "x", "function": {"name": "get_case", "arguments": ""}},
                                  {"function": {"name": "lookup_rule",
                                                "arguments": json.dumps({"question": "q"})}}])
    assert calls[0]["arguments"] == {} and calls[1]["arguments"] == {"question": "q"}
    assert calls[1]["id"] == "call_1"


def test_progress_events_follow_the_loop():
    bad = dict(GOOD_SUBMIT, rationale="About 3,41,000 left the account within days.")
    inv, _, _ = _inv([
        {"calls": [("get_case", {}), ("run_calculator", {}),
                   ("stress_test", {"disposition": "FILE"})]},
        {"calls": [("submit_assessment", bad)]},
        {"calls": [("submit_assessment", GOOD_SUBMIT)]},
    ])
    events = []
    t = inv.investigate("ALERT-01", on_event=events.append)
    assert t["status"] == "submitted"
    assert sum(e.startswith("Step ") for e in events) == 3
    assert "  get_case: ok" in events
    assert "  submit_assessment: rejected by validation, sent back" in events
    assert events[-1] == "  submit_assessment: accepted by validation"
