"""
aggregations.v1 — the calculator of record.

SELF-CONTAINED BY DESIGN: standard library only, no imports from this repo.
The exact bytes of this file are what gets executed (locally in an isolated
subprocess, or inside a Nebius Token Factory Sandbox) and what gets hashed into
CODE_SHA256 in COMPUTE_RUNS. Editing this file changes the hash of every future
run — that is intended; old runs keep the hash of the code that produced them.

Contract:
    stdin : JSON {"alert_id": str, "transactions": [...], "params": {...}}
    stdout: JSON {"program": "aggregations.v1", "facts": [...], "warnings": [...]}

Each fact is {fact_id, label, value, unit, derivation, txn_ids}. Numbers in a
Ground of Suspicion narrative must be traceable to a transaction amount or to a
fact produced here (see ddp.skills.validate_gos_evidence).

Regulatory parameters (thresholds) are INPUTS, not constants in this file, so the
corpus — not the code — is the source of truth and the rule ID travels with them.
"""

import json
import sys
from collections import defaultdict
from datetime import date

PROGRAM = "aggregations.v1"


def _d(s):
    try:
        return date.fromisoformat(str(s)[:10])
    except Exception:
        return None


def _amt(t):
    try:
        return int(round(float(t.get("amount_inr") or 0)))
    except Exception:
        return 0


