"""Page: Alert Queue."""

from __future__ import annotations

import streamlit as st

from ...money import format_inr
from ..cards import _intro, _stakes
from ..runtime import get_store
from ..widgets import _esc, _goto, disp_badge, sla_days_left, sla_pill


# ── page: Alert Queue ─────────────────────────────────────────────────────────
def page_alert_queue():
    st.header("Alert Queue")
    with st.container(border=True):
        s_l, s_r = st.columns([4, 1], vertical_alignment="center")
        s_l.markdown("**Start here.** Two alerts fired by the same rules on the same amount; one "
                     "was filed and one was closed. See what each decision rests on.")
        if s_r.button("Twin Cases →", type="primary", width="stretch", key="aq_twins"):
            _goto("Twin Cases")
    _stakes()
    _intro()
    st.caption("Most urgent first · SLA = 7 working days, counted from alert date until suspicion is recorded")

    rows = get_store().alerts_with_last_disposition()

    if not rows:
        st.info("No alerts found.")
        return

    for r in rows:
        r["SLA_DAYS"] = sla_days_left(r["ALERT_DATE"])
        r["AMOUNT"]   = float(r["ALERT_AMOUNT_INR"] or 0)
        r["WORK_STATUS"] = "DEFERRED" if r.get("LAST_DISPOSITION") == "DEFERRED" else r["ALERT_STATUS"]

    pending = [r for r in rows if r["WORK_STATUS"] != "REVIEWED"]
    due_soon = sum(1 for r in pending if 0 <= r["SLA_DAYS"] <= 1)
    overdue = sum(1 for r in pending if r["SLA_DAYS"] < 0)
    st.markdown(
        f'<div class="ddp-card"><div class="ddp-kicker">Review posture</div>'
        f'<strong>{len(pending)} awaiting a recorded decision</strong> · {due_soon} due within one '
        f'working day · {overdue} overdue · pending alerted amount '
        f'<strong>{format_inr(sum(r["AMOUNT"] for r in pending))}</strong>'
        '<div class="ddp-foot">Urgency is a review aid only. It does not determine whether activity '
        'is suspicious or whether a report should be filed.</div></div>',
        unsafe_allow_html=True,
    )

    # ── filter bar ─────────────────────────────────────────────────────────
    statuses = sorted({r["WORK_STATUS"] for r in rows})
    types    = sorted({r["ALERT_TYPE"] for r in rows})
    sources  = sorted({r["SIGNAL_SOURCE"] or "UNKNOWN" for r in rows})
    max_l    = max(1.0, round(max(r["AMOUNT"] for r in rows) / 1e5 + 0.5, 0))

    f_search, f_status, f_type, f_src, f_amt = st.columns([1.6, 1.6, 2, 1.6, 2])
    search = f_search.text_input("Search", placeholder="Alert ID or customer",
                                 key="aq_search").strip().lower()
    sel_status = f_status.multiselect(
        "Status", statuses,
        default=[s for s in statuses if s != "REVIEWED"] or statuses, key="aq_status")
    sel_type = f_type.multiselect("Type", types, format_func=lambda t: t.replace("_", " ").title(),
                                  key="aq_type")
    sel_src  = f_src.multiselect("Signal source", sources, key="aq_src")
    amt_lo, amt_hi = f_amt.slider("Amount (₹ lakh)", 0.0, float(max_l), (0.0, float(max_l)),
                                  key="aq_amt")

    shown = [
        r for r in rows
        if (not sel_status or r["WORK_STATUS"] in sel_status)
        and (not sel_type or r["ALERT_TYPE"] in sel_type)
        and (not sel_src or (r["SIGNAL_SOURCE"] or "UNKNOWN") in sel_src)
        and amt_lo <= r["AMOUNT"] / 1e5 <= amt_hi
        and (not search or search in r["ALERT_ID"].lower()
             or search in str(r["CUSTOMER_PROFILE"] or "").lower())
    ]
    # Undecided first, then by SLA urgency, then larger amounts
    shown.sort(key=lambda r: (r["WORK_STATUS"] == "REVIEWED", r["SLA_DAYS"], -r["AMOUNT"]))

    st.caption(f"Showing {len(shown)} of {len(rows)} alerts")
    st.divider()

    if not shown:
        st.info("No alerts match these filters.")
        return

    for r in shown:
        alert_id = r["ALERT_ID"]
        urgency = (disp_badge(r.get("LAST_DISPOSITION") or "REVIEWED")
                   if r["WORK_STATUS"] == "REVIEWED" else sla_pill(r["SLA_DAYS"]))
        summary, action_col = st.columns([5, 1], vertical_alignment="center")
        with summary:
            st.markdown(
                f'<div class="ddp-queue-row"><strong><code>{_esc(alert_id)}</code> · '
                f'{_esc(r["ALERT_TYPE"].replace("_", " ").title())}</strong> &nbsp; {urgency}'
                f'<div class="ddp-queue-meta"><span>Alerted amount: <strong>{format_inr(r["AMOUNT"])}</strong></span>'
                f'<span>Signal: <code>{_esc(r["SIGNAL_SOURCE"] or "UNKNOWN")}</code></span>'
                f'<span>Account: {_esc(r["ACCOUNT_TYPE"] or "—")}</span>'
                f'<span>Status: {_esc(r["WORK_STATUS"])}</span></div></div>',
                unsafe_allow_html=True,
            )
        with action_col:
            if st.button(f"Open {alert_id}", key=f"review_{alert_id}", width="stretch",
                         type="primary" if r["WORK_STATUS"] != "REVIEWED" else "secondary"):
                st.session_state["selected_alert"] = alert_id
                _goto("Disposition Panel")

        with st.expander("Customer profile", expanded=False):
            st.markdown(f"{r['CUSTOMER_PROFILE']}  \n"
                        f"**Account type:** {r['ACCOUNT_TYPE']}  ·  "
                        f"**Alert date:** {r['ALERT_DATE']}  ·  "
                        f"**Status:** {r['WORK_STATUS']}")
