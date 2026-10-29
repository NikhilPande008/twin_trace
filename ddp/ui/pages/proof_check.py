"""Page: Proof Check."""

from __future__ import annotations

import streamlit as st

from ...money import format_inr
from ...proofcheck import FORMS, INVENTED_EXTRA, attempt_recording, build_drafts, total_credit
from ..case_state import _ensure_computed
from ..runtime import _load_transactions, get_skills, get_store


# ── page: Dashboard ───────────────────────────────────────────────────────────
# ── page: Proof Check ─────────────────────────────────────────────────────────
def _figure_gate_panel(text, txns, facts):
    """Run the evidence gate on `text` and say what it found, in plain words."""
    check = get_skills().validate_gos_evidence(text, txns, facts)
    if check["passed"]:
        cites = "; ".join(f"{amt} ← {', '.join(ids)}" for amt, ids in check["fact_citations"].items())
        st.success("**Passes the figure check.** Every ₹ figure is a transaction amount or a "
                   "calculator fact" + (f": {cites}." if cites else "."))
        return
    parts = []
    if check["unsupported_claims"]:
        amts = ", ".join(f"`{a}`" for a in check["unsupported_claims"])
        parts.append(f"{amts} {'is' if len(check['unsupported_claims']) == 1 else 'are'} not a "
                     "transaction amount or a calculator fact.")
    if check.get("unparsed_amounts"):
        parts.append(", ".join(f"`{a}`" for a in check["unparsed_amounts"])
                     + " cannot be read as one exact figure.")
    st.error("**Blocked.** " + " ".join(parts))


def page_proof_check():
    st.header("Proof Check")
    st.markdown(
        "**Try to get a made-up number past the system.** A language model often adds figures up "
        "wrongly and states the total with confidence. Here, every ₹ figure in a Ground of "
        "Suspicion must be a single transaction amount or a fact from the *calculator of record*, "
        "a fixed program whose code, input and output are hashed. Anything else is blocked, "
        "including at the moment of recording.")
    st.caption("Works offline, with no model call. Recording is attempted in a throwaway ledger, "
               "so your own ledger is never touched.")

    options = [r["ALERT_ID"] for r in get_store().alert_ids()]
    c1, c2 = st.columns([1, 2])
    alert_id = c1.selectbox("Alert", options, index=0, key="pc_alert")
    form_label = c2.radio("How the figure is written", list(FORMS), horizontal=True,
                          key="pc_form",
                          help="The gate reads exact values, so every spelling of the same "
                               "amount is treated alike.")
    form = FORMS[form_label]

    computed = _ensure_computed(alert_id)
    facts = computed["facts"]
    txns = _load_transactions(alert_id)
    credit = total_credit(facts)
    if credit <= 0:
        st.info("This alert has no credits, so there is no total to misstate. Pick another alert.")
        return
    d = build_drafts(credit, form)
    st.markdown(f"The calculator of record says total credits are **{format_inr(credit)}** "
                f"(`F-TOTAL-CREDIT`, run `{computed['run_id']}`).")

    left, right = st.columns(2, gap="large")
    for col, side, title, blurb in (
            (left, "invented", "A draft with an invented total",
             f"Same sentence, but the total is {format_inr(d['invented_value'])} "
             f"({format_inr(INVENTED_EXTRA)} too high). Edit it to try your own."),
            (right, "grounded", "The same draft with the calculator's figure",
             "Same sentence and spelling; the total is the calculator's. Edit it to try your own.")):
        with col:
            st.markdown(f"#### {title}")
            st.caption(blurb)
            text = st.text_area(title, d[side], key=f"pc_{side}_{alert_id}_{form}", height=130,
                                label_visibility="collapsed")
            _figure_gate_panel(text, txns, facts)
            if st.button("Try to record this decision", key=f"pc_rec_{side}",
                         width="stretch"):
                st.session_state[f"pc_out_{side}"] = attempt_recording(alert_id, text)
            out = st.session_state.get(f"pc_out_{side}")
            if out:
                if out["recorded"]:
                    st.success(f"{out['message']} Throwaway ledger now has {out['ledger_rows']} "
                               f"row, chain verified: {out['chain_ok']}.")
                else:
                    st.error(f"{out['message']}  \n**Ledger rows written: {out['ledger_rows']}.**")
    with st.expander("What this does and does not prove"):
        st.markdown(
            "- It proves a figure is **traceable**: it equals a transaction amount, or a fact the "
            "hashed calculator produced from the case's transactions.  \n"
            "- It does **not** prove the sentence around a figure is true, or that the "
            "transactions themselves are accurate. Sentences without figures are listed for the "
            "officer's own review.  \n"
            "- Amounts written in words, and currencies other than rupees, are not read; a "
            "figure the parser cannot read as one exact value fails the check rather than "
            "passing unnoticed.")
