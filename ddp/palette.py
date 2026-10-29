"""
UI colour tokens for the light and dark themes, with the WCAG contrast arithmetic that
justifies them (T9.9).

Raw colour values live only in LIGHT and DARK below. App code uses the role constants, which
are CSS variables (`var(--ddp-…)`); `css_variables()` defines each one as
`light-dark(<light>, <dark>)`, so custom HTML follows Streamlit's theme switch in the browser
(Streamlit sets `color-scheme` on `.stApp`). `tests/test_accessibility.py` holds every
text/background pair to 4.5:1 in both themes. Meaning is never carried by colour alone: every
badge also carries its text label.
"""

from __future__ import annotations

import re

# Light values are the implementation brief's tokens; dark values are derived (DECISIONS.md).
LIGHT = {
    "canvas":     "#F8FAFC",   # page; = theme.light.backgroundColor
    "surface":    "#FFFFFF",   # cards, sidebar; = theme.light.secondaryBackgroundColor
    "text":       "#111827",   # = theme.light.textColor
    "text_muted": "#475569",
    "accent":     "#0B5C66",   # teal used as text and rules
    "action":     "#0B5C66",   # primary button fill under white text; = primaryColor
    "border":     "#CBD5E1",   # = borderColor
    "focus":      "#1D4ED8",
    "fork_row":   "#DDF6F7",
    "brand_bg":   "#DDF6F7", "brand_fg":   "#0B5C66",
    "success_bg": "#ECFDF5", "success_fg": "#047857",
    "warning_bg": "#FFFBEB", "warning_fg": "#92400E",
    "error_bg":   "#FEF2F2", "error_fg":   "#B91C1C",
    "info_bg":    "#F0F9FF", "info_fg":    "#0369A1",
    "neutral_bg": "#E2E8F0", "neutral_fg": "#475569",
    "officer_fg": "#9A3412",
}
DARK = {
    "canvas":     "#0F172A",
    "surface":    "#1E293B",
    "text":       "#F1F5F9",
    "text_muted": "#94A3B8",
    "accent":     "#7DD3DC",
    "action":     "#0E7490",
    "border":     "#334155",
    "focus":      "#60A5FA",
    "fork_row":   "#083344",
    "brand_bg":   "#083344", "brand_fg":   "#7DD3DC",
    "success_bg": "#022C22", "success_fg": "#6EE7B7",
    "warning_bg": "#451A03", "warning_fg": "#FCD34D",
    "error_bg":   "#450A0A", "error_fg":   "#FCA5A5",
    "info_bg":    "#082F49", "info_fg":    "#7DD3FC",
    "neutral_bg": "#334155", "neutral_fg": "#E2E8F0",
    "officer_fg": "#FDBA74",
}
THEMES = {"light": LIGHT, "dark": DARK}


def var(token: str) -> str:
    return f"var(--ddp-{token.replace('_', '-')})"


def css_variables() -> str:
    """Declarations for `.stApp`: each token resolves per the active Streamlit theme."""
    return ";".join(f"--ddp-{k.replace('_', '-')}:light-dark({LIGHT[k]},{DARK[k]})" for k in LIGHT)


def resolve(value: str, theme: str) -> str:
    """The hex a role constant (`var(--ddp-…)`) takes in a theme. For tests."""
    m = re.fullmatch(r"var\(--ddp-([a-z-]+)\)", value)
    return THEMES[theme][m.group(1).replace("-", "_")] if m else value


def _pair(name: str) -> tuple[str, str]:
    return var(f"{name}_bg"), var(f"{name}_fg")


# ── Roles used by app.py: (background, text) pairs and single colours ──────────
SUCCESS, WARNING, ERROR, INFO = _pair("success"), _pair("warning"), _pair("error"), _pair("info")
NEUTRAL, BRAND = _pair("neutral"), _pair("brand")

CARD_BG = var("surface")
CARD_BORDER = var("border")
TEXT = var("text")
MUTED_TEXT = var("text_muted")
ACCENT = var("accent")
FOCUS = var("focus")
FORK_ROW_BG = var("fork_row")  # the one stress-test row that flips the decision

DISP_STYLE = {
    "FILE":      ERROR,
    "NOT_FILE":  SUCCESS,
    "CONTESTED": WARNING,
    "OPEN":      INFO,
    "REVIEWED":  BRAND,
    "CLOSED":    NEUTRAL,
    "REOPENED":  ERROR,       # same colour as a reopened watch outcome (T12.14)
}
SLA_URGENT, SLA_SOON, SLA_OK = ERROR, WARNING, SUCCESS
SCORE_GOOD, SCORE_MID, SCORE_BAD = SUCCESS, WARNING, ERROR
READING_STYLE = {"FILE": ERROR, "NOT_FILE": SUCCESS}   # chips on each side of the verdict card

KIND_STYLE = {
    "Source facts":         BRAND,
    "Product heuristic":    NEUTRAL,
    "Model interpretation": INFO,
    "Unverified external":  WARNING,
    "Officer conclusion":   (var("neutral_bg"), var("officer_fg")),
}
EVIDENCE_BADGE = {
    "PROVEN":             ("🟢", *SUCCESS),
    "ASSUMED":            ("🟡", *WARNING),
    "NEEDS-VERIFICATION": ("🔴", *ERROR),
}
EVIDENCE_UNKNOWN = ("⚪", *NEUTRAL)
VERDICT_COLORS = {"HIGH": ERROR, "ELEVATED": WARNING, "LOW": SUCCESS}
RECOMMENDATION_COLORS = {      # (background, text) for the AI recommendation box
    "FILE":                  ERROR,
    "REVIEW":                WARNING,
    "INSUFFICIENT_EVIDENCE": INFO,
    "NOT_FILE":              SUCCESS,
}


def _rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _luminance(rgb: tuple[int, int, int]) -> float:
    def chan(v: int) -> float:
        c = v / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg: str, bg: str) -> float:
    """WCAG contrast ratio between two #rrggbb colours."""
    hi, lo = sorted((_luminance(_rgb(fg)), _luminance(_rgb(bg))), reverse=True)
    return (hi + 0.05) / (lo + 0.05)
# Watch outcomes (T12.6): the same three colours everywhere they appear.
WATCH_STYLE = {"holds": SUCCESS, "reopened": ERROR, "needs_review": WARNING,
               "repeat_closure": INFO, "contested": WARNING}
