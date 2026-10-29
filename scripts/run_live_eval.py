"""
One-command evaluation over the 16 seeded alerts, written to evals/REPORT-<date>-<mode>.md.

    python -m scripts.run_live_eval --mock        # offline: exercises the harness, no model
    python -m scripts.run_live_eval               # live: needs NEBIUS_API_KEY (Token Factory)
    python -m scripts.run_live_eval --alerts ALERT-01,ALERT-16 --skip-agent
    python -m scripts.run_live_eval --deterministic   # section 1 only: no model, no key

Sections
  1. Calculator + stress test (deterministic, both modes): signal verdict per alert vs the gold
     disposition, flip-set size, branch runs. The signals are product heuristics: agreement with
     gold is reported as a count, not an accuracy claim.
  2. Structured output (live): 11-factor assessment schema validity and repair retries.
  3. Agentic investigator (live): status, disposition vs gold, rejected submissions, tokens,
     latency.

In --mock mode sections 2 and 3 run against a scripted model so the harness itself is tested;
the report is stamped MOCK and its numbers say nothing about Nemotron. --deterministic runs
section 1 alone (no model call) and writes REPORT-<date>-deterministic.*, which is evidence
for section 1 only. Every report records the seed's SHA-256 (ddp.evidence_view.seed_fingerprint).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ddp.agent import SYSTEM as AGENT_SYSTEM, Investigator  # noqa: E402
from ddp.bootstrap import compute_params, open_store  # noqa: E402
from ddp.compute import ComputeRunner, backend_from_name  # noqa: E402
from ddp.config import get_settings  # noqa: E402
from ddp.evidence_view import seed_fingerprint  # noqa: E402
from ddp.llm import TokenFactoryClient  # noqa: E402
from ddp.skills import CoPilotSkills  # noqa: E402
from ddp.stress import StressTester  # noqa: E402
from ddp.structured import POE_IDS  # noqa: E402


def assessment_outcome(model_call: dict | None) -> str:
    """success | repaired | fallback, from CoPilotSkills.last_model_call after
    suspicion_evaluator returned. A fallback is 11 placeholder records, never a success."""
    mc = model_call or {}
    if mc.get("fallback") or mc.get("parse_failures", 0) >= 2:
        return "fallback"
    return "repaired" if mc.get("parse_failures") else "success"


class MockLLM:
    """Scripted model for --mock: follows the ideal tool path, cites only what it was given."""

    def __init__(self):
        self.last_call = {}

    def complete(self, prompt, tier="reasoning", **_):
        self.last_call = {"provider": "mock", "tier": tier, "usage": {}}
        return json.dumps({"factors": [
            {"factor_id": f, "factor_name": f, "assessment": "insufficient_data",
             "evidence": "mock", "evidence_txn_ids": [], "rules_cited": []} for f in POE_IDS]})

    def chat(self, messages, tier, tools=None, **_):
        self.last_call = {"provider": "mock", "tier": tier,
                          "usage": {"prompt_tokens": 0, "completion_tokens": 0}}
        done = {m.get("tool_call_id") for m in messages if m["role"] == "tool"}
        if "c-calc" not in done:
            return _turn([("c-case", "get_case", {}), ("c-calc", "run_calculator", {})])
        calc = next(json.loads(m["content"]) for m in messages if m.get("tool_call_id") == "c-calc")
        facts = {f["fact_id"]: f["value"] for f in calc["facts"]}
        disp = "FILE" if facts.get("F-FLAGGED-SHARE-BP", 0) >= 2500 else "NOT_FILE"
        if "c-stress" not in done:
            return _turn([("c-stress", "stress_test", {"disposition": disp})])
        return _turn([("c-submit", "submit_assessment", {
            "disposition": disp,
            "rationale": ("Mock rationale for the harness self-test: the disposition follows the "
                          "flagged outflow share computed by the calculator of record, and the "
                          "stress test was run before submitting."),
            "cited_fact_ids": sorted(facts)[:2], "cited_txn_ids": [], "cited_rule_ids": []})])


def _turn(calls):
    return {"role": "assistant", "content": "",
            "tool_calls": [{"id": i, "name": n, "arguments": a} for i, n, a in calls]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--deterministic", action="store_true",
                    help="calculator and stress test only: no model call, no key needed")
    ap.add_argument("--alerts", default="")
    ap.add_argument("--skip-agent", action="store_true")
    ap.add_argument("--skip-assessment", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "evals"))
    ap.add_argument("--tavily", action="store_true",
                    help="inject the Tavily adapter into the agent (needs TAVILY_API_KEY)")
    args = ap.parse_args(argv)

    settings = get_settings()
    if args.deterministic:
        args.skip_assessment = args.skip_agent = True
    if not args.mock and not args.deterministic and not settings.llm_configured:
        print("NEBIUS_API_KEY not set. Use --mock to exercise the harness offline.")
        return 2
    store = open_store(":memory:")
    runner = ComputeRunner(store, backend_from_name(settings.compute_backend))
    llm = MockLLM() if args.mock or args.deterministic else TokenFactoryClient(settings)
    skills = CoPilotSkills(store, llm=llm)
    tester = StressTester(runner, store)
    evidence_source = None
    if args.tavily:
        from ddp.evidence.tavily import TavilyEvidenceSource
        evidence_source = TavilyEvidenceSource(settings.tavily_api_key)
    tavily_state = ("injected" if evidence_source and evidence_source.api_key else
                    "requested but TAVILY_API_KEY not set" if args.tavily else "not injected")
    alerts = [a for a in store.query("SELECT * FROM ALERTS ORDER BY ALERT_ID")
              if not args.alerts or a["ALERT_ID"] in args.alerts.split(",")]
    started = datetime.now(timezone.utc)
    rows = []
    for a in alerts:
        aid, gold = a["ALERT_ID"], a["GOLD_DISPOSITION"]
        txns, params = store.transactions_for(aid), compute_params(store, aid)
        row = {"alert_id": aid, "type": a["ALERT_TYPE"], "gold": gold}
        st = tester.run(aid, txns, params, disposition=gold if gold in ("FILE", "NOT_FILE")
                        else None)
        row.update(verdict=st["base"]["verdict"], flip=st["smallest_flip_size"],
                   branches=st["search"]["runs_used"], backend=st["base"].get("backend_run_ref"))
        if not args.skip_assessment:
            t0 = time.monotonic()
            try:
                out = skills.suspicion_evaluator({"customer_kyc": a["CUSTOMER_PROFILE"],
                                                  "transactions": txns,
                                                  "signal_tags": json.loads(a["RFI_TRIGGERS"] or "[]"),
                                                  "alert_narrative": a["ALERT_NARRATIVE"]})
                mc = skills.last_model_call or {}
                row["assess"] = assessment_outcome(mc)
                row["assess_mode"] = mc.get("structured_mode")
                row["assess_parse_failures"] = mc.get("parse_failures", 0)
                row["assess_tokens_all_attempts"] = (mc.get("usage_all_attempts") or {}).get(
                    "total_tokens")
                row["assess_truncated"] = bool(mc.get("truncated"))
                row["assess_unknown_txn_citations"] = mc.get("factors_with_unknown_txn_ids", 0)
                # Audit trail for the classification: factor verdicts only, no evidence text.
                row["assess_factors"] = {f.get("factor_id"): f.get("assessment") for f in out}
            except Exception as e:  # noqa: BLE001
                row["assess"] = "failed"
                row["assess_error"] = str(e)[:120]
            row["assess_s"] = round(time.monotonic() - t0, 2)
        if not args.skip_agent:
            inv = Investigator(llm, store, skills, runner, lambda x: compute_params(store, x),
                               evidence_source=evidence_source)
            t = inv.investigate(aid)
            row.update(agent=t["status"],
                       agent_disp=(t.get("assessment") or {}).get("disposition"),
                       agent_steps=len(t["steps"]), agent_rejections=t.get("rejections", 0),
                       agent_tokens=sum((t.get("tokens") or {}).values()),
                       agent_s=t.get("latency_s"))
        rows.append(row)
        print(json.dumps(row, default=str))

    mode = "mock" if args.mock else ("deterministic" if args.deterministic else "live")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = started.strftime("%Y-%m-%d")
    (out / f"REPORT-{stamp}-{mode}.json").write_text(json.dumps(
        {"mode": mode, "started_utc": started.isoformat(), "seed_sha256": seed_fingerprint(),
         "agent_prompt_sha256": hashlib.sha256(AGENT_SYSTEM.encode()).hexdigest(),
         "stress_engine_sha256": hashlib.sha256(
             (ROOT / "ddp" / "stress" / "engine.py").read_bytes()).hexdigest(),
         "models": settings.models if mode != "deterministic" else {},
         "tavily": tavily_state,
         "base_url": settings.base_url, "compute_backend": settings.compute_backend,
         "rows": rows}, indent=1, default=str))
    (out / f"REPORT-{stamp}-{mode}.md").write_text(
        render(rows, mode, started, settings, tavily_state))
    print(f"\nwrote {out}/REPORT-{stamp}-{mode}.md")
    return 0


def render(rows, mode, started, settings, tavily_state="not injected") -> str:
    n = len(rows)
    hi_file = sum(1 for r in rows if r["gold"] == "FILE" and r["verdict"] == "HIGH")
    gold_file = sum(1 for r in rows if r["gold"] == "FILE")
    lines = [f"# Evaluation report — {started.strftime('%Y-%m-%d %H:%M UTC')} ({mode.upper()})", ""]
    if mode == "mock":
        lines += ["> **MOCK RUN.** Model calls were scripted to test the harness. Sections 2–3 "
                  "say nothing about Nemotron. Do not quote these numbers.", ""]
    if mode == "deterministic":
        lines += ["> **DETERMINISTIC RUN.** Calculator and stress test only; no model was called.",
                  ""]
    lines += [f"- Alerts: {n} (all synthetic) · compute backend: `{settings.compute_backend}`",
              f"- Seed SHA-256: `{seed_fingerprint()}`"]
    if mode != "deterministic":
        lines += [f"- Models: `{json.dumps(settings.models)}`",
                  f"- Tavily adapter in the agent: **{tavily_state}**"]
    lines += ["",
              "## 1. Calculator and stress test (deterministic)", "",
              f"Gold FILE alerts whose calculator signals are HIGH: **{hi_file} of {gold_file}**. "
              "The rest rest on evidence the calculator does not see (PEP status, narrative, "
              "RFI responses); the stress test says so in its notes.", "",
              "| alert | type | gold | signals | smallest flip set | branch runs |",
              "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['alert_id']} | {r['type']} | {r['gold']} | {r['verdict']} | "
                     f"{r['flip'] if r['flip'] is not None else '—'} | {r['branches']} |")
    if any("assess" in r for r in rows):
        count = {k: sum(1 for r in rows if r.get("assess") == k)
                 for k in ("success", "repaired", "fallback", "failed")}
        lines += ["", "## 2. Structured output — 11-factor assessment", "",
                  f"Model output schema-valid: **{count['success'] + count['repaired']} of {n}** "
                  f"(first try {count['success']}, after one repair {count['repaired']}). "
                  f"Fallback placeholders (not model output): {count['fallback']}. "
                  f"Errors: {count['failed']}.", "",
                  "| alert | outcome | parse failures | mode | seconds |", "|---|---|---|---|---|"]
        lines += [f"| {r['alert_id']} | {r.get('assess')} | {r.get('assess_parse_failures', '—')} | "
                  f"{r.get('assess_mode') or '—'} | {r.get('assess_s')} |" for r in rows]
    if any("agent" in r for r in rows):
        sub = [r for r in rows if r.get("agent") == "submitted"]
        agree = sum(1 for r in sub if r["agent_disp"] == r["gold"])
        lines += ["", "## 3. Agentic investigator", "",
                  f"Accepted submissions: **{len(sub)} of {n}** · agreeing with gold: "
                  f"**{agree} of {len(sub)}** · rejected submissions (caught by validation): "
                  f"**{sum(r.get('agent_rejections', 0) for r in rows)}**.", "",
                  "| alert | gold | status | agent | tool calls | rejected | tokens | seconds |",
                  "|---|---|---|---|---|---|---|---|"]
        lines += [f"| {r['alert_id']} | {r['gold']} | {r['agent']} | {r.get('agent_disp') or '—'} "
                  f"| {r['agent_steps']} | {r['agent_rejections']} | {r['agent_tokens']} | "
                  f"{r['agent_s']} |" for r in rows]
    flag = {"mock": " --mock", "deterministic": " --deterministic"}.get(mode, "")
    lines += ["", "Reproduce: `python -m scripts.run_live_eval" + flag
              + "`. Raw rows in the matching .json file.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
