"""Page: Regulatory Reference."""

from __future__ import annotations

import streamlit as st

from ...palette import EVIDENCE_BADGE, EVIDENCE_UNKNOWN
from ..lookback_view import lookback_section
from ..runtime import get_skills, get_store
from ..widgets import badge


# ── page: Regulatory Reference ────────────────────────────────────────────────
def page_regulatory():
    st.header("Regulatory Reference")
    st.caption("Search over the FIU-IND AML corpus (PROVEN + ASSUMED only): lexical, re-ranked "
               "with Token Factory embeddings when a key is set. Returns nothing when no rule "
               "covers the question.")

    query = st.text_input(
        "Ask a regulatory question",
        placeholder="e.g. What is the STR filing deadline? / What are the CTR obligations?",
    )

    col_limit, col_btn = st.columns([1, 3])
    limit = col_limit.number_input("Max results", min_value=1, max_value=10, value=5)

    if query:
        # P4: screen free-text regulatory question before corpus lookup
        _screen = get_skills().screen_request(query)
        if not _screen["allowed"]:
            st.error(f"Request refused: {_screen['reason']}")
        else:
            with st.spinner("Searching corpus…"):
                copilot = get_skills()
                results = copilot.regulatory_lookup(query, limit=int(limit))

        if _screen["allowed"] and not results:
            st.warning("No matching rules found.")
        elif _screen["allowed"]:
            st.success(f"{len(results)} rule(s) found")
            for r in results:
                ev = r.get("evidence_level", "UNKNOWN")
                icon, bg, fg = EVIDENCE_BADGE.get(ev, EVIDENCE_UNKNOWN)
                with st.expander(
                    f"{icon} {r['rule_id']} — {r.get('category', '')}  [{ev}]",
                    expanded=True,
                ):
                    st.markdown(badge(ev, bg, fg) + f"  &nbsp; **{r['rule_id']}**",
                                unsafe_allow_html=True)
                    st.markdown(f"**Rule:**  \n{r['rule_text']}")
                    if r.get("my_synthesis"):
                        st.markdown(f"**PO-lens synthesis:**  \n_{r['my_synthesis']}_")
                    cols = st.columns(3)
                    cols[0].markdown(f"**Source:** {r.get('source_document', '—')}")
                    cols[1].markdown(f"**Snapshot:** {r.get('snapshot_date', '—')}")
                    if r.get("source_url"):
                        cols[2].markdown(f"[Primary source link]({r['source_url']})")

    st.divider()
    lookback_section()

    st.divider()
    st.subheader("Key rules quick-reference")
    quick = get_store().corpus_by_ids(["STR-001", "STR-002", "CTR-001", "INS-001", "INS-003", "SB-002"])
    for r in quick:
        ev = r["EVIDENCE_LEVEL"]
        icon, bg, fg = EVIDENCE_BADGE.get(ev, EVIDENCE_UNKNOWN)
        st.markdown(
            f"{icon} **{r['RULE_ID']}** — {r['SUBCATEGORY']}  \n"
            f"{r['RULE_PREVIEW']}…  "
            + badge(ev, bg, fg),
            unsafe_allow_html=True,
        )
        st.markdown("")
