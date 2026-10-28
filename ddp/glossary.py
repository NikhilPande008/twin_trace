"""Plain-language definitions for the terms a first-time reader meets (T9.8).

Kept deliberately short and conservative: where a definition is this product's own, it says so.
"""

GLOSSARY = [
    ("Principal Officer (PO)", "The senior compliance officer a bank designates to decide whether "
     "to report suspicious activity to the financial intelligence unit."),
    ("FIU-IND", "India's Financial Intelligence Unit. Banks send it Suspicious Transaction "
     "Reports (STRs) and Cash Transaction Reports (CTRs)."),
    ("PMLA", "The Prevention of Money-Laundering Act, 2002: the law that creates the reporting "
     "duty."),
    ("STR", "Suspicious Transaction Report. Part (c) is the Ground of Suspicion."),
    ("Ground of Suspicion (GoS)", "The written reasoning in an STR for why the activity is "
     "suspicious. Generic or copy-pasted text is a recognised quality problem."),
    ("Tipping-off", "Telling the customer that a report is being or may be made. It is "
     "prohibited, so this tool refuses to draft any such message."),
    ("I4C", "The Indian Cyber Crime Coordination Centre. Its suspect registry is one source of "
     "'flagged' counterparties in the synthetic cases."),
    ("RFI (red-flag indicator)", "A recognised warning pattern, for example a pass-through of "
     "credits or cash just under a reporting threshold."),
    ("11 factors (POE)", "A structured list of 11 questions about the case (income, source of "
     "funds, geography, KYC and so on). This list is this product's compilation, not an "
     "FIU-IND-issued checklist."),
    ("Calculator of record", "A fixed program that computes the case's totals and ratios. Its "
     "code, input and output are hashed per run, so a figure can be re-checked later."),
    ("Modeled signal level", "LOW, ELEVATED or HIGH, computed by this product's own rules from "
     "calculator facts. It is not a finding of suspicion and not a regulatory threshold."),
    ("Hash-chained ledger", "Each decision row includes the hash of the one before it, so an "
     "edit or removal is detectable. Tamper-evident, not tamper-proof."),
    ("SLA", "The 7-working-day window for filing, counted from when suspicion is formed."),
    ("KYC", "Know Your Customer: the identity and profile information the bank holds."),
]
