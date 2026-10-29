"""Sign-in for the UI: st.login / st.user / st.secrets mapped onto ddp.identity (2026-10-28)."""

from __future__ import annotations

import streamlit as st

from ..identity import Identity, auth_configured, resolve


def _secrets() -> dict:
    """st.secrets as plain dicts; {} when there is no secrets.toml (the offline case)."""
    try:
        return {k: (dict(v) if hasattr(v, "items") else v) for k, v in st.secrets.items()}
    except Exception:  # noqa: BLE001
        return {}


def _user() -> dict:
    try:
        return {k: st.user.get(k) for k in ("is_logged_in", "email", "iss", "sub")}
    except Exception:  # noqa: BLE001
        return {}


def current_identity(typed_id: str = "") -> Identity:
    return resolve(_secrets(), _user(), typed_id)


def sign_in_controls() -> None:
    """Sidebar sign-in and sign-out; nothing is shown when sign-in is not configured."""
    if not auth_configured(_secrets()):
        return
    if _user().get("is_logged_in"):
        st.caption(current_identity().note)
        if st.button("Sign out", key="sign_out"):
            st.logout()
    elif st.button("Sign in", key="sign_in", type="primary"):
        st.login()
