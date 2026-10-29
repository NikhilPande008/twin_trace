"""Page: Decision Ledger (hash chain, reconstruct, package verifier)."""

from __future__ import annotations

import json

import streamlit as st

from ...compute import reproduce_recorded
from ...package import build_package, check_uploaded_package
from ...palette import EVIDENCE_BADGE, EVIDENCE_UNKNOWN, SLA_OK, SLA_SOON, SLA_URGENT
from ..inspection_view import inspection_view
from ..runtime import get_store
from ..widgets import badge, disp_badge


def _reconstruct_view(row: dict, meta: dict) -> None:
    """T3.3: show compute run, model calls, and corpus rules for a ledger decision."""
    compute_run_id = meta.get("compute_run_id")
    model_calls    = meta.get("model_calls") or []
    try:
        rules_cited = json.loads(str(row.get("RULES_CITED") or "[]"))
    except Exception:
        rules_cited = []

    rc1, rc2 = st.columns(2)
    with rc1:
        st.markdown("**Compute run**")
        if compute_run_id:
            run = get_store().get_compute_run(compute_run_id)
            if run:
                st.markdown(
                    f"- Run ID: `{run['RUN_ID']}`  \n"
                    f"- Backend: `{run['BACKEND']}`"
                    + (f" (`{run['BACKEND_RUN_REF']}`)" if run.get("BACKEND_RUN_REF") else "") +
                    f"  \n- Code SHA-256: `{run['CODE_SHA256'][:20]}…`  \n"
                    f"- Input SHA-256: `{run['INPUT_SHA256'][:20]}…`  \n"
                    f"- Output SHA-256: `{run['OUTPUT_SHA256'][:20]}…`  \n"
                    f"- Finished: {str(run.get('FINISHED_AT',''))[:19]}"
                )
                repro_key = f"repro_{row['DECISION_ID']}"
                if st.button("Reproduce", key=repro_key,
                             help="Re-run the archived program version on the inputs saved with "
                                  "this run, and compare the output hash. Current data is not used."):
                    with st.spinner("Reproducing…"):
                        try:
                            result = reproduce_recorded(get_store(), compute_run_id)
                        except Exception as ex:
                            result = {"status": "unavailable", "reason": str(ex)}
                    if result["status"] == "reproduced":
                        st.success("Reproduced from the recorded input and program version: "
                                   "the output hash matches.", icon="✅")
                    elif result["status"] == "unavailable":
                        st.warning(f"Reproduction not available: {result['reason']}")
                    else:
                        st.error(f"Reproduction mismatch: {result['reason']}", icon="❌")
            else:
                st.caption(f"Run `{compute_run_id}` not found in COMPUTE_RUNS.")
        else:
            st.caption("No compute run recorded for this decision.")

    try:
        _pkg = build_package(get_store(), row["DECISION_ID"])
        st.download_button(
            "Download decision package (JSON)", json.dumps(_pkg, indent=2, default=str),
            file_name=f"decision-package-{row['DECISION_ID'][:8]}.json", mime="application/json",
            key=f"pkg_{row['DECISION_ID']}",
            help="Recorded decision, calculator input and program, claim map and manifest. "
                 "Verify offline: python3 -m scripts.verify_package <file>")
    except Exception as ex:  # noqa: BLE001
        st.caption(f"Package not available: {ex}")

    with rc2:
        st.markdown("**Model calls**")
        if model_calls:
            for call in model_calls:
                usage = call.get("usage") or {}
                tier  = call.get("tier", "?")
                model = call.get("model_reported") or call.get("model_requested", "?")
                pt    = usage.get("prompt_tokens", "?")
                ct    = usage.get("completion_tokens", "?")
                lat   = call.get("latency_s")
                st.markdown(
                    f"- **{tier}** — `{model}`  \n"
                    f"  {pt}p + {ct}c tokens"
                    + (f" · {lat:.2f}s" if lat else "")
                )
        else:
            st.caption("No model calls recorded for this decision.")

    if rules_cited:
        st.markdown("**Corpus rules cited**")
        rule_rows = get_store().corpus_by_ids(rules_cited)
        if rule_rows:
            for rr in rule_rows:
                ev = rr["EVIDENCE_LEVEL"]
                icon, bg, fg = EVIDENCE_BADGE.get(ev, EVIDENCE_UNKNOWN)
                st.markdown(
                    f"{icon} **{rr['RULE_ID']}** — {rr['SUBCATEGORY']}  \n"
                    f"{rr['RULE_PREVIEW']}…  {badge(ev, bg, fg)}",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Rule IDs cited: " + ", ".join(f"`{r}`" for r in rules_cited))


# ── page: Decision Ledger ─────────────────────────────────────────────────────
def _package_verifier():
    """Re-check an exported decision package from one file, as a reviewer would. Programs are
    never executed unless this deployment already trusts their hash."""
    with st.expander("Verify a decision package (re-check a decision from one file)"):
        st.caption(
            "Upload a package exported from a decision's *Reconstruct decision* panel. The check "
            "needs no database and no API key: it recomputes the hashes, re-runs the recorded "
            "calculator on the recorded inputs, and confirms the ledger row hashes to its "
            "recorded value. It does not prove the ledger itself was not rewritten before export "
            "(tamper-evident, not tamper-proof), and it never runs a program it does not trust.")
        up = st.file_uploader("Decision package (.json)", type=["json"], key="pkg_upload")
        if up is None:
            return
        out = check_uploaded_package(up.getvalue(), get_store())
        if out["status"] == "invalid":
            st.error(out["message"])
            return
        (st.success if out["status"] == "verified" else st.error)(out["message"])
        for c in out["result"]["checks"]:
            st.markdown(("✅ " if c["ok"] else "❌ ") + f"`{c['name']}` — {c['detail']}")


def page_ledger():
    st.header("Decision Ledger")
    st.markdown(
        "Append-only audit trail",
        help="DECISION_LEDGER is append-only: no row may be updated or deleted. "
             "It is the primary defensibility record for FIU-IND inspections.",
    )

    _package_verifier()

    rows = get_store().ledger_joined()

    chain = get_store().verify_ledger_chain()
    if chain["ok"]:
        st.success(f"Hash chain verified — {chain['rows']} row(s), no edits or removals detected.",
                   icon="🔗")
    else:
        st.error(f"Hash chain BROKEN at row {chain['first_break_seq']}: {chain['detail']}")

    if not rows:
        st.info("No disposition decisions recorded yet. Use the Disposition Panel to file or close an alert.")
        return

    total    = len(rows)
    filed    = sum(1 for r in rows if r["DISPOSITION"] == "FILE")
    no_file  = sum(1 for r in rows if r["DISPOSITION"] == "NOT_FILE")
    overdue  = sum(1 for r in rows if (r["SLA_DAYS_REMAINING"] or 99) < 0)
    ratio    = round(filed * 100 / (filed + no_file), 1) if (filed + no_file) > 0 else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Decisions", total)
    c2.metric("FILE", filed)
    c3.metric("NOT_FILE", no_file)
    c4.metric("Alert-to-STR Ratio", f"{ratio}%",
              help="FIU-IND inspectors focus on this metric.")
    c5.metric("Overdue (SLA < 0)", overdue,
              delta=f"-{overdue}" if overdue else None,
              delta_color="inverse")

    st.divider()

    for r in rows:
        sla = r["SLA_DAYS_REMAINING"]
        sla_c = (SLA_URGENT if (sla is not None and sla < 0) else
                 SLA_SOON if (sla is not None and sla <= 2) else SLA_OK)[1]

        with st.expander(
            f"{r['ALERT_ID']} [{r['DISPOSITION']}] · {r['DECISION_MAKER_ID']} · "
            + f"{str(r['DECISION_MADE_AT'])[:16]}",
            expanded=False,
        ):
            st.markdown(disp_badge(r["DISPOSITION"]), unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Decision ID:** `{r['DECISION_ID']}`")
                st.markdown(f"**Customer:** `{r['CUSTOMER_REF']}`")
                _ref = r.get("STR_REFERENCE")
                st.markdown("**STR reference:** " + (
                    "pending — not yet filed in FINGate" if not _ref or str(_ref).startswith("PENDING")
                    else f"`{_ref}`"))
            with col2:
                st.markdown(f"**Suspicion formed:** {str(r.get('SUSPICION_FORMED_AT') or '—')[:19]}")
                st.markdown(f"**Decision made:** {str(r.get('DECISION_MADE_AT') or '—')[:19]}")
                st.markdown(
                    f"**SLA days remaining at decision:** "
                    f'<span style="color:{sla_c};font-weight:700">{sla}</span>',
                    unsafe_allow_html=True,
                )
            with col3:
                st.markdown(f"**Alert type:** {r.get('ALERT_TYPE') or '—'}")
                amt = r.get("ALERT_AMOUNT_INR")
                if amt:
                    st.markdown(f"**Amount:** ₹{float(amt):,.0f}")
                st.markdown(f"**Customer profile:** {str(r.get('CUSTOMER_PROFILE') or '—')[:100]}")

            st.markdown("**Rationale text (as recorded):**")
            st.text(r.get("RATIONALE_TEXT") or "—")

            # Decision provenance (WS-4 metadata)
            meta = r.get("METADATA_JSON")
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    pass
            if isinstance(meta, dict) and any(meta.values()):
                st.markdown("**Decision provenance:**")
                for k, v in meta.items():
                    if v:
                        st.markdown(f"- **{k}:** {v}")

            # T3.3 Reconstruct decision
            with st.expander("↩ Reconstruct decision", expanded=False):
                _reconstruct_view(r, meta or {})
            # T12.9 Inspection replay
            with st.expander("Inspection replay", expanded=False):
                inspection_view(r["DECISION_ID"])
