"""Disposition Panel evidence: signal brief, calculator of record, stress test, typology
search, run trace."""

from __future__ import annotations

import json

import streamlit as st

from ..bootstrap import build_stress_tester, compute_params
from ..config import get_settings
from ..money import format_inr
from ..palette import MUTED_TEXT, VERDICT_COLORS
from ..pipeline import RunTrace
from ..stress.headline import headline as stress_headline
from .case_state import _calls_mark, _current_computed, _ensure_computed, _log_calls_since
from .runtime import (_llm_ready, _load_transactions, get_pipeline, get_runner, get_skills,
                      get_store)
from .widgets import _kind, badge


def _signal_brief(selected, alert):
    """T3: deterministic Signal Brief — observed transaction facts (no LLM)."""
    txns = _load_transactions(selected)
    if not txns:
        return
    # Totals come from the calculator of record, never from UI arithmetic (CLAUDE.md §5).
    facts = {f["fact_id"]: f["value"] for f in _ensure_computed(selected)["facts"]}
    total_credit = facts.get("F-TOTAL-CREDIT", 0)
    total_debit  = facts.get("F-TOTAL-DEBIT", 0)
    counterparties = sorted({t["counterparty"] for t in txns if t.get("counterparty")})
    flagged = sorted({t["counterparty"] for t in txns if t.get("is_flagged")})
    dates = sorted(t["date"] for t in txns if t.get("date"))
    try:
        rfi = json.loads(str(alert.get("RFI_TRIGGERS") or "[]"))
    except Exception:
        rfi = []

    st.markdown(f"**Signal Brief — {alert['ALERT_ID']} · {alert['ALERT_TYPE'].replace('_', ' ').title()}**")
    _kind("Source facts", "transaction rows; totals from the calculator of record")
    st.caption(f"Source: {alert.get('SIGNAL_SOURCE', '—')}  ·  Why triggered: {', '.join(rfi) or '—'}")
    # exact calculator figures, never a rounded lakh value; a 2x2 grid and a smaller value font
    # (CSS on st-key-signal_brief_tiles) so ₹2,32,47,000 is not clipped in the proof column
    with st.container(key="signal_brief_tiles"):
        b1, b2 = st.columns(2)
        b1.metric("Credits", format_inr(total_credit), help="F-TOTAL-CREDIT, calculator of record")
        b2.metric("Debits", format_inr(total_debit), help="F-TOTAL-DEBIT, calculator of record")
        b3, b4 = st.columns(2)
        b3.metric("Transactions", len(txns))
        b4.metric("Flagged", len(flagged))
    if dates:
        st.caption(f"Observed window {dates[0]} → {dates[-1]}  ·  {len(counterparties)} counterparties")
    if flagged:
        st.caption("⚠ Flagged counterparties: " + ", ".join(flagged))
    st.caption("_Credits/Debits are F-TOTAL-CREDIT / F-TOTAL-DEBIT from the calculator of record; "
               "counts and dates are read from the transaction rows. No model involved._")
    st.divider()


