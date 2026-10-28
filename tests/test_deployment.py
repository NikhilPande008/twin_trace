"""
T7: public-demo isolation and call budget; decisions persist across a restart on the normal
file database. Offline.
"""
from __future__ import annotations

import pytest

from ddp.bootstrap import build, open_store
from ddp.config import Settings
from ddp.llm import CallBudget, FunctionLLM, LLMError
from ddp.skills import POE_FACTORS

POE = [{"factor_id": f, "factor_name": n, "assessment": "clear"} for f, n in POE_FACTORS]
TEXT = "Formed suspicion on the pass-through to the flagged handle."


def _record(skills):
    return skills.alert_disposition_recorder(
        alert_id="ALERT-01", customer_ref="CUST-01", disposition="FILE", rationale_text=TEXT,
        rules_cited=[], rfi_triggers=[], poe_assessment=POE)


def test_budget_refuses_visibly_after_limit():
    llm = CallBudget(FunctionLLM(lambda p: "ok"), max_calls=2)
    assert llm.complete("a") == "ok" and llm.complete("b") == "ok"
    with pytest.raises(LLMError) as e:
        llm.complete("c")
    assert e.value.kind == "budget"


def test_demo_mode_wraps_the_model_with_a_budget():
    s = Settings(api_key="k", demo_mode=True, demo_max_model_calls=3)
    _, skills, _, _ = build(s, store=open_store(":memory:"))
    assert isinstance(skills._llm, CallBudget) and skills._llm.max_calls == 3


def test_demo_sessions_are_isolated():
    s = Settings(demo_mode=True)
    a = build(s, store=open_store(":memory:"))
    b = build(s, store=open_store(":memory:"))
    _record(a[1])
    assert len(a[0].ledger_joined()) == 1
    assert b[0].ledger_joined() == []
    assert b[0].get_alert("ALERT-01")["ALERT_STATUS"] != "REVIEWED"


def test_decision_survives_restart_on_file_database(tmp_path):
    path = tmp_path / "ddp.sqlite3"
    store, skills, _, _ = build(Settings(), store=open_store(path))
    did = _record(skills)["decision_id"]
    store._conn.close()
    reopened = open_store(path)                     # a normal restart: same file, new process
    rows = reopened.ledger_joined()
    assert [r["DECISION_ID"] for r in rows] == [did]
    assert reopened.verify_ledger_chain()["ok"]
