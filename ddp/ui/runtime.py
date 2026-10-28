"""Shared runtime: store, skills, calculator runner and pipeline for the UI."""

from __future__ import annotations

import streamlit as st

from ..bootstrap import build, open_store
from ..config import get_settings


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
