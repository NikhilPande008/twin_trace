"""
Eval harness v2 (T3.2) — extended offline evaluation.

Adds to the baseline harness (eval_harness.py):
  E1. Gate catch rates — DeterministicPolicyGate must catch tipping-off and accusation
      patterns; benign narratives must pass.
  E2. Abstention precision — off-corpus queries must return []; common on-corpus queries
      must return at least one result.
  E3. Demo end-to-end — the "caught it" pipeline runs offline and the calculator gate
      blocks the wrong amount and passes the correct one.
  E4. Evidence store — Tavily mock returns items that land in EVIDENCE table.
  E5. Live model stubs — the harness records SKIP when NEBIUS_API_KEY is absent
      (numeric accuracy checks require a live run; see T1.1).

Run:
    python3 tests/eval_harness_v2.py
"""
from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path

# Ensure repo root is on the path when invoked directly
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddp.bootstrap import open_store, compute_params, seed
from ddp.compute import ComputeRunner
from ddp.compute.runner import LocalSubprocessBackend
from ddp.evidence.tavily import TavilyEvidenceSource
from ddp.gate import DeterministicPolicyGate
from ddp.pipeline import DispositionPipeline, RunTrace
from ddp.retrieval import CorpusIndex
from ddp.skills import CoPilotSkills
from ddp.store import Store

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"

results: list[dict] = []
fails = 0


def check(name: str, ok: bool | None, detail: str = "") -> None:
    global fails
    status = SKIP if ok is None else (PASS if ok else FAIL)
    results.append({"check": name, "status": status, "detail": detail})
    if status == FAIL:
        fails += 1
    symbol = {"PASS": "✓", "FAIL": "✗", "SKIP": "○"}[status]
    print(f"  {symbol} {name}" + (f": {detail}" if detail else ""))


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _store() -> Store:
    s = Store(":memory:")
    seed(s)
    return s


DEMO_TXNS = [
    {"txn_id": "V2-T1", "date": "2026-09-01", "type": "CREDIT",
     "amount_inr": 1_500_000, "channel": "CASH", "counterparty": "UNKNOWN", "is_flagged": True},
    {"txn_id": "V2-T2", "date": "2026-09-08", "type": "CREDIT",
     "amount_inr": 800_000,  "channel": "CASH", "counterparty": "UNKNOWN", "is_flagged": True},
    {"txn_id": "V2-T3", "date": "2026-09-15", "type": "DEBIT",
     "amount_inr": 1_200_000, "channel": "NEFT", "counterparty": "XYZ Corp", "is_flagged": False},
    {"txn_id": "V2-T4", "date": "2026-09-22", "type": "CREDIT",
     "amount_inr": 530_000,  "channel": "CASH", "counterparty": "UNKNOWN", "is_flagged": True},
]


# ── E1. DeterministicPolicyGate catch rates ───────────────────────────────────

def eval_gate_catch_rates() -> None:
    print("\nE1. DeterministicPolicyGate catch rates")
    gate = DeterministicPolicyGate()
    policies = ["tipping_off", "tipping_off_str", "tipping_off_disclosure", "tipping_off_customer",
                "accusation_without_evidence", "unnecessary_pii"]

    tipping_samples = [
        "An STR filed with FIU-IND is being prepared.",
        "We have filed a suspicious transaction report.",
        "This report discloses unusual activity.",
        "Reporting to FIU is imminent.",
        "We have informed the customer that an STR has been filed.",
        "The customer was told the account is under investigation.",
    ]
    for sample in tipping_samples:
        r = gate.check(sample, policies)
        check(
            f"tipping-off blocked: {sample[:40]!r}",
            not r["passed"],
            "violated" if not r["passed"] else "NOT BLOCKED",
        )

    accusation_samples = [
        "The customer is definitely engaged in money laundering.",
        "The customer is guilty of financial crime.",
    ]
    for sample in accusation_samples:
        r = gate.check(sample, policies)
        check(
            f"accusation blocked: {sample[:40]!r}",
            not r["passed"],
        )

    benign_samples = [
        "Transactions exhibit patterns consistent with layering.",
        "Source of funds cannot be determined from available documents.",
        "Further review is warranted given the volume and frequency.",
    ]
    for sample in benign_samples:
        r = gate.check(sample, policies)
        check(
            f"benign passes: {sample[:40]!r}",
            r["passed"],
        )


# ── E2. Abstention precision ──────────────────────────────────────────────────

def eval_abstention() -> None:
    print("\nE2. Abstention precision")
    store = _store()
    rows = store.corpus_rows()
    index = CorpusIndex(rows)

    off_corpus_queries = [
        "What is the VASP licensing fee?",
        "How do I set up a cryptocurrency exchange?",
        "What are the Basel III capital adequacy requirements?",
    ]
    for q in off_corpus_queries:
        results_q = index.search(q)
        check(
            f"off-corpus abstains: {q[:40]!r}",
            len(results_q) == 0,
            f"got {len(results_q)} result(s)",
        )

    on_corpus_queries = [
        "STR filing threshold",
        "cash transaction reporting",
        "beneficial ownership",
    ]
    for q in on_corpus_queries:
        results_q = index.search(q)
        check(
            f"on-corpus returns results: {q[:40]!r}",
            len(results_q) > 0,
            f"got {len(results_q)} result(s)",
        )


