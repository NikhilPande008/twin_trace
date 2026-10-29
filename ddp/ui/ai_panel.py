"""Disposition Panel proof column. Order matters (anti-anchoring): evidence first, the AI
assessment after it, the agent's disposition last."""

from __future__ import annotations

import json

import streamlit as st

from .. import platform_trace as PT
from ..bootstrap import build_investigator
from ..palette import EVIDENCE_BADGE, EVIDENCE_UNKNOWN, MUTED_TEXT, NEUTRAL, RECOMMENDATION_COLORS
from .case_state import (_add_model_call, _calls_mark, _current_assessment, _log_calls_since,
                         _model_label, _platform_calls, _trace)
from .evidence_panels import (_adverse_media_panel, _calculator_panel, _signal_brief,
                              _stress_panel, _trace_panel)
from .panel_view import panel_section
from .runtime import (_llm_ready, _load_transactions, get_pipeline, get_runner, get_skills,
                      get_store)
from .widgets import _kind, badge, disp_badge


def _ai_panel(selected, alert):
    """Right column. Order matters (anti-anchoring): evidence and the stress test first, AI
    outputs after, and the agent's advisory disposition last of all."""
    _ai_panel_core(selected, alert)
    panel_section(selected, alert)
    _agent_panel(selected)
    _trace_panel(selected)


def _agent_panel(selected):
    """Agentic investigator: Nemotron chooses the tools; every call is logged as evidence."""
    st.divider()
    st.markdown("#### Agentic investigation")
    _kind("Model interpretation", "advisory; a second route, not needed for a decision")
    st.caption("Nemotron (reasoning tier) plans the investigation with tool calls: case data, "
               "calculator, stress test, corpus, regulator search. Its submission is rejected "
               "if it cites anything the tools did not return.")
    inv = build_investigator(get_store(), get_skills(), get_runner())
    key = f"agent_{selected}"
    q = st.text_input("Question for the investigator (optional)", key=f"agent_q_{selected}")
    if st.button("Run investigator", key=f"agent_btn_{selected}", disabled=inv is None):
        with st.status(f"Investigating — {_model_label('reasoning')} with tools…",
                       expanded=True) as status:
            t = inv.investigate(selected, q.strip(), on_event=status.write)
            status.update(label=f"Investigation {t['status']}", expanded=False,
                          state="complete" if t["status"] == "submitted" else "error")
        st.session_state[key] = t
        _platform_calls(selected).extend(PT.call_rows("Agent tool loop", t.get("model_calls", [])))
        st.rerun()
    if inv is None:
        st.info("Needs `NEBIUS_API_KEY` (tool-calling model).")
    t = st.session_state.get(key)
    if not t:
        return
    st.caption(f"Status **{t['status']}** · {len(t['steps'])} tool calls · "
               f"{t.get('rejections', 0)} rejected submissions · "
               f"{t.get('tokens', {}).get('prompt', 0)}+{t.get('tokens', {}).get('completion', 0)} "
               f"tokens · {t.get('latency_s', 0)} s")
    for s in t["steps"]:
        icon = "✅" if s["ok"] else "⛔"
        with st.expander(f"{icon} step {s['step']} · {s['tool']}"):
            st.code(json.dumps(s["arguments"], indent=1), language="json")
            st.caption(s["result_preview"])
            st.caption(f"evidence `{s['evidence_id']}`")
    if t.get("reason"):
        st.warning(t["reason"])
    a = t.get("assessment")
    if a:
        with st.expander("Show the agent's advisory disposition (after your own review)"):
            st.markdown(disp_badge(a["disposition"]), unsafe_allow_html=True)
            st.markdown(a["rationale"])
            st.caption("Facts: " + ", ".join(a["cited_fact_ids"]) + " · txns: "
                       + ", ".join(a["cited_txn_ids"]) + " · rules: "
                       + (", ".join(a["cited_rule_ids"]) or "none"))


def _ai_panel_core(selected, alert):
    _case_evidence(selected, alert)
    _rule_lookup()
    assessment = _current_assessment(selected)
    if assessment is None:
        _assessment_prompt(selected, alert)
        return
    _assessment_view(assessment)


def _case_evidence(selected, alert):
    """Narrative, signal brief, calculator, stress test, typology search, red flags."""
    st.markdown(f"> {alert['ALERT_NARRATIVE']}")
    _signal_brief(selected, alert)
    _calculator_panel(selected)
    _stress_panel(selected)
    _adverse_media_panel(selected, alert)
    try:
        rfi_list = json.loads(str(alert.get("RFI_TRIGGERS") or "[]"))
    except Exception:
        rfi_list = []
    if rfi_list:
        st.markdown("**Red-flag indicators:** " + "  ·  ".join(f"`{r}`" for r in rfi_list))


