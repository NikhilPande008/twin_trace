"""Order-pattern scenarios (T12.2): fact patterns from FIU-IND Section 13 orders, replayed through
the real recorder, inspector, watch and inbox on an in-memory store."""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from ddp.bootstrap import compute_params, open_store  # noqa: E402
from ddp.compute import ComputeRunner  # noqa: E402
from ddp.enforcement import order_scenarios, orders  # noqa: E402
from ddp.inspection import inspect_decision  # noqa: E402
from ddp.skills import POE_FACTORS, CoPilotSkills  # noqa: E402
from ddp.stress import StressTester  # noqa: E402
from ddp.watch import DecisionWatch, alert_reasons, load_feed, registry_event  # noqa: E402

POE = [{"factor_id": f, "factor_name": n, "assessment": "clear"} for f, n in POE_FACTORS]
SCEN = {s["id"]: s for s in order_scenarios()}


def _record(store, runner, alert_id, disposition, text, customer_ref=None, days_ago=0,
            full=True):
    a = store.get_alert(alert_id)
    run_id = None
    if full:
        txns, params = store.transactions_for(alert_id), compute_params(store, alert_id)
        StressTester(runner, store).run(alert_id, txns, params, disposition=disposition)
        run_id = runner.run(alert_id, txns, params)["run_id"]
    formed = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat() if days_ago else None
    return CoPilotSkills(store).alert_disposition_recorder(
        alert_id=alert_id, customer_ref=customer_ref or a["CUSTOMER_REF"],
        disposition=disposition, rationale_text=text,
        rules_cited=json.loads(a["RULES_CITED"]), rfi_triggers=[], poe_assessment=POE,
        compute_run_id=run_id, suspicion_formed_at=formed)["decision_id"]


def _status(result, qid):
    return next(r for r in result["results"] if r["id"] == qid)["status"]


def test_every_scenario_cites_a_coded_order():
    ids = {o["order_id"] for o in orders()}
    assert all(s["source"] in ids for s in order_scenarios())


def test_os01_repeat_cursory_closures_are_counted_and_questioned():
    s, store = SCEN["OS-01"], open_store(":memory:")
    runner = ComputeRunner(store)
    for c in s["closures"]:
        _record(store, runner, c["alert_id"], "NOT_FILE", c["rationale"], s["customer_ref"],
                full=False)
    cur = s["current"]
    did = _record(store, runner, cur["alert_id"], cur["disposition"], cur["rationale"],
                  s["customer_ref"])
    chip = next(r for r in alert_reasons(store, cur["alert_id"]) if r["kind"] == "repeat_closure")
    assert chip["text"] == s["expect"]["inbox_chip"]
    r = inspect_decision(store, did, record=False)
    for qid, want in s["expect"]["inspector"].items():
        assert _status(r, qid) == want, qid


def test_os02_late_decision_is_flagged_on_the_timeline_question():
    s, store = SCEN["OS-02"], open_store(":memory:")
    cur = s["current"]
    did = _record(store, ComputeRunner(store), cur["alert_id"], cur["disposition"],
                  cur["rationale"], s["customer_ref"], days_ago=cur["suspicion_formed_days_ago"])
    assert _status(inspect_decision(store, did, record=False), "IQ-05") == "needs_review"


def test_os03_closure_reopens_when_the_facts_move():
    s, store = SCEN["OS-03"], open_store(":memory:")
    runner = ComputeRunner(store)
    cur = s["current"]
    did = _record(store, runner, cur["alert_id"], cur["disposition"], cur["rationale"])
    feed = {i["item_id"]: i for i in load_feed()["items"]}
    (ev,) = DecisionWatch(store, runner).apply(registry_event(feed[s["then_feed"][0]]))
    assert ev["OUTCOME"] == s["expect"]["watch_outcome"]
    assert _status(inspect_decision(store, did, record=False), "IQ-11") == "needs_review"
    assert any(r["kind"] == "reopened" for r in alert_reasons(store, cur["alert_id"]))
