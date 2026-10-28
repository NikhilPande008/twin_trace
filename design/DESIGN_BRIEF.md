# DESIGN_BRIEF.md — User, Problem, Mental Model & Visual Direction

**Date:** 2026-09-25

---

## 1. The user

**Role:** Principal Officer (PO) at a mid-sized Indian private bank.  
**Regulatory authority:** Designated under PMLA 2002 as the bank's AML compliance decision-maker.  
**Reports to:** FIU-IND (regulator), internal audit, RBI (supervisory).

### What the PO does weekly
- Reviews 8–15 alerts surfaced by transaction monitoring (MuleHunter.AI, DPIP, internal rules)
- For each alert: reads the signal, reviews customer KYC, evaluates against 11 suspicion factors, forms (or declines to form) suspicion
- If suspicion: drafts a Ground of Suspicion narrative (STR Part c), files via FINGate 2.0 within 7 working days
- If no suspicion: documents the closure rationale (inspectable by FIU-IND)
- Tracks ~30 open cases against the 7-WD SLA clock
- Prepares for FIU-IND inspections: every FILE and NOT_FILE decision must be reconstructable

### What the PO is NOT
- Not a data scientist. Does not think in "model confidence" or "feature importance."
- Not an AI operator. Does not want to "prompt" a system or "chat with AI."
- Not a dashboard consumer. Does not start the day by looking at charts.
- A regulatory professional who thinks in terms of: **signal → evidence → basis → decision → record.**

---

## 2. The problem

### The disposition gap
Detection is solved (MuleHunter, I4C, DPIP). What is NOT solved is:
1. **Structured evaluation** — mapping a signal to the 11 PO factors against evidence
2. **Defensible narrative** — writing a non-templated GoS that FIU-IND will accept
3. **Decision record** — maintaining an append-only audit trail that survives inspection
4. **SLA management** — tracking the 7-WD clock across 30+ open cases

### What the current UI gets wrong
The current UI was designed to demonstrate AI capabilities to hackathon judges. It presents the workflow as:
> Open list → Click button → AI runs → Read output → Click FILE

This is a **demo flow**, not an **investigation workflow**. The PO's actual cognitive process is:
> Why is this here → What happened → What do I know → What don't I know → What does the law say → What does the system think → Do I agree → Why → Record it

The UI must serve the second sequence, not the first.

---

## 3. The mental model

### The PO's cognitive sequence

```
SIGNAL        Why did this case enter my queue?
    ↓
EVIDENCE      What transactions, KYC facts, and external signals exist?
    ↓
FINDINGS      What does each piece of evidence establish or contradict?
    ↓
GAPS          What evidence is missing or unverifiable?
    ↓
REGULATORY    Which PMLA provisions, RBI directions, and FIU-IND guidelines apply?
BASIS
    ↓
SYSTEM        What does the copilot recommend, and on what basis?
ANALYSIS
    ↓
CHALLENGE     What could make that recommendation wrong?
    ↓
DECISION      FILE / NOT FILE / DEFER — in the PO's own words, with their reasoning
    ↓
RECORD        Immutable entry in the decision ledger, reconstructable at inspection
```

### Key UX implication
The primary interaction model is **investigation**, not **AI consultation**. The AI is a tool within the investigation — like a calculator on an accountant's desk. The desk is the product, not the calculator.

---

## 4. UX goals

| # | Goal | Measure |
|---|---|---|
| G-1 | PO can triage their queue in < 2 minutes | Time from page load to "I know which case to work on next" |
| G-2 | Case context visible without scrolling | Signal, KYC, amount, SLA, RFIs all above fold |
| G-3 | Evidence and gaps visible before recommendation | PO reads evidence before seeing AI opinion |
| G-4 | Regulatory basis traceable inline | Rule IDs link to source text without page switch |
| G-5 | Decision is a deliberate, confirmable action | PO reviews what they are recording before it becomes permanent |
| G-6 | Every decision is reconstructable | Ledger entry links back to evidence, assessment, and rationale |
| G-7 | AI boundary is architecturally clear | "The system assessed" vs "I decided" are visually distinct zones |

---

## 5. Three visual directions explored

### Direction A: Investigation Desk

**Visual metaphor:** A detective's desk — organized, layered, everything within reach but sorted by relevance. The workspace is dominated by the case file, with tools (search, AI, calculator) accessible from the margins.

**Typography:** Monospace for identifiers (ALERT-01, RFI-001, POE-003). Serif or slab-serif for the GoS narrative (communicating "legal document"). Sans-serif for UI labels and metadata.

**Color philosophy:** Warm neutrals (paper, ink, manila) with functional color only for evidence states and urgency. No brand color. No blue/purple AI aesthetic.

**Information density:** High. Multiple columns, compact typography, minimal padding. Closer to a Bloomberg terminal than a SaaS dashboard.

**Navigation:** Case-centric. The queue is a compact list; clicking a case opens the full investigation workspace. Supporting pages (ledger, reference) are accessible from context menus or inline links, not top-level nav.

**Evidence presentation:** Grouped by factor, with inline expansion. Each factor shows its evidence, rules cited, and assessment in a compact block. Contradictions are shown as side-by-side comparisons.

**Risks:** High information density can overwhelm. Streamlit's default padding fights against compact layouts. The "desk" metaphor could become decorative if pushed too far visually.

**AI-template risk:** Low. This direction looks nothing like a SaaS dashboard or AI chatbot.

