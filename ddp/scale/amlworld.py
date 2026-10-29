"""
Adapter for the IBM/ETH synthetic AML transaction datasets (T12.15): Altman et al., "Realistic
Synthetic Financial Transactions for Anti-Money Laundering Models", NeurIPS 2023 Datasets and
Benchmarks (arXiv 2306.16424).

Not downloaded (the human is asked first). The column layout below is ASSUMED from the paper's
public dataset files (HI-/LI-Small/Medium/Large "_Trans.csv"): Timestamp, From Bank, Account,
To Bank, Account, Amount Received, Receiving Currency, Amount Paid, Payment Currency,
Payment Format, Is Laundering. `load_accounts` checks the header and refuses a different one.

What the scale test can show, and what it cannot:
  * it CAN exercise the calculator of record and the signal rules on many labelled histories,
    and count how signal levels relate to the dataset's laundering labels;
  * it CANNOT say anything about Indian banking or UPI: the amounts are in the dataset's own
    currencies (carried in `amount_inr` only because that is the calculator's field name), there is
    no registry flag (is_flagged is always False) and no declared income. The report says so.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

EXPECTED_HEADER = ["Timestamp", "From Bank", "Account", "To Bank", "Account", "Amount Received",
                   "Receiving Currency", "Amount Paid", "Payment Currency", "Payment Format",
                   "Is Laundering"]


def _date(ts: str) -> str:
    """'2022/09/01 00:20' -> '2022-09-01'."""
    return ts.strip()[:10].replace("/", "-")


def load_accounts(path: str | Path, *, max_rows: int | None = None,
                  min_txns: int = 2) -> dict[str, dict]:
    """Group transactions by account into the calculator's shape.

    Returns {account_key: {"transactions": [...], "laundering": bool, "currencies": set}}, where
    each transaction is a CREDIT (money in) or DEBIT (money out) from that account's view.
    """
    accounts: dict[str, dict] = defaultdict(lambda: {"transactions": [], "laundering": False,
                                                     "currencies": set()})
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        if [h.strip() for h in header] != EXPECTED_HEADER:
            raise ValueError(f"unexpected header: {header}")
        for n, row in enumerate(reader):
            if max_rows is not None and n >= max_rows:
                break
            ts, fb, fa, tb, ta, amt_r, cur_r, amt_p, cur_p, fmt, lab = row
            src, dst = f"{fb.strip()}:{fa.strip()}", f"{tb.strip()}:{ta.strip()}"
            if src == dst:
                continue            # reinvestment between an account and itself
            laundering = lab.strip() == "1"
            date = _date(ts)
            for acct, kind, cp, amt, cur in ((src, "DEBIT", dst, amt_p, cur_p),
                                             (dst, "CREDIT", src, amt_r, cur_r)):
                a = accounts[acct]
                a["transactions"].append({
                    "txn_id": f"R{n}-{kind[0]}", "date": date, "type": kind,
                    "amount_inr": round(float(amt), 2), "channel": fmt.strip(),
                    "counterparty": cp, "is_flagged": False})
                a["currencies"].add(cur.strip())
                a["laundering"] = a["laundering"] or laundering
    return {k: v for k, v in accounts.items() if len(v["transactions"]) >= min_txns}