def _calculator_panel(selected):
    """Calculator of record: deterministic figures with code/input/output hashes."""
    computed = _current_computed(selected)
    head_l, head_r = st.columns([3, 1])
    head_l.markdown("**Calculator of record**")
    _kind("Source facts", "fixed, hashed program over the transaction rows")
    if head_r.button("Compute" if computed is None else "↻ Recompute",
                     key=f"compute_{selected}", width="stretch"):
        st.session_state.pop("computed", None)
        st.session_state.pop("computed_alert", None)
        computed = _ensure_computed(selected)
    if computed is None:
        st.caption("Runs a fixed, hashed program over this alert's transactions. Every ₹ "
                   "aggregate in the Ground of Suspicion must come from here or from a single "
                   "transaction.")
        st.divider()
        return
    prov = computed["provenance"]
    inr = [f for f in computed["facts"] if f["unit"] == "INR"]
    other = [f for f in computed["facts"] if f["unit"] != "INR"]
    for f in inr:
        st.markdown(f"`{f['fact_id']}` {f['label']}: **₹{f['value']:,}**  \n"
                    f"<span style='font-size:0.8em;color:{MUTED_TEXT}'>{f['derivation']} · "
                    f"txns {', '.join(f['txn_ids']) or '—'}</span>", unsafe_allow_html=True)
    if other:
        with st.expander(f"{len(other)} further computed fact(s)"):
            for f in other:
                st.markdown(f"`{f['fact_id']}` {f['label']}: **{f['value']}** {f['unit']}")
    for w in computed.get("warnings", []):
        st.caption(f"⚠ {w}")
    st.caption(
        f"Run `{prov['RUN_ID']}` · backend **{prov['BACKEND']}**"
        + (f" (`{prov['BACKEND_RUN_REF']}`)" if prov.get("BACKEND_RUN_REF") else "")
        + f" · code `{prov['CODE_SHA256'][:12]}…` · input `{prov['INPUT_SHA256'][:12]}…` "
        + f"· output `{prov['OUTPUT_SHA256'][:12]}…`")
    st.divider()


def _adverse_media_panel(selected: str, alert: dict) -> None:
    """Adverse-media evidence: show items fetched from Tavily, or prompt to fetch (T2.2)."""
    store = get_store()
    items = store.evidence_for_alert(selected, ev_type="adverse_media")
    tavily_ready = bool(get_settings().tavily_api_key)

    _kind("Unverified external", "web results, not about this customer")
    label = f"🔍 Typology context — web topic search ({len(items)} item(s))"
    with st.expander(label, expanded=(len(items) > 0)):
        if not tavily_ready:
            st.caption(
                "Adverse-media screening is disabled. "
                "Add `TAVILY_API_KEY` to `.env` to enable Tavily Search."
            )
            return

        st.caption("Searches the alert's **typology**, not this customer: no name, account or "
                   "transaction leaves the bank. Results are background reading, not evidence "
                   "about the customer, and zero results do not clear anyone.")
        if st.button("Search typology context", key=f"fetch_am_{selected}",
                     help="Tavily topic search built from the alert type only."):
            with st.spinner("Searching…"):
                _trace = RunTrace(alert_id=selected)
                get_pipeline().step_adverse_media(
                    "", {"alert_type": alert["ALERT_TYPE"]}, _trace, alert_id=selected)
            st.rerun()

        items = store.evidence_for_alert(selected, ev_type="adverse_media")
        screens = store.evidence_for_alert(selected, ev_type="adverse_media_screen")
        if screens:
            try:
                last = json.loads(screens[-1]["CONTENT_JSON"])
            except Exception:
                last = {}
            when = str(last.get("checked_at", ""))[:19]
            if not last.get("completed"):
                st.error(f"Last screen did not run ({last.get('status', 'unknown')}, {when}). "
                         "This is not a clear result — retry before relying on it. "
                         f"{last.get('detail', '')}")
            elif last.get("status") == "no_results":
                st.info(f"Last screen ran at {when} and returned no results.")
        if not items:
            if not screens:
                st.caption("Not screened yet for this alert.")
            return

        try:
            _q = json.loads(items[-1]["CONTENT_JSON"]).get("query_used", "")
        except Exception:
            _q = ""
        st.caption(
            f"{len(items)} item(s) · provider Tavily · query `{_q}` · not matched to this "
            "customer. Untrusted external content — verify before relying on it."
        )
        for row in items:
            try:
                content = json.loads(row["CONTENT_JSON"])
            except Exception:
                content = {}
            title   = content.get("title") or "—"
            url     = content.get("url") or ""
            snippet = content.get("snippet") or ""
            score   = float(content.get("score") or 0)
            with st.container():
                st.markdown(
                    f"**{title}**  \n"
                    f"[{url[:70]}]({url})  ·  relevance {score:.2f}",
                    unsafe_allow_html=False,
                )
                if snippet:
                    st.caption(f"> {snippet[:250]}" + ("…" if len(snippet) > 250 else ""))
                st.caption(
                    f"`{row['EVIDENCE_ID'][:16]}…` · "
                    f"content hash `{row['CONTENT_HASH'][:12]}…` · "
                    f"retrieved {str(row.get('CREATED_AT',''))[:19]}"
                )
                st.caption("_Topic result — not about this customer · untrusted external content_")
            st.divider()


