"""Watch rendering (T12.6): reason chips, the per-decision timeline and the "what changed" card."""

from __future__ import annotations

import streamlit as st

from ..palette import DISP_STYLE, NEUTRAL, VERDICT_COLORS, WATCH_STYLE
from ..watch import alert_reasons, timeline
from .widgets import _esc, badge

OUTCOME_LABEL = {"holds": "Holds", "reopened": "Reopened", "needs_review": "Needs review"}
CAUSE_LABEL = {"registry_update": "Registry update", "new_transaction": "New transaction",
               "rule_change": "Rule changed", "watch_pass": "Watch pass"}


def reason_chips(store, alert_id: str, index: dict | None = None) -> str:
    """HTML chips for the inbox row; '' when nothing has come back. Pass `index`
    (watch.reasons_index) when rendering many rows."""
    return "".join(
        '<span class="ddp-chip" style="background:{};color:{}">{}</span>'.format(
            *WATCH_STYLE.get(r["kind"], NEUTRAL), _esc(r["text"]))
        for r in alert_reasons(store, alert_id, index))


def what_changed_card(node: dict) -> None:
    """The latest open outcome, in the if-you-file / if-you-close wording of the verdict card."""
    d = node["detail"]
    v0, v1 = d.get("verdict_before"), d.get("verdict_after")
    reading = "If you close" if d.get("disposition") == "NOT_FILE" else "If you file"
    levels = (badge(v0, *VERDICT_COLORS.get(v0, NEUTRAL)) + " → "
              + badge(v1, *VERDICT_COLORS.get(v1, NEUTRAL))) if v0 and v1 else ""
    named = ('<div class="ddp-note">This exact change was listed as a reopen trigger when the '
             'decision was made.</div>') if d.get("named_at_decision") else ""
    fired = ""
    if "fired_after" in d:
        added = sorted(set(d["fired_after"]) - set(d.get("fired_before", [])))
        lost = sorted(set(d.get("fired_before", [])) - set(d["fired_after"]))
        fired = ('<div class="ddp-note">Signals now firing: ' + (", ".join(added) or "none new")
                 + " · no longer firing: " + (", ".join(lost) or "none") + "</div>")
    st.markdown(
        f'<div class="ddp-card"><div class="ddp-kicker">What changed since you decided · '
        f'{_esc(reading)}</div><div class="ddp-title">{_esc(d.get("trigger", ""))}</div>'
        f'<div>{levels}</div><div class="ddp-note">{_esc(d.get("reason", ""))}</div>{fired}{named}'
        f'<div class="ddp-foot">Re-run of the calculator of record on the inputs recorded with '
        f'the decision: run <code>{_esc(node.get("rerun_id") or "—")}</code>, parent '
        f'<code>{_esc(node.get("base_run_id") or "—")}</code>. Deterministic; no model call.</div>'
        f'</div>', unsafe_allow_html=True)


def render_timeline(store, alert_id: str, *, show_passes: bool = False) -> None:
    nodes = timeline(store, alert_id)
    if not nodes:
        st.caption("No recorded decision on this alert yet, so nothing is being watched.")
        return
    open_nodes = [n for n in nodes if n["type"] == "event" and n["outcome"] != "holds"]
    if open_nodes:
        what_changed_card(open_nodes[-1])
    rows = []
    for n in nodes:
        if n["type"] == "event" and n["cause"] == "watch_pass" and not show_passes:
            continue
        if n["type"] == "decision":
            head = "Decision " + badge(n["disposition"], *DISP_STYLE.get(n["disposition"], NEUTRAL))
            body = f'Calculator run <code>{_esc(n["run_id"] or "none cited")}</code>'
        else:
            head = (_esc(CAUSE_LABEL.get(n["cause"], n["cause"])) + " "
                    + badge(OUTCOME_LABEL[n["outcome"]], *WATCH_STYLE[n["outcome"]]))
            body = _esc(n["detail"].get("reason") or n["detail"].get("trigger", ""))
        rows.append(f'<tr><td style="white-space:nowrap">{_esc(n["at"][:16].replace("T", " "))}</td>'
                    f'<td>{head}<div class="ddp-note">{body}</div></td>'
                    f'<td><code>{_esc(n["hash"][:12])}…</code></td></tr>')
    st.markdown('<table class="ddp-table"><tr><th>When (UTC)</th><th>What</th><th>Row hash</th>'
                '</tr>' + "".join(rows) + "</table>", unsafe_allow_html=True)
