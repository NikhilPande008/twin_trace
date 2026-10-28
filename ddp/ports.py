"""
Port interfaces — typed contracts for all external adapters.

Each port is a Protocol. Real implementations are in the modules listed below;
test fakes are small callables or dataclasses that satisfy the same protocol.

Ports:
  LLMPort              — ddp/llm.py (TokenFactoryClient, FunctionLLM)
  ComputeBackendPort   — ddp/compute/runner.py (LocalSubprocessBackend, NebiusSandboxBackend)
  EvidenceSourcePort   — T2.1 (TavilyEvidenceSource, StaticEvidenceSource for tests)
  PolicyGatePort       — T3.1 (NemotronContentSafetyGate, PassthroughPolicyGate for tests)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMPort(Protocol):
    """Any object that can complete a prompt against a model tier."""
    last_call: dict

    def complete(
        self,
        prompt: str,
        tier: str = "reasoning",
        *,
        system: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.1,
        response_format: dict | None = None,
    ) -> str: ...


@runtime_checkable
class ComputeBackendPort(Protocol):
    """Execute a program with JSON on stdin; return (stdout_json, run_ref_or_None)."""
    name: str

    def execute(self, program: bytes, input_json: str) -> tuple[str, str | None]: ...


class EvidenceSourcePort(Protocol):
    """Fetch external evidence for a case subject and return evidence-item dicts."""

    def fetch(self, subject: str, case_context: dict) -> list[dict]:
        """
        Returns a list of evidence-item dicts, each with at minimum:
            evidence_id, type, source, content_hash, content_json, provenance_json, created_at

        Returns [] when the source is unavailable; never raises for configuration errors.
        """
        ...


class PolicyGatePort(Protocol):
    """Check a text passage against named policy categories."""

    def check(self, text: str, policies: list[str]) -> dict:
        """
        Returns:
            {
                passed:   bool,
                verdicts: [{policy, violated, reason}],
                raw:      str | None    — reasoning trace length only, not content
            }

        On gate unavailability for customer-facing text: raises PolicyGateError.
        """
        ...


class PolicyGateError(RuntimeError):
    """Raised when a required policy gate is unavailable and fail-closed applies."""


class StaticEvidenceSource:
    """Test fake that returns a fixed list of evidence items."""

    def __init__(self, items: list[dict] | None = None):
        self._items = items or []

    def fetch(self, subject: str, case_context: dict) -> list[dict]:
        return list(self._items)


class PassthroughPolicyGate:
    """Test fake that passes everything. Used when the gate is not wired yet."""

    def check(self, text: str, policies: list[str]) -> dict:
        return {
            "passed": True,
            "verdicts": [{"policy": p, "violated": False, "reason": ""} for p in policies],
            "raw": None,
        }
