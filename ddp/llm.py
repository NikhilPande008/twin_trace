"""
LLM access — Nebius Token Factory (OpenAI-compatible Chat Completions API).

Design rules:
- Skills request a TIER ("triage" | "reasoning" | "disposition"), never a model id.
- Every call's actual model id, token usage and latency are captured in `last_call`
  so the ledger can record exactly which NVIDIA model produced an output.
- No retries on 4xx (except 429); bounded retries on 429/5xx.
- Reasoning traces some Nemotron variants emit (<think>…</think>) are stripped from
  the returned text but kept in `last_call["reasoning_chars"]` as a length only —
  traces are NOT persisted to the ledger (they can contain case data verbatim).

[ASSUMED] endpoint path and payload follow the OpenAI Chat Completions contract that
Token Factory advertises. Verify with scripts/check_models.py before relying on it.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Callable, Protocol

from .config import Settings, get_settings

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


class LLMError(RuntimeError):
    """kind: timeout | rate_limited | server_error | client_error | network | not_configured |
    truncated (reply cut off at the output limit even after the retry; ddp/skills.py)."""

    def __init__(self, message: str, kind: str = "client_error"):
        super().__init__(message)
        self.kind = kind


def _error_kind(exc: Exception | None = None, status: int | None = None) -> str:
    if exc is not None:
        return "timeout" if "timeout" in type(exc).__name__.lower() else "network"
    if status == 429:
        return "rate_limited"
    return "server_error" if (status or 0) >= 500 else "client_error"


class LLMNotConfigured(LLMError):
    def __init__(self, message: str):
        super().__init__(message, kind="not_configured")


class LLM(Protocol):
    last_call: dict

    def complete(self, prompt: str, tier: str = "reasoning", *, system: str | None = None,
                 max_tokens: int | None = None, temperature: float = 0.1,
                 response_format: dict | None = None) -> str: ...


@dataclass
class TokenFactoryClient:
    settings: Settings = field(default_factory=get_settings)
    last_call: dict = field(default_factory=dict)
    # injectable for tests: fn(url, headers, json, timeout) -> response-like with .status_code/.json()/.text
    _post: Callable | None = None

    def model_for(self, tier: str) -> str:
        try:
            return self.settings.models[tier]
        except KeyError as e:
            raise LLMError(f"Unknown model tier '{tier}'. Known: {sorted(self.settings.models)}") from e

    def complete(self, prompt: str, tier: str = "reasoning", *, system: str | None = None,
                 max_tokens: int | None = None, temperature: float = 0.1,
                 response_format: dict | None = None) -> str:
        max_tokens = max_tokens or self.settings.max_output_tokens
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"messages": messages, "max_tokens": max_tokens, "temperature": temperature}
        # response_format: json_object by default; json_schema when STRUCTURED_OUTPUT_MODE asks
        # for it (ddp/structured.py validates locally either way and falls back on HTTP 400).
        if response_format is not None:
            payload["response_format"] = response_format
        data = self._post_chat(payload, tier)
        choice = (data.get("choices") or [{}])[0]
        raw = choice.get("message", {}).get("content") or ""
        self.last_call.update(finish_reason=choice.get("finish_reason"), max_tokens=max_tokens,
                              output_chars=len(raw))
        return self._strip_reasoning(raw)

    def chat(self, messages: list[dict], tier: str = "reasoning", *, tools: list[dict] | None = None,
             tool_choice: str | dict = "auto", max_tokens: int | None = None,
             temperature: float = 0.1) -> dict:
        """One Chat Completions turn with OpenAI-style tool calling.

        Returns the assistant message as {"role", "content", "tool_calls"}; tool_calls are
        normalised to [{"id", "name", "arguments": dict}] so callers never see transport
        quirks. [ASSUMED] Nemotron tool-call arguments may arrive as "" for no-arg tools
        (TensorRT-LLM #20503): treated as {}.
        """
        max_tokens = max_tokens or self.settings.max_output_tokens
        payload = {"messages": messages, "max_tokens": max_tokens, "temperature": temperature}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice
        data = self._post_chat(payload, tier)
        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message", {}) or {}
        self.last_call.update(finish_reason=choice.get("finish_reason"), max_tokens=max_tokens,
                              output_chars=len(msg.get("content") or ""))
        return {"role": "assistant",
                "content": self._strip_reasoning(msg.get("content") or ""),
                "tool_calls": normalise_tool_calls(msg.get("tool_calls") or [])}

    # ── transport ────────────────────────────────────────────────────────────
    def _strip_reasoning(self, raw: str) -> str:
        reasoning = _THINK_RE.findall(raw)
        self.last_call["reasoning_chars"] = sum(len(r) for r in reasoning)
        return _THINK_RE.sub("", raw).strip()

    def _post_chat(self, payload: dict, tier: str) -> dict:
        if not self.settings.api_key:
            raise LLMNotConfigured(
                "NEBIUS_API_KEY is not set. Add it to .env (see .env.example) or run in offline mode.")
        model = self.model_for(tier)
        payload = {"model": model, **payload}
        url = self.settings.base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {self.settings.api_key}",
                   "Content-Type": "application/json"}
        post = self._post or _requests_post
        delays = (0.0, 2.0, 5.0)
        last_err: str = ""
        errors: list[dict] = []          # every failed transport attempt, kept for provenance
        for attempt, delay in enumerate(delays):
            if delay:
                time.sleep(delay)
            t0 = time.monotonic()
            try:
                resp = post(url, headers=headers, json=payload, timeout=self.settings.request_timeout_s)
            except Exception as e:  # network-level failure
                last_err = f"{type(e).__name__}: {e}"
                errors.append({"attempt": attempt + 1, "kind": _error_kind(exc=e),
                               "detail": last_err[:200],
                               "latency_s": round(time.monotonic() - t0, 3)})
                continue
            latency = time.monotonic() - t0
            if resp.status_code == 200:
                data = resp.json()
                self.last_call = {
                    "provider": "nebius-token-factory",
                    "tier": tier,
                    "model_requested": model,
                    "model_reported": data.get("model", model),
                    "usage": data.get("usage", {}),
                    "latency_s": round(latency, 3),
                    "attempts": attempt + 1,
                    "transport_errors": errors,
                    "reasoning_chars": 0,
                }
                return data
            last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
            errors.append({"attempt": attempt + 1, "kind": _error_kind(status=resp.status_code),
                           "detail": f"HTTP {resp.status_code}", "latency_s": round(latency, 3)})
            if resp.status_code != 429 and resp.status_code < 500:
                break  # client error: retrying will not help
        kind = errors[-1]["kind"] if errors else "network"
        self.last_call = {"provider": "nebius-token-factory", "tier": tier,
                          "model_requested": model, "failed": True, "error_kind": kind,
                          "attempts": len(errors), "transport_errors": errors, "usage": {}}
        raise LLMError(f"Token Factory call failed for tier={tier} model={model}. {last_err}",
                       kind=kind)


class CallBudget:
    """Wraps an LLM and refuses calls past `max_calls` (public demo: one budget per browser
    session, so one visitor cannot exhaust the credits). Refusal is an LLMError of kind
    'budget' — visible, never a silent empty answer."""

    def __init__(self, llm, max_calls: int):
        self._llm, self.max_calls, self.used = llm, max_calls, 0

    @property
    def last_call(self) -> dict:
        return getattr(self._llm, "last_call", {})

    def _spend(self) -> None:
        if self.used >= self.max_calls:
            raise LLMError(f"Demo model-call budget of {self.max_calls} used for this session. "
                           "Reload the page for a new session, or run locally.", kind="budget")
        self.used += 1

    def complete(self, *args, **kwargs):
        self._spend()
        return self._llm.complete(*args, **kwargs)

    def chat(self, *args, **kwargs):
        self._spend()
        return self._llm.chat(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._llm, name)


def normalise_tool_calls(raw_calls: list) -> list[dict]:
    import json as _json
    out = []
    for i, c in enumerate(raw_calls):
        fn = (c or {}).get("function") or {}
        args = fn.get("arguments")
        if isinstance(args, str):
            args = args.strip() or "{}"
            try:
                args = _json.loads(args)
            except _json.JSONDecodeError:
                args = {"__unparseable__": args[:500]}
        out.append({"id": c.get("id") or f"call_{i}", "name": fn.get("name") or "",
                    "arguments": args if isinstance(args, dict) else {}})
    return out


@dataclass
class FunctionLLM:
    """Adapter so tests / offline demos can inject fn(prompt) -> str."""
    fn: Callable[[str], str]
    label: str = "injected-fn"
    last_call: dict = field(default_factory=dict)

    def complete(self, prompt: str, tier: str = "reasoning", **_: object) -> str:
        self.last_call = {"provider": self.label, "tier": tier,
                          "model_requested": self.label, "model_reported": self.label}
        return self.fn(prompt)


def _requests_post(url, headers, json, timeout):  # pragma: no cover - thin shim
    import requests

    return requests.post(url, headers=headers, json=json, timeout=timeout)
