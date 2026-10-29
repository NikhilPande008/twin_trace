"""Page: Watch — recorded decisions re-checked when the facts they rest on change (T12.5/T12.6)."""

from __future__ import annotations

import streamlit as st

from ...watch import DecisionWatch, load_feed, registry_event, scratch_twins
from ..runtime import get_runner, get_store
from ..watch_view import render_timeline
from ..widgets import _goto, _term


def page_watch():
    st.header("Watch")
    st.markdown(_term("A decision rests on a few facts. When one of them changes after the "
                      "decision is recorded (an I4C registry flag, a new transaction, a changed "
                      "rule), Twin Trace re-runs the calculator of record on the inputs saved with "
                      "the decision and tells the PO whether it still holds. Nothing here calls a "
                      "model."), unsafe_allow_html=True)
    _walkthrough()
    st.divider()
    _your_ledger()


def _walkthrough():
    st.subheader("Walkthrough: watch a closure reopen")
    st.caption("Runs on a scratch copy of the synthetic data: the twins are recorded there "
               "(ALERT-16 closed, ALERT-01 filed) and nothing is written to your ledger.")
    feed = load_feed()
    sim = st.session_state.get("_watch_sim")
    if sim is None:
        if st.button("Start the walkthrough", type="primary", key="watch_sim_start"):
            store, runner = scratch_twins()
            st.session_state["_watch_sim"] = {"store": store, "runner": runner, "applied": []}
            st.rerun()
        return

    store, runner, applied = sim["store"], sim["runner"], sim["applied"]
    watch = DecisionWatch(store, runner)
    st.markdown("**Synthetic registry feed** · apply each item in turn:")
    for item in feed["items"]:
        c_l, c_r = st.columns([4, 1], vertical_alignment="center")
        verb = "flags" if item["action"] == "flag" else "withdraws its flag on"
        c_l.markdown(f"`{item['item_id']}` · {item['received_on']} · the registry {verb} "
                     f"**{item['counterparty']}**  \n<small>{item['note']}</small>",
                     unsafe_allow_html=True)
        done = item["item_id"] in applied
        if c_r.button("Applied" if done else "Apply", key=f"watch_apply_{item['item_id']}",
                      disabled=done, width="stretch"):
            watch.apply(registry_event(item, feed["registry"]))
            applied.append(item["item_id"])
            st.rerun()
    tab16, tab01 = st.tabs(["ALERT-16 · closed", "ALERT-01 · filed"])
    with tab16:
        render_timeline(store, "ALERT-16")
    with tab01:
        render_timeline(store, "ALERT-01")
    chain = store.verify_events_chain()
    st.caption(f"Event chain: {'intact' if chain['ok'] else 'BROKEN — ' + chain['detail']} "
               f"({chain['rows']} rows, append-only).")
    if st.button("Reset the walkthrough", key="watch_sim_reset"):
        st.session_state.pop("_watch_sim", None)
        st.rerun()


def _your_ledger():
    st.subheader("Your ledger")
    store = get_store()
    watch = DecisionWatch(store, get_runner())
    standing = watch.standing_decisions()
    st.caption(f"{len(standing)} standing FILE / NOT_FILE decision(s) "
               "(latest DECISION_LEDGER row per alert).")
    if not standing:
        st.info("No decisions recorded yet. Record one on the Disposition Panel, or use the "
                "walkthrough above.")
        return
    feed = load_feed()
    if st.button(f"Run a watch pass over the {feed['registry']}", key="watch_run_feed"):
        result = watch.run_feed()
        opened = [e for e in result["events"] if e["OUTCOME"] != "holds"]
        st.success(f"Checked {len(feed['items'])} feed item(s) against {len(standing)} "
                   f"decision(s): {len(opened)} need attention.")
    for d in standing:
        with st.expander(f"{d['ALERT_ID']} · {d['DISPOSITION']}"):
            render_timeline(store, d["ALERT_ID"], show_passes=True)
            if st.button(f"Open {d['ALERT_ID']}", key=f"watch_open_{d['ALERT_ID']}"):
                st.session_state["selected_alert"] = d["ALERT_ID"]
                _goto("Disposition Panel")
    chain = store.verify_events_chain()
    st.caption(f"Event chain: {'intact' if chain['ok'] else 'BROKEN — ' + chain['detail']} "
               f"({chain['rows']} rows).")
