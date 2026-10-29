"""Watch page (T12.6) — the offline walkthrough reopens ALERT-16 and leaves the real ledger alone."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.test_app_smoke import _app  # noqa: E402


def _text(at) -> str:
    return " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)


def test_walkthrough_reopens_the_closure_offline_on_a_scratch_copy():
    with tempfile.TemporaryDirectory() as tmp:
        at = _app(str(Path(tmp) / "watch.sqlite3"))
        at.run()
        at.sidebar.radio[0].set_value("Watch").run()
        at.button(key="watch_sim_start").click().run()
        assert not at.exception, at.exception
        at.button(key="watch_apply_REG-0001").click().run()
        assert "Reopened" not in _text(at)
        at.button(key="watch_apply_REG-0002").click().run()
        assert not at.exception, at.exception
        text = _text(at)
        assert "What changed since you decided" in text and "City General Hospital" in text
        assert "listed as a reopen trigger" in text
        # the real ledger got nothing
        from ddp.bootstrap import open_store
        assert not open_store(str(Path(tmp) / "watch.sqlite3")).query(
            "SELECT 1 FROM DECISION_LEDGER")
