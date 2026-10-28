"""Disposition Panel, right column: the officer's Ground of Suspicion and decision, confirmation
and recording."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import streamlit as st

from ..gate import DeterministicPolicyGate
from ..identity import SELF_ASSERTED
from ..palette import NEUTRAL, SCORE_BAD, SCORE_GOOD, SCORE_MID
from .case_state import (_add_model_call, _calls_mark, _current_assessment, _current_computed,
                         _current_gos, _ensure_computed, _log_calls_since, _model_calls,
                         _model_label, _trace)
from .runtime import _load_transactions, get_pipeline, get_skills
from .officer import current_identity
from .widgets import IST, _kind, _session_user_id, _set_sticky, _sha, _sticky, badge


def _decision_rail(selected, alert):
    """Right column, after the evidence: the officer's draft and decision."""
    # ── Ground of Suspicion ────────────────────────────────────────────────
    st.markdown("#### Ground of Suspicion",
                help="Part (c) of an STR: the officer's written reasoning for why the activity "
                     "is suspicious. Every ₹ figure in it is checked against the case's "
                     "transactions and the calculator of record.")
    _kind("Officer conclusion", "your text; an AI draft is a starting point you edit")
    assessment = _current_assessment(selected)
    gos        = _current_gos(selected)
    text_key   = f"gos_text_{selected}"

    if gos is None:
        if not _draft_with_ai(selected, assessment, text_key):
            return
    else:
        _draft_checks(selected, gos, text_key)

    narrative = _narrative_editor(selected, text_key)
    if gos is not None:
        _recheck_button(selected, gos, narrative)

    # ── Decision ───────────────────────────────────────────────────────────
    po_id, suspicion_ts, str_ref, ident = _decision_inputs(selected)
    if assessment:
        _counter_evidence(selected, assessment)
    _decision_buttons(selected, alert, narrative, ident, suspicion_ts, str_ref, assessment)


def _draft_with_ai(selected, assessment, text_key) -> bool:
    """No draft yet: offer an AI draft once the assessment exists. Returns False when the
    draft could not be produced; the rest of the rail is then not shown."""
    if assessment is not None:
        if st.button("✍️ Draft with AI", key=f"draft_{selected}"):
            # Tipping-off screen before any model invocation, then the pipeline's draft and
            # policy-gate steps, all recorded on this alert's run trace.
            trace = _trace(selected)
            screen_step = get_pipeline().step_screen("Draft Ground of Suspicion narrative",
                                                     trace)
            if screen_step.status == "blocked":
                st.error(f"Request refused: {screen_step.blocked_reason}")
            else:
                computed = _ensure_computed(selected)
                mark = _calls_mark()
                with st.spinner(f"Drafting Part (c) — {_model_label('disposition')}, then "
                                f"quality check — {_model_label('triage')}…"):
                    draft_step = get_pipeline().step_draft(
                        st.session_state["case_ctx"], assessment, computed, trace)
                _log_calls_since(selected, "Draft + quality check", mark)
                if draft_step.status != "ok":
                    st.error(f"The draft could not be produced: {draft_step.blocked_reason}")
                    return False
                result = draft_step.outputs["gos"]
                get_pipeline().step_policy_gate(result["narrative"], trace)
                _add_model_call(selected, result.get("drafting_model"))
                result["checked_sha256"] = _sha(result["narrative"])
                st.session_state["gos_result"] = result
                st.session_state["gos_alert"]  = selected
                _set_sticky(text_key, result["narrative"])
                st.rerun()
    else:
        st.caption("Open **Show the proof** and run the AI assessment for a draft, or write "
                   "your own.")
    return True


