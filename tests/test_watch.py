"""Decision watch (T12.4 / T12.5) — offline, local calculator, no network."""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from ddp.bootstrap import compute_params, open_store  # noqa: E402
from ddp.compute import ComputeRunner  # noqa: E402
from ddp.skills import POE_FACTORS, CoPilotSkills  # noqa: E402
from ddp.stress import StressTester  # noqa: E402
from ddp.watch import DecisionWatch, load_feed, registry_event  # noqa: E402

POE = [{"factor_id": f, "factor_name": n, "assessment": "clear"} for f, n in POE_FACTORS]
FEED = {i["item_id"]: i for i in load_feed()["items"]}
CLOSE_16 = ("Credits are family support and one hospital payment backed by an invoice on file; "
            "the senders are KYC-linked family members and no counterparty is on a registry.")
FILE_01 = ("Debits went to the I4C-flagged handle C within days of credits from unknown UPI "
           "handles, a pass-through pattern inconsistent with the declared salary.")


def _record(store, runner, alert, disposition, text, *, stress=False):
    txns = store.transactions_for(alert)
    params = compute_params(store, alert)
    if stress:
        StressTester(runner, store).run(alert, txns, params, disposition=disposition)
    run = runner.run(alert, txns, params)
    alert_row = store.get_alert(alert)
    return CoPilotSkills(store).alert_disposition_recorder(
        alert_id=alert, customer_ref=alert_row["CUSTOMER_REF"], disposition=disposition,
        rationale_text=text, rules_cited=json.loads(alert_row["RULES_CITED"]), rfi_triggers=[],
        poe_assessment=POE, compute_run_id=run["run_id"])


@pytest.fixture()
def env():
    store = open_store(":memory:")
    runner = ComputeRunner(store)
    d16 = _record(store, runner, "ALERT-16", "NOT_FILE", CLOSE_16, stress=True)
    d01 = _record(store, runner, "ALERT-01", "FILE", FILE_01)
    return store, runner, DecisionWatch(store, runner), d16["decision_id"], d01["decision_id"]


def _apply(watch, item_id):
    return watch.apply(registry_event(FEED[item_id]))


def test_flagging_the_sister_does_not_reopen_the_closure(env):
    store, _, watch, d16, _ = env
    (ev,) = _apply(watch, "REG-0001")
    assert ev["DECISION_ID"] == d16 and ev["OUTCOME"] == "holds"
    assert store.get_alert("ALERT-16")["ALERT_STATUS"] != "REOPENED"


def test_flagging_the_hospital_reopens_and_names_the_fact(env):
    store, _, watch, d16, _ = env
    (ev,) = _apply(watch, "REG-0002")
    detail = json.loads(ev["OUTCOME_JSON"])
    assert ev["OUTCOME"] == "reopened"
    assert detail["verdict_before"] == "ELEVATED" and detail["verdict_after"] == "HIGH"
    assert "City General Hospital" in detail["trigger"]
    assert detail["named_at_decision"] is True          # the stress test listed it as a trigger
    assert store.get_alert("ALERT-16")["ALERT_STATUS"] == "REOPENED"


def test_withdrawn_flag_puts_the_file_under_review(env):
    _, _, watch, _, d01 = env
    (ev,) = _apply(watch, "REG-0003")
    detail = json.loads(ev["OUTCOME_JSON"])
    assert ev["DECISION_ID"] == d01 and ev["OUTCOME"] == "needs_review"
    assert detail["verdict_before"] == "HIGH" and detail["verdict_after"] != "HIGH"


def test_rerun_uses_recorded_inputs_and_links_to_the_base_run(env):
    store, _, watch, d16, _ = env
    store._exec("UPDATE TRANSACTIONS SET AMOUNT_INR = 1 WHERE ALERT_ID = 'ALERT-16'")
    (ev,) = _apply(watch, "REG-0002")
    rerun = store.get_compute_run(ev["RERUN_ID"])
    assert rerun["PARENT_RUN_ID"] == ev["BASE_RUN_ID"]
    assert all(t["amount_inr"] != 1 for t in json.loads(rerun["INPUT_JSON"])["transactions"])
    assert ev["OUTCOME"] == "reopened"                   # current rows were not used


def test_replaying_an_item_writes_nothing(env):
    store, _, watch, _, _ = env
    first = _apply(watch, "REG-0002")[0]
    again = _apply(watch, "REG-0002")[0]
    assert again["status"] == "already_recorded" and again["EVENT_ID"] == first["EVENT_ID"]
    assert len(store.all_events()) == 1


