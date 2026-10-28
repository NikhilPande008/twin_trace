"""
Rupee amounts in free text → exact values, for the GoS evidence gate (T7.1).

Supported forms (case-insensitive), each normalised to an exact Decimal number of rupees:
  prefix   ₹3,25,000 · ₹ 325000 · Rs. 3,25,000 · Rs.28K · INR 3250000 · ₹32.5 lakh · Rs 1.2 Cr
  bare     32.5 lakh · 3 lakhs · 1.2 crore            (lakh/lac/crore words imply rupees)
  suffix   3250000 INR · 3,25,000 rupees · 5,000/-
Commas may be Indian (32,50,000) or western (3,250,000). Multipliers: K / thousand = 10^3,
L / lakh / lac = 10^5, Cr / crore = 10^7.

Anything that looks monetary but cannot be read as one exact figure is returned UNPARSED, never
skipped: a currency marker with no number ("₹ thirty lakh"), or a range ("₹3-4 lakh"). The
gate treats unparsed amounts as failures, so a new phrasing fails closed instead of slipping by.

Not handled (outside deterministic coverage): amounts written in words, other currencies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

_NUM = r"\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+(?:\.\d+)?"
_MULT = r"lakhs?|lacs?|crores?|thousand|cr|l|k"
_PRE = r"₹|\bRs\b\.?|\bINR\b"

_AMOUNT_RE = re.compile(
    rf"(?P<pre>{_PRE})\s*(?P<n1>{_NUM})(?:\s*(?P<rng>[-–—])\s*(?P<n2>{_NUM}))?"
    rf"(?:\s*(?P<m1>{_MULT})\b)?"
    rf"|\b(?P<n3>{_NUM})\s*(?P<m3>lakhs?|lacs?|crores?)\b(?:\s*(?:rupees|INR)\b)?"
    rf"|\b(?P<n4>{_NUM})(?:\s*/-|\s+rupees\b|\s+INR\b)",
    re.IGNORECASE,
)
_MARKER_RE = re.compile(_PRE, re.IGNORECASE)

_MULTIPLIER = {"k": 10**3, "thousand": 10**3, "l": 10**5, "lakh": 10**5, "lakhs": 10**5,
               "lac": 10**5, "lacs": 10**5, "cr": 10**7, "crore": 10**7, "crores": 10**7}


@dataclass(frozen=True)
class Mention:
    raw: str
    start: int
    value: Decimal | None      # exact rupees; None when unparsed
    reason: str = ""           # why it is unparsed


def _value(num: str, mult: str | None) -> Decimal | None:
    try:
        v = Decimal(num.replace(",", ""))
    except InvalidOperation:
        return None
    return v * _MULTIPLIER[mult.lower()] if mult else v


def extract_amounts(text: str) -> list[Mention]:
    """Every monetary mention in `text`, in order. Unparsed ones have value=None."""
    out: list[Mention] = []
    spans: list[tuple[int, int]] = []
    for m in _AMOUNT_RE.finditer(text or ""):
        raw = m.group(0).strip()
        spans.append(m.span())
        if m.group("pre"):
            if m.group("rng"):
                out.append(Mention(raw, m.start(), None, "range, not one figure"))
                continue
            num, mult = m.group("n1"), m.group("m1")
        elif m.group("n3"):
            num, mult = m.group("n3"), m.group("m3")
        else:
            num, mult = m.group("n4"), None
        value = _value(num, mult)
        out.append(Mention(raw, m.start(), value, "" if value is not None else "unreadable"))
    for m in _MARKER_RE.finditer(text or ""):
        if not any(a <= m.start() < b for a, b in spans):
            snippet = text[m.start():m.start() + 24].split("\n")[0]
            out.append(Mention(snippet, m.start(), None, "currency marker without a figure"))
    return sorted(out, key=lambda x: x.start)


def rupee_evidence(transactions: list[dict], facts) -> set[Decimal]:
    """Admissible rupee figures: single transaction amounts and INR calculator facts."""
    out = {Decimal(int(t.get("amount_inr") or 0)) for t in transactions}
    out.discard(Decimal(0))              # a missing transaction amount is not evidence
    for f in facts or []:                # a fact recorded as 0 is
        if f.get("unit") == "INR" and isinstance(f.get("value"), (int, float)):
            out.add(Decimal(int(f["value"])))
    return out


def unsupported_money(text: str, allowed: set[Decimal]) -> list[str]:
    """Monetary mentions in `text` that are unreadable or not exactly in `allowed`."""
    return [m.raw for m in extract_amounts(text) if m.value is None or m.value not in allowed]


def format_inr(value: Decimal | int) -> str:
    """₹ with Indian digit grouping: 3250000 → ₹32,50,000."""
    v = Decimal(value)
    whole, frac = divmod(abs(v), 1)
    s = str(int(whole))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        head = ",".join([head[max(i - 2, 0):i] for i in range(len(head), 0, -2)][::-1])
        s = f"{head},{tail}"
    if frac:
        s += str(frac.normalize())[1:]
    return f"{'-' if v < 0 else ''}₹{s}"
