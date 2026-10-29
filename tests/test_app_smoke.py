"""
Headless UI smoke test (streamlit.testing.AppTest): every page renders without an
exception on a fresh seeded database, with NO API key (offline mode), and the
calculator of record runs from the Disposition Panel.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PAGES = ["Alert Queue", "Twin Cases", "Proof Check", "Disposition Panel", "Decision Ledger", "Watch", "Dashboard", "Measured Results", "Regulatory Reference"]


def _app(db_path: str):
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    st.cache_resource.clear()  # runtime is cached per process; each test gets a fresh DB
    os.environ["DDP_DB_PATH"] = db_path
    os.environ.pop("NEBIUS_API_KEY", None)
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)


def _proof_on(at):
    at.toggle(key="show_proof").set_value(True).run()


def test_all_pages_render_offline():
    with tempfile.TemporaryDirectory() as tmp:
        at = _app(str(Path(tmp) / "smoke.sqlite3"))
        at.run()
        assert not at.exception, at.exception
        for page in PAGES:
            at.sidebar.radio[0].set_value(page).run()
            assert not at.exception, f"{page}: {at.exception}"
    print(f"  [PASS] app — all {len(PAGES)} pages render offline without exceptions")


def test_calculator_runs_from_disposition_panel():
    with tempfile.TemporaryDirectory() as tmp:
        at = _app(str(Path(tmp) / "smoke.sqlite3"))
        at.run()
        at.sidebar.radio[0].set_value("Disposition Panel").run()
        _proof_on(at)
        # The Signal Brief runs the calculator on first view (its totals are calculator facts),
        # so the button may already read "Recompute".
        btn = next(b for b in at.button if b.label in ("Compute", "↻ Recompute"))
        btn.click().run()
        assert not at.exception, at.exception
        text = " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)
        assert "F-TOTAL-CREDIT" in text and "backend **local**" in text, text[:500]
    print("  [PASS] app — calculator of record runs from the Disposition Panel with provenance")


def test_stress_test_runs_from_disposition_panel():
    with tempfile.TemporaryDirectory() as tmp:
        at = _app(str(Path(tmp) / "smoke.sqlite3"))
        at.run()
        at.sidebar.radio[0].set_value("Disposition Panel").run()
        _proof_on(at)
        next(b for b in at.button if b.label == "Run stress test").click().run()
        assert not at.exception, at.exception
        text = " ".join(m.value for m in at.markdown)
        assert "What would lower the modeled level" in text and "I4C-flagged" in text, text[:800]
    print("  [PASS] app — decision stress test runs offline from the Disposition Panel")


def _md(at) -> str:
    return " ".join(m.value for m in at.main.markdown)


def test_verdict_card_leads_and_proof_is_collapsed():
    with tempfile.TemporaryDirectory() as tmp:
        at = _app(str(Path(tmp) / "smoke.sqlite3"))
        at.run()
        at.sidebar.radio[0].set_value("Disposition Panel").run()
        assert not at.exception, at.exception
        text = _md(at)
        # the header shows the exact alerted amount, Indian grouping, never a rounded lakh figure
        assert "Alerted amount ₹3,45,000 ·" in text and "(3.5L)" not in text
        assert "What the decision rests on" in text
        assert "This FILE rests on exactly one fact." in text           # if you file
        assert "registry flag on UPI handle C (I4C-flagged) is correct" in text
        assert "This closure goes against HIGH calculator signals." in text  # if you close
        # the proof is present but collapsed: no evidence, hashes or AI section until toggled
        assert at.toggle(key="show_proof").value is False
        assert "Calculator of record" not in text and "AI suspicion assessment" not in text
        assert not [b for b in at.button if b.label in ("Run stress test",
                                                        "Run 11-Factor Assessment")]
        _proof_on(at)
        text = _md(at)
        assert "Calculator of record" in text and "AI suspicion assessment" in text
        # Signal Brief tiles show the calculator's exact totals, not rounded lakh values
        tiles = {m.label: m.value for m in at.metric}
        assert tiles["Credits"] == "₹3,45,000" and tiles["Debits"] == "₹3,40,700", tiles
        # the card comes before the proof in reading order
        assert text.index("What the decision rests on") < text.index("Calculator of record")
    print("  [PASS] app — verdict card leads; the proof is one toggle away")


def test_platform_strip_offline_is_honest():
    with tempfile.TemporaryDirectory() as tmp:
        at = _app(str(Path(tmp) / "smoke.sqlite3"))
        at.run()
        at.sidebar.radio[0].set_value("Disposition Panel").run()
        strip = " ".join(m.value for m in at.main.markdown if "Platform trace" in m.value)
        assert strip.count("not called yet") == 3
        assert "Local isolated subprocess" in strip and "HTTP 403" in strip
        assert "Token Factory not configured" in strip
        assert "Sandbox ·" not in strip
    print("  [PASS] app — platform strip shows no calls offline and the real compute backend")


def test_alert16_closure_reading_needs_no_radio_flip():
    with tempfile.TemporaryDirectory() as tmp:
        at = _app(str(Path(tmp) / "smoke.sqlite3"))
        at.run()
        at.session_state["selected_alert"] = "ALERT-16"
        at.sidebar.radio[0].set_value("Disposition Panel").run()
        text = _md(at)
        assert "This closure comes with reopen conditions." in text
        assert "Brother (KYC-linked family) reported to a registry" in text
        assert "Sister" not in text.split("If you close")[1].split("ddp-foot")[0]
    print("  [PASS] app — ALERT-16's reopen conditions show without touching the radio")


def test_twin_cases_page_shows_the_fork():
    with tempfile.TemporaryDirectory() as tmp:
        at = _app(str(Path(tmp) / "smoke.sqlite3"))
        at.run()
        at.sidebar.radio[0].set_value("Twin Cases").run()
        assert not at.exception, at.exception
        text = _md(at)
        assert "ALERT-01" in text and "ALERT-16" in text
        assert "registry flag on UPI handle C (I4C-flagged) is correct" in text   # load-bearing
        assert "Brother (KYC-linked family) reported to a registry" in text      # reopen trigger
        assert "the difference" in text and "Material flow with a flagged counterparty" in text
        assert "₹3,45,000" in text
        captions = " ".join(c.value for c in at.caption)
        assert "does not choose them" in captions
    print("  [PASS] app — Twin Cases shows both alerts and what each decision rests on")


def test_alert_queue_names_the_user_and_cited_stakes():
    with tempfile.TemporaryDirectory() as tmp:
        at = _app(str(Path(tmp) / "smoke.sqlite3"))
        at.run()
        assert not at.exception, at.exception
        text = _md(at)
        assert "Who this is for" in text and "Principal Officer" in text
        for rid in ("STR-002", "INS-001", "INS-002", "SB-003"):
            assert f"<code>{rid}</code>" in text, rid
        assert "NEEDS-VERIFICATION" not in text.split("What is at stake")[1].split("ddp-foot")[0]
    print("  [PASS] app — Alert Queue names the user and the cited stakes")


TESTS = [test_alert_queue_names_the_user_and_cited_stakes, test_all_pages_render_offline, test_calculator_runs_from_disposition_panel,
         test_stress_test_runs_from_disposition_panel, test_verdict_card_leads_and_proof_is_collapsed,
         test_alert16_closure_reading_needs_no_radio_flip, test_twin_cases_page_shows_the_fork]

if __name__ == "__main__":
    print("Running headless app smoke tests...\n")
    passed = failed = 0
    for fn in TESTS:
        try:
            fn()
            passed += 1
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  [FAIL] {fn.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{passed}/{passed + failed} tests passed.")
    if failed:
        sys.exit(1)