def _rule_lookup():
    with st.expander("🔍 Lookup a rule", expanded=False):
        q = st.text_input("Regulatory question", key="inline_rule_q",
                          placeholder="e.g. What is the STR filing deadline?")
        if st.button("Search", key="inline_rule_btn") and q.strip():
            # P4: screen free-text user query before corpus lookup
            _screen = get_skills().screen_request(q.strip())
            if not _screen["allowed"]:
                st.error(f"Request refused: {_screen['reason']}")
            else:
                with st.spinner("Searching corpus…"):
                    results = get_skills().regulatory_lookup(q.strip(), limit=3)
                if not results:
                    st.caption("No matching rules found.")
                for r in results:
                    ev = r.get("evidence_level", "UNKNOWN")
                    icon, bg, fg = EVIDENCE_BADGE.get(ev, EVIDENCE_UNKNOWN)
                    st.markdown(
                        f"{icon} **{r['rule_id']}** — {r.get('category', '')} {badge(ev, bg, fg)}  \n"
                        f"{r['rule_text']}",
                        unsafe_allow_html=True,
                    )


def _assessment_prompt(selected, alert):
    """No assessment yet: explain it and offer to run it (needs a model key)."""
    st.markdown("#### AI suspicion assessment",
                help="The case is assessed against 11 factors (income, source of funds, "
                     "geography, KYC and so on). The list is this product's compilation, "
                     "not an FIU-IND-issued checklist.")
    _kind("Model interpretation", "recommended route: advisory, shown after the evidence")
    st.caption("Evaluates the alert against 11 factors (Nemotron, reasoning tier).")
    if not _llm_ready():
        st.info("Model access is not configured. Add `NEBIUS_API_KEY` to `.env` "
                "(see `.env.example`) to enable AI assessment and drafting. "
                "Everything else — computed facts, evidence gate, ledger — works offline.")
    if st.button("Run 11-Factor Assessment", type="primary", disabled=not _llm_ready()):
        case_ctx = {
            "customer_kyc":    alert["CUSTOMER_PROFILE"],
            "transactions":    _load_transactions(selected),
            "signal_tags":     json.loads(str(alert.get("RFI_TRIGGERS") or "[]")),
            "alert_narrative": alert["ALERT_NARRATIVE"],
        }
        mark = _calls_mark()
        with st.spinner(f"Evaluating against 11 factors — {_model_label('reasoning')}…"):
            step = get_pipeline().step_assess(case_ctx, _trace(selected))
        _log_calls_since(selected, "11-factor assessment", mark)
        if step.status != "ok":
            st.error(f"The AI assessment could not run: {step.blocked_reason}")
            st.caption("You can still write the Ground of Suspicion and record a decision.")
        elif step.outputs.get("parse_failed"):
            # The 11 placeholders are not the model's view; showing them would read as
            # "the case lacks data" when it was the model's reply that failed.
            st.error("The AI assessment failed: the model's reply was not valid JSON after "
                     "one retry. No factor was assessed. Run it again.")
            st.caption("You can still write the Ground of Suspicion and record a decision.")
        else:
            st.session_state["poe_assessment"] = step.outputs["assessments"]
            _add_model_call(selected, step.model_call)
            st.session_state["assessed_alert"] = selected
            st.session_state["case_ctx"] = case_ctx
            st.rerun()


def _assessment_view(assessment):
    copilot   = get_skills()
    triggered = [f for f in assessment if f.get("assessment") == "triggered"]
    clear     = [f for f in assessment if f.get("assessment") == "clear"]
    insuff    = [f for f in assessment if f.get("assessment") == "insufficient_data"]
    sufficiency = copilot.evidence_sufficiency_summary(assessment)

    h_l, h_r = st.columns([3, 1])
    h_l.markdown("#### AI suspicion assessment")
    _kind("Model interpretation", "advisory; you may disagree and say why")
    if h_r.button("↻ Re-run", width="stretch"):
        for key in ["poe_assessment", "assessed_alert", "gos_result", "gos_alert"]:
            st.session_state.pop(key, None)
        st.rerun()

    tab_a, tab_g, tab_p = st.tabs(
        ["Assessment", f"Evidence Gaps ({len(insuff)})", "Investigation Plan"]
    )

    with tab_a:
        _assessment_tab(assessment, triggered, clear, insuff, sufficiency)
    with tab_g:
        _gaps_tab(insuff, sufficiency)
    with tab_p:
        _plan_tab(triggered, insuff)


