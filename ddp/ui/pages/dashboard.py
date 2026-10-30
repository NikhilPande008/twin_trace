"""Page: Inspection Readiness Dashboard."""

from __future__ import annotations

import streamlit as st

from ..runtime import get_store
from ..widgets import sla_days_left


def page_dashboard():
    st.header("Inspection Readiness Dashboard")
    st.caption("Internal governance view. The alert-to-STR ratio is an internal metric that "
               "inspectors are understood to examine (INS-003, ASSUMED); FIU-IND publishes no "
               "benchmark for it.")

    alerts_rows = get_store().dashboard_alerts()
    ledger_rows = get_store().dashboard_ledger()

    open_a    = sum(1 for r in alerts_rows if r["ALERT_STATUS"] == "OPEN")
    reviewed  = sum(1 for r in alerts_rows if r["ALERT_STATUS"] == "REVIEWED")
    filed     = sum(1 for r in ledger_rows if r["DISPOSITION"] == "FILE")
    not_filed = sum(1 for r in ledger_rows if r["DISPOSITION"] == "NOT_FILE")
    deferred  = sum(1 for r in ledger_rows if r["DISPOSITION"] == "DEFERRED")
    # open alerts past the window, counted as the Alert Queue counts them; and decisions
    # that were recorded after it
    open_overdue = sum(1 for r in alerts_rows if r["ALERT_STATUS"] == "OPEN"
                       and r.get("ALERT_DATE") and sla_days_left(r["ALERT_DATE"]) < 0)
    late      = sum(1 for r in ledger_rows if (r["SLA_DAYS_REMAINING"] or 99) < 0)
    ratio     = round(filed * 100 / (filed + not_filed), 1) if (filed + not_filed) > 0 else None

    st.subheader("Alert Pipeline")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Open (pending review)", open_a)
    c2.metric("Reviewed", reviewed)
    c3.metric("Filed (STR)", filed)
    c4.metric("Not Filed", not_filed)

    st.subheader("Inspection readiness (internal metrics)")
    m1, m2, m3 = st.columns(3)

    if ratio is not None:
        m1.metric(
            "Alert-to-STR Ratio",
            f"{ratio}%",
            help="Internal governance metric (no FIU-IND benchmark published — Gap DG-04). Too low = suppression risk; too high = over-filing.",
        )
    else:
        m1.metric("Alert-to-STR Ratio", "—", help="Record some decisions first.")

    m2.metric("Open alerts past 7 WD", open_overdue,
              help="Counted from the alert date, as on the Alert Queue. Decisions recorded "
                   f"after the 7-working-day window: {late}.")
    m3.metric("Deferred / Pending Info", deferred)

    st.divider()
    st.subheader("Alert Breakdown by Type")

    type_counts: dict[str, int] = {}
    for r in alerts_rows:
        t = r["ALERT_TYPE"].replace("_", " ").title()
        type_counts[t] = type_counts.get(t, 0) + 1

    if type_counts:
        import json as _json
        chart_data = [{"type": k, "count": v} for k, v in sorted(type_counts.items(), key=lambda x: -x[1])]
        st.bar_chart(
            data={r["type"]: r["count"] for r in chart_data},
            width="stretch",
            height=300,
        )

    st.subheader("Signal Source Mix")
    src_counts: dict[str, int] = {}
    for r in alerts_rows:
        s = r.get("SIGNAL_SOURCE") or "UNKNOWN"
        src_counts[s] = src_counts.get(s, 0) + 1
    for src, cnt in sorted(src_counts.items(), key=lambda x: -x[1]):
        pct = round(cnt * 100 / len(alerts_rows)) if alerts_rows else 0
        st.markdown(f"`{src}` — {cnt} alerts ({pct}%)")

    st.divider()
    st.subheader("Token usage (Nebius Token Factory)")
    usage = get_store().token_usage_summary()
    if usage["total"] == 0:
        st.caption(
            "No model calls recorded yet. Token usage is tracked automatically "
            "from recorded decisions once you run the AI assessment and record a disposition."
        )
    else:
        u1, u2, u3 = st.columns(3)
        u1.metric("Prompt tokens", f"{usage['total_prompt']:,}")
        u2.metric("Completion tokens", f"{usage['total_completion']:,}")
        u3.metric("Total tokens", f"{usage['total']:,}",
                  help="Across all recorded decisions in the local ledger. "
                       "Resets when the database is re-seeded.")

        if usage["by_tier"]:
            tier_order = ["triage", "reasoning", "disposition"]
            rows_table = [
                t for t in tier_order if t in usage["by_tier"]
            ] + [t for t in usage["by_tier"] if t not in tier_order]

            st.markdown("**By tier**")
            hdr, h2, h3, h4 = st.columns([2, 2, 2, 2])
            hdr.markdown("**Tier**")
            h2.markdown("**Prompt**")
            h3.markdown("**Completion**")
            h4.markdown("**Total**")
            for tier in rows_table:
                b = usage["by_tier"][tier]
                c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
                c1.markdown(f"`{tier}`")
                c2.markdown(f"{b['prompt']:,}")
                c3.markdown(f"{b['completion']:,}")
                c4.markdown(f"{b['prompt'] + b['completion']:,}")

        st.caption(
            f"Derived from {usage['decisions_with_model_calls']} decision(s) that recorded model calls. "
            "Counts reflect only calls made through this app's ledger — not probe scripts or harness runs. "
            "Token costs depend on the tier's model; check the Token Factory console for billing details."
        )

    st.divider()
    st.caption(
        "Alert-to-STR ratio is an internal governance metric. "
        "No official FIU-IND benchmark has been publicly confirmed (Gap DG-04). "
        "Inspect the not-filed rationale column in the Decision Ledger for inspection readiness."
    )
