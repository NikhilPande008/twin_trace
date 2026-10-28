"""
UI flow through the pipeline (T9.1): the real buttons, a scripted model endpoint, no network.

The Disposition Panel must run compute, screen, assess, draft and the policy gate through
DispositionPipeline, so every step lands on one RunTrace the officer can inspect.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FIXTURES = ROOT / "tests" / "fixtures"


class _Resp:
    status_code = 200
    text = ""

    def __init__(self, content: str):
        self._content = content

    def json(self):
        return {"model": "scripted-model", "usage": {"prompt_tokens": 10, "completion_tokens": 5},
                "choices": [{"finish_reason": "stop", "message": {"content": self._content}}]}


def _scripted_post(url, headers, json, timeout):  # noqa: A002 - matches requests.post
    prompt = json["messages"][-1]["content"]
    if "11 PO evaluation factors" in prompt:
        body = {"factors": globals()["_json"].loads((FIXTURES / "poe_assessment_valid.json").read_text())}
    elif "quality-control reviewer" in prompt:
        from ddp.skills import CHECKLIST_ITEMS
        body = {"items": [{"item_number": i + 1, "item": t, "applies": False, "note": "ok"}
                          for i, t in enumerate(CHECKLIST_ITEMS)]}
    else:  # drafting prompt
        return _Resp("I formed suspicion because the credits do not fit the declared profile.")
    return _Resp(globals()["_json"].dumps(body))


_json = json


def _app(db_path: str):
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    import ddp.llm
    st.cache_resource.clear()
    os.environ["DDP_DB_PATH"] = db_path
    os.environ["NEBIUS_API_KEY"] = "test-key"
    os.environ["TAVILY_API_KEY"] = ""
    ddp.llm._requests_post = _scripted_post
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)


def test_assess_and_draft_land_on_one_run_trace():
    with tempfile.TemporaryDirectory() as tmp:
        at = _app(str(Path(tmp) / "pipe.sqlite3"))
        at.run()
        at.sidebar.radio[0].set_value("Disposition Panel").run()
        at.toggle(key="show_proof").set_value(True).run()
        assert not at.exception, at.exception

        next(b for b in at.button if b.label == "Run 11-Factor Assessment").click().run()
        assert not at.exception, at.exception
        assert at.session_state["assessed_alert"] == "ALERT-01"

        next(b for b in at.button if "Draft with AI" in b.label).click().run()
        assert not at.exception, at.exception
        assert at.session_state["gos_alert"] == "ALERT-01"

        trace = at.session_state["run_trace_ALERT-01"]
        names = [s.name for s in trace.steps]
        for expected in ("compute", "assess", "screen", "draft", "policy_gate"):
            assert expected in names, names
        assert names.index("compute") < names.index("assess") < names.index("draft")
        assert any("Pipeline run trace" in e.label for e in at.expander)

        # the platform strip reports the calls that were made, by tier, with the reported model
        calls = at.session_state["platform_ALERT-01"]
        assert {c["tier"] for c in calls} >= {"reasoning", "disposition"}
        assert all(c["model"] == "scripted-model" for c in calls)
        strip = " ".join(m.value for m in at.main.markdown if "Platform trace" in m.value)
        assert "scripted-model" in strip and "call(s)" in strip
        assert any(e.label.startswith("Model calls for ALERT-01") for e in at.expander)
    print("  [PASS] app — assess and draft run through the pipeline on one run trace")


def test_assessment_failure_is_shown_not_swallowed():
    with tempfile.TemporaryDirectory() as tmp:
        at = _app(str(Path(tmp) / "pipe2.sqlite3"))
        import ddp.llm

        def boom(url, headers, json, timeout):  # noqa: A002
            raise ConnectionError("network down")
        ddp.llm._requests_post = boom
        at.run()
        at.sidebar.radio[0].set_value("Disposition Panel").run()
        at.toggle(key="show_proof").set_value(True).run()
        next(b for b in at.button if b.label == "Run 11-Factor Assessment").click().run()
        assert not at.exception, at.exception
        assert any("could not run" in e.value for e in at.error), [e.value for e in at.error]
        assert "poe_assessment" not in at.session_state or not at.session_state["poe_assessment"]
        trace = at.session_state["run_trace_ALERT-01"]
        assert [s.status for s in trace.steps if s.name == "assess"] == ["error"]
    print("  [PASS] app — a model outage is reported, not swallowed or crashed")


def test_proof_check_page_blocks_invented_and_records_grounded():
    with tempfile.TemporaryDirectory() as tmp:
        at = _app(str(Path(tmp) / "proof.sqlite3"))
        at.run()
        at.sidebar.radio[0].set_value("Proof Check").run()
        assert not at.exception, at.exception
        assert any("Blocked." in e.value for e in at.error), [e.value for e in at.error]
        assert any("Passes the figure check" in e.value for e in at.success)

        next(b for b in at.button if b.key == "pc_rec_invented").click().run()
        assert not at.exception, at.exception
        assert any("Ledger rows written: 0" in e.value for e in at.error)

        next(b for b in at.button if b.key == "pc_rec_grounded").click().run()
        assert any("Recorded" in e.value for e in at.success)

        # the visitor's own ledger is untouched
        from ddp.bootstrap import open_store
        assert open_store(str(Path(tmp) / "proof.sqlite3")).verify_ledger_chain()["rows"] == 0
    print("  [PASS] app — Proof Check blocks the invented total and leaves the real ledger alone")


TESTS = [test_assess_and_draft_land_on_one_run_trace, test_assessment_failure_is_shown_not_swallowed,
         test_proof_check_page_blocks_invented_and_records_grounded]

if __name__ == "__main__":
    for fn in TESTS:
        fn()


def test_cut_off_assessment_is_an_error_not_eleven_gaps():
    with tempfile.TemporaryDirectory() as tmp:
        at = _app(str(Path(tmp) / "pipe3.sqlite3"))
        import ddp.llm

        class _Cut(_Resp):
            def json(self):
                d = super().json()
                d["choices"][0]["finish_reason"] = "length"
                return d

        ddp.llm._requests_post = lambda url, headers, json, timeout: _Cut('{"factors": [')  # noqa: A002
        at.run()
        at.sidebar.radio[0].set_value("Disposition Panel").run()
        at.toggle(key="show_proof").set_value(True).run()
        next(b for b in at.button if b.label == "Run 11-Factor Assessment").click().run()
        assert not at.exception, at.exception
        errors = [e.value for e in at.error]
        assert any("could not run" in e and "cut off" in e for e in errors), errors
        assert "poe_assessment" not in at.session_state or not at.session_state["poe_assessment"]
        assert not any("lack the data" in w.value for w in at.warning)
    print("  [PASS] app — a cut-off model reply is reported, not shown as 11 data gaps")