def compute(payload):
    txns = payload.get("transactions") or []
    params = payload.get("params") or {}
    facts, warnings = [], []

    def fact(fid, label, value, unit, derivation, ids):
        facts.append({"fact_id": fid, "label": label, "value": value, "unit": unit,
                      "derivation": derivation, "txn_ids": sorted(set(i for i in ids if i))})

    credits = [t for t in txns if t.get("type") == "CREDIT"]
    debits = [t for t in txns if t.get("type") == "DEBIT"]
    c_total = sum(_amt(t) for t in credits)
    d_total = sum(_amt(t) for t in debits)

    fact("F-TOTAL-CREDIT", "Total credits", c_total, "INR",
         "sum(amount_inr) over CREDIT transactions", [t.get("txn_id") for t in credits])
    fact("F-TOTAL-DEBIT", "Total debits", d_total, "INR",
         "sum(amount_inr) over DEBIT transactions", [t.get("txn_id") for t in debits])
    fact("F-TXN-COUNT", "Transaction count", len(txns), "count",
         "count of transactions in the case record", [t.get("txn_id") for t in txns])

    # ── pass-through ratio ─────────────────────────────────────────────────
    if c_total > 0:
        ratio_bp = int(round(d_total * 10000 / c_total))  # basis points, integer => exact
        fact("F-PASSTHROUGH-BP", "Debits as share of credits", ratio_bp, "basis_points",
             "round(total_debit * 10000 / total_credit)",
             [t.get("txn_id") for t in txns])
    dates = sorted(filter(None, (_d(t.get("date")) for t in txns)))
    if dates:
        fact("F-WINDOW-DAYS", "Observed window (days, inclusive)", (dates[-1] - dates[0]).days + 1,
             "days", "last txn date - first txn date + 1", [t.get("txn_id") for t in txns])

    # ── flagged counterparty exposure ──────────────────────────────────────
    flagged = [t for t in txns if t.get("is_flagged")]
    if flagged:
        f_total = sum(_amt(t) for t in flagged)
        fact("F-FLAGGED-AMOUNT", "Amount involving flagged counterparties", f_total, "INR",
             "sum(amount_inr) where is_flagged", [t.get("txn_id") for t in flagged])
        if c_total > 0:
            fact("F-FLAGGED-SHARE-BP", "Flagged outflow as share of credits",
                 int(round(sum(_amt(t) for t in flagged if t.get("type") == "DEBIT") * 10000 / c_total)),
                 "basis_points", "round(flagged DEBIT total * 10000 / total_credit)",
                 [t.get("txn_id") for t in flagged])
            f_in = [t for t in flagged if t.get("type") == "CREDIT"]
            fact("F-FLAGGED-INFLOW-SHARE-BP", "Flagged inflow as share of credits",
                 int(round(sum(_amt(t) for t in f_in) * 10000 / c_total)),
                 "basis_points", "round(flagged CREDIT total * 10000 / total_credit)",
                 [t.get("txn_id") for t in f_in])

    # ── credits against declared income (param comes from the KYC profile) ──
    inc = params.get("declared_monthly_income_inr") or {}
    income = inc.get("amount_inr")
    if income and c_total > 0:
        fact("F-DECLARED-INCOME", "Declared monthly income (from KYC profile)",
             int(income), "INR",
             f"declared_monthly_income_inr parameter (source: {inc.get('source', 'UNSPECIFIED')})",
             [])
        fact("F-INCOME-MULTIPLE-X10", "Credits as a multiple of declared monthly income (x10)",
             int(round(c_total * 10 / income)), "tenths",
             f"round(total_credit * 10 / {income}) (declared monthly income, source: "
             f"{inc.get('source', 'UNSPECIFIED')})", [t.get("txn_id") for t in credits])

    ann = params.get("declared_annual_income_inr") or {}
    if ann.get("amount_inr"):
        fact("F-DECLARED-ANNUAL-INCOME", "Declared annual income (from KYC profile)",
             int(ann["amount_inr"]), "INR",
             f"declared_annual_income_inr parameter (source: {ann.get('source', 'UNSPECIFIED')})",
             [])

    # ── fan-in / fan-out ───────────────────────────────────────────────────
    srcs = {t.get("counterparty") for t in credits if t.get("counterparty")}
    dsts = {t.get("counterparty") for t in debits if t.get("counterparty")}
    fact("F-FAN-IN", "Distinct credit counterparties", len(srcs), "count",
         "count(distinct counterparty) over CREDIT", [t.get("txn_id") for t in credits])
    fact("F-FAN-OUT", "Distinct debit counterparties", len(dsts), "count",
         "count(distinct counterparty) over DEBIT", [t.get("txn_id") for t in debits])

    # ── cash: monthly aggregation against the reporting threshold ──────────
    ctr = params.get("cash_threshold") or {}
    threshold = ctr.get("amount_inr")
    rule_id = ctr.get("rule_id", "UNSPECIFIED")
    cash = [t for t in txns if str(t.get("channel") or "").upper() == "CASH"]
    if cash:
        by_month = defaultdict(list)
        for t in cash:
            d = _d(t.get("date"))
            if d:
                by_month[d.strftime("%Y-%m")].append(t)
        for month in sorted(by_month):
            rows = by_month[month]
            m_credit = sum(_amt(t) for t in rows if t.get("type") == "CREDIT")
            m_debit = sum(_amt(t) for t in rows if t.get("type") == "DEBIT")
            ids = [t.get("txn_id") for t in rows]
            fact(f"F-CASH-{month}-CREDIT", f"Cash credits in {month}", m_credit, "INR",
                 "sum(amount_inr) over CASH CREDIT in calendar month", ids)
            fact(f"F-CASH-{month}-DEBIT", f"Cash debits in {month}", m_debit, "INR",
                 "sum(amount_inr) over CASH DEBIT in calendar month", ids)
            if threshold:
                individually_below = all(_amt(t) < threshold for t in rows)
                fact(f"F-CASH-{month}-ABOVE-THRESHOLD",
                     f"Cash credits in {month} exceed threshold ({rule_id})",
                     1 if m_credit > threshold else 0, "bool",
                     f"monthly CASH CREDIT total > {threshold} (param from {rule_id})", ids)
                fact(f"F-CASH-{month}-ALL-BELOW",
                     f"Every cash transaction in {month} individually below threshold",
                     1 if individually_below else 0, "bool",
                     f"all(amount_inr < {threshold}) over CASH in month", ids)
        if not threshold:
            warnings.append("cash_threshold not supplied: monthly totals computed, threshold test skipped")

    # ── near-threshold clustering (structuring signal) ─────────────────────
    band = params.get("near_threshold_band") or {}
    b_hi, b_lo = band.get("upper_inr"), band.get("lower_inr")
    if b_hi and b_lo is not None:
        near = [t for t in cash if b_lo <= _amt(t) < b_hi]
        fact("F-NEAR-THRESHOLD-COUNT", f"Cash txns in [{b_lo}, {b_hi})", len(near), "count",
             "count of CASH txns with lower <= amount < upper", [t.get("txn_id") for t in near])

    missing_ids = sum(1 for t in txns if not t.get("txn_id"))
    if missing_ids:
        warnings.append(f"{missing_ids} transaction(s) without txn_id cannot be cited")
    return {"program": PROGRAM, "alert_id": payload.get("alert_id"),
            "facts": facts, "warnings": warnings}


if __name__ == "__main__":
    out = compute(json.loads(sys.stdin.read() or "{}"))
    sys.stdout.write(json.dumps(out, sort_keys=True))
