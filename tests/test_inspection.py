"""Inspection replay and pre-inspection check (T12.9 / T12.10) — offline."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from ddp.bootstrap import compute_params, open_store  # noqa: E402
from ddp.compute import ComputeRunner  # noqa: E402
from ddp.inspection import (check_findings, cross_examine, inspect_decision,  # noqa: E402
                            pre_inspect, record_rows)
from ddp.llm import FunctionLLM  # noqa: E402
from ddp.skills import POE_FACTORS, CoPilotSkills  # noqa: E402
from ddp.stress import StressTester  # noqa: E402
from ddp.watch import DEMO_RATIONALES, DecisionWatch  # noqa: E402

POE = [{"factor_id": f, "factor_name": n, "assessment": "clear"} for f, n in POE_FACTORS]


def _status(result, qid):
    return next(r for r in result["results"] if r["id"] == qid)["status"]


@pytest.fixture()
def store():
    return open_store(":memory:")


def _full(store, alert="ALERT-16"):
    runner = ComputeRunner(store)
    disp, text = DEMO_RATIONALES[alert]
    txns, params = store.transactions_for(alert), compute_params(store, alert)
    StressTester(runner, store).run(alert, txns, params, disposition=disp)
    store.record_evidence(alert, "adverse_media_screen", "tavily:screen",
                          {"status": "ok", "completed": True, "result_count": 5})
    run = runner.run(alert, txns, params)
    a = store.get_alert(alert)
    return CoPilotSkills(store).alert_disposition_recorder(
        alert_id=alert, customer_ref=a["CUSTOMER_REF"], disposition=disp, rationale_text=text,
        rules_cited=json.loads(a["RULES_CITED"]), rfi_triggers=[], poe_assessment=POE,
        compute_run_id=run["run_id"], decision_maker_id="PO-7",
        decision_maker_basis="oidc (st.login, officer allow-list)")["decision_id"]


def _template(store, alert="ALERT-16"):
    """A cursory closure: the pattern the UBI 13/2024 order describes."""
    a = store.get_alert(alert)
    return CoPilotSkills(store).alert_disposition_recorder(
        alert_id=alert, customer_ref=a["CUSTOMER_REF"], disposition="NOT_FILE",
        rationale_text="Reviewed; activity consistent with profile. Closed.", rules_cited=[],
        rfi_triggers=[], poe_assessment=[])["decision_id"]


def test_full_record_answers_more_than_a_cursory_closure(store):
    full = inspect_decision(store, _full(store), record=False)
    other = open_store(":memory:")
    cursory = inspect_decision(other, _template(other), record=False)
    assert full["answered"] > cursory["answered"]
    for q in ("IQ-01", "IQ-02", "IQ-04", "IQ-08"):
        assert _status(full, q) == "answered", q
        assert _status(cursory, q) != "answered", q
    # The seed cites RFI-001/RFI-005, which are NEEDS-VERIFICATION: flagged, not passed.
    iq6 = next(r for r in full["results"] if r["id"] == "IQ-06")
    assert iq6["status"] == "needs_review" and "RFI-001" in iq6["answer"]
    assert _status(cursory, "IQ-06") == "unanswered"


def test_full_record_answers_the_reproduction_and_identity_questions(store):
    r = inspect_decision(store, _full(store), record=False)
    assert _status(r, "IQ-04") == "answered" and _status(r, "IQ-07") == "answered"
    assert _status(r, "IQ-09") == "answered"
    assert _status(r, "IQ-11") == "unanswered"         # never re-checked yet


def test_recheck_question_follows_the_watch(store):
    did = _full(store)
    DecisionWatch(store, ComputeRunner(store)).run_feed()
    assert _status(inspect_decision(store, did, record=False), "IQ-11") == "needs_review"


def test_earlier_closure_on_the_same_customer_is_flagged(store):
    cust = store.get_alert("ALERT-16")["CUSTOMER_REF"]
    CoPilotSkills(store).alert_disposition_recorder(
        alert_id="ALERT-07", customer_ref=cust, disposition="NOT_FILE",
        rationale_text="Seasonal receipts with invoices; no registry hit; closed after review.",
        rules_cited=[], rfi_triggers=[], poe_assessment=POE)
    r = inspect_decision(store, _full(store), record=False)
    hit = next(x for x in r["results"] if x["id"] == "IQ-10")
    assert hit["status"] == "needs_review" and len(hit["rows"]) == 1


def test_inspection_is_deterministic_and_recorded(store):
    did = _full(store)
    a = inspect_decision(store, did, record=False)
    b = inspect_decision(store, did)
    assert [r["status"] for r in a["results"]] == [r["status"] for r in b["results"]]
    assert store.get_evidence(b["evidence_id"])["TYPE"] == "inspection"


def test_pre_inspection_writes_nothing_and_skips_the_recheck(store):
    before = store.query("SELECT COUNT(*) AS n FROM EVIDENCE")[0]["n"]
    r = pre_inspect(store, alert_id="ALERT-16", disposition="NOT_FILE",
                    rationale=DEMO_RATIONALES["ALERT-16"][1], rules_cited=["STR-001"],
                    poe_assessment=POE, compute_run_id=None, suspicion_formed_at="2026-10-01",
                    decision_maker_id="PO-7", decision_maker_basis="self-asserted",
                    evidence_check={"passed": True, "amounts_checked": 0})
    assert _status(r, "IQ-11") == "not_applicable" and r["pending"]
    assert "IQ-02" in r["gaps"]                          # no stress test recorded yet
    assert store.query("SELECT COUNT(*) AS n FROM EVIDENCE")[0]["n"] == before


def test_recorder_keeps_the_pre_inspection_gaps(store):
    a = store.get_alert("ALERT-16")
    res = CoPilotSkills(store).alert_disposition_recorder(
        alert_id="ALERT-16", customer_ref=a["CUSTOMER_REF"], disposition="NOT_FILE",
        rationale_text=DEMO_RATIONALES["ALERT-16"][1], rules_cited=[], rfi_triggers=[],
        poe_assessment=POE, pre_inspection={"bank_sha256": "x", "answered": 5, "asked": 10,
                                            "gaps": ["IQ-02"]})
    meta = json.loads(store.get_decision(res["decision_id"])["METADATA_JSON"])
    assert meta["pre_inspection"]["gaps"] == ["IQ-02"]


# ── layer 2: citations are checked by code, with seeded faults ────────────────
def test_seeded_citation_faults_are_rejected(store):
    did = _full(store)
    rows = record_rows(store, did)
    good = next(r for r in rows if r.startswith("evidence:"))
    other = open_store(":memory:")
    foreign = next(r for r in record_rows(other, _full(other, "ALERT-01")) if r.startswith("run:"))
    rows_with_foreign = dict(rows, **{foreign: dict(record_rows(other, other.latest_decisions()[0]
                                                                 ["DECISION_ID"])[foreign])})
    tampered = dict(rows_with_foreign)
    tampered[good] = dict(tampered[good], raw=tampered[good]["raw"] + " ")
    findings = [
        {"question": "ok", "answered": True, "cited_rows": [f"ledger:{did}"], "note": ""},
        {"question": "made up", "answered": True, "cited_rows": ["evidence:EV-fake"], "note": ""},
        {"question": "foreign", "answered": True, "cited_rows": [foreign], "note": ""},
        {"question": "tampered", "answered": True, "cited_rows": [good], "note": ""},
        {"question": "no cite", "answered": True, "cited_rows": [], "note": ""},
        {"question": "open", "answered": False, "cited_rows": [], "note": ""},
    ]
    out = check_findings(findings, tampered, "ALERT-16")
    assert {f["question"] for f in out["accepted"]} == {"ok", "open"}
    reasons = {f["question"]: list(f["rejected_citations"].values()) for f in out["rejected"]}
    assert reasons["made up"] == ["not a row in this record"]
    assert reasons["foreign"] == ["belongs to another alert"]
    assert reasons["tampered"] == ["stored content does not match its recorded hash"]


def test_cross_examination_with_a_scripted_model(store):
    did = _full(store)

    def reply(prompt):
        return json.dumps({"findings": [
            {"question": "Was the invoice verified?", "answered": False, "cited_rows": [],
             "note": "Not in the rows."},
            {"question": "Why closed?", "answered": True, "cited_rows": [f"ledger:{did}"],
             "note": "Rationale recorded."},
            {"question": "Invented", "answered": True, "cited_rows": ["run:RUN-nope"],
             "note": ""}]})
    out = cross_examine(CoPilotSkills(store, llm=FunctionLLM(reply)), store, did)
    assert out["status"] == "ok"
    assert len(out["accepted"]) == 2 and len(out["rejected"]) == 1


def test_cross_examination_without_a_model_fails_closed(store):
    out = cross_examine(CoPilotSkills(store), store, _full(store))
    assert out["status"] == "unavailable" and out["accepted"] == []


def test_inspection_replay_renders_on_the_ledger_page_offline():
    import tempfile
    from tests.test_app_smoke import _app
    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / "i.sqlite3")
        did = _full(open_store(db))
        at = _app(db)
        at.run()
        at.sidebar.radio[0].set_value("Decision Ledger").run()
        at.button(key=f"inspect_{did}").click().run()
        assert not at.exception, at.exception
        text = " ".join(m.value for m in at.markdown)
        assert "The record answers" in text and "IQ-01" in text
