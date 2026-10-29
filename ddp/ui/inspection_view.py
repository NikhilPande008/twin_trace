"""Inspection replay view (T12.9) for one recorded decision, on the Decision Ledger page."""

from __future__ import annotations

import streamlit as st

from ..inspection import cross_examine, inspect_decision
from .runtime import _llm_ready, get_skills, get_store

ICON = {"answered": "✅", "needs_review": "🟠", "unanswered": "⛔", "not_applicable": "·"}


def inspection_view(decision_id: str) -> None:
    key = f"_inspection_{decision_id}"
    if st.button("Run inspection replay", key=f"inspect_{decision_id}"):
        st.session_state[key] = {"det": inspect_decision(get_store(), decision_id)}
    res = st.session_state.get(key)
    if not res:
        st.caption("Puts the inspector questions (from FIU-IND Section 13 orders) to this record "
                   "and answers each from the record alone. Deterministic; no model.")
        return
    det = res["det"]
    st.markdown(f"**The record answers {det['answered']} of {det['asked']} questions.** "
                f"Question bank v{det['bank_version']} · `{det['bank_sha256'][:12]}…`")
    for r in det["results"]:
        refs = ", ".join(f"`{x}`" for x in r["rows"][:4])
        st.markdown(f"{ICON[r['status']]} **{r['id']}** {r['question']}  \n"
                    f"<small>{r['answer']}{' · ' + refs if refs else ''}</small>",
                    unsafe_allow_html=True)
    if st.button("Cross-examine with Nemotron", key=f"xexam_{decision_id}",
                 disabled=not _llm_ready(),
                 help="A model lists what an inspector would still ask. It may call a question "
                      "answered only by citing row IDs; code checks every citation."):
        with st.spinner("Cross-examining the record…"):
            res["x"] = cross_examine(get_skills(), get_store(), decision_id, det)
    x = res.get("x")
    if x:
        if x["status"] != "ok":
            st.warning(f"Cross-examination unavailable: {x['reason']}")
            return
        st.markdown(f"**Model cross-examination** · {len(x['accepted'])} finding(s) accepted · "
                    f"{len(x['rejected'])} rejected for citing rows that are not in this record, "
                    "belong to another alert, or no longer match their hash")
        for f in x["accepted"]:
            mark = "answered by " + ", ".join(f"`{c}`" for c in f["cited_rows"]) if f["answered"] \
                else "**not answered by the record**"
            st.markdown(f"- {f['question']} · {mark}  \n<small>{f['note']}</small>",
                        unsafe_allow_html=True)
        for f in x["rejected"]:
            st.markdown(f"- ~~{f['question']}~~ · rejected: "
                        + "; ".join(f"`{k}` {v}" for k, v in f["rejected_citations"].items())
                        if f["rejected_citations"] else f"- ~~{f['question']}~~ · rejected: no citation")
