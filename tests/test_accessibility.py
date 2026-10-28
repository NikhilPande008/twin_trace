"""Colour pairs meet WCAG AA text contrast (4.5:1) in both themes, and the themes stay in sync (T9.9)."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

from ddp import palette as P

ROOT = Path(__file__).resolve().parent.parent
AA = 4.5
THEMES = ("light", "dark")


def _pairs():
    for name, (bg, fg) in P.KIND_STYLE.items():
        yield f"kind:{name}", fg, bg
    for name, (_icon, bg, fg) in {**P.EVIDENCE_BADGE, "UNKNOWN": P.EVIDENCE_UNKNOWN}.items():
        yield f"evidence:{name}", fg, bg
    for name, (bg, fg) in P.VERDICT_COLORS.items():
        yield f"verdict:{name}", fg, bg
    for name, (bg, fg) in P.RECOMMENDATION_COLORS.items():
        yield f"recommendation:{name}", fg, bg
        yield f"recommendation-note:{name}", P.MUTED_TEXT, bg
    for name, (bg, fg) in P.DISP_STYLE.items():
        yield f"disposition:{name}", fg, bg
    for name, (bg, fg) in P.READING_STYLE.items():
        yield f"reading:{name}", fg, bg
    for name, (bg, fg) in [("sla_urgent", P.SLA_URGENT), ("sla_soon", P.SLA_SOON),
                           ("sla_ok", P.SLA_OK), ("score_good", P.SCORE_GOOD),
                           ("score_mid", P.SCORE_MID), ("score_bad", P.SCORE_BAD)]:
        yield name, fg, bg
        yield f"{name}-bare", fg, P.var("canvas")          # also shown as bare coloured text
    yield "fork-row", P.TEXT, P.FORK_ROW_BG
    for fg in (P.TEXT, P.MUTED_TEXT, P.ACCENT):
        for bg in ("canvas", "surface"):
            yield f"{fg}-on-{bg}", fg, P.var(bg)


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("name,fg,bg", list(_pairs()))
def test_text_contrast(theme, name, fg, bg):
    f, b = P.resolve(fg, theme), P.resolve(bg, theme)
    assert P.contrast(f, b) >= AA, (theme, name, round(P.contrast(f, b), 2))


@pytest.mark.parametrize("theme", THEMES)
def test_primary_button_text_contrast(theme):
    assert P.contrast("#FFFFFF", P.THEMES[theme]["action"]) >= AA     # Streamlit draws white text


def test_both_themes_define_the_same_tokens():
    assert P.LIGHT.keys() == P.DARK.keys()


def test_css_variables_cover_every_role():
    css = P.css_variables()
    for k in P.LIGHT:
        assert f"--ddp-{k.replace('_', '-')}:light-dark({P.LIGHT[k]},{P.DARK[k]})" in css


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("key,token", [("textColor", "text"), ("backgroundColor", "canvas"),
                                       ("secondaryBackgroundColor", "surface"),
                                       ("primaryColor", "action"), ("borderColor", "border")])
def test_streamlit_theme_matches_tokens(theme, key, token):
    cfg = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text())
    assert cfg["theme"][theme][key].lower() == P.THEMES[theme][token].lower()


def test_no_raw_colours_in_app():
    from ddp.ui import source_files   # app.py and every ddp/ui module
    for path in source_files():
        assert not re.findall(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", path.read_text()), path.name


def test_contrast_helper_known_values():
    assert round(P.contrast("#000000", "#ffffff"), 1) == 21.0
    assert round(P.contrast("#777777", "#777777"), 1) == 1.0
