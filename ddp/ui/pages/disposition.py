"""Page: Disposition Panel (verdict card first, proof behind a toggle, decision rail)."""

from __future__ import annotations

import streamlit as st

from ...palette import NEUTRAL
from ..ai_panel import _ai_panel
from ..cards import _platform_strip, _provenance_status, _verdict_card, _workbench_steps
from ..case_state import _current_assessment, _ensure_computed
from ..decision_rail import _decision_rail
from ..runtime import get_store
from ..widgets import _sticky, badge, sla_days_left, sla_pill


# ── page: Disposition Panel ───────────────────────────────────────────────────
def page_disposition():
    alerts = get_store().alert_ids()
    options = [r["ALERT_ID"] for r in alerts]
    if not options:
        st.info("No alerts found.")
        return
    alert_id = st.session_state.get("selected_alert")
    idx = options.index(alert_id) if alert_id in options else 0

    head_l, head_r = st.columns([3, 1])
    head_l.header("Disposition Panel")
    selected = head_r.selectbox("Alert", options, index=idx)
    st.session_state["selected_alert"] = selected

    alert = get_store().get_alert(selected)
    if not alert:
        st.error("Alert not found.")
        return

    _case_header(selected, alert)
    _workbench_steps()
    _provenance_status(selected)
    _verdict_card(selected)
    _platform_strip(selected)
    # Evidence first in reading and keyboard order (D1). On a narrow screen the columns stack:
    # proof (evidence → sensitivity → model interpretation) → draft → decision.
    ev_col, dec_col = st.columns([3, 2], gap="large")
    with ev_col:
        shadow = _sticky("show_proof", False)
        on = st.toggle("Show the proof", key="show_proof",
                       help="The transactions, calculator facts and hashes, every stress-test "
                            "branch, and the AI's assessment, in that order.")
        st.session_state[shadow] = on
        if on:
            _ai_panel(selected, alert)
        else:
            st.caption("Inside: the alert narrative and transactions · calculator facts with code, "
                       "input and output hashes · every stress-test branch · typology search · "
                       "rule lookup · the AI's 11-factor assessment and the agent (advisory, "
                       "after the evidence).")
    with dec_col:
        _decision_rail(selected, alert)


def _case_header(selected, alert):
    amt  = float(alert["ALERT_AMOUNT_INR"] or 0)
    days = sla_days_left(alert["ALERT_DATE"])
    st.markdown(
        f"**{alert['ALERT_ID']} — {alert['ALERT_TYPE'].replace('_', ' ').title()}**"
        f"&nbsp;&nbsp;{sla_pill(days)}&nbsp;&nbsp;"
        + badge("SYNTHETIC DATA", *NEUTRAL),
        unsafe_allow_html=True,
    )
    st.markdown(
        f"Alerted amount ₹{amt:,.0f} ({amt/1e5:.1f}L) · `{alert['SIGNAL_SOURCE']}` · "
        f"{alert['ACCOUNT_TYPE']} · alerted {alert['ALERT_DATE']}  \n"
        f"{alert['CUSTOMER_PROFILE']}"
    )
    computed = _ensure_computed(selected)        # deterministic, local; no model call
    missing = []
    if _current_assessment(selected) is None:
        missing.append("AI assessment not run")
    else:
        gaps = [f["factor_id"] for f in _current_assessment(selected)
                if f.get("assessment") == "insufficient_data"]
        if gaps:
            missing.append("insufficient data on " + ", ".join(gaps))
    missing += [w for w in computed.get("warnings", [])]
    if missing:
        st.caption("**Not yet known:** " + " · ".join(missing))
