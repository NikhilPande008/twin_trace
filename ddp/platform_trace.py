"""
Platform trace: which Nemotron tier answered which step, and where the calculator ran.

Built only from records the code already keeps — `CoPilotSkills.call_log` entries, the agent's
`model_calls`, and the calculator run's provenance — so the strip cannot show a call that did not
happen. Token counts and seconds are call telemetry, not case figures.
"""

from __future__ import annotations

TIERS = ("triage", "reasoning", "disposition")

# Sandboxes probe, 2026-10-21: HTTP 403 from /sandboxes/v1/instances (DECISIONS.md).
SANDBOX_STATUS = ("Token Factory Sandboxes: not used — the probe was refused (HTTP 403, access not "
                  "provisioned on this account, 2026-10-21).")


def call_rows(step: str, calls: list[dict]) -> list[dict]:
    rows = []
    for c in calls:
        usage = c.get("usage") or {}
        rows.append({"step": step, "tier": c.get("tier") or "—",
                     "model": c.get("model_reported") or c.get("model_requested") or "—",
                     "tokens": (usage.get("prompt_tokens") or 0)
                     + (usage.get("completion_tokens") or 0),
                     "seconds": round(float(c.get("latency_s") or 0), 1),
                     "ok": not c.get("failed")})
    return rows


def by_tier(rows: list[dict], configured: dict[str, str]) -> list[dict]:
    """One entry per tier: the configured model, and what actually ran this session."""
    out = []
    for tier in TIERS:
        mine = [r for r in rows if r["tier"] == tier]
        reported = sorted({r["model"] for r in mine if r["model"] != "—"})
        out.append({"tier": tier, "model": ", ".join(reported) or configured.get(tier, "—"),
                    "calls": len(mine), "failed": sum(1 for r in mine if not r["ok"]),
                    "tokens": sum(r["tokens"] for r in mine),
                    "seconds": round(sum(r["seconds"] for r in mine), 1)})
    return out


def compute_line(provenance: dict) -> dict:
    backend = provenance.get("BACKEND")
    ref = provenance.get("BACKEND_RUN_REF")
    if backend == "nebius-sandbox" and ref:
        label = f"Token Factory Sandbox · run ref {ref}"
        note = ""
    else:
        label = "Local isolated subprocess (python -I, empty environment)"
        note = SANDBOX_STATUS
    return {"backend": backend, "label": label, "run_id": provenance.get("RUN_ID"),
            "code_sha256": provenance.get("CODE_SHA256", ""), "note": note}


def short_model(model_id: str) -> str:
    return model_id.split("/", 1)[-1] if model_id else "—"
