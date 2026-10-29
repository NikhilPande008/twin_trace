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

# Inline tooltips (T12.14): the short form a reader meets in running text -> its definition.
TOOLTIPS = {
    "Principal Officer": GLOSSARY[0][1],
    "PO": GLOSSARY[0][1],
    "FIU-IND": GLOSSARY[1][1],
    "PMLA": GLOSSARY[2][1],
    "STR": GLOSSARY[3][1],
    "Ground of Suspicion": GLOSSARY[4][1],
    "GoS": GLOSSARY[4][1],
    "Tipping-off": GLOSSARY[5][1],
    "I4C": GLOSSARY[6][1],
    "KYC": GLOSSARY[13][1],
    "SLA": GLOSSARY[12][1],
}


def with_tooltips(escaped_text: str) -> str:
    """Wrap the first occurrence of each known term in an <abbr> with its definition. Takes text
    that is ALREADY HTML-escaped and contains no tags."""
    import html
    import re
    out = escaped_text
    for term in sorted(TOOLTIPS, key=len, reverse=True):
        pat = re.compile(rf"(?<![\w>-]){re.escape(term)}(?![\w-])")
        title = html.escape(TOOLTIPS[term], quote=True)
        out = pat.sub(lambda m: f'<abbr title="{title}">{m.group(0)}</abbr>', out, count=1)
    return out