def _assessment_tab(assessment, triggered, clear, insuff, sufficiency):
    m1, m2, m3 = st.columns(3)
    m1.metric("Triggered", len(triggered))
    m2.metric("Clear", len(clear))
    m3.metric("Insufficient data", len(insuff))

    for fac in assessment:
        asmt = fac.get("assessment", "insufficient_data")
        icon = "🔴" if asmt == "triggered" else ("🟢" if asmt == "clear" else "⚪")
        with st.expander(f"{icon} {fac.get('factor_id')} — {fac.get('factor_name')}",
                         expanded=(asmt == "triggered")):
            st.markdown(f"**Assessment:** `{asmt}`")
            st.markdown(f"**Evidence:** {fac.get('evidence', '—')}")
            txn_ids = fac.get("evidence_txn_ids") or []
            if txn_ids:
                st.markdown(f"**Supported by transactions:** {', '.join(txn_ids)}")
            cited = fac.get("rules_cited") or []
            if cited:
                st.markdown(f"**Rules cited:** {', '.join(cited)}")

    _ai_recommendation(sufficiency, triggered, insuff)


def _ai_recommendation(sufficiency, triggered, insuff):
    # AI Recommendation — last, after the evidence (WS-5)
    rec = sufficiency["recommendation"]
    _rec_label = {"FILE": "FILE", "REVIEW": "REVIEW — further evidence needed",
                  "INSUFFICIENT_EVIDENCE": "INSUFFICIENT EVIDENCE — cannot recommend",
                  "NOT_FILE": "NOT FILE"}.get(rec, rec)
    rec_bg = (*RECOMMENDATION_COLORS.get(rec, NEUTRAL), _rec_label)
    st.markdown(
        f'<div style="background:{rec_bg[0]};border-left:4px solid {rec_bg[1]};'
        f'padding:12px 16px;border-radius:4px;margin:8px 0">'
        f'<span style="color:{rec_bg[1]};font-weight:700;font-size:1.05em">AI Recommendation: {rec_bg[2]}</span><br>'
        f'<span style="font-size:0.85em;color:{MUTED_TEXT}">Based on {len(triggered)} triggered factor(s) '
        f'and {len(insuff)} gap(s). The Principal Officer must form an independent view.</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    with st.expander("What would change this recommendation?", expanded=False):
        if rec == "FILE":
            st.markdown(
                "This recommendation would change to **REVIEW** or **NOT FILE** if:\n"
                "- The customer provides documented proof of source of funds that explains the transaction pattern.\n"
                "- The beneficiary counterparty is removed from the I4C Suspect Registry.\n"
                "- Prior similar transactions are found to have legitimate explanations on file.\n"
                "- KYC documents reveal a declared business activity consistent with the credits."
            )
        elif rec == "INSUFFICIENT_EVIDENCE":
            st.markdown(
                "This recommendation would change to **FILE** or **NOT FILE** once:\n"
                "- The evidence gaps are resolved (KYC obtained, source of funds documented, etc.).\n"
                "- The PO has sufficient facts to form a reasonable view on whether suspicion is warranted."
            )
        else:
            st.markdown(
                "This recommendation would change to **FILE** if:\n"
                "- A pattern of similar transactions is identified across linked accounts.\n"
                "- The beneficiary counterparty is flagged in a regulatory watchlist.\n"
                "- New information emerges inconsistent with the documented explanation."
            )


def _gaps_tab(insuff, sufficiency):
    if not insuff:
        st.success("Every factor had enough data to assess.")
    else:
        if sufficiency["recommendation"] == "INSUFFICIENT_EVIDENCE":
            st.warning(
                f"{len(insuff)} factor(s) lack the data needed to form a defensible view. "
                f"Obtain the missing information before deciding to FILE or CLOSE."
            )
        for gap in sufficiency["gaps"]:
            st.markdown(f"- **{gap['factor_id']} ({gap['factor_name']}):** {gap['evidence']}")


def _plan_tab(triggered, insuff):
    st.caption("Investigative steps derived from the triggered factors. "
               "The PO conducts each step and forms their own view.")
    plan_items = []
    triggered_ids = {f["factor_id"] for f in triggered}
    insuff_ids    = {f["factor_id"] for f in insuff}

    if "POE-002" in triggered_ids or "POE-005" in triggered_ids:
        plan_items.append("Verify declared occupation/income against payroll records or tax filings.")
    if "POE-003" in triggered_ids:
        plan_items.append("Pull 12-month account statement; identify any prior similar high-velocity periods.")
    if "POE-006" in triggered_ids:
        plan_items.append("Request documentary proof of source of funds (invoice, contract, or bank confirmation) for each credit.")
    if "POE-007" in triggered_ids:
        plan_items.append("Run beneficiary counterparty(ies) through I4C Suspect Registry and internal watchlists.")
    if "POE-008" in triggered_ids:
        plan_items.append("Check if the same burst-frequency pattern appears in prior periods or linked accounts.")
    if "POE-011" in triggered_ids:
        plan_items.append("Verify SWIFT correspondent chain; check if any intermediary bank is on FATF grey/black list.")
    if "POE-012" in insuff_ids:
        plan_items.append("Obtain current KYC: re-verify identity documents, address, and Aadhaar linkage before filing.")
    if not plan_items:
        plan_items.append("No specific investigative steps required for current triggered factors.")
    for item in plan_items:
        st.markdown(f"- {item}")
