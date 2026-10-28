"""
T7.1: every way of writing a rupee figure is read and checked exactly; nothing slips past the
evidence gate by phrasing. Offline.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from ddp.bootstrap import compute_params, open_store, parse_declared_annual_income
from ddp.compute import ComputeRunner
from ddp.money import extract_amounts, format_inr
from ddp.skills import CoPilotSkills

SAME_FIGURE = ["₹32,50,000", "₹ 3250000", "₹3,250,000", "Rs. 32,50,000", "Rs 32,50,000",
               "Rs.3250000", "INR 3250000", "INR 32,50,000", "₹32.5 lakh", "₹32.5 lakhs",
               "Rs. 32.5 lac", "₹32.5L", "32.5 lakh", "3250000 INR", "32,50,000 rupees",
               "₹3250K", "₹0.325 crore", "Rs 0.325 Cr"]


@pytest.mark.parametrize("text", SAME_FIGURE)
def test_equivalent_forms_normalise_to_one_value(text):
    vals = [m.value for m in extract_amounts(f"Funds of {text} moved.")]
    assert vals == [Decimal(3250000)], (text, vals)


@pytest.mark.parametrize("text, reason", [
    ("₹3-4 lakh", "range"), ("Rs. 3–4 lakh", "range"),
    ("₹ thirty lakh", "without a figure"), ("an INR amount", "without a figure"),
])
def test_unreadable_amounts_are_reported_not_skipped(text, reason):
    ms = extract_amounts(text)
    assert ms and ms[0].value is None and reason in ms[0].reason


@pytest.mark.parametrize("text", [
    "TXN-001 on 2026-08-19", "98.6% of credits", "15.4 times income", "POE-007 and RFI-001",
    "3 linked accounts", "the last week",
])
def test_non_money_is_ignored(text):
    assert extract_amounts(text) == []


def test_format_inr_indian_grouping():
    assert format_inr(3250000) == "₹32,50,000"
    assert format_inr(950) == "₹950"
    assert format_inr(Decimal("110000.5")) == "₹1,10,000.5"


def _alert01():
    store = open_store(":memory:")
    txns = store.transactions_for("ALERT-01")
    run = ComputeRunner(store).run("ALERT-01", txns, compute_params(store, "ALERT-01"))
    return CoPilotSkills(store), txns, run["facts"]


@pytest.mark.parametrize("text", SAME_FIGURE)
def test_invented_total_fails_in_every_form(text):
    skills, txns, facts = _alert01()
    res = skills.validate_gos_evidence(f"Funds totalling {text} moved to handle C.", txns, facts)
    assert res["passed"] is False, text


@pytest.mark.parametrize("text", ["₹3-4 lakh", "₹ thirty lakh"])
def test_unreadable_amount_fails_the_gate(text):
    skills, txns, facts = _alert01()
    res = skills.validate_gos_evidence(f"Funds of about {text} moved.", txns, facts)
    assert res["passed"] is False and res["unparsed_amounts"]


def test_real_transaction_amount_passes_in_any_form():
    skills, txns, facts = _alert01()
    amt = txns[0]["amount_inr"]                     # 1,10,000 for ALERT-01
    for form in (format_inr(amt), f"Rs. {amt:,}", f"INR {amt}", f"{amt / 100000:g} lakh"):
        res = skills.validate_gos_evidence(f"A credit of {form} arrived.", txns, facts)
        assert res["passed"], (form, res)


def test_near_miss_is_not_rounded_through():
    """The old gate accepted anything within 1%; a figure off by ₹500 must now fail."""
    skills, txns, facts = _alert01()
    amt = txns[0]["amount_inr"] + 500
    res = skills.validate_gos_evidence(f"A credit of ₹{amt:,} arrived.", txns, facts)
    assert res["passed"] is False


def test_total_needs_a_calculator_fact():
    skills, txns, facts = _alert01()
    total = next(f["value"] for f in facts if f["fact_id"] == "F-TOTAL-CREDIT")
    text = f"Credits totalled {format_inr(total)}."
    assert skills.validate_gos_evidence(text, txns)["passed"] is False
    res = skills.validate_gos_evidence(text, txns, facts)
    assert res["passed"] and res["fact_citations"] == {format_inr(total): ["F-TOTAL-CREDIT"]}


def test_count_fact_is_not_a_rupee_amount():
    """Right number, wrong unit: a count fact cannot support a ₹ figure."""
    skills, txns, facts = _alert01()
    n = next(f["value"] for f in facts if f["fact_id"] == "F-TXN-COUNT")
    assert skills.validate_gos_evidence(f"Only ₹{n} moved.", txns, facts)["passed"] is False


def test_annual_income_parser():
    assert parse_declared_annual_income("Rs.4.5L/year declared") == 450_000
    assert parse_declared_annual_income("Declared annual income ₹3.6L.") == 360_000
    assert parse_declared_annual_income("Rs.4.2Cr declared annual turnover") is None
    assert parse_declared_annual_income("Rs.3-4L/year") is None
    assert parse_declared_annual_income("Rs.28K/month") is None


def test_annual_income_fact_from_seed_profile():
    store = open_store(":memory:")
    params = compute_params(store, "ALERT-12")          # "Rs.4.5L/year declared"
    assert params["declared_annual_income_inr"]["amount_inr"] == 450_000
    run = ComputeRunner(store).run("ALERT-12", store.transactions_for("ALERT-12"), params)
    assert {f["fact_id"]: f["value"] for f in run["facts"]}["F-DECLARED-ANNUAL-INCOME"] == 450_000


def test_zero_valued_fact_is_supported_but_zero_needs_the_fact():
    """A credit-only case: F-TOTAL-DEBIT is 0. '₹0' cites a real fact; without facts it fails."""
    txns = [{"txn_id": "T99-1", "date": "2026-09-01", "type": "CREDIT", "amount_inr": 240000,
             "counterparty": "Unidentified individual", "is_flagged": False}]
    facts = ComputeRunner(None).run("SYN-0", txns, {})["facts"]
    assert {f["fact_id"]: f["value"] for f in facts}.get("F-TOTAL-DEBIT") == 0
    text = "No funds left the account (F-TOTAL-DEBIT ₹0)."
    skills = CoPilotSkills(None)
    assert skills.validate_gos_evidence(text, txns, facts)["passed"]
    assert not skills.validate_gos_evidence(text, txns)["passed"]
