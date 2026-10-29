"""
No Streamlit deprecation warnings from the UI (2026-10-28).

Streamlit reports deprecated arguments (for example `use_container_width`) through its own
logger, not as a Python DeprecationWarning, so `-W error::DeprecationWarning` does not see them.
This walks every page headlessly with the proof shown and fails on any deprecation log line.
"""

from __future__ import annotations

import logging
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.test_app_smoke import PAGES, _app  # noqa: E402


class _Collect(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.lines: list[str] = []

    def emit(self, record):
        # Everything this logger emits is a deprecation; the text does not say "deprecated"
        # ("Please replace `use_container_width` with `width`").
        self.lines.append(record.getMessage())


def test_page_walk_logs_no_streamlit_deprecation():
    handler = _Collect()
    logger = logging.getLogger("streamlit.deprecation_util")
    logger.addHandler(handler)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            at = _app(str(Path(tmp) / "deprecation.sqlite3"))
            at.run()
            for page in PAGES:
                at.sidebar.radio[0].set_value(page).run()
                if page == "Disposition Panel":
                    at.toggle(key="show_proof").set_value(True).run()
                assert not at.exception, f"{page}: {at.exception}"
    finally:
        logger.removeHandler(handler)
    assert not handler.lines, handler.lines


from ddp.ui import source_files  # noqa: E402

UI_SOURCES = source_files()


def test_ui_source_has_no_use_container_width():
    """The walk misses elements that render only after a model call, and Streamlit 1.56 accepts
    `use_container_width` on st.button without logging. So the source is scanned too."""
    hits = [f"{p.name}:{i}" for p in UI_SOURCES
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
            if "use_container_width" in line]
    assert not hits, hits
