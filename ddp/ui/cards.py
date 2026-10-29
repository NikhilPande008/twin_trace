"""Cards shown above the evidence: verdict card, platform trace, provenance status, stakes and
intro."""

from __future__ import annotations

import streamlit as st

from .. import platform_trace as PT, verdict as V
from ..config import get_settings
from ..palette import ACCENT, EVIDENCE_BADGE, MUTED_TEXT, READING_STYLE, VERDICT_COLORS
from ..stakes import STAKES, USER
from .case_state import _current_computed, _ensure_computed, _platform_calls, _readings
from .runtime import _llm_ready, get_store
from .widgets import _chips, _esc, badge, _term


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
                          for r in rows], hide_index=True, width="stretch")


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
        rows += (f"<tr><td>{_term(s['claim'])}</td>"
                 f"<td style='white-space:nowrap'><code>{_esc(r['RULE_ID'])}</code> "
                 f"{badge(r['EVIDENCE_LEVEL'], bg, fg)}</td><td>{_esc(s['here'])}</td></tr>")
    st.markdown(
        f'<div class="ddp-card"><div class="ddp-kicker">Who this is for</div>'
        f'<div style="margin:0 0 14px">{_term(USER)}</div>'
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
