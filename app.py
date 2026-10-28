"""
Twin Trace
Principal Officer workflow UI (Streamlit, runs locally or on any container host).

Data from ddp.store (SQLite); models from Nebius Token Factory (ddp.llm);
figures from the calculator of record (ddp.compute).

Pages (sidebar):
  Alert Queue · Twin Cases (ALERT-01 vs ALERT-16) · Proof Check · Disposition Panel (verdict card
  first, proof behind a toggle, GoS drafting) · Decision Ledger · Dashboard · Measured Results ·
  Regulatory Reference
"""

import hashlib
import html
import json
import sys
from pathlib import Path
from datetime import date, datetime, timedelta, timezone

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from ddp.bootstrap import (build, build_investigator, build_stress_tester, compute_params,  # noqa: E402
                           open_store)
from ddp.config import get_settings  # noqa: E402
from ddp.compute import reproduce_recorded  # noqa: E402
from ddp.package import build_package, check_uploaded_package  # noqa: E402
from ddp.gate import DeterministicPolicyGate  # noqa: E402
from ddp.evidence_view import (latest_live_holdout, live_eval_reports,  # noqa: E402
                               summarise_live)
from ddp.glossary import GLOSSARY  # noqa: E402
from ddp.palette import (ACCENT, CARD_BG, CARD_BORDER, DISP_STYLE,  # noqa: E402
                         EVIDENCE_BADGE, EVIDENCE_UNKNOWN, FOCUS, FORK_ROW_BG, KIND_STYLE,
                         MUTED_TEXT, NEUTRAL, READING_STYLE, RECOMMENDATION_COLORS,
                         SCORE_BAD, SCORE_GOOD, SCORE_MID, SLA_OK, SLA_SOON, SLA_URGENT,
                         VERDICT_COLORS, css_variables, var)
from ddp import verdict as V  # noqa: E402
from ddp.stakes import STAKES, USER  # noqa: E402
from ddp import platform_trace as PT  # noqa: E402
from ddp.money import format_inr  # noqa: E402
from ddp.llm import LLMNotConfigured  # noqa: E402
from ddp.pipeline import RunTrace  # noqa: E402
from ddp.proofcheck import (FORMS, INVENTED_EXTRA, attempt_recording,  # noqa: E402
                            build_drafts, total_credit)
from ddp.stress.headline import headline as stress_headline  # noqa: E402


# ── wiring ────────────────────────────────────────────────────────────────────
@st.cache_resource
def _shared_runtime():
    return build(get_settings())


def _runtime():
    """One shared database normally (decisions persist across restarts). In public demo mode
    every browser session gets its own seeded in-memory database: visitors cannot see or
    overwrite each other's work, and nothing persists past the session."""
    settings = get_settings()
    if settings.demo_mode:
        if "_session_runtime" not in st.session_state:
            st.session_state["_session_runtime"] = build(settings, store=open_store(":memory:"))
        return st.session_state["_session_runtime"]
    return _shared_runtime()


def get_store():
    return _runtime()[0]


def get_skills():
    return _runtime()[1]


def get_runner():
    return _runtime()[2]


def get_pipeline():
    return _runtime()[3]


def _load_transactions(alert_id: str) -> list[dict]:
    """Governed transaction ledger for an alert, in the dict shape the skills expect."""
    return get_store().transactions_for(alert_id)


def _llm_ready() -> bool:
    return get_settings().llm_configured


# What kind of statement a section holds (D1). Text labels, not colour alone.
# Colours live in ddp/palette.py, where tests hold them to WCAG AA contrast.


def _kind(label: str, note: str = "") -> None:
    bg, fg = KIND_STYLE[label]
    st.markdown(badge(label, bg, fg) + (f"&nbsp; <small>{note}</small>" if note else ""),
                unsafe_allow_html=True)


def _sha(text: str) -> str:
    return hashlib.sha256((text or "").encode()).hexdigest()


def _service_status(kind: str) -> str:
    """'Configured · last call succeeded 12:03 UTC' / '… failed (rate_limited)' / 'Unavailable'."""
    cfg = get_settings()
    if kind == "model":
        if not cfg.llm_configured:
            return "Unavailable (no NEBIUS_API_KEY)"
        log = getattr(get_skills(), "call_log", [])
        if not log:
            return "Configured · no call yet this session"
        last = log[-1]
        when = st.session_state.get("_last_model_check", "")
        if last.get("failed"):
            return f"Configured · last call failed ({last.get('error_kind', 'error')})"
        return "Configured · last call succeeded" + (f" {when}" if when else "")
    if not cfg.tavily_api_key:
        return "Unavailable (no TAVILY_API_KEY)"
    return "Configured · " + st.session_state.get("_last_tavily", "no search yet this session")

# ── constants ─────────────────────────────────────────────────────────────────
def badge(text: str, bg: str, fg: str) -> str:
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 8px;'
        f'border-radius:4px;font-size:0.78em;font-weight:600">{text}</span>'
    )

def disp_badge(disposition: str) -> str:
    return badge(disposition, *DISP_STYLE.get(disposition, NEUTRAL))

# ── SLA helpers ───────────────────────────────────────────────────────────────
SLA_WORKING_DAYS = 7
IST = timezone(timedelta(hours=5, minutes=30))

def _to_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])

def sla_days_left(alert_date) -> int:
    """Working days (Mon–Fri, no holiday calendar) left in the 7-WD window,
    counted from the alert date. Negative = overdue."""
    start = _to_date(alert_date)
    today = datetime.now(IST).date()
    elapsed, d = 0, start
    while d < today:
        d += timedelta(days=1)
        if d.weekday() < 5:
            elapsed += 1
    return SLA_WORKING_DAYS - elapsed

def sla_style(days: int) -> tuple[str, str]:
    if days <= 1:
        return SLA_URGENT
    if days <= 4:
        return SLA_SOON
    return SLA_OK

def sla_pill(days: int) -> str:
    if days < 0:
        label = f"{-days} WD overdue"
    elif days == 0:
        label = "Due today"
    else:
        label = f"{days} WD left"
    return badge(label, *sla_style(days))

def _session_user_id() -> str:
    """Session user identity from Streamlit runtime context; empty string locally."""
    for attr in ("user", "experimental_user"):
        try:
            u = getattr(st, attr, None)
            name = (u.get("user_name") or u.get("login_name") or u.get("email")) if u else None
            if name:
                return str(name)
        except Exception:
            continue
    return ""

def _sticky(key: str, default):
    """Streamlit drops an unrendered widget's state on page switch; restore it
    from a shadow key. Call before the widget; write the value back after."""
    shadow = f"_keep_{key}"
    if key not in st.session_state:
        st.session_state[key] = st.session_state.get(shadow, default)
    return shadow

