"""Small rendering helpers shared by every page: badges, SLA pills, sticky widget state, page CSS,
navigation."""

from __future__ import annotations

import hashlib
import html
from datetime import date, datetime, timedelta, timezone

import streamlit as st

from ..palette import (ACCENT, CARD_BG, CARD_BORDER, DISP_STYLE, FOCUS, FORK_ROW_BG, KIND_STYLE,
                       MUTED_TEXT, NEUTRAL, SLA_OK, SLA_SOON, SLA_URGENT, css_variables, var)


def _kind(label: str, note: str = "") -> None:
    bg, fg = KIND_STYLE[label]
    st.markdown(badge(label, bg, fg) + (f"&nbsp; <small>{note}</small>" if note else ""),
                unsafe_allow_html=True)


def _sha(text: str) -> str:
    return hashlib.sha256((text or "").encode()).hexdigest()


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
abbr[title]{{text-decoration:underline dotted;text-underline-offset:3px;cursor:help}}
:focus-visible{{outline:2px solid {FOCUS} !important;outline-offset:2px}}
@media (max-width: 760px){{
  .ddp-card{{padding:14px 14px 12px}}
  .ddp-workbench-nav span{{flex:1 1 42%;text-align:center}}
  .ddp-queue-row{{padding:11px 12px}}
}}
</style>""", unsafe_allow_html=True)


def _esc(text) -> str:
    return html.escape(str(text))


def _term(text) -> str:
    """Escaped text with inline glossary tooltips on known terms (T12.14)."""
    from ..glossary import with_tooltips
    return with_tooltips(_esc(text))


def _chips(items: list[str], style: tuple[str, str]) -> str:
    bg, fg = style
    return "".join(f'<span class="ddp-chip" style="background:{bg};color:{fg}">{_esc(i)}</span>'
                   for i in items)


def _goto(page: str) -> None:
    """Navigate to another page. The sidebar radio (key="page") is already instantiated by the
    time a page body runs, so we stage the target and let main() apply it before the radio."""
    st.session_state["_nav_to"] = page
    st.rerun()
