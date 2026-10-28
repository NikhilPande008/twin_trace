"""
Counter-hypotheses a Principal Officer (or an FIU-IND reviewer) could raise against a decision.

A hypothesis never edits the case record. It produces a modified COPY of the transactions that
the calculator of record is re-run on, as a separate, hashed branch run.

  EXPLAIN(txn)        the PO accepts a documented legitimate explanation for one transaction,
                      so it is excluded from the suspicious pattern
  UNFLAG(cp)          a registry hit on a counterparty turns out to be a false positive
                      (the exact failure in ALERT-16: a shared merchant handle)
  FLAG(cp)            a counterparty is later reported to a registry (I4C, internal watch list)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Hypothesis:
    kind: str       # EXPLAIN | UNFLAG | FLAG
    target: str     # txn_id or counterparty name

    @property
    def hid(self) -> str:
        return f"{self.kind}:{self.target}"

    def label(self) -> str:
        return {
            "EXPLAIN": f"Transaction {self.target} has a documented legitimate explanation",
            "UNFLAG": f"The registry flag on '{self.target}' is a false positive",
            "FLAG": f"'{self.target}' is reported to a registry",
        }[self.kind]

    def to_dict(self) -> dict:
        return {"id": self.hid, "kind": self.kind, "target": self.target, "label": self.label()}


def apply(transactions: list[dict], hyps: tuple[Hypothesis, ...] | list[Hypothesis]) -> list[dict]:
    excluded = {h.target for h in hyps if h.kind == "EXPLAIN"}
    unflag = {h.target for h in hyps if h.kind == "UNFLAG"}
    flag = {h.target for h in hyps if h.kind == "FLAG"}
    out = []
    for t in transactions:
        if t.get("txn_id") in excluded:
            continue
        t2 = dict(t)
        cp = t2.get("counterparty")
        if cp in unflag:
            t2["is_flagged"] = False
        if cp in flag:
            t2["is_flagged"] = True
        out.append(t2)
    return out


def challenges_to_file(transactions: list[dict]) -> list[Hypothesis]:
    """Hypotheses that could WEAKEN a decision to file."""
    hyps = [Hypothesis("UNFLAG", cp) for cp in sorted(
        {t.get("counterparty") for t in transactions if t.get("is_flagged") and t.get("counterparty")})]
    hyps += [Hypothesis("EXPLAIN", t["txn_id"]) for t in transactions if t.get("txn_id")]
    return hyps


def challenges_to_close(transactions: list[dict]) -> list[Hypothesis]:
    """Hypotheses that could STRENGTHEN the case against a decision not to file."""
    return [Hypothesis("FLAG", cp) for cp in sorted(
        {t.get("counterparty") for t in transactions
         if not t.get("is_flagged") and t.get("counterparty")})]
