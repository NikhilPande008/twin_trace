"""
Policy gates for GoS narrative text (T3.1).

Two gates run in sequence:
  1. DeterministicPolicyGate — regex-based, runs always, never calls the model.
     Catches tipping-off language, direct accusations and unnecessary PII patterns.
     This is the hard, fail-closed layer.

  2. NemotronContentSafetyGate — STUBBED. When wired, it calls the Nemotron triage
     model to score the narrative for content policy violations. Until T3.1 is
     finished it falls back to passing everything (PassthroughPolicyGate contract).

[PROVEN] DeterministicPolicyGate catch rates measured in tests/test_gate.py.
[STUBBED] NemotronContentSafetyGate — live model needed for T3.1.
"""

from __future__ import annotations

import re
from typing import Any

from .ports import PolicyGatePort


# Bump when a pattern changes; recorded with every decision so a verdict can be traced to rules.
GATE_VERSION = "deterministic-2026-10-21"

# Policies that block recording outright. tipping_off_str is advisory at recording: a GoS goes
# to FIU-IND and may reference filings (open question, DECISIONS.md 2026-10-21).
BLOCKING_AT_RECORDING = ("tipping_off_customer",)

# ── 1. Deterministic gate ──────────────────────────────────────────────────────

# Building blocks for `tipping_off_customer`. `[^.]{0,N}?` keeps a match inside one sentence.
# A GoS goes to FIU-IND, so a bare filing reference ("companion STRs filed for ACCT-10-1") is
# legitimate there (see the scenario 06/09/10 gold drafts). The offence is telling the customer,
# so this policy needs a tell-verb, a customer, and the thing that must not be disclosed.
_REPORT = r"(?:STRs?|CTRs?|ATRs?|suspicious\s+transaction\s+reports?)"
_TELL_VERB = r"(?:inform(?:ed|ing|s)?|told|tell(?:ing|s)?|notif(?:y|ied|ies|ying)|" \
             r"advis(?:e|ed|es|ing)|warn(?:ed|ing|s)?|let|" \
             r"tip(?:ped|ping|s)?\s+off|made\s+aware|making\s+aware)"
_PARTY = r"(?:customer|account[\s-]?holder|client)"
# What must not be disclosed: a report, the FIU, or that the customer is under investigation.
# Deliberately left out, because fraud victims and routine KYC produce them innocently:
# bare "suspicious", "alert(ed)", "flagged" (I4C-flagged handles, fraud-flagged UPI debits),
# "complaint", "police", "under review" (KYC updates); and beneficiary/remitter as the party.
_SECRET = r"(?:" + _REPORT + r"|FIU(?:-IND)?|financial\s+intelligence\s+unit|" \
          r"report(?:ed|ing)?\s+(?:to|with)\s+(?:the\s+)?(?:regulator|authorities)|" \
          r"regulatory\s+(?:report|filing)|suspicion|" \
          r"under\s+(?:investigation|monitoring|scrutiny|surveillance)|" \
          r"being\s+(?:investigated|monitored|scrutini[sz]ed))"

# Patterns the PO's narrative MUST NOT contain. Each entry is (policy_id, pattern, reason).
# Order matters: earlier matches are reported first.
_TIPPING_OFF_PATTERNS: list[tuple[str, re.Pattern, str]] = [
    (
        "tipping_off_str",
        re.compile(
            r"\b(suspicious\s+transaction\s+report|STR\s+filed|STR\s+will\s+be|"
            r"we\s+(have\s+)?filed|fiu.{0,10}report|atr\s+filed|CTR\s+filed)\b",
            re.IGNORECASE,
        ),
        "Text discloses or implies a regulatory filing (tipping-off: PML Rules Rule 8(6), SB-003)",
    ),
    (
        "tipping_off_disclosure",
        re.compile(
            r"\b(this\s+report|this\s+disclosure|this\s+filing|reporting\s+to\s+(FIU|RBI|ED))\b",
            re.IGNORECASE,
        ),
        "Text references a report or disclosure in a way that could tip off the customer",
    ),
    (
        "tipping_off_customer",
        re.compile(
            # "we informed the customer that an STR ...", "told the client he is under investigation"
            r"\b" + _TELL_VERB + r"\b[^.]{0,25}?\b" + _PARTY + r"s?\b[^.]{0,80}?\b" + _SECRET
            + r"\b"
            # "the customer has been informed that the account is under review"
            + r"|\b" + _PARTY + r"s?\b[^.]{0,30}?\b(?:has|have|had|was|were|is|are|been|being|"
            r"will\s+be)\b[^.]{0,15}?\b" + _TELL_VERB + r"\b[^.]{0,80}?\b" + _SECRET + r"\b",
            re.IGNORECASE,
        ),
        "Text says the customer was or will be told about a report, the FIU, or the suspicion "
        "(tipping-off: PML Rules Rule 8(6), SB-003)",
    ),
    (
        "accusation_without_evidence",
        re.compile(
            r"\b(is\s+guilty|is\s+a\s+criminal|is\s+engaged\s+in\s+money\s+launder|"
            r"is\s+laundering|is\s+definitely|is\s+certainly\s+(guilty|criminal))\b",
            re.IGNORECASE,
        ),
        "Text makes a definitive guilt accusation without hedging (corpus DG-09)",
    ),
    (
        "unnecessary_pii",
        re.compile(
            r"\b\d{12}\b"   # 12-digit Aadhaar-like number in the narrative
            r"|\bPAN[A-Z]{5}\d{4}[A-Z]\b"  # PAN card pattern
            r"|\b\d{10,11}\b(?=.{0,20}(mobile|phone|contact))",
            re.IGNORECASE,
        ),
        "Text contains a potential PII token (Aadhaar / PAN / phone) that should be redacted",
    ),
]


class DeterministicPolicyGate:
    """
    Regex-based policy gate. Always runs; never calls the model.

    Returns a verdict dict matching PolicyGatePort.check() contract:
      {passed: bool, verdicts: [{policy: str, violated: bool, reason: str}]}
    """
    name = "deterministic"

    def check(self, text: str, policies: list[str]) -> dict[str, Any]:
        verdicts = []
        overall_passed = True
        for policy_id, pattern, reason in _TIPPING_OFF_PATTERNS:
            if policies and not any(policy_id.startswith(p) for p in policies):
                continue
            violated = bool(pattern.search(text))
            if violated:
                overall_passed = False
            verdicts.append({
                "policy":   policy_id,
                "violated": violated,
                "reason":   reason if violated else "",
            })
        return {"passed": overall_passed, "verdicts": verdicts, "gate": self.name}


# ── 2. Nemotron Content Safety gate (STUBBED) ──────────────────────────────────

class NemotronContentSafetyGate:
    """
    [STUBBED] Nemotron-based content-safety check.

    When wired (T3.1), calls the triage model with a safety-classification prompt
    and returns a structured verdict. Until then it delegates to DeterministicPolicyGate
    so the deterministic layer's catches are never lost.

    Accepts an optional `llm` so tests can inject a fake.
    """
    name = "nemotron_content_safety"

    def __init__(self, llm=None):
        self._llm = llm
        self._deterministic = DeterministicPolicyGate()

    def check(self, text: str, policies: list[str]) -> dict[str, Any]:
        # STUBBED: always fall through to deterministic gate.
        # TODO (T3.1): if self._llm, call triage model for additional checks.
        result = self._deterministic.check(text, policies)
        result["gate"] = self.name
        result["stub"] = True
        return result