def _set_sticky(key: str, value):
    st.session_state[key] = value
    st.session_state[f"_keep_{key}"] = value

def _style():
    st.markdown(f"""<style>
.stApp{{{css_variables()}}}
.ddp-workbench-nav{{display:flex;flex-wrap:wrap;gap:6px;margin:4px 0 14px}}
.ddp-workbench-nav span{{border:1px solid {CARD_BORDER};border-radius:3px;padding:4px 8px;
  color:{MUTED_TEXT};font-size:.78rem;font-weight:600}}
.ddp-workbench-nav span:first-child{{background:{var('brand_bg')};color:{ACCENT};border-color:{ACCENT}}}
.ddp-card{{background:{CARD_BG};border:1px solid {CARD_BORDER};border-top:3px solid {ACCENT};
  border-radius:10px;padding:18px 20px 14px;margin:6px 0 18px}}
.ddp-kicker{{color:{ACCENT};font-size:.72rem;font-weight:700;letter-spacing:.09em;
  text-transform:uppercase;margin:0 0 6px}}
.ddp-row{{display:flex;flex-wrap:wrap;gap:16px}}
.ddp-half{{flex:1 1 280px;min-width:0}}
.ddp-title{{font-size:1.12rem;font-weight:650;line-height:1.35;margin:2px 0 8px}}
.ddp-chip{{display:inline-block;padding:3px 10px;margin:0 6px 6px 0;border-radius:12px;
  font-size:.82rem;font-weight:600}}
.ddp-note{{color:{MUTED_TEXT};font-size:.8rem;margin:4px 0 0}}
.ddp-foot{{color:{MUTED_TEXT};font-size:.78rem;border-top:1px solid {CARD_BORDER};
  margin-top:12px;padding-top:8px}}
.ddp-table{{width:100%;border-collapse:collapse;font-size:.92rem}}
.ddp-table td,.ddp-table th{{padding:7px 10px;border-bottom:1px solid {CARD_BORDER};text-align:left}}
.ddp-table th{{color:{MUTED_TEXT};font-weight:600;font-size:.78rem;text-transform:uppercase;
  letter-spacing:.06em}}
.ddp-fork td{{background:{FORK_ROW_BG}}}
.ddp-fork td:first-child{{border-left:3px solid {ACCENT}}}
.ddp-queue-row{{border:1px solid {CARD_BORDER};border-left:4px solid {ACCENT};border-radius:4px;
  padding:12px 14px;margin:8px 0;background:{CARD_BG}}}
.ddp-queue-meta{{display:flex;flex-wrap:wrap;gap:8px 16px;color:{MUTED_TEXT};font-size:.82rem;margin-top:5px}}
.ddp-provenance{{border-left:3px solid {ACCENT};padding:8px 12px;margin:8px 0;background:{var('brand_bg')};
  font-size:.84rem}}
:focus-visible{{outline:2px solid {FOCUS} !important;outline-offset:2px}}
@media (max-width: 760px){{
  .ddp-card{{padding:14px 14px 12px}}
  .ddp-workbench-nav span{{flex:1 1 42%;text-align:center}}
  .ddp-queue-row{{padding:11px 12px}}
}}
</style>""", unsafe_allow_html=True)


def _esc(text) -> str:
    return html.escape(str(text))


def _chips(items: list[str], style: tuple[str, str]) -> str:
    bg, fg = style
    return "".join(f'<span class="ddp-chip" style="background:{bg};color:{fg}">{_esc(i)}</span>'
                   for i in items)


def _workbench_steps() -> None:
    """Task landmarks, not a mandatory wizard. They preserve the PO's investigation order."""
    st.markdown(
        '<nav class="ddp-workbench-nav" aria-label="Case review landmarks">'
        '<span>1 · Understand alert</span><span>2 · Inspect evidence</span>'
        '<span>3 · Write &amp; check</span><span>4 · Review &amp; save</span></nav>',
        unsafe_allow_html=True,
    )


def _provenance_status(selected: str) -> None:
    """Make the source and trust boundary legible before any model interpretation."""
    computed = _current_computed(selected)
    if computed is None:
        return
    p = computed["provenance"]
    st.markdown(
        '<div class="ddp-provenance"><strong>Evidence status · deterministic calculation available</strong>'
        f'<br>Transaction rows were processed locally by run <code>{_esc(p["RUN_ID"])}</code>. '
        'Amounts can be checked against this run; that does not establish a recipient, purpose, '
        'or the truth of the source records. Model advice, if requested, remains advisory.</div>',
        unsafe_allow_html=True,
    )


def _reading_html(r: dict, kicker: str) -> str:
    style = READING_STYLE[r["disposition"]]
    chips = (f'<div class="ddp-note">{_esc(r["chip_label"])}</div>' + _chips(r["chips"], style)
             + (f'<span class="ddp-note">+{r["more"]} more in the proof</span>' if r["more"] else "")
             if r["chips"] else f'<div class="ddp-note">{_esc(r["detail"])}</div>')
    notes = "".join(f'<div class="ddp-note">{_esc(n)}</div>' for n in r["notes"]
                    if r["chips"])
    return (f'<div class="ddp-half"><div class="ddp-kicker">{_esc(kicker)}</div>'
            f'<div class="ddp-title">{_esc(r["title"])}</div>{chips}{notes}</div>')


def _readings(alert_id: str) -> dict:
    """Both deterministic stress-test readings for an alert, once per session (no model call).
    They also seed the stress-test panel inside the proof, so either choice there is ready."""
    key = f"readings_{alert_id}"
    if key not in st.session_state:
        tester = build_stress_tester(get_store(), get_skills(), get_runner())
        reps = V.readings(tester, get_store(), alert_id, compute_params(get_store(), alert_id))
        st.session_state[key] = reps
        for d, r in reps.items():
            st.session_state.setdefault(f"stress_{alert_id}_{d}", r)
    return st.session_state[key]


def _verdict_card(selected: str) -> None:
    c = V.card(_readings(selected))
    bg, fg = VERDICT_COLORS[c["level"]]
    st.markdown(
        f'<div class="ddp-card"><div class="ddp-kicker">What the decision rests on</div>'
        f'<div class="ddp-note" style="margin:0 0 12px">Modeled signal level '
        f'{badge(c["level"], bg, fg)} &nbsp;·&nbsp; you choose the disposition; both readings '
        f'are shown</div><div class="ddp-row">'
        + _reading_html(c["file"], "If you file")
        + _reading_html(c["close"], "If you close")
        + f'</div><div class="ddp-foot">Deterministic: {c["runs"]} runs of the calculator of record, '
          f'no model. Signal rules are this product\'s heuristics, not FIU-IND criteria. '
          f'HIGH is not a finding of suspicion; LOW is not evidence of innocence.</div></div>',
        unsafe_allow_html=True)


