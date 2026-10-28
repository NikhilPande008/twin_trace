"""
Who the product is for and what is at stake, each claim tied to a corpus rule.

Every `rule_id` must resolve to a PROVEN or ASSUMED corpus rule (tests/test_stakes.py). The `here`
line says what this build does about it, and must stay true of the code. No figures beyond the
rule's own wording: impact numbers live in docs/IMPACT.md, not in the app (CLAUDE.md §5).
"""

from __future__ import annotations

USER = ("A bank's Principal Officer under India's PMLA. For each alert they decide whether to "
        "file a Suspicious Transaction Report with FIU-IND or close it, and must be able to "
        "defend either choice at inspection.")

STAKES = [
    {"rule_id": "STR-002",
     "claim": "An STR is due within 7 working days of forming suspicion.",
     "here": "Every alert shows working days left, counted from the alert date."},
    {"rule_id": "INS-001",
     "claim": "Inspectors look at alerts that were not filed; a closure without a written "
              "reason is a recognised inspection risk (governance practice, not a circular).",
     "here": "A closure cannot be recorded without a rationale, and comes with the conditions "
             "that would reopen it."},
    {"rule_id": "INS-002",
     "claim": "Inspectors check that the decision was made by the Principal Officer or an "
              "authorised delegate.",
     "here": "Each ledger row records the officer ID and time (self-asserted: no sign-in in "
             "this build)."},
    {"rule_id": "SB-003",
     "claim": "No one may reveal to the customer that an STR is filed or being considered "
              "(tipping-off).",
     "here": "Such requests are refused before any model call; drafts are checked for "
             "disclosure language."},
]

RULE_IDS = [s["rule_id"] for s in STAKES]