def _draft_checks(selected, gos, text_key):
    """Checks on the current draft: quality score, hard gate, figures, policy gate, dates."""
    score = gos["quality_score"]
    style = SCORE_GOOD if score >= 8 else (SCORE_MID if score >= 5 else SCORE_BAD)
    stale = gos.get("checked_sha256") != _sha(st.session_state.get(text_key, ""))
    status = "NOT RE-CHECKED" if stale else gos["status"]
    st.markdown(
        f'Model quality check <span style="color:{style[1]};font-weight:700">{score}/10</span>'
        f'&nbsp;&nbsp;{badge(status, *(NEUTRAL if stale else style))}',
        unsafe_allow_html=True,
    )
    if stale:
        st.warning("The text changed after this check. The score and status above are for "
                   "the earlier text; use **Re-check edited draft**. Figures below are always "
                   "checked against the current text.")
    if not gos.get("hard_gate_passed", True):
        detail = gos.get("hard_gate_failure") or ""
        unsupported = gos.get("unsupported_facts") or []
        bad_txn_ids = gos.get("unresolved_txn_ids") or []
        st.error(
            "**Hard gate BLOCKED:** one or more amounts in the narrative are not found "
            "in the transaction record or the calculator facts. Revise before filing."
            + (f"  \n{detail}" if detail else "")
            + ("  \nAmounts not found: " + ", ".join(f"`{u}`" for u in unsupported) if unsupported else "")
            + ("  \nTXN IDs not resolved: " + ", ".join(f"`{t}`" for t in bad_txn_ids) if bad_txn_ids else "")
        )
        st.caption(
            "**To repair:** for each amount above, either (a) replace it with a calculator "
            "fact ID shown in the **Figures in this text** panel below, "
            "(b) replace it with a single transaction amount, "
            "or (c) remove the sentence. "
            "Your draft text is preserved — the gate blocked only the filing, not your edits."
        )
    if gos.get("fact_citations"):
        st.caption("Figures backed by the calculator of record "
                   f"(run `{gos.get('compute_run_id')}`): " +
                   "  ·  ".join(f"{amt} ← {', '.join(ids)}"
                                for amt, ids in gos["fact_citations"].items()))
    # Policy gate verdict on the current draft
    _gate = DeterministicPolicyGate()
    _verdict = _gate.check(
        st.session_state.get(f"gos_text_{selected}", gos.get("narrative", "")),
        ["tipping_off_str", "tipping_off_disclosure", "accusation_without_evidence",
         "unnecessary_pii"],
    )
    if not _verdict["passed"]:
        _blocked = [v for v in _verdict["verdicts"] if v["violated"]]
        st.error(
            "**Policy gate BLOCKED** — narrative contains prohibited content:\n" +
            "\n".join(f"- `{v['policy']}`: {v['reason']}" for v in _blocked),
            icon="🚫",
        )
    else:
        st.success("Policy gate: no prohibited language detected.", icon="✅")
    # Soft warnings — do not block, but surface for PO review
    if gos.get("out_of_range_dates"):
        st.warning(
            "**Date check:** " + ", ".join(f"`{d}`" for d in gos["out_of_range_dates"])
            + " — mentioned date(s) outside the transaction window. Verify."
        )
    if gos.get("quality_failures"):
        with st.expander(f"{len(gos['quality_failures'])} quality issue(s) to fix"):
            for item in gos["quality_failures"]:
                st.markdown(f"- {item}")


def _narrative_editor(selected, text_key) -> str:
    """The officer's Ground of Suspicion text, and the figures it contains."""
    shadow = _sticky(text_key, "")
    narrative = st.text_area(
        "Ground of Suspicion (Part c)",
        key=text_key,
        height=200,
        label_visibility="collapsed",
        placeholder="Write the Ground of Suspicion (Part c) here, or generate an AI draft.",
    )
    st.session_state[shadow] = narrative
    _claims_panel(selected, narrative)
    return narrative


def _recheck_button(selected, gos, narrative):
    if st.button("Re-check edited draft", key=f"recheck_{selected}"):
        mark = _calls_mark()
        with st.spinner(f"Re-checking narrative — {_model_label('triage')}…"):
            q = get_skills().str_quality_checker(
                narrative, st.session_state.get("case_ctx") or {},
                computed=_current_computed(selected))
        _log_calls_since(selected, "Quality re-check", mark)
        gos.update({
            "quality_score":     q["quality_score"],
            "quality_failures":  q["failures"],
            "hard_gate_passed":  q.get("hard_gate_passed", True),
            "hard_gate_failure": q.get("hard_gate_failure", ""),
            "unsupported_facts": q.get("unsupported_facts", []),
            "fact_citations":    q.get("fact_citations", {}),
            "status": "READY" if (q["quality_score"] >= 8 and q.get("hard_gate_passed", True))
                      else "NEEDS_REVISION",
            "checked_sha256":    _sha(narrative),
        })
        st.rerun()


