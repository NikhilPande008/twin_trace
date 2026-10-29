"""Per-alert session state on the Disposition Panel: calculator run, AI assessment, draft, run
trace, model calls."""

from __future__ import annotations

import streamlit as st

from .. import platform_trace as PT, verdict as V
from ..bootstrap import build_stress_tester, compute_params
from ..config import get_settings
from ..pipeline import RunTrace
from .runtime import _load_transactions, get_pipeline, get_runner, get_skills, get_store


def _platform_calls(selected: str) -> list[dict]:
    return st.session_state.setdefault(f"platform_{selected}", [])


def _calls_mark() -> int:
    return len(get_skills().call_log)


def _log_calls_since(selected: str, step: str, mark: int) -> None:
    _platform_calls(selected).extend(PT.call_rows(step, get_skills().call_log[mark:]))


def _model_label(tier: str) -> str:
    return f"{PT.short_model(get_settings().models.get(tier, ''))} ({tier} tier)"


def _readings(alert_id: str) -> dict:
    """Both deterministic stress-test readings for an alert, once per session (no model call).
    They also seed the stress-test panel inside the proof, so either choice there is ready."""
    key = f"readings_{alert_id}"
    if key not in st.session_state:
        tester = build_stress_tester(get_store(), get_skills(), get_runner())
        reps = V.readings(tester, get_store(), alert_id, compute_params(get_store(), alert_id))
        st.session_state[key] = reps
        for d, r in reps.items():
            st.session_state.setdefault(f"stress_{alert_id}_{d}", r)
    return st.session_state[key]


def _current_assessment(selected):
    if st.session_state.get("assessed_alert") == selected:
        return st.session_state.get("poe_assessment")
    return None


def _current_computed(selected):
    if st.session_state.get("computed_alert") == selected:
        return st.session_state.get("computed")
    return None


def _trace(selected) -> RunTrace:
    """One pipeline run trace per alert per session; every step the UI runs is added to it."""
    key = f"run_trace_{selected}"
    if key not in st.session_state:
        st.session_state[key] = RunTrace(alert_id=selected)
    return st.session_state[key]


def _ensure_computed(selected):
    """Run the calculator of record for this alert if not already run this session."""
    computed = _current_computed(selected)
    if computed is None:
        step = get_pipeline().step_compute(selected, _load_transactions(selected),
                                           compute_params(get_store(), selected),
                                           _trace(selected))
        if step.status != "ok":
            st.error(f"The calculator of record could not run: {step.blocked_reason}")
            st.stop()
        computed = step.outputs["computed"]
        st.session_state["computed"] = computed
        st.session_state["computed_alert"] = selected
    return computed


def _model_calls(selected):
    return [c for c in st.session_state.get(f"model_calls_{selected}", []) if c]


def _add_model_call(selected, call):
    if call:
        st.session_state.setdefault(f"model_calls_{selected}", []).append(
            {k: call.get(k) for k in ("tier", "model_requested", "model_reported", "usage", "latency_s")})


def _current_gos(selected):
    if st.session_state.get("gos_alert") == selected:
        return st.session_state.get("gos_result")
    return None