**Feasibility in Streamlit:** Challenging. Streamlit fights density. Would require extensive `unsafe_allow_html` to override default spacing.

### Direction B: Decision Workbench

**Visual metaphor:** A structured workflow bench — the case moves through visible stages (Signal → Evidence → Analysis → Decision), with the current stage prominently framed. Think: an IDE for compliance decisions.

**Typography:** One typeface family (system sans-serif or IBM Plex Sans). Size hierarchy communicates priority: large for the case identity and SLA, medium for evidence and findings, small for metadata.

**Color philosophy:** Neutral background with a restrained functional palette. Evidence states use distinct hues but at low saturation. The decision action (FILE) uses the only high-saturation color on the page — it's the only thing that "pops."

**Information density:** Medium-high. Sections are visually separated but compact within each section. Uses horizontal space (columns, side-by-side) rather than vertical scroll.

**Navigation:** Stage-based within the case. The workspace has visible phases, but the PO can jump between them. Queue and ledger are secondary views.

**Evidence presentation:** Each factor is a compact row with an evidence-state indicator (icon + label, not color alone). Triggered factors are expanded by default; clear factors are collapsed. Gaps are called out in a dedicated section with specific "what is missing" language.

**Decision presentation:** Separated from the analysis by a visible boundary (horizontal rule + section header). Includes a review summary: "You are about to record: FILE for ALERT-01 based on 5 triggered factors and the following rationale…" before the confirm button.

**Risks:** "Stage" metaphor could feel like a wizard/stepper if overdone. Compliance decisions are not strictly linear — the PO may revisit evidence after reading the recommendation.

**AI-template risk:** Medium-low. The stage structure is uncommon in AI demos. The functional color palette avoids the blue/purple AI aesthetic.

**Feasibility in Streamlit:** Good. `st.columns()` for horizontal layout, `st.tabs()` or `st.expander()` for information grouping, `st.container()` for visual sections. No custom JS required.

### Direction C: Evidence Ledger

**Visual metaphor:** A regulatory filing — the entire workspace is structured as a document that the PO is building. Each section corresponds to a part of the STR or decision record. The act of investigating IS the act of building the filing.

**Typography:** Document-like. Clear heading hierarchy. Body text is readable at length (the GoS narrative is the centerpiece). Citations are visually distinct (smaller, indented, with source references).

**Color philosophy:** Near-monochrome. White/off-white background with black text. Color used only for evidence states and the one high-stakes action (FILE). The palette communicates: serious, precise, no-nonsense.

**Information density:** Medium. Document layout with generous line spacing for readability. Evidence is presented as numbered items within sections, not as cards or badges.

**Navigation:** Document-scroll. The case workspace is one long page with a floating table of contents. The PO scrolls through their case like reading a brief.

**Evidence presentation:** Each piece of evidence is a numbered paragraph with inline citations. Contradictions are called out with "cf." cross-references. Gaps are listed as "Evidence not available for: [factor]."

**Decision presentation:** The final section of the document. "Decision: FILE / NOT FILE" is a formal statement, not a button. The PO types their rationale into a structured section that mirrors the STR format.

**Risks:** Long-scroll document could feel slow and academic. Not optimized for rapid triage. The formal structure could make the PO feel like they're filling out a form rather than investigating.

**AI-template risk:** Very low. Documents do not look like AI apps.

**Feasibility in Streamlit:** Moderate. Streamlit can render long-form markdown well. The floating TOC would need `unsafe_allow_html` with `position: sticky`. The formal structure maps well to Streamlit's top-to-bottom rendering model.

---

## 6. Selected direction

### Direction B: Decision Workbench — with elements of A

**Rationale:**

1. **Workflow fit:** The PO's cognitive sequence is stage-like (signal → evidence → analysis → decision) but not strictly linear. Direction B's stage visibility + jump-to-any-stage matches this.

2. **Information hierarchy:** Direction B's "SLA and case identity are the largest things on screen" principle directly serves G-2. The PO always knows which case they're looking at and how much time they have.

3. **Investigation usability:** Direction A's density is desirable but Streamlit fights it. Direction B's medium-high density with horizontal layout is achievable.

4. **Evidence readability:** Direction B's compact factor rows with state indicators are more scannable than A's layered desk or C's numbered paragraphs.

5. **Regulatory traceability (from A):** Direction A's inline rule citations should be adopted. When a factor cites RFI-001, the PO should be able to see the rule text without switching pages.

6. **Decision accountability:** Direction B's explicit review-before-confirm step directly serves G-5. This is the single most important interaction design decision.

7. **Visual differentiation:** Direction B with a neutral, functional palette is the least likely to look like a SaaS template or AI chatbot.

8. **Feasibility:** Direction B is the most achievable within Streamlit's constraints. No custom JS, no custom components, no external CSS.

9. **Accessibility:** Direction B's use of icons + labels (not color alone) for evidence states is the most accessible pattern.

10. **Performance:** Streamlit re-runs the full script on every interaction. Direction B's sectioned layout minimizes the visual disruption of re-renders compared to C's long-scroll document.

**Trade-offs:**
- Direction B does not have A's visual distinctiveness. Mitigation: adopt A's color philosophy (warm neutrals) and typography mixing (monospace for IDs).
- Direction B's stage metaphor could feel like a wizard. Mitigation: stages are visible but not enforced. All sections of the case are always accessible.
- Direction C's document-like GoS editing is appealing but doesn't fit Streamlit's rerun model well. Mitigation: the GoS editor in Direction B is still a prominent, well-framed text area.
