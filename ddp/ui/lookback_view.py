"""Rule-change review screen (T12.13), on the Regulatory Reference page."""

from __future__ import annotations

import streamlit as st

from ..config import get_settings
from ..lookback import affected_decisions, check_rule, domain_allowed, promote, proposals
from ..palette import NEUTRAL, SUCCESS, WARNING
from .officer import current_identity
from .runtime import _llm_ready, get_runner, get_skills, get_store
from .widgets import _esc, badge


def lookback_section() -> None:
    st.subheader("Has a cited rule changed at its source?")
    st.caption("Tavily fetches the rule's source page (regulator domains only). Nemotron proposes "
               "the passage that states the rule today; it is kept only if it appears word for "
               "word on the page. A kept passage is PENDING: never used for answers until an "
               "officer promotes it, and promotion sends every decision citing the rule for review. "
               "The corpus YAML itself is edited by a person.")
    store = get_store()
    rules = [r for r in store.corpus_rows() if domain_allowed(r.get("SOURCE_URL") or "")]
    ready = _llm_ready() and bool(get_settings().tavily_api_key)
    c_rule, c_btn = st.columns([3, 1], vertical_alignment="bottom")
    rule_id = c_rule.selectbox("Rule", [r["RULE_ID"] for r in rules], key="lookback_rule",
                               format_func=lambda rid: f"{rid} · {next(x['SUBCATEGORY'] for x in rules if x['RULE_ID'] == rid)}")
    n = len(affected_decisions(store, rule_id))
    st.caption(f"{n} standing decision(s) cite {rule_id} (latest ledger row per alert, "
               "RULES_CITED contains the rule).")
    if c_btn.button("Check the source", key="lookback_go", disabled=not ready, width="stretch"):
        with st.spinner("Fetching the source and checking the passage…"):
            st.session_state["_lookback_last"] = check_rule(
                store, get_skills(), rule_id, tavily_key=get_settings().tavily_api_key)
    if not ready:
        st.info("Needs `NEBIUS_API_KEY` and `TAVILY_API_KEY`.")
    last = st.session_state.get("_lookback_last")
    if last:
        _result(last)
    rows = proposals(store)
    if rows:
        st.markdown("**Proposals so far**")
        for p in rows:
            _proposal_row(p)


def _result(r: dict) -> None:
    if r.get("status") != "ok":
        st.warning(f"No proposal: {r.get('status')} {r.get('detail', '')}")
        return
    before, match, after = r.get("context") or ("", "", "")
    if r["QUOTE_VERIFIED"]:
        st.markdown(f"{badge('VERIFIED VERBATIM', *SUCCESS)} {_esc(r['RULE_ID'])} · "
                    f"page `{r['PAGE_SHA256'][:12]}…` · [{_esc(r['SOURCE_URL'])}]({r['SOURCE_URL']})",
                    unsafe_allow_html=True)
        st.markdown(f'<div class="ddp-provenance">…{_esc(before)}<mark>{_esc(match)}</mark>'
                    f'{_esc(after)}…</div>', unsafe_allow_html=True)
    else:
        st.markdown(badge("REJECTED: NOT ON THE PAGE", *WARNING), unsafe_allow_html=True)
        st.caption(f"Proposed passage: “{r.get('QUOTE') or ''}”")
    st.caption(r["SUMMARY"])


def _proposal_row(p: dict) -> None:
    store = get_store()
    status = ("PROMOTED" if p.get("PROMOTED_BY") else p["STATUS"])
    style = {"PROMOTED": SUCCESS, "PENDING": NEUTRAL}.get(status, WARNING)
    with st.expander(f"{p['RULE_ID']} · {status} · {p['CREATED_AT'][:16]}"):
        st.markdown(badge(status, *style) + f" changed: {bool(p['CHANGED'])}" if p["QUOTE_VERIFIED"]
                    else badge(status, *style), unsafe_allow_html=True)
        st.caption(f"“{p.get('QUOTE') or ''}” · {p['SUMMARY']}")
        if p.get("PROMOTED_BY"):
            st.caption(f"Promoted by {p['PROMOTED_BY']} at {p['PROMOTED_AT'][:16]}.")
        elif p["STATUS"] == "PENDING" and not p["CHANGED"]:
            st.caption("The source states the same requirement as the corpus: nothing to promote.")
        elif p["STATUS"] == "PENDING":
            ident = current_identity(st.session_state.get("po_id", ""))
            if st.button("Promote (recorded with your officer ID)", key=f"promote_{p['PROPOSAL_ID']}",
                         disabled=not ident.officer_id):
                out = promote(store, get_runner(), p["PROPOSAL_ID"], ident.officer_id, ident.basis)
                st.success(f"Promoted. {len(out['events'])} decision(s) sent for review.")
            if not ident.officer_id:
                st.caption("Enter your Principal Officer ID on the Disposition Panel (or sign in) "
                           "to promote.")
