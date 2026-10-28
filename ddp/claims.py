"""
Claim map for a Ground of Suspicion (T2 / D2): what each rupee figure is, where it comes from,
and how far the deterministic checks reach.

Each monetary mention gets one status:
  verified_calculation  equals an INR fact of the cited calculator run (fact IDs, derivation)
  source_transaction    equals a single transaction amount (transaction IDs)
  needs_review          equals a transaction amount, but the sentence names a different
                        counterparty than the one that transaction involves
  unsupported           matches neither
  unparsed              not readable as one exact figure (range, words)

"Verified" means the figure matches the recorded inputs. It does not mean those inputs are true,
and it does not check the rest of the sentence. Sentences with no checked figure are listed as
outside deterministic coverage, for human review.
"""

from __future__ import annotations

import re
from decimal import Decimal

from .money import extract_amounts, format_inr

STATUS_LABEL = {
    "verified_calculation": "Amount matches calculation",
    "source_transaction": "Amount matches transaction",
    "needs_review": "Context needs your review",
    "unsupported": "Unsupported claim",
    "unparsed": "Cannot check this amount",
}

# A sentence ends at . ! ? + whitespace, except after abbreviations common in these texts
# ("Rs. 1,40,000", "No. 4", "Ltd.", "Pvt.", "approx.", "viz.", "e.g.", "i.e.").
_SENTENCE_END = re.compile(
    r"(?<![Rr]s\.)(?<!No\.)(?<!Ltd\.)(?<!Pvt\.)(?<!pprox\.)(?<!viz\.)(?<!e\.g\.)(?<!i\.e\.)"
    r"(?<=[.!?])\s+|\n+")


def _sentences(text: str) -> list[tuple[int, int, str]]:
    out, start = [], 0
    for m in _SENTENCE_END.finditer(text):
        if text[start:m.start()].strip():
            out.append((start, m.start(), text[start:m.start()]))
        start = m.end()
    if text[start:].strip():
        out.append((start, len(text), text[start:]))
    return out


def _party_key(counterparty: str) -> str:
    """'UPI handle C (I4C-flagged)' → 'upi handle c'; 'Unknown UPI handle A' → 'upi handle a'."""
    key = re.sub(r"\(.*?\)", "", counterparty or "").strip().lower()
    return re.sub(r"^(unknown|unidentified)\s+", "", key)


def claim_map(narrative: str, transactions: list[dict], facts: list[dict] | None = None,
              run_id: str | None = None) -> dict:
    """Return {"claims": [...], "coverage": {...}} for `narrative`."""
    facts = facts or []
    by_fact: dict[Decimal, list[dict]] = {}
    for f in facts:
        if f.get("unit") == "INR" and isinstance(f.get("value"), (int, float)):
            by_fact.setdefault(Decimal(int(f["value"])), []).append(f)
    by_txn: dict[Decimal, list[dict]] = {}
    for t in transactions:
        if t.get("amount_inr"):
            by_txn.setdefault(Decimal(int(t["amount_inr"])), []).append(t)
    parties = {_party_key(t.get("counterparty", "")) for t in transactions} - {""}

    sentences = _sentences(narrative or "")
    claims, covered = [], set()
    for m in extract_amounts(narrative or ""):
        idx = next((i for i, (a, b, _) in enumerate(sentences) if a <= m.start < b), None)
        sentence = sentences[idx][2].strip() if idx is not None else ""
        claim = {"raw": m.raw, "value": None if m.value is None else int(m.value),
                 "display": None if m.value is None else format_inr(m.value),
                 "sentence": sentence, "fact_ids": [], "txn_ids": [], "derivation": "",
                 "run_id": None, "note": ""}
        if m.value is None:
            claim.update(status="unparsed", note=m.reason)
        elif m.value in by_fact:
            fs = by_fact[m.value]
            claim.update(status="verified_calculation", run_id=run_id,
                         fact_ids=[f["fact_id"] for f in fs],
                         derivation="; ".join(f.get("derivation", "") for f in fs),
                         txn_ids=sorted({t for f in fs for t in (f.get("txn_ids") or [])}))
        elif m.value in by_txn:
            ts = by_txn[m.value]
            claim.update(status="source_transaction", txn_ids=[t["txn_id"] for t in ts])
            low = sentence.lower()
            named = {p for p in parties if p and p in low}
            own = {_party_key(t.get("counterparty", "")) for t in ts}
            if named and not (named & own):
                claim.update(status="needs_review",
                             note=f"amount belongs to {sorted(own)}, sentence names {sorted(named)}")
        else:
            claim["status"] = "unsupported"
        claim["label"] = STATUS_LABEL[claim["status"]]
        claims.append(claim)
        # A needs_review figure is already flagged for the officer; do not list it twice.
        if idx is not None and claim["status"] in ("verified_calculation", "source_transaction",
                                                    "needs_review"):
            covered.add(idx)

    uncovered = [s.strip() for i, (_, _, s) in enumerate(sentences) if i not in covered]
    return {"claims": claims,
            "coverage": {"sentences": len(sentences), "with_checked_figure": len(covered),
                         "outside_deterministic_coverage": uncovered}}