def _platform_calls(selected: str) -> list[dict]:
    return st.session_state.setdefault(f"platform_{selected}", [])


def _calls_mark() -> int:
    return len(get_skills().call_log)


def _log_calls_since(selected: str, step: str, mark: int) -> None:
    _platform_calls(selected).extend(PT.call_rows(step, get_skills().call_log[mark:]))


def _model_label(tier: str) -> str:
    return f"{PT.short_model(get_settings().models.get(tier, ''))} ({tier} tier)"


def _platform_strip(selected: str) -> None:
    """Which Nemotron tier answered which step for this alert, and where the calculator ran."""
    rows = _platform_calls(selected)
    tiers = PT.by_tier(rows, get_settings().models)
    comp = PT.compute_line(_ensure_computed(selected)["provenance"])
    pills = ""
    for t in tiers:
        used = (f"{t['calls']} call(s) · {t['tokens']:,} tokens · {t['seconds']} s"
                + (f" · {t['failed']} failed" if t["failed"] else "")) if t["calls"] else "not called yet"
        color = ACCENT if t["calls"] else MUTED_TEXT
        pills += (f'<div class="ddp-half" style="flex-basis:200px"><div class="ddp-note">'
                  f'{_esc(t["tier"])}</div><div style="font-weight:600;color:{color}">'
                  f'{_esc(PT.short_model(t["model"]))}</div><div class="ddp-note">{_esc(used)}</div>'
                  f'</div>')
    key_note = ("" if _llm_ready() else
                '<div class="ddp-note">Token Factory not configured (no NEBIUS_API_KEY): the '
                'deterministic steps above ran without a model.</div>')
    st.markdown(
        f'<div class="ddp-card" style="padding:12px 18px 10px">'
        f'<div class="ddp-kicker">Platform trace · Nebius Token Factory · NVIDIA Nemotron</div>'
        f'<div class="ddp-row">{pills}</div>{key_note}'
        f'<div class="ddp-foot">Calculator: {_esc(comp["label"])} · run <code>{_esc(comp["run_id"])}'
        f'</code> · code <code>{_esc(comp["code_sha256"][:12])}…</code>'
        + (f'<br>{_esc(comp["note"])}' if comp["note"] else "") + '</div></div>',
        unsafe_allow_html=True)
    if rows:
        with st.expander(f"Model calls for {selected} this session ({len(rows)})"):
            st.dataframe([{k: r[k] for k in ("step", "tier", "model", "tokens", "seconds", "ok")}
                          for r in rows], hide_index=True, use_container_width=True)


def _glossary():
    for term, meaning in GLOSSARY:
        st.markdown(f"**{term}** — {meaning}")


def _intro():
    """First-visit orientation in plain language: what this is, and a three-minute path."""
    with st.expander("What am I looking at?"):
        st.markdown(
            "**What this is.** Banks in India must report suspicious activity to the financial "
            "intelligence unit (FIU-IND). For each alert a Principal Officer decides whether to "
            "file a Suspicious Transaction Report (STR) or close it, and must defend that call "
            "later. This tool helps, and will not let an AI invent a number: every rupee figure "
            "must come from a transaction or from a fixed, hashed calculator.\n\n"
            "**Try it in three minutes**\n"
            "1. **Twin Cases** — two look-alike alerts, one filed and one closed: what each "
            "decision rests on, side by side.\n"
            "2. **Proof Check** — try to slip a made-up total past the gate.\n"
            "3. **Decision Ledger** — record a decision, check the hash chain, and download a "
            "package anyone can re-verify.\n\n"
            "All data is synthetic. Nothing is filed with FIU-IND; decisions go to a local "
            "ledger only. AI steps need a Token Factory key; the steps above work without one.")


def _stakes():
    """Who this is for and what is at stake; each claim cites a PROVEN/ASSUMED corpus rule."""
    rules = {r["RULE_ID"]: r for r in get_store().corpus_rows()}   # NEEDS-VERIFICATION excluded
    rows = ""
    for s in STAKES:
        r = rules.get(s["rule_id"])
        if r is None:
            continue
        _icon, bg, fg = EVIDENCE_BADGE[r["EVIDENCE_LEVEL"]]
        rows += (f"<tr><td>{_esc(s['claim'])}</td>"
                 f"<td style='white-space:nowrap'><code>{_esc(r['RULE_ID'])}</code> "
                 f"{badge(r['EVIDENCE_LEVEL'], bg, fg)}</td><td>{_esc(s['here'])}</td></tr>")
    st.markdown(
        f'<div class="ddp-card"><div class="ddp-kicker">Who this is for</div>'
        f'<div style="margin:0 0 14px">{_esc(USER)}</div>'
        f'<div class="ddp-kicker">What is at stake</div><table class="ddp-table">'
        f'<tr><th>The rule</th><th>Source</th><th>What this tool does</th></tr>{rows}</table>'
        f'<div class="ddp-foot">Rules from this project\'s corpus snapshot; only PROVEN and '
        f'ASSUMED rules are used. All data in this app is synthetic.</div></div>',
        unsafe_allow_html=True)
    with st.expander("Read the cited rules"):
        for s in STAKES:
            r = rules.get(s["rule_id"])
            if r is not None:
                st.markdown(f"**{r['RULE_ID']}** ({r['EVIDENCE_LEVEL']}) — {r['RULE_TEXT']}  \n"
                            f"<small>Source: {_esc(r['SOURCE_DOCUMENT'])}, "
                            f"{_esc(r['SOURCE_SECTION'])}</small>", unsafe_allow_html=True)


def _goto(page: str) -> None:
    """Navigate to another page. The sidebar radio (key="page") is already instantiated by the
    time a page body runs, so we stage the target and let main() apply it before the radio."""
    st.session_state["_nav_to"] = page
    st.rerun()


