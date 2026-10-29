"""
Tier panel (T12.7): three Nemotron sizes assess the same case independently; where they disagree,
the alert is routed to the officer as contested instead of carrying one model's call.

  triage       Nemotron 3 Nano 30B      ┐
  reasoning    Nemotron 3 Super 120B    ├─ the same 11-factor prompt, the same case, in parallel
  disposition  Nemotron 3 Ultra 550B    ┘

Everything after the model calls is deterministic: each tier's recommendation comes from
CoPilotSkills.evidence_sufficiency_summary (a count rule over its factor assessments), a factor
"splits" when the tiers assess it differently, and the panel is contested when the tiers'
recommendations differ. The fact that splits the decision comes from the stress test's minimal
flip sets (calculator of record), never from a model.

Why: on the dated runs the single agent filed every contested development case (4/4) and two prompt
changes did not move that (evals/AGENT-LEAN-2026-10-28.md, AGENT-FRAMING-2026-10-28.md). The panel
changes the structure instead of the prompt. Whether disagreement actually picks out contested
cases is measured, not assumed (scripts/run_panel_eval.py).
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from .skills import POE_FACTORS

TIERS = ("triage", "reasoning", "disposition")


def panel_verdict(per_tier: dict[str, list[dict] | None], summarize) -> dict:
    """Deterministic comparison of the tiers' assessments. `per_tier` maps tier -> assessment
    list (None when that tier failed); `summarize` is evidence_sufficiency_summary."""
    done = {t: a for t, a in per_tier.items() if a is not None}
    recs = {t: summarize(a)["recommendation"] for t, a in done.items()}
    grid = []
    for fid, fname in POE_FACTORS:
        by_tier = {}
        for t, a in done.items():
            hit = next((f for f in a if f.get("factor_id") == fid), None)
            by_tier[t] = (hit or {}).get("assessment", "missing")
        grid.append({"factor_id": fid, "factor_name": fname, "by_tier": by_tier,
                     "split": len(set(by_tier.values())) > 1})
    distinct = set(recs.values())
    return {
        "tiers_answered": sorted(done), "tiers_failed": sorted(set(per_tier) - set(done)),
        "recommendations": recs,
        "contested": len(done) >= 2 and len(distinct) > 1,
        "unanimous": recs[next(iter(recs))] if len(done) >= 2 and len(distinct) == 1 else None,
        "complete": len(done) == len(per_tier),
        "split_factors": [g["factor_id"] for g in grid if g["split"]],
        "grid": grid,
    }


def splitting_fact(stress_report: dict | None) -> str | None:
    """The smallest flip set from the stress test, as one sentence (deterministic)."""
    if not stress_report:
        return None
    sets = stress_report.get("minimal_flip_sets") or []
    if not sets:
        return None
    smallest = min(sets, key=len)
    return " + ".join(h["label"] for h in smallest)


class TierPanel:
    """`make_skills()` returns a fresh CoPilotSkills with its own client per call, so the three
    tiers can run in parallel without sharing a client's per-call state."""

    def __init__(self, make_skills, tiers: tuple[str, ...] = TIERS, parallel: bool = True):
        self.make_skills = make_skills
        self.tiers = tiers
        self.parallel = parallel

    def _one(self, tier: str, case_context: dict) -> dict:
        sk = self.make_skills()
        t0 = time.monotonic()
        try:
            assessment = sk.suspicion_evaluator(case_context, tier=tier)
            call = dict(sk.last_model_call or {})
            if call.get("fallback"):
                return {"tier": tier, "assessment": None, "call": call,
                        "error": "the reply could not be parsed after one repair",
                        "seconds": round(time.monotonic() - t0, 2)}
            return {"tier": tier, "assessment": assessment, "call": call, "error": None,
                    "seconds": round(time.monotonic() - t0, 2)}
        except Exception as e:  # noqa: BLE001 — a failed tier is reported, never hidden
            return {"tier": tier, "assessment": None, "call": dict(sk.last_model_call or {}),
                    "error": f"{type(e).__name__}: {str(e)[:200]}",
                    "seconds": round(time.monotonic() - t0, 2)}

    def run(self, case_context: dict, *, stress_report: dict | None = None,
            store=None, alert_id: str | None = None) -> dict:
        if self.parallel:
            with ThreadPoolExecutor(max_workers=len(self.tiers)) as ex:
                results = list(ex.map(lambda t: self._one(t, case_context), self.tiers))
        else:
            results = [self._one(t, case_context) for t in self.tiers]
        by_tier = {r["tier"]: r for r in results}
        summarize = self.make_skills().evidence_sufficiency_summary
        verdict = panel_verdict({t: by_tier[t]["assessment"] for t in self.tiers}, summarize)
        report = {
            **verdict,
            "splitting_fact": splitting_fact(stress_report),
            "calls": {t: {k: by_tier[t]["call"].get(k) for k in
                          ("model_requested", "model_reported", "usage", "latency_s",
                           "finish_reason", "parse_failures")}
                      for t in self.tiers},
            "errors": {t: by_tier[t]["error"] for t in self.tiers if by_tier[t]["error"]},
            "seconds": {t: by_tier[t]["seconds"] for t in self.tiers},
            "assessments": {t: by_tier[t]["assessment"] for t in self.tiers},
        }
        if store is not None and alert_id:
            report["evidence_id"] = store.record_evidence(
                alert_id, "tier_panel", "tier_panel.v1",
                {k: v for k, v in report.items() if k != "seconds"},
                {"tiers": list(self.tiers), "calls": report["calls"]})
        return report
