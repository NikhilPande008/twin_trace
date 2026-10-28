"""The Proof Check demonstration behaves as it claims, in every currency form (T9.7)."""

from __future__ import annotations

import pytest

from ddp.bootstrap import compute_params, open_store
from ddp.compute import ComputeRunner
from ddp.proofcheck import (FORMS, attempt_recording, build_drafts, render_amount,
                            total_credit)
from ddp.skills import CoPilotSkills


@pytest.fixture(scope="module")
def case():
    store = open_store(":memory:")
    txns = store.transactions_for("ALERT-01")
    run = ComputeRunner(store).run("ALERT-01", txns, compute_params(store, "ALERT-01"))
    return store, txns, run["facts"], total_credit(run["facts"])


@pytest.mark.parametrize("form", list(FORMS.values()))
def test_invented_blocked_and_grounded_passes_in_every_form(case, form):
    store, txns, facts, credit = case
    d = build_drafts(credit, form)
    sk = CoPilotSkills(store)
    bad = sk.validate_gos_evidence(d["invented"], txns, facts)
    good = sk.validate_gos_evidence(d["grounded"], txns, facts)
    assert not bad["passed"], (form, d["invented"])
    assert good["passed"], (form, d["grounded"], good["unsupported_claims"], good["unparsed_amounts"])
    assert any("F-TOTAL-CREDIT" in ids for ids in good["fact_citations"].values())


@pytest.mark.parametrize("form", list(FORMS.values()))
def test_recording_boundary_refuses_invented_and_accepts_grounded(form):
    store = open_store(":memory:")
    credit = total_credit(ComputeRunner(store).run(
        "ALERT-01", store.transactions_for("ALERT-01"), compute_params(store, "ALERT-01"))["facts"])
    d = build_drafts(credit, form)
    refused = attempt_recording("ALERT-01", d["invented"])
    assert not refused["recorded"] and refused["ledger_rows"] == 0 and "Not recorded" in refused["message"]
    ok = attempt_recording("ALERT-01", d["grounded"])
    assert ok["recorded"] and ok["ledger_rows"] == 1 and ok["chain_ok"]


def test_demo_never_touches_the_real_ledger():
    real = open_store(":memory:")
    before = real.verify_ledger_chain()["rows"]
    attempt_recording("ALERT-01", build_drafts(345000, "inr")["grounded"])
    assert real.verify_ledger_chain()["rows"] == before == 0


def test_render_forms_are_the_same_figure():
    assert render_amount(345000, "inr") == "₹3,45,000"
    assert render_amount(345000, "rs") == "Rs. 3,45,000"
    assert render_amount(345000, "code") == "INR 345000"
    assert render_amount(345000, "lakh") == "₹3.45 lakh"