# ── page: Alert Queue ─────────────────────────────────────────────────────────
def page_alert_queue():
    st.header("Alert Queue")
    with st.container(border=True):
        s_l, s_r = st.columns([4, 1], vertical_alignment="center")
        s_l.markdown("**Start here.** Two alerts fired by the same rules on the same amount; one "
                     "was filed and one was closed. See what each decision rests on.")
        if s_r.button("Twin Cases →", type="primary", use_container_width=True, key="aq_twins"):
            _goto("Twin Cases")
    _stakes()
    _intro()
    st.caption("Most urgent first · SLA = 7 working days, counted from alert date until suspicion is recorded")

    rows = get_store().alerts_with_last_disposition()

    if not rows:
        st.info("No alerts found.")
        return

    for r in rows:
        r["SLA_DAYS"] = sla_days_left(r["ALERT_DATE"])
        r["AMOUNT"]   = float(r["ALERT_AMOUNT_INR"] or 0)
        r["WORK_STATUS"] = "DEFERRED" if r.get("LAST_DISPOSITION") == "DEFERRED" else r["ALERT_STATUS"]

    pending = [r for r in rows if r["WORK_STATUS"] != "REVIEWED"]
    due_soon = sum(1 for r in pending if 0 <= r["SLA_DAYS"] <= 1)
    overdue = sum(1 for r in pending if r["SLA_DAYS"] < 0)
    st.markdown(
        f'<div class="ddp-card"><div class="ddp-kicker">Review posture</div>'
        f'<strong>{len(pending)} awaiting a recorded decision</strong> · {due_soon} due within one '
        f'working day · {overdue} overdue · pending alerted amount '
        f'<strong>{format_inr(sum(r["AMOUNT"] for r in pending))}</strong>'
        '<div class="ddp-foot">Urgency is a review aid only. It does not determine whether activity '
        'is suspicious or whether a report should be filed.</div></div>',
        unsafe_allow_html=True,
    )

    # ── filter bar ─────────────────────────────────────────────────────────
    statuses = sorted({r["WORK_STATUS"] for r in rows})
    types    = sorted({r["ALERT_TYPE"] for r in rows})
    sources  = sorted({r["SIGNAL_SOURCE"] or "UNKNOWN" for r in rows})
    max_l    = max(1.0, round(max(r["AMOUNT"] for r in rows) / 1e5 + 0.5, 0))

    f_search, f_status, f_type, f_src, f_amt = st.columns([1.6, 1.6, 2, 1.6, 2])
    search = f_search.text_input("Search", placeholder="Alert ID or customer",
                                 key="aq_search").strip().lower()
    sel_status = f_status.multiselect(
        "Status", statuses,
        default=[s for s in statuses if s != "REVIEWED"] or statuses, key="aq_status")
    sel_type = f_type.multiselect("Type", types, format_func=lambda t: t.replace("_", " ").title(),
                                  key="aq_type")
    sel_src  = f_src.multiselect("Signal source", sources, key="aq_src")
    amt_lo, amt_hi = f_amt.slider("Amount (₹ lakh)", 0.0, float(max_l), (0.0, float(max_l)),
                                  key="aq_amt")

    shown = [
        r for r in rows
        if (not sel_status or r["WORK_STATUS"] in sel_status)
        and (not sel_type or r["ALERT_TYPE"] in sel_type)
        and (not sel_src or (r["SIGNAL_SOURCE"] or "UNKNOWN") in sel_src)
        and amt_lo <= r["AMOUNT"] / 1e5 <= amt_hi
        and (not search or search in r["ALERT_ID"].lower()
             or search in str(r["CUSTOMER_PROFILE"] or "").lower())
    ]
    # Undecided first, then by SLA urgency, then larger amounts
    shown.sort(key=lambda r: (r["WORK_STATUS"] == "REVIEWED", r["SLA_DAYS"], -r["AMOUNT"]))

    st.caption(f"Showing {len(shown)} of {len(rows)} alerts")
    st.divider()

    if not shown:
        st.info("No alerts match these filters.")
        return

    for r in shown:
        alert_id = r["ALERT_ID"]
        urgency = (disp_badge(r.get("LAST_DISPOSITION") or "REVIEWED")
                   if r["WORK_STATUS"] == "REVIEWED" else sla_pill(r["SLA_DAYS"]))
        summary, action_col = st.columns([5, 1], vertical_alignment="center")
        with summary:
            st.markdown(
                f'<div class="ddp-queue-row"><strong><code>{_esc(alert_id)}</code> · '
                f'{_esc(r["ALERT_TYPE"].replace("_", " ").title())}</strong> &nbsp; {urgency}'
                f'<div class="ddp-queue-meta"><span>Alerted amount: <strong>{format_inr(r["AMOUNT"])}</strong></span>'
                f'<span>Signal: <code>{_esc(r["SIGNAL_SOURCE"] or "UNKNOWN")}</code></span>'
                f'<span>Account: {_esc(r["ACCOUNT_TYPE"] or "—")}</span>'
                f'<span>Status: {_esc(r["WORK_STATUS"])}</span></div></div>',
                unsafe_allow_html=True,
            )
        with action_col:
            if st.button(f"Open {alert_id}", key=f"review_{alert_id}", use_container_width=True,
                         type="primary" if r["WORK_STATUS"] != "REVIEWED" else "secondary"):
                st.session_state["selected_alert"] = alert_id
                _goto("Disposition Panel")

        with st.expander("Customer profile", expanded=False):
            st.markdown(f"{r['CUSTOMER_PROFILE']}  \n"
                        f"**Account type:** {r['ACCOUNT_TYPE']}  ·  "
                        f"**Alert date:** {r['ALERT_DATE']}  ·  "
                        f"**Status:** {r['WORK_STATUS']}")

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
            if st.button(f"Open {aid} →", key=f"twin_open_{aid}", use_container_width=True):
                _open_alert(aid)
    runs = sum(V.card(reps[i])["runs"] for i in V.TWIN_PAIR)
    st.caption("Scenario decisions are this repo's synthetic, author-labelled outcomes: the stress "
               "test does not choose them. It shows what each one rests on and what would overturn "
               f"it, from {runs} runs of the calculator of record and no model. Signal rules are "
               "product heuristics, not FIU-IND criteria. The hospital invoice and family links "
               "that explain the closure are in the case file, outside the calculator.")


# ── page: Disposition Panel ───────────────────────────────────────────────────
def page_disposition():
    alerts = get_store().alert_ids()
    options = [r["ALERT_ID"] for r in alerts]
    if not options:
        st.info("No alerts found.")
        return
    alert_id = st.session_state.get("selected_alert")
    idx = options.index(alert_id) if alert_id in options else 0

    head_l, head_r = st.columns([3, 1])
    head_l.header("Disposition Panel")
    selected = head_r.selectbox("Alert", options, index=idx)
    st.session_state["selected_alert"] = selected

    alert = get_store().get_alert(selected)
    if not alert:
        st.error("Alert not found.")
        return

    _case_header(selected, alert)
    _workbench_steps()
    _provenance_status(selected)
    _verdict_card(selected)
    _platform_strip(selected)
    # Evidence first in reading and keyboard order (D1). On a narrow screen the columns stack:
    # proof (evidence → sensitivity → model interpretation) → draft → decision.
    ev_col, dec_col = st.columns([3, 2], gap="large")
    with ev_col:
        shadow = _sticky("show_proof", False)
        on = st.toggle("Show the proof", key="show_proof",
                       help="The transactions, calculator facts and hashes, every stress-test "
                            "branch, and the AI's assessment, in that order.")
        st.session_state[shadow] = on
        if on:
            _ai_panel(selected, alert)
        else:
            st.caption("Inside: the alert narrative and transactions · calculator facts with code, "
                       "input and output hashes · every stress-test branch · typology search · "
                       "rule lookup · the AI's 11-factor assessment and the agent (advisory, "
                       "after the evidence).")
    with dec_col:
        _decision_rail(selected, alert)