def _decision_inputs(selected):
    """Officer ID (signed-in or self-asserted), when suspicion was formed (IST → UTC) and the
    FINGate reference."""
    now_ist = datetime.now(IST).replace(second=0, microsecond=0)
    d_key, t_key = f"susp_date_{selected}", f"susp_time_{selected}"
    po_shadow = _sticky("po_id", _session_user_id())
    d_shadow  = _sticky(d_key, now_ist.date())
    t_shadow  = _sticky(t_key, now_ist.time())

    c_po, c_date, c_time = st.columns(3)
    ident = current_identity()          # decides which ID field shows: signed-in or typed
    if ident.signed_in:
        c_po.text_input("Principal Officer ID", value=ident.officer_id or "not signed in",
                        disabled=True, key="po_id_signed_in")
        po_id = ident.officer_id
    else:
        po_id = c_po.text_input("Principal Officer ID", key="po_id")
        ident = current_identity(po_id)
    susp_date = c_date.date_input("Suspicion formed", key=d_key, max_value=now_ist.date(),
                                  help="SLA clock: 7 working days from this point.")
    susp_time = c_time.time_input("Time (IST)", key=t_key, step=300)
    st.session_state[po_shadow] = po_id
    st.session_state[d_shadow], st.session_state[t_shadow] = susp_date, susp_time
    suspicion_ts = (datetime.combine(susp_date, susp_time, tzinfo=IST)
                    .astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

    str_ref = st.text_input("FINGate STR reference, once filed (optional)",
                            placeholder="FINGATEREF-XXXX", key="str_ref_input",
                            help="This app does not file with FIU-IND. Leave blank until you have "
                                 "filed in FINGate; the decision is then recorded as pending.")
    return po_id, suspicion_ts, str_ref, ident


def _counter_evidence(selected, assessment):
    # ── T9: counter-evidence to the leading call (bounded, not autonomous) ──
    _sk  = get_skills()
    _rec = _sk.evidence_sufficiency_summary(assessment)["recommendation"]
    _proposed = "FILE" if _rec == "FILE" else "NOT_FILE"
    _chal = _sk.challenge_disposition(_proposed, assessment, _load_transactions(selected))
    if _chal["counter_evidence"] or _chal["open_gaps"]:
        _icon = {"strong": "🔴", "moderate": "🟠", "none": "🟢"}.get(_chal["challenge_strength"], "•")
        with st.expander(
            f"{_icon} Counter-evidence to the leading call "
            f"({_proposed.replace('_',' ')} · {_chal['challenge_strength']})",
            expanded=_chal["recommendation_conflict"],
        ):
            st.caption("What argues against the leading disposition. Confirm, revise, "
                       "or record why it does not change your decision.")
            for c in _chal["counter_evidence"]:
                refs = f"  _(txns: {', '.join(str(r) for r in c['refs'])})_" if c.get("refs") else ""
                st.markdown(f"- **{c['type'].replace('_',' ')}** — {c['detail']}{refs}")
            if _chal["open_gaps"]:
                st.markdown("**Open gaps:** " +
                            ", ".join(g["factor_id"] for g in _chal["open_gaps"]))


def _decision_buttons(selected, alert, narrative, ident, suspicion_ts, str_ref, assessment):
    st.markdown("#### Decision")
    _kind("Officer conclusion", "recorded locally; nothing is sent to FIU-IND")
    st.caption(ident.note)
    # Stacked, full width: readable in a narrow column and on a phone.
    action = None
    if st.button("Record decision to file", type="primary", width="stretch",
                 help="Review, then confirm. Records in the local ledger only."):
        action = "FILE"
    if st.button("Close without filing", width="stretch"):
        action = "NOT_FILE"
    if st.button("Defer — await information", width="stretch"):
        action = "DEFERRED"

    pending_key = f"pending_decision_{selected}"
    if action:
        if not ident.can_record:
            st.warning(ident.note if ident.signed_in or ident.basis != SELF_ASSERTED else
                       "Enter your Principal Officer ID before recording a decision.")
        elif len(narrative.strip()) < 20:
            st.warning("Write the Ground of Suspicion / closure rationale before recording a decision.")
        else:
            st.session_state[pending_key] = {"action": action, "text_sha256": _sha(narrative)}

    pending = st.session_state.get(pending_key)
    if pending:
        _confirm_decision(selected, alert, pending, narrative, ident, suspicion_ts,
                          str_ref, assessment or [])


def _confirm_decision(selected, alert, pending, narrative, ident, suspicion_ts, str_ref,
                      assessment):
    """D4: show exactly what will be recorded and its checks; record only on confirmation."""
    pending_key = f"pending_decision_{selected}"
    action = pending["action"]
    computed = _current_computed(selected)
    check = get_skills().validate_gos_evidence(narrative, _load_transactions(selected),
                                               (computed or {}).get("facts"))
    policy = DeterministicPolicyGate().check(
        narrative,
        ["tipping_off_str", "tipping_off_disclosure", "accusation_without_evidence",
         "unnecessary_pii"],
    )
    with st.container(border=True):
        st.markdown(f"**Confirm: record {action.replace('_', ' ')} for {selected}**")
        if pending["text_sha256"] != _sha(narrative):
            st.warning("The text changed since you pressed the button. Review the current "
                       "text below; it is what will be recorded.")
        po_id = ident.officer_id
        st.markdown(f"- Officer: `{po_id}` ("
                    + ("signed in, OpenID Connect" if ident.signed_in else "self-asserted")
                    + ")  \n"
                    f"- Suspicion formed: {suspicion_ts}  \n"
                    f"- STR reference: " + (
                        f"`{str_ref}`" if (action == "FILE" and str_ref) else
                        "pending — not yet filed in FINGate" if action == "FILE" else "n/a"))
        st.text_area("Text to be recorded (read-only)", narrative, disabled=True,
                     key=f"confirm_text_{selected}", height=120)
        n_rev = len(check.get("needs_review", []))
        n_out = len(check["coverage"]["outside_deterministic_coverage"])
        st.markdown(
            f"- Figures: **{'pass' if check['passed'] else 'FAIL — will be refused'}** "
            f"({check['fact_coverage']['amounts_checked']} checked, {n_rev} need review)  \n"
            f"- Sentences outside deterministic checks: {n_out}  \n"
            f"- Policy flags: " + (", ".join(v["policy"] for v in policy["verdicts"]
                                            if v["violated"]) or "none"))
        policy_passed = policy["passed"]
        if not policy_passed:
            st.error("This draft contains policy-blocked language. It cannot be recorded until it is revised.")
        st.caption("Confirmation records a local decision only. It does not transmit an STR, notify a customer, "
                   "or establish that an external filing has occurred.")
        ack = True
        if n_rev or n_out:
            ack = st.checkbox("I have reviewed the figures marked 'Needs review' and the "
                              "sentences no automatic check covers.", key=f"ack_{selected}")
        c1, c2 = st.columns(2)
        if c1.button("Confirm and record", type="primary", disabled=not (ack and check["passed"] and policy_passed
                                                                     and ident.can_record),
                     key=f"confirm_{selected}"):
            st.session_state.pop(pending_key, None)
            _record_disposition(
                selected, alert, narrative, action, po_id, suspicion_ts,
                (str_ref or "PENDING-FINGATEREF") if action == "FILE" else None, assessment,
                validated_draft_sha256=_sha(narrative), identity=ident)
        if c2.button("Cancel", key=f"cancel_{selected}"):
            st.session_state.pop(pending_key, None)
            st.rerun()


def _claims_panel(selected, narrative):
    """D2: every figure in the CURRENT text, what it is and where it comes from. Recomputed on
    every change, so it can never show a stale verdict."""
    if not narrative.strip():
        return
    computed = _current_computed(selected)
    check = get_skills().validate_gos_evidence(narrative, _load_transactions(selected),
                                               (computed or {}).get("facts"))
    claims = check["claims"]
    with st.expander(f"Figures in this text ({len(claims)}) · "
                     + ("all supported" if check["passed"] else "some NOT supported"),
                     expanded=not check["passed"] or bool(check.get("needs_review"))):
        if computed is None:
            st.caption("Calculator not run yet: totals cannot be verified until it is "
                       "(Compute, in the evidence column).")
        for c in claims:
            head = f"**{c['label']}** · {c['display'] or c['raw']}"
            if c["status"] == "verified_calculation":
                st.markdown(head + f" ← {', '.join(c['fact_ids'])} (run `{c['run_id'] or (computed or {}).get('run_id')}`)")
                st.caption(f"Derivation: {c['derivation']}  ·  source rows: "
                           + (", ".join(c["txn_ids"]) or "—")
                           + "  ·  This check does not verify the recipient, purpose or interpretation.")
            elif c["status"] == "source_transaction":
                st.markdown(head + f" ← transaction {', '.join(c['txn_ids'])}")
                st.caption("This check does not verify the recipient, purpose or interpretation.")
            elif c["status"] == "needs_review":
                st.markdown(head + f" ← {', '.join(c['txn_ids'])}")
                st.caption(f"Check the wording: {c['note']}")
            else:
                st.markdown(head + (f" — {c['note']}" if c["note"] else
                                    " — not a transaction amount or calculator fact"))
                if c["status"] == "unsupported":
                    st.caption("Replace with a calculator fact (run Compute in the evidence column) "
                               "or a specific transaction amount, or remove the sentence.")
        out = check["coverage"]["outside_deterministic_coverage"]
        if out:
            st.caption(f"{len(out)} sentence(s) contain no checkable figure; they need your own "
                       "review: " + " / ".join(f"“{x[:80]}”" for x in out[:4])
                       + (" …" if len(out) > 4 else ""))


def _record_disposition(alert_id, alert, rationale, disposition,
                        po_id, suspicion_ts, str_ref, poe_assessment,
                        validated_draft_sha256=None, identity=None):
    rules = json.loads(str(alert.get("RULES_CITED") or "[]"))
    rfis  = json.loads(str(alert.get("RFI_TRIGGERS") or "[]"))
    try:
        with st.spinner("Recording decision in DECISION_LEDGER…"):
            copilot = get_skills()
            result  = copilot.alert_disposition_recorder(
                alert_id           = alert_id,
                customer_ref       = alert["CUSTOMER_REF"],
                disposition        = disposition,
                rationale_text     = rationale,
                rules_cited        = rules,
                rfi_triggers       = rfis,
                poe_assessment     = poe_assessment,
                decision_maker_id  = po_id,
                suspicion_formed_at= suspicion_ts,
                str_reference      = str_ref,
                ai_recommendation  = (copilot.evidence_sufficiency_summary(poe_assessment)["recommendation"]
                                      if poe_assessment else None),
                model_name         = next((c.get("model_reported") for c in reversed(_model_calls(alert_id))), None),
                model_calls        = _model_calls(alert_id),
                compute_run_id     = (_current_computed(alert_id) or {}).get("run_id"),
                evidence_txn_ids   = sorted({t for f in poe_assessment for t in (f.get("evidence_txn_ids") or [])}),
                validated_draft_sha256 = validated_draft_sha256,
                agent_run_ref      = (st.session_state.get(f"agent_{alert_id}") or {}).get("trace_id"),
                decision_maker_basis    = identity.basis if identity else SELF_ASSERTED,
                decision_maker_identity = (identity.claims or None) if identity else None,
            )
    except ValueError as e:
        st.warning(str(e))
        return
    if result["status"] == "already_recorded":
        st.info(f"Already recorded — `{result['decision_id']}`. Nothing new was written.")
        return
    st.success(
        f"Decision recorded in the local ledger — `{result['decision_id']}`  \n"
        f"Disposition: **{disposition}**"
        + (" · no report has been sent to FIU-IND" if disposition == "FILE" else "") + "  \n"
        f"SLA days remaining: **{result['sla_days_remaining']}**  \n"
        f"Ledger row hash: `{result['row_hash'][:16]}…`"
    )
    # clear assessment state so panel is fresh for next alert
    for key in ["poe_assessment", "assessed_alert", "gos_result", "gos_alert",
                "computed", "computed_alert", f"model_calls_{alert_id}"]:
        st.session_state.pop(key, None)
    st.cache_data.clear()
