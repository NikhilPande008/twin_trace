"""
Proof Check (T9.7): an offline demonstration that a made-up figure cannot get through.

Two drafts are built from one alert's calculator facts. One states a total the calculator never
produced; the other states the calculator's own figure. Both are written in the currency form the
visitor chooses, because the gate reads exact values: "₹3,45,000", "Rs. 3,45,000", "INR 345000"
and "₹3.45 lakh" are the same figure.

Recording is attempted against a THROWAWAY in-memory ledger seeded from the same data, so the
demonstration exercises the real recording boundary without touching the visitor's own ledger.
No model and no network are involved.
"""

from __future__ import annotations

from decimal import Decimal

from .bootstrap import compute_params, open_store
from .compute import ComputeRunner
from .money import format_inr
from .skills import CoPilotSkills

FORMS = {
    "₹ with Indian commas": "inr",
    "Rs. prefix": "rs",
    "INR prefix, no commas": "code",
    "lakh": "lakh",
}
INVENTED_EXTRA = 50_000          # the "model's" arithmetic error: a plausible but wrong total


def render_amount(value: int, form: str) -> str:
    if form == "rs":
        return format_inr(value).replace("₹", "Rs. ")
    if form == "code":
        return f"INR {int(value)}"
    if form == "lakh":
        lakh = (Decimal(int(value)) / Decimal(100_000)).normalize()
        return f"₹{lakh:f} lakh"
    return format_inr(value)


def total_credit(facts: list[dict]) -> int:
    for f in facts:
        if f["fact_id"] == "F-TOTAL-CREDIT":
            return int(f["value"])
    return 0


def build_drafts(credit: int, form: str) -> dict:
    """{"invented": text, "grounded": text, "invented_value": int, "grounded_value": int}."""
    invented = credit + INVENTED_EXTRA
    tail = " arrived within days and were passed on to the flagged counterparty, which does not fit the declared profile."
    return {
        "invented_value": invented,
        "grounded_value": credit,
        "invented": f"I formed suspicion because credits totalling {render_amount(invented, form)}" + tail,
        "grounded": f"I formed suspicion because credits totalling {render_amount(credit, form)}" + tail,
    }


def attempt_recording(alert_id: str, text: str) -> dict:
    """Try to record `text` as a FILE decision in a throwaway ledger.

    Returns {"recorded": bool, "message": str, "ledger_rows": int, "chain_ok": bool}.
    """
    store = open_store(":memory:")
    txns = store.transactions_for(alert_id)
    run = ComputeRunner(store).run(alert_id, txns, compute_params(store, alert_id))
    skills = CoPilotSkills(store)
    try:
        res = skills.alert_disposition_recorder(
            alert_id=alert_id, customer_ref="DEMO", disposition="FILE", rationale_text=text,
            rules_cited=[], rfi_triggers=[], poe_assessment=[], compute_run_id=run["run_id"])
        msg = f"Recorded (row hash {res['row_hash'][:16]}…)."
        recorded = True
    except ValueError as e:
        msg, recorded = str(e), False
    chain = store.verify_ledger_chain()
    return {"recorded": recorded, "message": msg, "ledger_rows": chain["rows"],
            "chain_ok": chain["ok"]}