def _case_header(selected, alert):
    amt  = float(alert["ALERT_AMOUNT_INR"] or 0)
    days = sla_days_left(alert["ALERT_DATE"])
    st.markdown(
        f"**{alert['ALERT_ID']} — {alert['ALERT_TYPE'].replace('_', ' ').title()}**"
        f"&nbsp;&nbsp;{sla_pill(days)}&nbsp;&nbsp;"
        + badge("SYNTHETIC DATA", *NEUTRAL),
        unsafe_allow_html=True,
    )
    st.markdown(
        f"Alerted amount ₹{amt:,.0f} ({amt/1e5:.1f}L) · `{alert['SIGNAL_SOURCE']}` · "
        f"{alert['ACCOUNT_TYPE']} · alerted {alert['ALERT_DATE']}  \n"
        f"{alert['CUSTOMER_PROFILE']}"
    )
    computed = _ensure_computed(selected)        # deterministic, local; no model call
    missing = []
    if _current_assessment(selected) is None:
        missing.append("AI assessment not run")
    else:
        gaps = [f["factor_id"] for f in _current_assessment(selected)
                if f.get("assessment") == "insufficient_data"]
        if gaps:
            missing.append("insufficient data on " + ", ".join(gaps))
    missing += [w for w in computed.get("warnings", [])]
    if missing:
        st.caption("**Not yet known:** " + " · ".join(missing))


def _current_assessment(selected):
    if st.session_state.get("assessed_alert") == selected:
        return st.session_state.get("poe_assessment")
    return None


def _current_computed(selected):
    if st.session_state.get("computed_alert") == selected:
        return st.session_state.get("computed")
    return None


def _trace(selected) -> RunTrace:
    """One pipeline run trace per alert per session; every step the UI runs is added to it."""
    key = f"run_trace_{selected}"
    if key not in st.session_state:
        st.session_state[key] = RunTrace(alert_id=selected)
    return st.session_state[key]


def _ensure_computed(selected):
    """Run the calculator of record for this alert if not already run this session."""
    computed = _current_computed(selected)
    if computed is None:
        step = get_pipeline().step_compute(selected, _load_transactions(selected),
                                           compute_params(get_store(), selected),
                                           _trace(selected))
        if step.status != "ok":
            st.error(f"The calculator of record could not run: {step.blocked_reason}")
            st.stop()
        computed = step.outputs["computed"]
        st.session_state["computed"] = computed
        st.session_state["computed_alert"] = selected
    return computed


def _model_calls(selected):
    return [c for c in st.session_state.get(f"model_calls_{selected}", []) if c]


def _add_model_call(selected, call):
    if call:
        st.session_state.setdefault(f"model_calls_{selected}", []).append(
            {k: call.get(k) for k in ("tier", "model_requested", "model_reported", "usage", "latency_s")})


def _current_gos(selected):
    if st.session_state.get("gos_alert") == selected:
        return st.session_state.get("gos_result")
    return None


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
                        return
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
    else:
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

    if gos is not None and st.button("Re-check edited draft", key=f"recheck_{selected}"):
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

    # ── Decision ───────────────────────────────────────────────────────────
    now_ist = datetime.now(IST).replace(second=0, microsecond=0)
    d_key, t_key = f"susp_date_{selected}", f"susp_time_{selected}"
    po_shadow = _sticky("po_id", _session_user_id())
    d_shadow  = _sticky(d_key, now_ist.date())
    t_shadow  = _sticky(t_key, now_ist.time())

    c_po, c_date, c_time = st.columns(3)
    po_id = c_po.text_input("Principal Officer ID", key="po_id")
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

    # ── T9: counter-evidence to the leading call (bounded, not autonomous) ──
    if assessment:
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

    st.markdown("#### Decision")
    _kind("Officer conclusion", "recorded locally; nothing is sent to FIU-IND")
    st.caption("Officer ID is self-asserted: this build has no sign-in.")
    # Stacked, full width: readable in a narrow column and on a phone.
    action = None
    if st.button("Record decision to file", type="primary", use_container_width=True,
                 help="Review, then confirm. Records in the local ledger only."):
        action = "FILE"
    if st.button("Close without filing", use_container_width=True):
        action = "NOT_FILE"
    if st.button("Defer — await information", use_container_width=True):
        action = "DEFERRED"

    pending_key = f"pending_decision_{selected}"
    if action:
        if not po_id.strip():
            st.warning("Enter your Principal Officer ID before recording a decision.")
        elif len(narrative.strip()) < 20:
            st.warning("Write the Ground of Suspicion / closure rationale before recording a decision.")
        else:
            st.session_state[pending_key] = {"action": action, "text_sha256": _sha(narrative)}

    pending = st.session_state.get(pending_key)
    if pending:
        _confirm_decision(selected, alert, pending, narrative, po_id.strip(), suspicion_ts,
                          str_ref, assessment or [])


