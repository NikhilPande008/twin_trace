"""
Disposition pipeline — explicit, resumable steps with a structured run trace.

Pipeline steps (see ARCHITECTURE.md §3.3):
  screen → compute → adverse_media → assess → draft → gates → human_decision → ledger

Each step is wrapped in a StepResult so the UI, the eval harness, and the video can
show per-step latency, model calls, gate results, and evidence IDs — without digging
through session_state.

The DispositionPipeline class wraps the existing CoPilotSkills and ComputeRunner
calls with NO behaviour change. The RunTrace accumulates as steps run.

Phases wired so far:
  ① screen         — CoPilotSkills.screen_request          [PROVEN]
  ② compute        — ComputeRunner.run                      [PROVEN]
  ③ adverse_media  — EvidenceSourcePort.fetch               [PROVEN offline; live run in evals/]
  ④ assess         — CoPilotSkills.suspicion_evaluator      [ASSUMED — live model]
  ⑤ draft          — CoPilotSkills.ground_of_suspicion_writer [ASSUMED]
  ⑥ gates          — deterministic + quality + policy       [deterministic PROVEN; others T1.1/T3.1]
  ⑦ human_decision — CoPilotSkills.alert_disposition_recorder [PROVEN]
  ⑧ ledger         — Store.append_decision                  [PROVEN]
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .ports import EvidenceSourcePort, PassthroughPolicyGate, PolicyGatePort, StaticEvidenceSource


@dataclass
class StepResult:
    name: str
    status: str                          # "ok" | "blocked" | "skipped" | "error"
    outputs: dict = field(default_factory=dict)
    latency_s: float = 0.0
    model_call: dict = field(default_factory=dict)
    blocked_reason: str = ""
    evidence_ids: list[str] = field(default_factory=list)


@dataclass
class RunTrace:
    alert_id: str
    steps: list[StepResult] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add(self, result: StepResult) -> None:
        self.steps.append(result)

    @property
    def blocked(self) -> bool:
        return any(s.status == "blocked" for s in self.steps)

    @property
    def total_latency_s(self) -> float:
        return round(sum(s.latency_s for s in self.steps), 3)

    @property
    def total_prompt_tokens(self) -> int:
        return sum(
            (s.model_call.get("usage") or {}).get("prompt_tokens", 0)
            for s in self.steps
        )

    @property
    def total_completion_tokens(self) -> int:
        return sum(
            (s.model_call.get("usage") or {}).get("completion_tokens", 0)
            for s in self.steps
        )

    def to_dict(self) -> dict:
        return {
            "alert_id": self.alert_id,
            "started_at": self.started_at,
            "total_latency_s": self.total_latency_s,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "steps": [
                {
                    "name": s.name,
                    "status": s.status,
                    "latency_s": s.latency_s,
                    "blocked_reason": s.blocked_reason,
                    "evidence_ids": s.evidence_ids,
                    "model_call": {
                        k: v for k, v in s.model_call.items()
                        if k in ("tier", "model_requested", "model_reported", "usage", "latency_s")
                    },
                    **{
                        k: v for k, v in s.outputs.items()
                        if k not in ("narrative", "assessments", "checklist", "gos")
                    },
                }
                for s in self.steps
            ],
        }


class DispositionPipeline:
    """
    Thin orchestrator that runs the disposition steps in order and collects a RunTrace.

    It delegates to CoPilotSkills and ComputeRunner — no new logic here. The value is:
    - a single entry point the UI and eval harness can call
    - a structured trace the video/evaluator can inspect
    - explicit step boundaries for resumability

    Usage:
        pipe = DispositionPipeline(skills, runner)
        trace, result = pipe.run_to_draft(alert_id, case_context, transactions, params)
        # PO reviews; then:
        pipe.record_decision(trace, disposition, rationale, ...)
    """

    def __init__(
        self,
        skills,                               # CoPilotSkills
        runner,                               # ComputeRunner
        evidence_source: EvidenceSourcePort | None = None,
        policy_gate: PolicyGatePort | None = None,
        store=None,                           # Store — optional; used to persist evidence rows
    ):
        self._skills = skills
        self._runner = runner
        self._evidence_source: EvidenceSourcePort = evidence_source or StaticEvidenceSource()
        self._policy_gate: PolicyGatePort = policy_gate or PassthroughPolicyGate()
        self._store = store

    # ── ① screen ─────────────────────────────────────────────────────────────

    def step_screen(self, request_text: str, trace: RunTrace) -> StepResult:
        t0 = time.monotonic()
        result = self._skills.screen_request(request_text)
        step = StepResult(
            name="screen",
            status="blocked" if not result["allowed"] else "ok",
            outputs=result,
            latency_s=round(time.monotonic() - t0, 3),
            blocked_reason=result.get("reason", "") if not result["allowed"] else "",
        )
        trace.add(step)
        return step

    # ── ② compute ────────────────────────────────────────────────────────────

    def step_compute(
        self,
        alert_id: str,
        transactions: list[dict],
        params: dict,
        trace: RunTrace,
    ) -> StepResult:
        t0 = time.monotonic()
        try:
            computed = self._runner.run(alert_id, transactions, params)
            step = StepResult(
                name="compute",
                status="ok",
                outputs={"computed": computed,
                         "run_id": computed["run_id"],
                         "fact_count": len(computed.get("facts", [])),
                         "backend": computed.get("provenance", {}).get("BACKEND", "unknown")},
                latency_s=round(time.monotonic() - t0, 3),
            )
        except Exception as e:
            step = StepResult(
                name="compute", status="error",
                outputs={}, latency_s=round(time.monotonic() - t0, 3),
                blocked_reason=str(e),
            )
        trace.add(step)
        return step

    # ── ③ adverse_media ──────────────────────────────────────────────────────

    def step_adverse_media(
        self,
        subject: str,
        case_context: dict,
        trace: RunTrace,
        alert_id: str = "",
    ) -> StepResult:
        """Calls EvidenceSourcePort.fetch and persists items when store is available (T2.1).

        The screen outcome (source.last_status, when the source reports one) is kept apart from
        the hit list: "no_results" is status ok, "no_key" is skipped, any failure is error. Each
        attempt is also stored as an `adverse_media_screen` evidence row, so the file shows that
        a screen ran and found nothing, or that it did not run.
        """
        t0 = time.monotonic()
        try:
            items = self._evidence_source.fetch(subject, case_context)
            screen = dict(getattr(self._evidence_source, "last_status", None) or
                          {"status": "ok" if items else "no_results", "completed": True})
            if self._store and alert_id:
                for item in items:
                    row = dict(item)
                    row["alert_id"] = alert_id
                    self._store.append_evidence(row)
                if screen.get("status") != "no_key":
                    screen["evidence_id"] = self._store.record_evidence(
                        alert_id, "adverse_media_screen",
                        f"{getattr(self._evidence_source, 'name', 'evidence')}:screen",
                        dict(screen, item_count=len(items)))
            if screen.get("completed"):
                status, reason = "ok", ""
            elif screen.get("status") == "no_key":
                status, reason = "skipped", "adverse-media screening not configured"
            else:
                status = "error"
                reason = f"adverse-media screen failed ({screen.get('status')}): " \
                         f"{screen.get('detail', '')}".rstrip(": ")
            step = StepResult(
                name="adverse_media",
                status=status,
                outputs={"evidence_items": items, "item_count": len(items),
                         "screen_status": screen.get("status"), "screen": screen},
                latency_s=round(time.monotonic() - t0, 3),
                blocked_reason=reason,
                evidence_ids=[i.get("evidence_id", "") for i in items if i.get("evidence_id")],
            )
        except Exception as e:
            step = StepResult(
                name="adverse_media", status="error",
                outputs={}, latency_s=round(time.monotonic() - t0, 3),
                blocked_reason=str(e),
            )
        trace.add(step)
        return step

    # ── ④ assess ─────────────────────────────────────────────────────────────

    def step_assess(self, case_context: dict, trace: RunTrace) -> StepResult:
        t0 = time.monotonic()
        try:
            assessments = self._skills.suspicion_evaluator(case_context)
            parse_failed = all(
                a.get("assessment") == "insufficient_data" and
                "could not be parsed" in a.get("evidence", "")
                for a in assessments
            )
            step = StepResult(
                name="assess",
                status="ok",
                outputs={
                    "assessments": assessments,
                    "triggered_count": sum(1 for a in assessments if a.get("assessment") == "triggered"),
                    "parse_failed": parse_failed,
                },
                latency_s=round(time.monotonic() - t0, 3),
                model_call=dict(self._skills.last_model_call),
            )
        except Exception as e:
            step = StepResult(
                name="assess", status="error",
                outputs={}, latency_s=round(time.monotonic() - t0, 3),
                blocked_reason=str(e),
            )
        trace.add(step)
        return step

    # ── ⑤ draft ──────────────────────────────────────────────────────────────

    def step_draft(
        self,
        case_context: dict,
        assessments: list[dict],
        computed: dict | None,
        trace: RunTrace,
    ) -> StepResult:
        t0 = time.monotonic()
        try:
            gos = self._skills.ground_of_suspicion_writer(case_context, assessments, computed)
            step = StepResult(
                name="draft",
                status="ok",
                outputs={
                    "narrative": gos.get("narrative", ""),
                    "quality_score": gos.get("quality_score", 0),
                    "hard_gate_passed": gos.get("hard_gate_passed", False),
                    "status": gos.get("status", "NEEDS_REVISION"),
                    "compute_run_id": gos.get("compute_run_id"),
                    "gos": gos,            # full draft result (quality, gate and citation detail)
                },
                latency_s=round(time.monotonic() - t0, 3),
                model_call=dict(self._skills.last_model_call),
            )
        except Exception as e:
            step = StepResult(
                name="draft", status="error",
                outputs={}, latency_s=round(time.monotonic() - t0, 3),
                blocked_reason=str(e),
            )
        trace.add(step)
        return step

    # ── ⑥c policy gate ───────────────────────────────────────────────────────

    def step_policy_gate(self, text: str, trace: RunTrace) -> StepResult:
        """DeterministicPolicyGate in the app; PassthroughPolicyGate (passes all) by default."""
        t0 = time.monotonic()
        try:
            verdict = self._policy_gate.check(
                text, ["tipping_off", "unnecessary_pii", "accusation_without_evidence"]
            )
            step = StepResult(
                name="policy_gate",
                status="blocked" if not verdict["passed"] else "ok",
                outputs=verdict,
                latency_s=round(time.monotonic() - t0, 3),
                blocked_reason=(
                    "; ".join(
                        v["reason"] for v in verdict.get("verdicts", []) if v.get("violated")
                    )
                    if not verdict["passed"] else ""
                ),
            )
        except Exception as e:
            step = StepResult(
                name="policy_gate", status="error",
                outputs={}, latency_s=round(time.monotonic() - t0, 3),
                blocked_reason=str(e),
            )
        trace.add(step)
        return step

    # ── convenience: run_to_draft ─────────────────────────────────────────────

    def run_to_draft(
        self,
        alert_id: str,
        case_context: dict,
        transactions: list[dict],
        params: dict,
        subject: str = "",
        screen_text: str = "",
    ) -> tuple[RunTrace, dict]:
        """
        Run steps ①–⑥ and return (trace, result_dict). Fails closed.

        The run stops at the first step whose output a later step depends on and that did not
        succeed (compute error, assess error or unparseable assessment, draft error), and
        returns blocked=True naming that step. A policy-gate block or gate error also returns
        blocked=True; the draft is still returned so the PO can see what to revise.
        An adverse-media failure does not block (nothing downstream consumes it), but it is
        reported in `adverse_media_status` and never shown as "no hits".

        result_dict keys:
            blocked, blocked_step, blocked_reason, computed, assessments, gos_result,
            adverse_media_status, run_trace_dict (JSON-serialisable summary)
        """
        trace = RunTrace(alert_id=alert_id)
        result = {"computed": None, "assessments": [], "gos_result": {},
                  "adverse_media_status": None}

        def done(step: StepResult | None = None) -> tuple[RunTrace, dict]:
            result.update(blocked=step is not None,
                          blocked_step=step.name if step else None,
                          blocked_reason=(step.blocked_reason or f"{step.name} {step.status}")
                          if step else "",
                          run_trace_dict=trace.to_dict())
            return trace, result

        # ① screen
        if screen_text:
            screen_step = self.step_screen(screen_text, trace)
            if screen_step.status == "blocked":
                return done(screen_step)

        # ② compute — the draft's evidence gate needs these facts
        compute_step = self.step_compute(alert_id, transactions, params, trace)
        if compute_step.status != "ok":
            return done(compute_step)
        result["computed"] = compute_step.outputs["computed"]

        # ③ adverse_media (returns [] without TAVILY_API_KEY; persists items when store is wired)
        am_step = self.step_adverse_media(subject or alert_id, case_context, trace,
                                          alert_id=alert_id)
        result["adverse_media_status"] = am_step.outputs.get("screen_status") or am_step.status

        # ④ assess
        assess_step = self.step_assess(case_context, trace)
        if assess_step.status == "ok" and assess_step.outputs.get("parse_failed"):
            assess_step.status = "error"
            assess_step.blocked_reason = "assessment output could not be parsed"
        if assess_step.status != "ok":
            return done(assess_step)
        result["assessments"] = assess_step.outputs.get("assessments", [])

        # ⑤ draft
        draft_step = self.step_draft(case_context, result["assessments"], result["computed"],
                                     trace)
        if draft_step.status != "ok":
            return done(draft_step)
        result["gos_result"] = draft_step.outputs
        narrative = draft_step.outputs.get("narrative", "")
        if not narrative.strip():
            draft_step.status = "error"
            draft_step.blocked_reason = "draft returned no narrative"
            return done(draft_step)

        # ⑥c policy gate
        gate_step = self.step_policy_gate(narrative, trace)
        if gate_step.status != "ok":
            return done(gate_step)
        return done()
