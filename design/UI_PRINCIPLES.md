# UI_PRINCIPLES.md — Product-Specific UX & Design Principles

**Date:** 2026-09-25  
**Product:** FIU-IND AML Copilot — Principal Officer Investigation Workspace  
**Design direction:** Decision Workbench (Direction B + elements of A)

---

## How to use this document

Every UI decision during implementation should pass through these principles. When two principles conflict, the one listed first wins. When a feature request cannot satisfy a principle, document the trade-off explicitly.

---

## Principle 1: Evidence before opinion

The PO must encounter the facts before the system's interpretation.

**In practice:**
- Alert signal, KYC profile, transaction data, and evidence state are visible before the AI assessment is rendered
- The "Run Assessment" action is user-initiated, never automatic
- AI recommendations appear in a visually subordinate zone — the evidence zone is the primary visual real estate
- The AI panel never obscures or overlays the evidence panel

**Anti-pattern:** Auto-running the assessment on page load, placing the AI recommendation at the top of the screen, or making the AI output visually dominant (large font, bright color, card elevation).

---

## Principle 2: The decision belongs to the PO

Every interaction must reinforce that the system assists; the PO decides.

**In practice:**
- Decision actions (FILE / DEFER / CLOSE) are in a visually distinct zone separated from AI output
- The confirmation step shows exactly what will be recorded: the decision, the rationale, the factors cited, the PO's identity, and the timestamp
- Language throughout uses "The system assessed…" / "You are recording…" — never "We recommend…" or "The AI decided…"
- After recording, the decision is attributed to the PO by name, not to the system

**Anti-pattern:** "AI recommends FILE — click to confirm." Conflating the system's assessment with the PO's decision. Using first-person plural ("We found…") for AI output.

---

## Principle 3: Urgency is SLA, not decoration

Color and visual weight encode regulatory deadlines, not aesthetic emphasis.

**In practice:**
- Red means "SLA breach imminent or overdue" — nothing else
- Amber means "SLA pressure — attention needed within 1–2 working days"
- Green means "SLA comfortable — 3+ working days remaining"
- These three colors are the ONLY warm/alert colors in the palette. No other element uses red, amber, or green for emphasis
- SLA countdown is the most prominent element in the Alert Queue row and the Case Header

**Anti-pattern:** Using red for FILE buttons, error states, and SLA warnings interchangeably. Using green for "success" feedback and SLA comfort simultaneously. Adding color for visual interest.

---

## Principle 4: Every number has a unit, every claim has a source

Regulatory decisions require precision. The UI never presents a datum without its context.

**In practice:**
- Amounts always show currency symbol and denomination: ₹85,00,000 (₹85L), never "8500000"
- Dates show IST with the format the PO expects: "18 Sep 2026 14:30 IST"
- Rule citations show the rule ID AND are expandable to show the rule text inline: "RFI-003 (Dormant reactivation)" → click → full rule text
- Evidence levels (PROVEN / ASSUMED) are visible on every claim, using icon + label, not color alone
- AI-generated text is labeled with its source model and the assessment timestamp

**Anti-pattern:** Bare numbers without units. Rule IDs without accessible definitions. Evidence presented without its confidence level. AI output without provenance.

---

## Principle 5: Silence is a signal

Missing evidence is as important as present evidence. The UI must make absence visible.

**In practice:**
- Factors with insufficient data are shown explicitly, not hidden: "POE-005 (Income Level): No evidence available"
- Gaps are grouped in a dedicated section, not mixed into the factor list where they can be overlooked
- The decision confirmation includes: "Evidence gaps remain for: [factor list]" — the PO acknowledges gaps before recording
- An alert with many gaps looks visually different from one with complete evidence (different visual weight, not just a count)

**Anti-pattern:** Hiding factors with no evidence. Showing only triggered factors. Collapsing "insufficient" factors by default. Treating gaps as non-information.

---

## Principle 6: The audit trail is the product

The primary output of this product is not an AI recommendation — it is a defensible decision record.

**In practice:**
- The Decision Ledger is not a secondary view — it is the product's proof of value
- Every recorded decision links back to the evidence, assessment, and rationale that produced it
- The GoS narrative is visually framed as a legal document — it is the text that FIU-IND will read
- Timestamps, PO identity, and SLA compliance are displayed on every ledger entry without expansion
- The GoS textarea is the largest, most prominent input element on the Disposition page

**Anti-pattern:** Treating the ledger as a log table. Hiding decision provenance behind expanders. Making the GoS textarea look like a comment box. Prioritizing the AI assessment visually over the PO's narrative.

---

## Principle 7: Regulatory context is inline, not elsewhere

