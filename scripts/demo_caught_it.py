"""
Demo script: "Caught it" — the calculator gate stops a wrong total (T2.3).

Shows two scenarios back-to-back without touching the model:

  Case A  The GoS draft cites ₹32.5 L total cash deposits. The figure is a
          hallucination — the calculator's total is ₹28.3 L.
          → validate_gos_evidence blocks it: EVIDENCE_FAIL (wrong amount).

  Case B  The GoS draft uses the calculator's own ₹28.3 L figure (fact_id=AGG-001).
          → validate_gos_evidence passes: EVIDENCE_PASS.

Run:
    python3 -m scripts.demo_caught_it

No network, no API key needed.
"""
from __future__ import annotations

import json
import textwrap

from ddp.bootstrap import open_store, compute_params
from ddp.compute import ComputeRunner
from ddp.compute.runner import LocalSubprocessBackend as SubprocessBackend
from ddp.skills import CoPilotSkills

# ── Case transactions (synthetic) ─────────────────────────────────────────────

ALERT_ID = "DEMO-001"

TRANSACTIONS = [
    {"txn_id": "D-T1", "date": "2026-09-01", "type": "CREDIT",
     "amount_inr": 1_500_000, "channel": "CASH", "counterparty": "UNKNOWN", "is_flagged": True},
    {"txn_id": "D-T2", "date": "2026-09-08", "type": "CREDIT",
     "amount_inr": 800_000,  "channel": "CASH", "counterparty": "UNKNOWN", "is_flagged": True},
    {"txn_id": "D-T3", "date": "2026-09-15", "type": "DEBIT",
     "amount_inr": 1_200_000, "channel": "NEFT", "counterparty": "XYZ Corp", "is_flagged": False},
    {"txn_id": "D-T4", "date": "2026-09-22", "type": "CREDIT",
     "amount_inr": 530_000,  "channel": "CASH", "counterparty": "UNKNOWN", "is_flagged": True},
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def _inr(amount: float) -> str:
    return f"₹{amount / 100_000:.1f} L"


def _separator(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print("─" * 60)


def _print_result(label: str, result: dict) -> None:
    passed = result.get("passed", True)
    symbol = "✓" if passed else "✗"
    status = "PASS" if passed else "BLOCKED"
    unsupported = result.get("unsupported_claims", [])
    print(f"  {symbol} {label}: {status}")
    for v in unsupported:
        print(f"      BLOCKED: {v}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    store = open_store(":memory:")
    params = compute_params(store)
    runner = ComputeRunner(store, SubprocessBackend())
    skills = CoPilotSkills(store, llm=None)

    # Run the calculator of record
    computed = runner.run(ALERT_ID, TRANSACTIONS, params)
    facts = computed["facts"]
    # Total of all CREDIT transactions
    cash_total = next(
        (f["value"] for f in facts if f["fact_id"] == "F-TOTAL-CREDIT"),
        None,
    )
    if cash_total is None:
        print("ERROR: F-TOTAL-CREDIT not found in computed facts")
        print("Available fact IDs:", [f["fact_id"] for f in facts])
        return

    print()
    print("=" * 60)
    print("  Twin Trace — 'Caught It' Demo  (T2.3)")
    print("=" * 60)
    print()
    print("  Calculator of record ran on synthetic transactions.")
    print(f"  Actual total cash deposits: {_inr(cash_total)}")

    # ── Case A: wrong total (hallucination) ───────────────────────────────────
    wrong_amount = 3_250_000   # ₹32,50,000 — not a real transaction, not a computed fact
    wrong_str = f"₹{wrong_amount:,}"
    correct_str = f"₹{int(cash_total):,}"

    _separator("Case A — Hallucinated total (should be BLOCKED)")
    print(textwrap.dedent(f"""\
        Draft GoS:
          "The customer made total cash deposits of {wrong_str} across four
           transactions in September 2026, all below the ₹10,00,000 CTR threshold ..."
    """).rstrip())

    result_a = skills.validate_gos_evidence(
        narrative=(
            f"total cash deposits of {wrong_str} across four transactions"
        ),
        transactions=TRANSACTIONS,
        computed_facts=facts,
    )
    _print_result("Evidence gate", result_a)

    # ── Case B: correct computed fact ─────────────────────────────────────────
    _separator("Case B — Computed fact properly cited (should PASS)")
    print(textwrap.dedent(f"""\
        Draft GoS:
          "Total credits amount to {correct_str} (F-TOTAL-CREDIT,
           run {computed['run_id'][:8]}…), derived from flagged CASH CREDIT
           transactions in September 2026, each below the ₹10,00,000 CTR threshold ..."
    """).rstrip())

    result_b = skills.validate_gos_evidence(
        narrative=(
            f"Total credits amount to {correct_str} (F-TOTAL-CREDIT, "
            f"run {computed['run_id'][:8]}"
        ),
        transactions=TRANSACTIONS,
        computed_facts=facts,
    )
    _print_result("Evidence gate", result_b)

    # ── Summary ───────────────────────────────────────────────────────────────
    _separator("Summary")
    case_a_blocked = not result_a.get("passed", True)
    case_b_passed = result_b.get("passed", False)

    print(f"  Case A (wrong total)   → {'BLOCKED ✓' if case_a_blocked else 'PASSED ✗ (unexpected)'}")
    print(f"  Case B (correct total) → {'PASSED ✓' if case_b_passed else 'BLOCKED ✗ (unexpected)'}")
    print()

    if case_a_blocked and case_b_passed:
        print("  DEMO PASSED — the calculator gate correctly blocked the hallucinated")
        print("  total and let the verified fact through.")
    else:
        print("  DEMO FAILED — check validate_gos_evidence logic.")
    print()


if __name__ == "__main__":
    main()