def _confirm_decision(selected, alert, pending, narrative, po_id, suspicion_ts, str_ref,
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
        st.markdown(f"- Officer: `{po_id}` (self-asserted)  \n"
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
        if c1.button("Confirm and record", type="primary", disabled=not (ack and check["passed"] and policy_passed),
                     key=f"confirm_{selected}"):
            st.session_state.pop(pending_key, None)
            _record_disposition(
                selected, alert, narrative, action, po_id, suspicion_ts,
                (str_ref or "PENDING-FINGATEREF") if action == "FILE" else None, assessment,
                validated_draft_sha256=_sha(narrative))
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
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Transactions", len(txns))
    b2.metric("Credits", format_inr(total_credit) if total_credit < 1e5 else
              f"₹{total_credit / 1e5:.2f}L", help=f"F-TOTAL-CREDIT = {format_inr(total_credit)}")
    b3.metric("Debits", format_inr(total_debit) if total_debit < 1e5 else
              f"₹{total_debit / 1e5:.2f}L", help=f"F-TOTAL-DEBIT = {format_inr(total_debit)}")
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
                     key=f"compute_{selected}", use_container_width=True):
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


def _ai_panel(selected, alert):
    """Right column. Order matters (anti-anchoring): evidence and the stress test first, AI
    outputs after, and the agent's advisory disposition last of all."""
    _ai_panel_core(selected, alert)
    _agent_panel(selected)
    _trace_panel(selected)

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
    if c2.button("Run stress test", key=f"stress_btn_{selected}", use_container_width=True,
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
    m2.metric("Challenges survived", f"{rob['survived']} / {rob['single_hypotheses']}",
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
                     use_container_width=True, hide_index=True)
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
        st.dataframe(rows, hide_index=True, use_container_width=True)
        st.caption(f"Total tokens this trace: {trace.total_prompt_tokens} prompt + "
                   f"{trace.total_completion_tokens} completion.")


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

    assessment = _current_assessment(selected)
    if assessment is None:
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
        return

    copilot   = get_skills()
    triggered = [f for f in assessment if f.get("assessment") == "triggered"]
    clear     = [f for f in assessment if f.get("assessment") == "clear"]
    insuff    = [f for f in assessment if f.get("assessment") == "insufficient_data"]
    sufficiency = copilot.evidence_sufficiency_summary(assessment)

    h_l, h_r = st.columns([3, 1])
    h_l.markdown("#### AI suspicion assessment")
    _kind("Model interpretation", "advisory; you may disagree and say why")
    if h_r.button("↻ Re-run", use_container_width=True):
        for key in ["poe_assessment", "assessed_alert", "gos_result", "gos_alert"]:
            st.session_state.pop(key, None)
        st.rerun()

    tab_a, tab_g, tab_p = st.tabs(
        ["Assessment", f"Evidence Gaps ({len(insuff)})", "Investigation Plan"]
    )

    with tab_a:
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

    with tab_g:
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

    with tab_p:
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


def _record_disposition(alert_id, alert, rationale, disposition,
                        po_id, suspicion_ts, str_ref, poe_assessment,
                        validated_draft_sha256=None):
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

# ── page: Dashboard ───────────────────────────────────────────────────────────
# ── page: Proof Check ─────────────────────────────────────────────────────────
def _figure_gate_panel(text, txns, facts):
    """Run the evidence gate on `text` and say what it found, in plain words."""
    check = get_skills().validate_gos_evidence(text, txns, facts)
    if check["passed"]:
        cites = "; ".join(f"{amt} ← {', '.join(ids)}" for amt, ids in check["fact_citations"].items())
        st.success("**Passes the figure check.** Every ₹ figure is a transaction amount or a "
                   "calculator fact" + (f": {cites}." if cites else "."))
        return
    parts = []
    if check["unsupported_claims"]:
        amts = ", ".join(f"`{a}`" for a in check["unsupported_claims"])
        parts.append(f"{amts} {'is' if len(check['unsupported_claims']) == 1 else 'are'} not a "
                     "transaction amount or a calculator fact.")
    if check.get("unparsed_amounts"):
        parts.append(", ".join(f"`{a}`" for a in check["unparsed_amounts"])
                     + " cannot be read as one exact figure.")
    st.error("**Blocked.** " + " ".join(parts))


def page_proof_check():
    st.header("Proof Check")
    st.markdown(
        "**Try to get a made-up number past the system.** A language model often adds figures up "
        "wrongly and states the total with confidence. Here, every ₹ figure in a Ground of "
        "Suspicion must be a single transaction amount or a fact from the *calculator of record*, "
        "a fixed program whose code, input and output are hashed. Anything else is blocked, "
        "including at the moment of recording.")
    st.caption("Works offline, with no model call. Recording is attempted in a throwaway ledger, "
               "so your own ledger is never touched.")

    options = [r["ALERT_ID"] for r in get_store().alert_ids()]
    c1, c2 = st.columns([1, 2])
    alert_id = c1.selectbox("Alert", options, index=0, key="pc_alert")
    form_label = c2.radio("How the figure is written", list(FORMS), horizontal=True,
                          key="pc_form",
                          help="The gate reads exact values, so every spelling of the same "
                               "amount is treated alike.")
    form = FORMS[form_label]

    computed = _ensure_computed(alert_id)
    facts = computed["facts"]
    txns = _load_transactions(alert_id)
    credit = total_credit(facts)
    if credit <= 0:
        st.info("This alert has no credits, so there is no total to misstate. Pick another alert.")
        return
    d = build_drafts(credit, form)
    st.markdown(f"The calculator of record says total credits are **{format_inr(credit)}** "
                f"(`F-TOTAL-CREDIT`, run `{computed['run_id']}`).")

    left, right = st.columns(2, gap="large")
    for col, side, title, blurb in (
            (left, "invented", "A draft with an invented total",
             f"Same sentence, but the total is {format_inr(d['invented_value'])} "
             f"({format_inr(INVENTED_EXTRA)} too high). Edit it to try your own."),
            (right, "grounded", "The same draft with the calculator's figure",
             "Same sentence and spelling; the total is the calculator's. Edit it to try your own.")):
        with col:
            st.markdown(f"#### {title}")
            st.caption(blurb)
            text = st.text_area(title, d[side], key=f"pc_{side}_{alert_id}_{form}", height=130,
                                label_visibility="collapsed")
            _figure_gate_panel(text, txns, facts)
            if st.button("Try to record this decision", key=f"pc_rec_{side}",
                         use_container_width=True):
                st.session_state[f"pc_out_{side}"] = attempt_recording(alert_id, text)
            out = st.session_state.get(f"pc_out_{side}")
            if out:
                if out["recorded"]:
                    st.success(f"{out['message']} Throwaway ledger now has {out['ledger_rows']} "
                               f"row, chain verified: {out['chain_ok']}.")
                else:
                    st.error(f"{out['message']}  \n**Ledger rows written: {out['ledger_rows']}.**")
    with st.expander("What this does and does not prove"):
        st.markdown(
            "- It proves a figure is **traceable**: it equals a transaction amount, or a fact the "
            "hashed calculator produced from the case's transactions.  \n"
            "- It does **not** prove the sentence around a figure is true, or that the "
            "transactions themselves are accurate. Sentences without figures are listed for the "
            "officer's own review.  \n"
            "- Amounts written in words, and currencies other than rupees, are not read; a "
            "figure the parser cannot read as one exact value fails the check rather than "
            "passing unnoticed.")


# ── page: Measured Results ────────────────────────────────────────────────────
def page_measured_results():
    st.header("Measured Results")
    st.markdown(
        "Every number on this page is computed from a dated report committed in `evals/`. "
        "Nothing is typed in by hand, and each section names the file, date and code revision it "
        "came from. **All cases are synthetic. The set is small, and its labels were assigned by "
        "the author, not by an expert panel, so none of this is an accuracy claim.**")

    h = latest_live_holdout()
    st.subheader("1. The same model, with and without the controls")
    if not h:
        st.info("No live holdout run is committed in `evals/`.")
    else:
        c = h["conditions"]
        base, full = c["C2_baseline_no_controls"], c["C3_full_product"]
        st.markdown("**Drafts containing at least one figure that is not a transaction amount or "
                    "a calculator fact**")
        m1, m2, m3 = st.columns(3)
        m1.metric("Same model, no controls",
                  f"{base['drafts_with_unsupported']} of {base['drafts']}",
                  help=f"{base['unsupported_figures_total']} unsupported figures among "
                       f"{base['figures_total']} figures written.")
        m2.metric("Full product",
                  f"{full['drafts_with_unsupported']} of {full['drafts']}",
                  help=f"{full['unsupported_figures_total']} unsupported figures among "
                       f"{full['figures_total']} figures written. The drafter is the same "
                       "model; the gate decides what is accepted.")
        m3.metric("In drafts the product accepted",
                  f"{full['unsupported_in_accepted']} figures",
                  help=f"Unsupported figures found in the {full['accepted_by_gate']} drafts the "
                       "gate accepted.")
        st.caption(
            f"Same {h['cases']} synthetic cases and inputs in every condition. The product's own "
            "drafter still put model-computed figures into half the drafts; the gate stopped "
            "those drafts from being accepted. Run `" + str(h["dir"]) + f"`, {str(h['started_utc'])[:16]} "
            f"UTC, code revision `{h['git_rev']}`, dataset `{h['dataset']}` "
            f"(sha256 `{str(h['dataset_sha256'])[:12]}…`).")

        st.subheader("2. Does the gate catch seeded faults?")
        g1, g2, g3 = st.columns(3)
        g1.metric("Faults caught (all seeded)", f"{h['caught']} of {h['faults_total']}")
        g2.metric("…of the kinds it is designed to catch", f"{h['caught_designed']} of {h['designed_total']}")
        g3.metric("Supported narratives wrongly rejected", f"{h['false_rejections']} of {h['supported_total']}")
        st.caption("The misses are shown, not tuned away: the gate checks figures, not whether the "
                   "sentence around a figure is true.")
        with st.expander(f"All {h['faults_total']} seeded faults and what the gate did"):
            st.dataframe([{"case": f["case"], "fault": f["fault"],
                           "outcome": "caught" if f["caught"] else "MISSED",
                           "labelled": f["expected"], "gate said": f["got"], "text": f["text"]}
                          for f in h["faults"]], hide_index=True, use_container_width=True)
        if h["label_mismatches"]:
            st.warning("Where the gate disagreed with the author's label: " + " · ".join(
                f"{m['case']} {m['fault'].replace('_', ' ')}: “{m['text']}”"
                for m in h["label_mismatches"]))

    st.subheader("3. Live Nemotron run over 16 synthetic alerts")
    reports = live_eval_reports()
    if not reports:
        st.info("No live 16-alert report is committed in `evals/`.")
    else:
        path, rep = reports[0]
        r = summarise_live(rep, path)
        a1, a2, a3, a4 = st.columns(4)
        a1.metric("11-factor output valid", f"{r['assess_model_valid']} of {r['alerts']}",
                  help="Schema-valid model output, first try or after one repair. Fallback "
                       f"placeholders are never counted. Outcomes: {r['assess_outcomes']}.")
        a2.metric("Agent agrees on clear cases", f"{r['clear_agree']} of {r['clear_cases']}",
                  help=f"An always-FILE rule would get {r['clear_gold_file']} of "
                       f"{r['clear_cases']} right.")
        a3.metric("Rejected submissions", r["agent_rejections"],
                  help=f"Agent submissions rejected by validation, across "
                       f"{r['agent_alerts_with_rejection']} alerts; each was returned to the "
                       "model, which corrected it.")
        a4.metric("Contested cases filed", f"{r['contested_filed']} of {r['contested']}",
                  help="Ambiguous by design. The agent leans towards filing.")
        st.caption(
            f"Median time per alert: {r['median_assess_s']} s for the 11-factor assessment and "
            f"{r['median_agent_s']} s for the agent. `{r['source']}`, "
            f"{str(r['started_utc'])[:16]} UTC, compute backend `{r['compute_backend']}`. "
            f"{r['assess_truncated']} assessments were cut off at the token limit and repaired.")
        st.caption("Stress test (deterministic): only "
                   f"{r['stress_high']} of {r['gold_file']} gold-FILE alerts reach a HIGH modeled "
                   "level from calculator signals, because most seeded alerts are one summary "
                   "transaction. The rest rest on evidence the calculator does not see.")

    with st.expander("What these results do not show", expanded=True):
        st.markdown(
            "- **Small, author-labelled, synthetic.** Six holdout cases and sixteen development "
            "alerts support no general accuracy claim.  \n"
            "- **No officer study.** Review time, corrections and real-world error rates were "
            "not measured.  \n"
            "- **The gate checks figures only.** Wrong-party and invented-context statements "
            "built from real figures pass it and are listed for human review.  \n"
            "- **One model family, one run each.** Model output varies between runs.  \n"
            "- **No cost figure is shown** because none was measured here.")


def page_dashboard():
    st.header("Inspection Readiness Dashboard")
    st.caption("Internal governance view. The alert-to-STR ratio is an internal metric that "
               "inspectors are understood to examine (INS-003, ASSUMED); FIU-IND publishes no "
               "benchmark for it.")

    alerts_rows = get_store().dashboard_alerts()
    ledger_rows = get_store().dashboard_ledger()

    open_a    = sum(1 for r in alerts_rows if r["ALERT_STATUS"] == "OPEN")
    reviewed  = sum(1 for r in alerts_rows if r["ALERT_STATUS"] == "REVIEWED")
    filed     = sum(1 for r in ledger_rows if r["DISPOSITION"] == "FILE")
    not_filed = sum(1 for r in ledger_rows if r["DISPOSITION"] == "NOT_FILE")
    deferred  = sum(1 for r in ledger_rows if r["DISPOSITION"] == "DEFERRED")
    overdue   = sum(1 for r in ledger_rows if (r["SLA_DAYS_REMAINING"] or 99) < 0)
    ratio     = round(filed * 100 / (filed + not_filed), 1) if (filed + not_filed) > 0 else None

    st.subheader("Alert Pipeline")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Open (pending review)", open_a)
    c2.metric("Reviewed", reviewed)
    c3.metric("Filed (STR)", filed)
    c4.metric("Not Filed", not_filed)

    st.subheader("Key FIU-IND Inspection Metrics")
    m1, m2, m3 = st.columns(3)

    if ratio is not None:
        m1.metric(
            "Alert-to-STR Ratio",
            f"{ratio}%",
            help="Internal governance metric (no FIU-IND benchmark published — Gap DG-04). Too low = suppression risk; too high = over-filing.",
        )
    else:
        m1.metric("Alert-to-STR Ratio", "—", help="Record some decisions first.")

    m2.metric("SLA Breaches (>7 WD)", overdue,
              delta=f"{overdue} overdue" if overdue else None,
              delta_color="inverse")
    m3.metric("Deferred / Pending Info", deferred)

    st.divider()
    st.subheader("Alert Breakdown by Type")

    type_counts: dict[str, int] = {}
    for r in alerts_rows:
        t = r["ALERT_TYPE"].replace("_", " ").title()
        type_counts[t] = type_counts.get(t, 0) + 1

    if type_counts:
        import json as _json
        chart_data = [{"type": k, "count": v} for k, v in sorted(type_counts.items(), key=lambda x: -x[1])]
        st.bar_chart(
            data={r["type"]: r["count"] for r in chart_data},
            use_container_width=True,
            height=300,
        )

    st.subheader("Signal Source Mix")
    src_counts: dict[str, int] = {}
    for r in alerts_rows:
        s = r.get("SIGNAL_SOURCE") or "UNKNOWN"
        src_counts[s] = src_counts.get(s, 0) + 1
    for src, cnt in sorted(src_counts.items(), key=lambda x: -x[1]):
        pct = cnt * 100 // len(alerts_rows) if alerts_rows else 0
        st.markdown(f"`{src}` — {cnt} alerts ({pct}%)")

    st.divider()
    st.subheader("Token usage (Nebius Token Factory)")
    usage = get_store().token_usage_summary()
    if usage["total"] == 0:
        st.caption(
            "No model calls recorded yet. Token usage is tracked automatically "
            "from recorded decisions once you run the AI assessment and record a disposition."
        )
    else:
        u1, u2, u3 = st.columns(3)
        u1.metric("Prompt tokens", f"{usage['total_prompt']:,}")
        u2.metric("Completion tokens", f"{usage['total_completion']:,}")
        u3.metric("Total tokens", f"{usage['total']:,}",
                  help="Across all recorded decisions in the local ledger. "
                       "Resets when the database is re-seeded.")

        if usage["by_tier"]:
            tier_order = ["triage", "reasoning", "disposition"]
            rows_table = [
                t for t in tier_order if t in usage["by_tier"]
            ] + [t for t in usage["by_tier"] if t not in tier_order]

            st.markdown("**By tier**")
            hdr, h2, h3, h4 = st.columns([2, 2, 2, 2])
            hdr.markdown("**Tier**")
            h2.markdown("**Prompt**")
            h3.markdown("**Completion**")
            h4.markdown("**Total**")
            for tier in rows_table:
                b = usage["by_tier"][tier]
                c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
                c1.markdown(f"`{tier}`")
                c2.markdown(f"{b['prompt']:,}")
                c3.markdown(f"{b['completion']:,}")
                c4.markdown(f"{b['prompt'] + b['completion']:,}")

        st.caption(
            f"Derived from {usage['decisions_with_model_calls']} decision(s) that recorded model calls. "
            "Counts reflect only calls made through this app's ledger — not probe scripts or harness runs. "
            "Token costs depend on the tier's model; check the Token Factory console for billing details."
        )

    st.divider()
    st.caption(
        "Alert-to-STR ratio is an internal governance metric. "
        "No official FIU-IND benchmark has been publicly confirmed (Gap DG-04). "
        "Inspect the not-filed rationale column in the Decision Ledger for inspection readiness."
    )

# ── page: Regulatory Reference ────────────────────────────────────────────────
def page_regulatory():
    st.header("Regulatory Reference")
    st.caption("Lexical search over the FIU-IND AML corpus (PROVEN + ASSUMED only). "
               "Returns nothing when no rule covers the question.")

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

# ── main shell ────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="Twin Trace",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="auto",   # collapses on narrow screens
    )

    # Sidebar branding
    with st.sidebar:
        st.markdown("### Twin Trace")
        _cfg = get_settings()
        st.caption(
            "AML alert decision support · **synthetic data only** · not affiliated with or "
            "approved by FIU-IND  \n"
            f"Models (Token Factory): {_service_status('model')}  \n"
            f"Web search (Tavily): {_service_status('tavily')}  \n"
            f"Compute: {_cfg.compute_backend}"
            + ("  \n**Public demo:** your session has its own data, reset on reload; "
               f"{_cfg.demo_max_model_calls} model calls per session." if _cfg.demo_mode else "")
        )
        st.divider()

        pages = [
            "Alert Queue",
            "Twin Cases",
            "Proof Check",
            "Disposition Panel",
            "Decision Ledger",
            "Dashboard",
            "Measured Results",
            "Regulatory Reference",
        ]
        # Allow page navigation via session_state (e.g. from Alert Queue buttons).
        # key="page" binds the radio directly to session_state — no index= needed,
        # which avoids the double-click issue caused by index= fighting widget state.
        if "_nav_to" in st.session_state:
            st.session_state["page"] = st.session_state.pop("_nav_to")
        if "page" not in st.session_state or st.session_state["page"] not in pages:
            st.session_state["page"] = pages[0]
        selected_page = st.radio("Navigate", pages, key="page")

        with st.expander("Glossary"):
            _glossary()
        st.divider()
        st.caption("Corpus snapshot: 2026-09-17  \n"
                   "PROVEN: 15  ·  ASSUMED: 21  \n"
                   "NEEDS-VERIFICATION: 13 (excluded from output)  \n"
                   "POE framework: product-compiled (DG-19)")

    # Route to page
    _style()
    if selected_page == "Alert Queue":
        page_alert_queue()
    elif selected_page == "Twin Cases":
        page_twins()
    elif selected_page == "Proof Check":
        page_proof_check()
    elif selected_page == "Disposition Panel":
        page_disposition()
    elif selected_page == "Decision Ledger":
        page_ledger()
    elif selected_page == "Dashboard":
        page_dashboard()
    elif selected_page == "Measured Results":
        page_measured_results()
    elif selected_page == "Regulatory Reference":
        page_regulatory()


if __name__ == "__main__":
    main()
