"""Evidence-first workbench affordances render in the real Streamlit application."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _app(db_path: str):
    import streamlit as st
    from streamlit.testing.v1 import AppTest

    st.cache_resource.clear()
    os.environ["DDP_DB_PATH"] = db_path
    os.environ.pop("NEBIUS_API_KEY", None)
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)


def _main_text(at) -> str:
    return " ".join(m.value for m in at.main.markdown) + " ".join(c.value for c in at.main.caption)


def test_queue_uses_investigation_rows_and_exact_amounts():
    with tempfile.TemporaryDirectory() as tmp:
        at = _app(str(Path(tmp) / "workbench.sqlite3"))
        at.run()
        assert not at.exception, at.exception
        text = _main_text(at)
        assert "Review posture" in text
        assert "Urgency is a review aid only" in text
        assert "Alerted amount:" in text
        assert any(b.label == "Open ALERT-01" for b in at.button)


def test_case_workspace_exposes_landmarks_and_provenance_before_ai():
    with tempfile.TemporaryDirectory() as tmp:
        at = _app(str(Path(tmp) / "workbench.sqlite3"))
        at.run()
        at.sidebar.radio[0].set_value("Disposition Panel").run()
        assert not at.exception, at.exception
        text = _main_text(at)
        assert "1 · Understand alert" in text
        assert "2 · Inspect evidence" in text
        assert "Evidence status · deterministic calculation available" in text
        assert "that does not establish a recipient, purpose" in text


def test_confirmation_copy_does_not_imply_a_regulatory_submission():
    source = (ROOT / "app.py").read_text()
    assert "Confirmation records a local decision only" in source
    assert "It does not transmit an STR" in source
    assert '"tipping_off_str", "tipping_off_disclosure", "accusation_without_evidence"' in source
