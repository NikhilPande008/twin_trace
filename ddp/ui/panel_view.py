"""Tier panel view (T12.8). AI output, so it sits in the AI section after the evidence."""

from __future__ import annotations

import json

import streamlit as st

from .. import platform_trace as PT
from ..bootstrap import build_panel
from ..palette import NEUTRAL, RECOMMENDATION_COLORS, SUCCESS, ERROR, WARNING
from .runtime import _load_transactions, get_skills, get_store
from .widgets import _esc, _kind, badge

TIER_LABEL = {"triage": "Nano", "reasoning": "Super", "disposition": "Ultra"}
CELL = {"triggered": ERROR, "clear": SUCCESS, "insufficient_data": WARNING}


def latest_panel(store, alert_id: str) -> dict | None:
    rows = store.evidence_for_alert(alert_id, "tier_panel")
    return json.loads(rows[-1]["CONTENT_JSON"]) if rows else None


def _stress_report(store, alert_id):
    rows = store.evidence_for_alert(alert_id, "stress_test")
    return json.loads(rows[-1]["CONTENT_JSON"]) if rows else None


def panel_section(selected: str, alert: dict) -> None:
    st.divider()
    st.markdown("#### Tier panel: do three model sizes agree?")
    _kind("Model interpretation", "advisory; disagreement sends the alert to you as contested")
    st.caption("Nemotron Nano, Super and Ultra each assess the case independently, in parallel, "
               "on Nebius Token Factory. Whether they agree is computed from their answers, not "
               "asked of a model.")
    store = get_store()
    panel = build_panel(store, session_llm=getattr(get_skills(), "_llm", None))
    if st.button("Run the tier panel (3 models)", key=f"panel_btn_{selected}",
                 disabled=panel is None):
        case = {"customer_kyc": alert["CUSTOMER_PROFILE"],
                "transactions": _load_transactions(selected),
                "signal_tags": json.loads(str(alert.get("RFI_TRIGGERS") or "[]")),
                "alert_narrative": alert["ALERT_NARRATIVE"]}
        with st.spinner("Three tiers assessing in parallel…"):
            panel.run(case, stress_report=_stress_report(store, selected), store=store,
                      alert_id=selected)
        st.rerun()
    if panel is None:
        st.info("Needs `NEBIUS_API_KEY`.")
    r = latest_panel(store, selected)
    if r:
        render_panel(r)


def render_panel(r: dict) -> None:
    tiers = [t for t in ("triage", "reasoning", "disposition") if t in r["recommendations"]
             or t in r.get("tiers_failed", [])]
    if r["contested"]:
        head = badge("CONTESTED", *WARNING) + " The models disagree: this alert needs your judgement."
    elif r["unanimous"]:
        head = (badge("AGREE", *SUCCESS) + " All answering tiers recommend "
                + badge(r["unanimous"], *RECOMMENDATION_COLORS.get(r["unanimous"], NEUTRAL)))
    else:
        head = badge("INCOMPLETE", *NEUTRAL) + " Fewer than two tiers answered."
    split = ", ".join(r["split_factors"]) or "none"
    fact = r.get("splitting_fact") or "no single counter-hypothesis flips the modeled level"
    st.markdown(f"{head}  \n<small>Models split on: {_esc(split)}. "
                f"The calculator says the decision turns on: {_esc(fact)}.</small>",
                unsafe_allow_html=True)
    hdr = "".join(f"<th>{TIER_LABEL[t]}<div class='ddp-note'>"
                  f"{_esc(PT.short_model((r['calls'].get(t) or {}).get('model_reported') or (r['calls'].get(t) or {}).get('model_requested') or ''))}"
                  f"</div></th>" for t in tiers)
    rec_row = "".join(
        "<td>" + (badge(r["recommendations"][t], *RECOMMENDATION_COLORS.get(r["recommendations"][t], NEUTRAL))
                  if t in r["recommendations"] else badge("FAILED", *NEUTRAL)) + "</td>"
        for t in tiers)
    body = []
    for g in r["grid"]:
        cells = "".join(
            "<td>" + (badge(g["by_tier"][t].replace("_", " "), *CELL.get(g["by_tier"][t], NEUTRAL))
                      if t in g["by_tier"] else "—") + "</td>" for t in tiers)
        cls = ' class="ddp-fork"' if g["split"] else ""
        body.append(f"<tr{cls}><td>{_esc(g['factor_id'])} · {_esc(g['factor_name'])}</td>{cells}</tr>")
    st.markdown(f'<table class="ddp-table"><tr><th>Factor</th>{hdr}</tr>'
                f'<tr><td><strong>Recommendation</strong></td>{rec_row}</tr>{"".join(body)}</table>',
                unsafe_allow_html=True)
    if r.get("errors"):
        st.caption("Failed tiers: " + "; ".join(f"{TIER_LABEL[t]}: {e}" for t, e in r["errors"].items()))