# What evidence would confirm each counter-hypothesis (D3). Wording only; no data source.
EVIDENCE_TO_VERIFY = {
    "EXPLAIN": lambda t: f"documents explaining transaction {t} (e.g. invoice, agreement, RFI reply)",
    "UNFLAG":  lambda t: f"written confirmation from the registry that the flag on '{t}' was wrong",
    "FLAG":    lambda t: f"a registry or law-enforcement report naming '{t}'",
}


def _stress_panel(selected):
    """Decision Stress Test: counterfactual branch runs of the calculator (works offline)."""
    st.markdown("**Decision sensitivity (stress test)**")
    _kind("Product heuristic", "signal rules are this product's, not FIU-IND criteria")
    st.caption("What does this decision rest on, and what would change it? The calculator is "
               "re-run on every counter-hypothesis; each branch is a hashed run of its own.")
    c1, c2 = st.columns([2, 1])
    disp = c1.radio("Proposed disposition", ["FILE", "NOT_FILE"], horizontal=True,
                    key=f"stress_disp_{selected}")
    key = f"stress_{selected}_{disp}"
    if c2.button("Run stress test", key=f"stress_btn_{selected}", width="stretch",
                 help="Re-runs every branch; with a Token Factory key, also writes a memo "
                      "(Nemotron, triage tier) that is rejected if it adds any number."):
        mark = _calls_mark()
        with st.status("Running counterfactual branches…", expanded=True) as status:
            tester = build_stress_tester(get_store(), get_skills(), get_runner())
            st.session_state[key] = tester.run(
                selected, _load_transactions(selected), compute_params(get_store(), selected),
                disposition=disp, with_memo=_llm_ready(), on_progress=status.write)
            status.update(label="Stress test complete", state="complete", expanded=False)
        _log_calls_since(selected, "Stress-test memo", mark)
        st.rerun()
    r = st.session_state.get(key)
    if not r:
        st.divider()
        return
    bg, fg = VERDICT_COLORS[r["base"]["verdict"]]
    rob = r["robustness"]
    m1, m2, m3 = st.columns(3)
    m1.markdown("Modeled signal level " + badge(r["base"]["verdict"], bg, fg),
                unsafe_allow_html=True)
    m2.metric("Challenges survived",
              f"{rob['survived']} / {rob['single_hypotheses']}" if rob.get("meaningful", True)
              else "n/a",
              help="How many of the single counter-hypotheses leave the modeled level unchanged.")
    m3.metric("Branch runs", f"{r['search']['runs_used']} / {r['search']['budget']}")
    hl = stress_headline(r)
    {"warning": st.warning, "success": st.success, "info": st.info}[hl["tone"]](
        f"**{hl['title']}** {hl['detail']}")
    st.caption("A level computed by this product's rules from calculator facts. HIGH is not a "
               "finding of suspicion, and LOW is not evidence of innocence.")
    for s in r["base"]["signals"]:
        icon = ("🔴" if s["strength"] == "strong" else "🟠") if s["fired"] else "⚪"
        st.markdown(f"{icon} {s['label']} <span style='font-size:0.8em;color:{MUTED_TEXT}'>"
                    f"({s['strength']}; {s['explanation']}; "
                    f"{', '.join(f'{k}={v}' for k, v in s['facts_used'].items())})</span>",
                    unsafe_allow_html=True)
    level_of = {tuple(sorted(b["hypotheses"])): b["verdict"] for b in r["branches"]}
    if r["mode"] == "weaken":
        st.markdown("**What would lower the modeled level** — each row is an assumption, the "
                    "level it leads to, and the evidence that would confirm it:")
        if not r["minimal_flip_sets"]:
            st.success(f"No combination of up to {r['search']['max_set_size']} of the tested "
                       "assumptions lowers the modeled level.")
        for f in r["minimal_flip_sets"]:
            new = level_of.get(tuple(sorted(h["id"] for h in f)), "lower")
            st.markdown("- " + "  **and**  ".join(h["label"] for h in f)
                        + f"  → modeled level **{r['base']['verdict']} → {new}**  \n"
                        + "  _To verify:_ " + "; ".join(EVIDENCE_TO_VERIFY[h["kind"]](h["target"])
                                                        for h in f))
    else:
        st.markdown("**Suggested reopen conditions** (advisory: nothing monitors these "
                    "automatically; set a review if you rely on them):")
        if not r["reopen_triggers"]:
            st.success("No single registry hit on an existing counterparty raises the modeled "
                       "level to HIGH.")
        for t in r["reopen_triggers"]:
            st.markdown("- " + "  **and**  ".join(t["if"])
                        + f"  → modeled level `{t['verdict_change']}`")
    if r["search"].get("budget_exhausted"):
        st.warning(f"Search stopped at the run budget ({r['search']['budget']} runs): smaller "
                   "sets were checked first, but larger combinations were not all tried.")
    with st.expander("What this analysis does not cover"):
        st.markdown(
            "- Only the assumptions listed: explaining a transaction, a registry flag being "
            "wrong, or a counterparty becoming flagged.  \n"
            "- Not the narrative, KYC documents, PEP status, RFI answers, or anything the "
            "calculator does not compute.  \n"
            f"- Sets are minimal **within** the tested assumptions and the run budget.")
    for n in r["notes"]:
        st.warning(n)
    memo = r.get("memo")
    if memo and memo.get("status") == "ok":
        st.info(f"**Nemotron memo** (numbers checked against the calculator): {memo['summary']}")
    elif memo:
        st.caption(f"Memo {memo['status']}: {memo.get('reason', '')} — deterministic summary used.")
    with st.expander(f"All {len(r['branches'])} branches"):
        st.dataframe([{"hypotheses": " + ".join(b["hypotheses"]), "verdict": b["verdict"],
                       "flips": b["flips"], "run_id": b["run_id"]} for b in r["branches"]],
                     width="stretch", hide_index=True)
    st.caption(f"Base run `{r['base']['run_id']}` · evidence `{r.get('evidence_id', '—')}` · "
               "signal thresholds are product heuristics, not regulatory thresholds.")
    st.divider()


def _trace_panel(selected):
    """What the pipeline ran for this alert in this session: step, outcome, time, model, tokens."""
    trace = st.session_state.get(f"run_trace_{selected}")
    if not trace or not trace.steps:
        return
    st.divider()
    with st.expander(f"Pipeline run trace · {len(trace.steps)} steps · {trace.total_latency_s} s"):
        st.caption("Every pipeline step run for this alert in this session. The trace itself is "
                   "not stored; the compute runs and evidence rows it refers to are.")
        rows = []
        for s in trace.steps:
            mc = s.model_call or {}
            usage = mc.get("usage") or {}
            tokens = (usage.get("prompt_tokens") or 0) + (usage.get("completion_tokens") or 0)
            rows.append({"step": s.name, "status": s.status, "seconds": s.latency_s,
                         "model": mc.get("model_reported") or mc.get("model_requested") or "—",
                         "tokens": tokens or "—", "note": s.blocked_reason or ""})
        st.dataframe(rows, hide_index=True, width="stretch")
        st.caption(f"Total tokens this trace: {trace.total_prompt_tokens} prompt + "
                   f"{trace.total_completion_tokens} completion.")
