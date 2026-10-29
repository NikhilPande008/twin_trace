"""Streamlit UI for Twin Trace, split out of app.py (2026-10-28). app.py is the entry point:
sidebar and page routing. Pages live in ddp/ui/pages/, shared rendering in ddp/ui/."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent


def source_files() -> list[Path]:
    """Every UI source file, for the guard tests that scan UI source (colours, rule IDs, copy)."""
    return [_ROOT / "app.py"] + sorted(Path(__file__).resolve().parent.rglob("*.py"))