The PO should never need to leave the case to understand the legal basis.

**In practice:**
- When a factor cites a rule (RFI-001, POE-003), the rule text is accessible inline — via tooltip, expander, or adjacent panel
- The Regulatory Reference page exists for browsing, but the investigation workspace must be self-contained
- PMLA provisions cited in the assessment include a one-line plain-language summary, not just the section number
- Evidence tags (PROVEN / ASSUMED) include a one-line explanation of what the tag means on first encounter

**Anti-pattern:** Linking to the Regulatory Reference page from the Disposition Panel. Showing rule IDs as plain text with no expansion. Requiring the PO to memorize what "RFI-003" means.

---

## Principle 8: Visual hierarchy = decision hierarchy

The visual weight of an element reflects its importance in the decision, not its technical complexity.

**In practice:**
- Case identity + SLA: largest, most prominent (the PO must always know what case they're on and how much time remains)
- Evidence and findings: second tier — the factual basis for the decision
- AI assessment: third tier — a tool, not the answer
- Decision controls: visually separated from all the above, with the FILE action as the only high-saturation element on the page
- Metadata (timestamps, model ID, assessment version): smallest, least prominent

**Anti-pattern:** Making the AI recommendation visually dominant. Giving all sections equal visual weight. Using card elevation or borders to make less-important sections look important.

---

## Principle 9: Investigation, not form-filling

The workspace should feel like an investigation desk, not a data-entry form.

**In practice:**
- Information is presented for reading and analysis, not just for data entry
- The GoS editor supports narrative writing — it's a text area with adequate height, not a one-line input
- The PO can navigate between evidence, assessment, and regulatory context without losing their place
- "Read → Evaluate → Write → Record" is the interaction flow, not "Fill field 1 → Fill field 2 → Submit"

**Anti-pattern:** Sequential form wizards. Required-field asterisks on every input. "Step 1 of 4" progress bars. Inline validation errors during composition.

---

## Principle 10: Density over decoration

Screen space communicates information, not visual interest.

**In practice:**
- Padding and whitespace serve scannability (grouping related items, separating unrelated ones) — not aesthetics
- No decorative borders, shadows, or gradients. Elevation is functional (sticky headers, floating SLA badge)
- Expanders are used to manage density, not to hide content that should be visible
- The two-column layout maximizes horizontal use — the investigation workspace should feel wide, not narrow

**Anti-pattern:** Large card padding with small content. Decorative separators between every row. Rounded-corner cards with shadows for every data group. Whitespace that pushes critical information below the fold.

---

## Design anti-patterns to actively avoid

These are patterns that would make the product look like a generic AI SaaS application:

| Anti-pattern | Why it fails | What to do instead |
|---|---|---|
| `st.metric` card grid at top of page | Canonical "AI dashboard" — recognizable in 2 seconds | Inline key values in the case header or alert row |
| Emoji icons (🏦, 🟢, ✍️) | Signals prototype/demo stage | Text labels with HTML-styled indicators |
| "Chat with AI" text input | Positions the product as an AI chatbot | Purpose-specific action buttons: "Run Assessment", "Draft GoS", "Check Quality" |
| Spinner → expander results | The default "call AI, show results" pattern | Results rendered in-place in the AI panel, no expand/collapse gate |
| Equal-weight sidebar navigation | Five pages of equal importance = no hierarchy | Primary workflow (Queue → Case → Decision) with secondary pages subordinate |
| Dark theme with neon badges | Default Streamlit dark mode aesthetic | Warm neutral palette with functional color only |
| "Powered by AI" / "AI-generated" banners | Positions the product as an AI demo | Quiet attribution: model ID and timestamp in small text, no banner |

---

## Decision vocabulary

Use these terms consistently across the UI:

| Concept | Use | Don't use |
|---|---|---|
| The system's output | "System assessment", "Copilot analysis" | "AI recommendation", "AI decision", "Model output" |
| The PO's action | "Your decision", "Record your finding" | "Confirm recommendation", "Accept AI result" |
| FILE action | "File STR" | "Submit", "Send", "Approve" |
| NOT FILE action | "Close — no suspicion formed" | "Reject", "Dismiss", "Archive" |
| DEFER action | "Defer — additional EDD required" | "Pending", "In progress", "Under review" |
| Ground of Suspicion | "Ground of Suspicion narrative" | "Report text", "STR body", "Description" |
| Evidence | "Evidence", "Findings" | "Data points", "Signals", "Features" |
| Missing evidence | "Evidence gap", "Not available" | "Insufficient data", "N/A", "Unknown" |
| Assessment factor | "Evaluation factor" (+ factor name) | "Check", "Criterion", "Rule" |
