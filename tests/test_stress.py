"""Decision Stress Test — offline tests (local subprocess backend, no network)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from ddp.bootstrap import compute_params, open_store, parse_declared_monthly_income  # noqa: E402
from ddp.compute import ComputeRunner  # noqa: E402
from ddp.llm import FunctionLLM  # noqa: E402
from ddp.skills import CoPilotSkills  # noqa: E402
from ddp.stress import StressTester  # noqa: E402
from ddp.stress.engine import numbers_in  # noqa: E402
from ddp.stress.signals import evaluate_signals, verdict  # noqa: E402


@pytest.fixture()
def env():
    store = open_store(":memory:")
    runner = ComputeRunner(store)
    return store, runner, StressTester(runner, store)


def _run(env, alert, disposition, **kw):
    store, _, tester = env
    return tester.run(alert, store.transactions_for(alert), compute_params(store, alert),
                      disposition=disposition, **kw)


def test_income_parse():
    assert parse_declared_monthly_income("Rs.28K/month declared") == 28_000
    assert parse_declared_monthly_income("Rs.1.8L/month declared") == 180_000
    assert parse_declared_monthly_income("Rs.8-15K/month declared") is None  # range: no guess
    assert parse_declared_monthly_income("Rs.4.2Cr declared annual turnover") is None


def test_income_multiple_fact(env):
    store, runner, _ = env
    facts = {f["fact_id"]: f for f in runner.run(
        "ALERT-01", store.transactions_for("ALERT-01"), compute_params(store, "ALERT-01"))["facts"]}
    assert facts["F-INCOME-MULTIPLE-X10"]["value"] == round(345000 * 10 / 28000)  # 123 = 12.3x
    assert "CUSTOMER_PROFILE:ALERT-01" in facts["F-INCOME-MULTIPLE-X10"]["derivation"]


def test_file_rests_on_the_i4c_flag(env):
    r = _run(env, "ALERT-01", "FILE")
    assert r["base"]["verdict"] == "HIGH"
    sets = [sorted(h["id"] for h in s) for s in r["minimal_flip_sets"]]
    assert ["UNFLAG:UPI handle C (I4C-flagged)"] in sets          # single point of failure
    assert ["EXPLAIN:T01-3", "EXPLAIN:T01-5"] in sets             # both flagged debits
    assert r["smallest_flip_size"] == 1
    # minimality: no reported set contains another reported set
    for a in sets:
        for b in sets:
            assert a == b or not set(a) < set(b)


def test_not_file_twin_gets_reopen_triggers(env):
    r = _run(env, "ALERT-16", "NOT_FILE")
    assert r["base"]["verdict"] == "ELEVATED"
    triggers = {t["hypotheses"][0] for t in r["reopen_triggers"] if len(t["hypotheses"]) == 1}
    assert "FLAG:City General Hospital (invoice on file)" in triggers
    assert "FLAG:Brother (KYC-linked family)" in triggers
    # 75,000 / 345,000 is below the flagged-share heuristic: flagging the sister alone does not flip
    assert "FLAG:Sister (KYC-linked family)" not in triggers


def test_branch_runs_are_recorded_with_provenance(env):
    store, _, _ = env
    r = _run(env, "ALERT-01", "FILE")
    rows = store.query("SELECT * FROM COMPUTE_RUNS WHERE PARENT_RUN_ID = ?", (r["base"]["run_id"],))
    assert len(rows) == r["search"]["runs_used"] > 0
    assert all(json.loads(row["HYPOTHESIS_JSON"]) for row in rows)
    ev = store.get_evidence(r["evidence_id"])
    assert ev["TYPE"] == "stress_test"
    assert set(json.loads(ev["PROVENANCE_JSON"])["branch_run_ids"]) == {x["RUN_ID"] for x in rows}


def test_budget_is_respected(env):
    r = _run(env, "ALERT-01", "FILE", budget=3)
    assert r["search"]["runs_used"] <= 3 and r["search"]["budget_exhausted"]


def test_case_record_is_not_mutated(env):
    store, _, _ = env
    before = store.transactions_for("ALERT-01")
    _run(env, "ALERT-01", "FILE")
    assert store.transactions_for("ALERT-01") == before


def test_signals_ignore_fan_in_without_outflow():
    facts = [{"fact_id": "F-FAN-IN", "value": 4}, {"fact_id": "F-FAN-OUT", "value": 0}]
    assert not next(s for s in evaluate_signals(facts) if s.signal_id == "S-FAN-IN").fired
    assert verdict(evaluate_signals(facts)) == "LOW"


def _memo_llm(text):
    return FunctionLLM(lambda prompt: text)


def test_memo_with_grounded_numbers_is_accepted(env):
    store, runner, _ = env
    skills = CoPilotSkills(store, llm=_memo_llm(json.dumps({
        "summary": "The filing rests on the I4C flag; transaction T01-3 for 246500 matters.",
        "load_bearing_evidence": ["flag on UPI handle C"], "reopen_triggers": []})))
    r = StressTester(runner, store, skills).run(
        "ALERT-01", store.transactions_for("ALERT-01"), compute_params(store, "ALERT-01"),
        disposition="FILE", with_memo=True)
    assert r["memo"]["status"] == "ok"


def test_memo_with_invented_number_is_rejected(env):
    store, runner, _ = env
    skills = CoPilotSkills(store, llm=_memo_llm(json.dumps({
        "summary": "Roughly 87% of funds, about 300,123, went out.",
        "load_bearing_evidence": [], "reopen_triggers": []})))
    r = StressTester(runner, store, skills).run(
        "ALERT-01", store.transactions_for("ALERT-01"), compute_params(store, "ALERT-01"),
        disposition="FILE", with_memo=True)
    assert r["memo"]["status"] == "rejected"
    assert "summary" in r and r["summary"]  # deterministic summary always present


def test_memo_with_invented_lakh_figure_is_rejected(env):
    store, runner, _ = env
    skills = CoPilotSkills(store, llm=_memo_llm(json.dumps({
        "summary": "The filing rests on the I4C flag; about Rs. 2 lakh went to handle C.",
        "load_bearing_evidence": [], "reopen_triggers": []})))
    r = StressTester(runner, store, skills).run(
        "ALERT-01", store.transactions_for("ALERT-01"), compute_params(store, "ALERT-01"),
        disposition="FILE", with_memo=True)
    assert r["memo"]["status"] == "rejected"


def test_numbers_in_ignores_identifiers():
    assert numbers_in("T01-3 and ALERT-01 moved 2,46,500") == {246500.0}


def test_eval_harness_mock_mode(tmp_path):
    from scripts.run_live_eval import main
    assert main(["--mock", "--alerts", "ALERT-01,ALERT-16", "--out", str(tmp_path)]) == 0
    report = next(tmp_path.glob("REPORT-*-mock.md")).read_text()
    assert "MOCK RUN" in report and "| ALERT-01 | MULE_PASSTHROUGH | FILE | HIGH | 1 |" in report
    assert "| ALERT-01 | FILE | submitted |" in report, "mock agent must still reach a submission"
