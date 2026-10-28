"""
Officer identity for a recorded decision (2026-10-28).

Two bases, both written into the hash-chained ledger row (DECISION_MAKER_ID and METADATA_JSON,
which are hashed fields):

  oidc           sign-in is configured ([auth] in .streamlit/secrets.toml) and the officer signed
                 in with st.login (OpenID Connect) as an email on the officer allow-list
                 ([officers] in the same file). The ledger gets the allow-listed officer ID, the
                 issuer and a SHA-256 of the provider's subject, never the email.
  self-asserted  no sign-in is configured (offline mode). The officer types an ID; the row says
                 it is self-asserted.

When sign-in is configured, nobody records without signing in as an allow-listed officer.
Pure functions over plain dicts, so the rules are testable without Streamlit or a provider.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

AUTH_KEYS = ("redirect_uri", "cookie_secret", "client_id", "client_secret", "server_metadata_url")
SELF_ASSERTED = "self-asserted (no authentication in this build)"
OIDC = "oidc (st.login, officer allow-list)"


@dataclass(frozen=True)
class Identity:
    officer_id: str                 # DECISION_MAKER_ID; "" when recording is not allowed
    basis: str                      # SELF_ASSERTED | OIDC
    can_record: bool
    note: str                       # one line for the UI
    claims: dict = field(default_factory=dict)   # METADATA_JSON["decision_maker_identity"]

    @property
    def signed_in(self) -> bool:
        return self.basis == OIDC


def auth_configured(secrets: dict) -> bool:
    auth = secrets.get("auth") or {}
    return all(auth.get(k) for k in AUTH_KEYS)


def officer_allowlist(secrets: dict) -> dict[str, str]:
    """email (lower case) -> officer ID, from [officers] in secrets.toml."""
    return {str(k).strip().lower(): str(v).strip()
            for k, v in (secrets.get("officers") or {}).items() if str(v).strip()}


def resolve(secrets: dict, user: dict, typed_id: str = "") -> Identity:
    """Who is recording, and on what basis. `user` is st.user as a dict."""
    if not auth_configured(secrets):
        oid = (typed_id or "").strip()
        return Identity(oid, SELF_ASSERTED, bool(oid),
                        "Officer ID is self-asserted: no sign-in is configured (offline mode).")
    if not user.get("is_logged_in"):
        return Identity("", OIDC, False, "Sign in (sidebar) to record a decision.")
    email = str(user.get("email") or "").strip().lower()
    oid = officer_allowlist(secrets).get(email, "")
    if not oid:
        return Identity("", OIDC, False,
                        "Signed in, but this account is not on the officer allow-list: "
                        "decisions cannot be recorded.")
    iss, sub = str(user.get("iss") or ""), str(user.get("sub") or "")
    return Identity(oid, OIDC, True, f"Signed in as {oid} (OpenID Connect).",
                    {"issuer": iss, "subject_sha256": hashlib.sha256(f"{iss}|{sub}".encode()).hexdigest()})
