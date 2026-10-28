"""Page: Twin Cases (ALERT-01 vs ALERT-16)."""

from __future__ import annotations

import streamlit as st

from ... import verdict as V
from ...money import format_inr
from ...palette import VERDICT_COLORS
from ..cards import _reading_html
from ..case_state import _readings
from ..runtime import get_store
from ..widgets import _esc, _goto, badge, disp_badge


# ── page: Twin Cases ──────────────────────────────────────────────────────────
def _open_alert(alert_id: str) -> None:
    st.session_state["selected_alert"] = alert_id
    _goto("Disposition Panel")


def page_twins():
    st.header("Twin Cases")
    st.markdown("Two alerts fired by the same rules on the same amount. In the scenario, one was "
                "filed and one was closed. Here is what each decision rests on.")
    store = get_store()
    a_id, b_id = V.TWIN_PAIR
    alerts = {i: store.get_alert(i) for i in V.TWIN_PAIR}
    reps = {i: _readings(i) for i in V.TWIN_PAIR}
    facts = {i: V.base_facts(store, reps[i]["FILE"]) for i in V.TWIN_PAIR}

    same = V.shared_features(alerts[a_id], alerts[b_id], facts[a_id], facts[b_id])
    fmt = lambda v: format_inr(v) if isinstance(v, (int, float)) else _esc(v)  # noqa: E731
    rows = "".join(f"<tr><td>{_esc(f['label'])}</td><td>{fmt(f['a'])}</td><td>{fmt(f['b'])}</td>"
                   f"<td>{'same' if f['same'] else 'different'}</td></tr>" for f in same)
    sig = V.signal_contrast(reps[a_id]["FILE"], reps[b_id]["FILE"])
    mark = lambda fired: "● fired" if fired else "○ —"  # noqa: E731
    fork_attr = ' class="ddp-fork"'
    rows += ('<tr><th colspan="4" style="padding-top:16px">What the calculator of record finds'
             '</th></tr>')
    rows += "".join(
        f"<tr{fork_attr if s['differs'] else ''}><td>Signal: {_esc(s['label'])}</td>"
        f"<td>{mark(s['a'])}</td><td>{mark(s['b'])}</td>"
        f"<td>{'<b>the difference</b>' if s['differs'] else 'same'}</td></tr>" for s in sig)
    st.markdown(
        f'<div class="ddp-card"><div class="ddp-kicker">Same alert, two outcomes</div>'
        f'<table class="ddp-table"><tr><th>What the alert rules saw</th><th>{a_id}</th>'
        f'<th>{b_id}</th><th></th></tr>'
        f'{rows}</table></div>', unsafe_allow_html=True)

    cols = st.columns(2, gap="large")
    for col, aid in zip(cols, V.TWIN_PAIR):
        alert = alerts[aid]
        gold = alert["GOLD_DISPOSITION"]
        r = V.reading(reps[aid][gold])
        bg, fg = VERDICT_COLORS[reps[aid][gold]["base"]["verdict"]]
        label = "If you file" if gold == "FILE" else "If you close"
        with col:
            st.markdown(
                f'<div class="ddp-card"><div class="ddp-kicker">{aid} · scenario decision</div>'
                f'<div style="margin:0 0 10px">{disp_badge(gold)} &nbsp; modeled level '
                f'{badge(reps[aid][gold]["base"]["verdict"], bg, fg)}</div>'
                f'<div class="ddp-note" style="margin:0 0 10px">{_esc(alert["CUSTOMER_PROFILE"])}'
                f'</div><div class="ddp-row">{_reading_html(r, label)}</div></div>',
                unsafe_allow_html=True)
            if st.button(f"Open {aid} →", key=f"twin_open_{aid}", width="stretch"):
                _open_alert(aid)
    runs = sum(V.card(reps[i])["runs"] for i in V.TWIN_PAIR)
    st.caption("Scenario decisions are this repo's synthetic, author-labelled outcomes: the stress "
               "test does not choose them. It shows what each one rests on and what would overturn "
               f"it, from {runs} runs of the calculator of record and no model. Signal rules are "
               "product heuristics, not FIU-IND criteria. The hospital invoice and family links "
               "that explain the closure are in the case file, outside the calculator.")