def test_same_change_same_outcome_hash_on_a_fresh_store():
    hashes = []
    for _ in range(2):
        store = open_store(":memory:")
        runner = ComputeRunner(store)
        _record(store, runner, "ALERT-16", "NOT_FILE", CLOSE_16, stress=True)
        (ev,) = DecisionWatch(store, runner).apply(registry_event(FEED["REG-0002"]))
        hashes.append(ev["OUTCOME_SHA256"])
    assert hashes[0] == hashes[1]


def test_events_are_append_only_and_chained(env):
    store, _, watch, _, _ = env
    watch.run_feed()
    assert store.verify_events_chain()["ok"]
    with pytest.raises(sqlite3.DatabaseError):
        store._exec("UPDATE DECISION_EVENTS SET OUTCOME = 'holds'")
    with pytest.raises(sqlite3.DatabaseError):
        store._exec("DELETE FROM DECISION_EVENTS")


def test_feed_pass_records_a_check_on_every_standing_decision(env):
    store, _, watch, d16, d01 = env
    result = watch.run_feed()
    assert {p["DECISION_ID"] for p in result["passes"]} == {d16, d01}
    outcomes = {(e["DECISION_ID"], e["OUTCOME"]) for e in result["events"]}
    assert (d16, "reopened") in outcomes and (d01, "needs_review") in outcomes


def test_unrelated_item_touches_no_decision(env):
    _, _, watch, _, _ = env
    item = {"item_id": "REG-X", "action": "flag", "counterparty": "Nobody in these cases"}
    assert watch.apply(registry_event(item)) == []


def test_rule_change_flags_only_decisions_citing_the_rule(env):
    _, _, watch, d16, d01 = env
    evs = watch.apply({"cause": "rule_change", "rule_id": "STR-002", "change_ref": "test"})
    assert [e["DECISION_ID"] for e in evs] == [d01]      # ALERT-16 does not cite STR-002
    assert evs[0]["OUTCOME"] == "needs_review"


def test_decision_without_a_saved_run_is_needs_review_not_holds(env):
    store, _, watch, _, _ = env
    alert = store.get_alert("ALERT-16")
    CoPilotSkills(store).alert_disposition_recorder(
        alert_id="ALERT-16", customer_ref=alert["CUSTOMER_REF"], disposition="NOT_FILE",
        rationale_text=CLOSE_16 + " Reviewed again.", rules_cited=[], rfi_triggers=[],
        poe_assessment=POE)
    (ev,) = _apply(watch, "REG-0001")
    assert ev["OUTCOME"] == "needs_review" and ev["RERUN_ID"] is None


def test_a_reopen_never_touches_the_ledger(env):
    store, _, watch, _, _ = env
    before = store.query("SELECT DECISION_ID, ROW_HASH FROM DECISION_LEDGER ORDER BY SEQ")
    watch.run_feed()
    assert store.query("SELECT DECISION_ID, ROW_HASH FROM DECISION_LEDGER ORDER BY SEQ") == before
    assert store.verify_ledger_chain()["ok"]



def test_registry_state_is_cumulative(env):
    """Sister flagged alone holds; a later credit from her pushes the flagged share over the
    line only if her flag is still applied (code review 2026-10-29)."""
    store, _, watch, d16, _ = env
    (first,) = _apply(watch, "REG-0001")
    assert first["OUTCOME"] == "holds"
    txn = {"txn_id": "T16-NEW", "date": "2026-11-20", "type": "CREDIT", "amount_inr": 20000.0,
           "channel": "UPI", "counterparty": "Sister (KYC-linked family)", "is_flagged": False}
    (ev,) = watch.apply({"cause": "new_transaction", "alert_id": "ALERT-16", "transaction": txn})
    detail = json.loads(ev["OUTCOME_JSON"])
    assert ev["OUTCOME"] == "reopened", detail
    assert detail["earlier_changes"] and "Sister" in detail["earlier_changes"][0]


def test_replaying_an_item_runs_no_calculator(env):
    store, _, watch, _, _ = env
    _apply(watch, "REG-0002")
    runs = store.query("SELECT COUNT(*) AS n FROM COMPUTE_RUNS")[0]["n"]
    _apply(watch, "REG-0002")
    assert store.query("SELECT COUNT(*) AS n FROM COMPUTE_RUNS")[0]["n"] == runs


def test_reasons_index_matches_per_alert_lookup(env):
    from ddp.watch import alert_reasons, reasons_index
    store, _, watch, _, _ = env
    watch.run_feed()
    ix = reasons_index(store)
    for a in ("ALERT-01", "ALERT-16", "ALERT-07"):
        assert alert_reasons(store, a, ix) == alert_reasons(store, a)