# ── E3. Calculator gate end-to-end ────────────────────────────────────────────

def eval_calculator_gate() -> None:
    print("\nE3. Calculator gate (demo 'caught it')")
    store = _store()
    params = compute_params(store)
    runner = ComputeRunner(store, LocalSubprocessBackend())
    skills = CoPilotSkills(store, llm=None)

    computed = runner.run("EVAL-001", DEMO_TXNS, params)
    facts = computed["facts"]
    credit_total = next(
        (f["value"] for f in facts if f["fact_id"] == "F-TOTAL-CREDIT"), None
    )
    check("calculator produced F-TOTAL-CREDIT", credit_total is not None)
    if credit_total is None:
        return

    wrong = credit_total + 500_000
    r_bad = skills.validate_gos_evidence(
        narrative=f"total deposits of ₹{int(wrong):,}",
        transactions=DEMO_TXNS,
        computed_facts=facts,
    )
    check("wrong amount blocked by gate", not r_bad["passed"])

    r_good = skills.validate_gos_evidence(
        narrative=f"total deposits of ₹{int(credit_total):,} (F-TOTAL-CREDIT)",
        transactions=DEMO_TXNS,
        computed_facts=facts,
    )
    check("correct computed fact passes gate", r_good["passed"])


# ── E4. Evidence store round-trip ─────────────────────────────────────────────

def eval_evidence_store() -> None:
    print("\nE4. Evidence store round-trip (Tavily mock)")
    store = _store()

    def fake_post(url, json=None, timeout=None):
        resp = types.SimpleNamespace()
        resp.status_code = 200
        resp.json = lambda: {"results": [
            {"title": "Fraud article", "url": "https://example.com/f1",
             "content": "Some adverse-media content about financial fraud.",
             "score": 0.85, "published_date": "2026-01-01"},
        ]}
        return resp

    src = TavilyEvidenceSource(api_key="test-key", _post=fake_post)

    class _FakeSkills:
        pass
    class _FakeRunner:
        pass

    pipe = DispositionPipeline(
        _FakeSkills(), _FakeRunner(),
        evidence_source=src,
        store=store,
    )
    trace = RunTrace(alert_id="ALT-001")
    step = pipe.step_adverse_media("Test Subject", {}, trace, alert_id="ALT-001")
    check("step status ok", step.status == "ok")
    check("1 evidence ID recorded in trace", len(step.evidence_ids) == 1)

    rows = store.evidence_for_alert("ALT-001", ev_type="adverse_media")
    check("evidence row persisted to store", len(rows) == 1)
    if rows:
        content = json.loads(rows[0]["CONTENT_JSON"])
        check("untrusted sentinel in stored content",
              content.get("[untrusted_external_content]") is True)

    # Verify no-key path leaves store empty
    store2 = _store()
    src_nokey = TavilyEvidenceSource(api_key=None)
    pipe2 = DispositionPipeline(
        _FakeSkills(), _FakeRunner(),
        evidence_source=src_nokey,
        store=store2,
    )
    trace2 = RunTrace(alert_id="ALT-002")
    pipe2.step_adverse_media("Subject", {}, trace2, alert_id="ALT-002")
    rows2 = store2.evidence_for_alert("ALT-002")
    check("no-key path leaves evidence table empty", len(rows2) == 0)


# ── E5. Live model stubs ──────────────────────────────────────────────────────

def eval_live_model_stubs() -> None:
    print("\nE5. Live model accuracy (SKIP without NEBIUS_API_KEY)")
    key = os.environ.get("NEBIUS_API_KEY")
    if not key:
        check("suspicion_evaluator numeric accuracy", None,
              "SKIP — add NEBIUS_API_KEY to run live model checks (T1.1)")
        check("GoS hallucination rate on 16 alerts", None,
              "SKIP — add NEBIUS_API_KEY to run live model checks (T1.1)")
        check("quality_score mean on 16 alerts", None,
              "SKIP — add NEBIUS_API_KEY to run live model checks (T1.1)")
    else:
        # Live path (T1.1): placeholder for when key is available
        check("suspicion_evaluator numeric accuracy", None,
              "live path not yet implemented in this harness — see T1.1")


# ── Runner ────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("  Twin Trace — Eval Harness v2 (T3.2)")
    print("=" * 60)

    eval_gate_catch_rates()
    eval_abstention()
    eval_calculator_gate()
    eval_evidence_store()
    eval_live_model_stubs()

    passes = sum(1 for r in results if r["status"] == PASS)
    skips  = sum(1 for r in results if r["status"] == SKIP)
    total  = len(results)

    print(f"\n{'=' * 60}")
    print(f"  {passes}/{total} checks passed, {fails} failed, {skips} skipped")
    if fails:
        print("\n  FAILING CHECKS:")
        for r in results:
            if r["status"] == FAIL:
                print(f"    ✗ {r['check']}: {r['detail']}")
    else:
        print("  All definitive checks PASSED.")
    print()
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
