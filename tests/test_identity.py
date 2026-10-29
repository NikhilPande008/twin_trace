"""
Officer identity on a recorded decision (2026-10-28): OIDC sign-in via st.login with an officer
allow-list, or a clearly labelled self-asserted ID when no sign-in is configured. The basis and
the provider claims are hashed into the ledger chain.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from ddp import CoPilotSkills
from ddp.bootstrap import open_store
from ddp.identity import OIDC, SELF_ASSERTED, resolve
from ddp.store import Store

ROOT = Path(__file__).resolve().parent.parent
AUTH = {"redirect_uri": "http://localhost:8501/oauth2callback", "cookie_secret": "x" * 32,
        "client_id": "test-client", "client_secret": "test-secret",
        "server_metadata_url": "https://idp.test/.well-known/openid-configuration"}
SECRETS = {"auth": AUTH, "officers": {"Officer.One@bank.example": "PO-001"}}
SIGNED_IN = {"is_logged_in": True, "email": "officer.one@bank.example",
             "iss": "https://idp.test", "sub": "subject-123"}


# ── rules (pure) ──────────────────────────────────────────────────────────────
def test_without_sign_in_configured_the_id_is_self_asserted():
    i = resolve({}, {}, " PO-007 ")
    assert (i.officer_id, i.basis, i.can_record) == ("PO-007", SELF_ASSERTED, True)
    assert "self-asserted" in i.note and "offline" in i.note
    assert resolve({}, {}, "").can_record is False


def test_configured_but_not_signed_in_cannot_record():
    i = resolve(SECRETS, {"is_logged_in": False}, "PO-007")   # a typed ID is ignored
    assert i.basis == OIDC and not i.can_record and i.officer_id == ""


def test_signed_in_but_not_allow_listed_cannot_record():
    i = resolve(SECRETS, dict(SIGNED_IN, email="someone.else@bank.example"))
    assert not i.can_record and "allow-list" in i.note


def test_allow_listed_officer_records_under_the_roster_id_not_the_email():
    i = resolve(SECRETS, SIGNED_IN)
    assert (i.officer_id, i.basis, i.can_record) == ("PO-001", OIDC, True)
    assert i.claims["issuer"] == "https://idp.test" and len(i.claims["subject_sha256"]) == 64
    assert "bank.example" not in json.dumps(i.claims)


def test_incomplete_auth_section_is_offline_mode():
    assert resolve({"auth": dict(AUTH, client_secret="")}, SIGNED_IN, "PO-9").basis == SELF_ASSERTED


# ── ledger: the basis and claims are inside the hash chain ───────────────────
POE = [{"factor_id": "POE-007", "assessment": "triggered", "evidence": "flagged handle"}]


def _record(skills, **kw):
    return skills.alert_disposition_recorder(
        alert_id="ALERT-01", customer_ref="CUST-01", disposition="FILE",
        rationale_text="Formed suspicion on the pass-through to the flagged handle.",
        rules_cited=[], rfi_triggers=[], poe_assessment=POE, **kw)


def test_signed_in_identity_is_hashed_into_the_ledger_row():
    store = open_store(":memory:")
    i = resolve(SECRETS, SIGNED_IN)
    _record(CoPilotSkills(store), decision_maker_id=i.officer_id,
            decision_maker_basis=i.basis, decision_maker_identity=i.claims)
    row = store.query("SELECT DECISION_MAKER_ID, METADATA_JSON FROM DECISION_LEDGER")[0]
    meta = json.loads(row["METADATA_JSON"])
    assert row["DECISION_MAKER_ID"] == "PO-001" and meta["decision_maker_id_basis"] == OIDC
    assert meta["decision_maker_identity"] == i.claims
    assert store.verify_ledger_chain()["ok"]
    # Rewriting the basis after the fact breaks the chain (tamper-evident).
    store._conn.executescript("DROP TRIGGER LEDGER_NO_UPDATE;")
    store._exec("UPDATE DECISION_LEDGER SET METADATA_JSON = ?",
                (row["METADATA_JSON"].replace(OIDC, SELF_ASSERTED),))
    assert not store.verify_ledger_chain()["ok"]


def test_default_basis_is_unchanged_self_asserted():
    store = open_store(":memory:")
    _record(CoPilotSkills(store))
    meta = json.loads(store.query("SELECT METADATA_JSON FROM DECISION_LEDGER")[0]["METADATA_JSON"])
    assert meta["decision_maker_id_basis"] == SELF_ASSERTED and "decision_maker_identity" not in meta


# ── the app ───────────────────────────────────────────────────────────────────
def _app(db_path: str, secrets: dict | None = None):
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    st.cache_resource.clear()
    os.environ["DDP_DB_PATH"] = db_path
    os.environ.pop("NEBIUS_API_KEY", None)
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    for k, v in (secrets or {}).items():
        at.secrets[k] = v
    return at


NARRATIVE = ("Closed after review: the credits are family support with documents on file and "
             "no onward transfer to any flagged party.")


def _record_close(at):
    """Disposition Panel, ALERT-01: write a rationale, press Close without filing, confirm."""
    at.sidebar.radio[0].set_value("Disposition Panel").run()
    at.text_area(key="gos_text_ALERT-01").set_value(NARRATIVE).run()
    next(b for b in at.button if b.label == "Close without filing").click().run()
    for c in at.checkbox:
        if c.key == "ack_ALERT-01":
            c.check().run()
    confirm = [b for b in at.button if b.label == "Confirm and record"]
    if confirm and not confirm[0].disabled:
        confirm[0].click().run()
    assert not at.exception, at.exception


def _ledger(db_path):
    return Store(db_path).query("SELECT DECISION_MAKER_ID, METADATA_JSON FROM DECISION_LEDGER")


def test_app_offline_labels_the_typed_id_as_self_asserted():
    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / "id0.sqlite3")
        at = _app(db)
        at.run()
        at.sidebar.radio[0].set_value("Disposition Panel").run()
        at.text_input(key="po_id").set_value("PO-007").run()
        _record_close(at)
        assert not [b for b in at.sidebar.button if b.label == "Sign in"]
        assert any("no sign-in is configured" in c.value for c in at.caption)
        rows = _ledger(db)
        assert [r["DECISION_MAKER_ID"] for r in rows] == ["PO-007"]
        assert json.loads(rows[0]["METADATA_JSON"])["decision_maker_id_basis"] == SELF_ASSERTED


def test_app_signed_in_officer_records_under_the_allow_listed_id(monkeypatch):
    from ddp.ui import officer
    monkeypatch.setattr(officer, "_user", lambda: dict(SIGNED_IN))
    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / "id1.sqlite3")
        at = _app(db, SECRETS)
        at.run()
        assert [b.label for b in at.sidebar.button] == ["Sign out"]
        at.sidebar.radio[0].set_value("Disposition Panel").run()
        field = at.text_input(key="po_id_signed_in")
        assert field.value == "PO-001" and field.disabled
        _record_close(at)
        rows = _ledger(db)
        assert [r["DECISION_MAKER_ID"] for r in rows] == ["PO-001"]
        meta = json.loads(rows[0]["METADATA_JSON"])
        assert meta["decision_maker_id_basis"] == OIDC
        assert meta["decision_maker_identity"]["issuer"] == "https://idp.test"
        assert "bank.example" not in rows[0]["METADATA_JSON"]


def test_app_configured_but_signed_out_cannot_record(monkeypatch):
    from ddp.ui import officer
    monkeypatch.setattr(officer, "_user", lambda: {"is_logged_in": False})
    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / "id2.sqlite3")
        at = _app(db, SECRETS)
        at.run()
        assert [b.label for b in at.sidebar.button] == ["Sign in"]
        _record_close(at)
        assert any("Sign in (sidebar)" in w.value for w in at.warning)
        assert _ledger(db) == []
