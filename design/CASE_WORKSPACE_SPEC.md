# CASE_WORKSPACE_SPEC.md — Case Investigation Workspace Specification

**Date:** 2026-09-25  
**Product:** FIU-IND AML Copilot — Decision Workbench  
**Scope:** The Disposition Panel — the primary workspace where the PO investigates a case and records a decision

---

## 1. Purpose

This is the screen where the product's value is delivered. The PO spends 80% of their time here. Every other page (Queue, Ledger, Dashboard, Reference) serves this one.

The workspace must support the PO's cognitive sequence:
1. **Orient** — What case am I looking at? How much time do I have?
2. **Understand** — What triggered this alert? What do I know about this customer?
3. **Evaluate** — What does each piece of evidence establish? What's missing?
4. **Analyze** — What does the system recommend, and on what basis?
5. **Challenge** — What could make that recommendation wrong?
6. **Decide** — FILE, DEFER, or CLOSE — in my own words, with my reasoning
7. **Record** — Confirm and commit the permanent decision record

---

## 2. Layout

### 2.1 Overall structure

```
┌─────────────────────────────────────────────────────────────┐
│  CASE HEADER                                                │
│  ALERT-07 · CUST-MH-114 · ₹85,00,000 · ● 2 WD left       │
├────────────────────────┬────────────────────────────────────┤
│  DECISION RAIL (40%)   │  AI PANEL (60%)                    │
│                        │                                    │
│  [Context]             │  [Run 11-Factor Assessment]        │
│  [Evidence Gaps]       │  [Assessment Tabs]                 │
│  [GoS Editor]          │  [GoS Draft]                       │
│  [Decision Controls]   │  [Quality Score]                   │
│                        │  [Regulatory Inline]               │
└────────────────────────┴────────────────────────────────────┘
```

**Implementation:** `st.columns([2, 3], gap="large")`

### 2.2 Design rationale

**Left column = PO's workspace.** Everything the PO reads, writes, and decides lives here. This is the decision rail — it contains the facts (context), the gaps (evidence callout), the narrative (GoS editor), and the action (decision controls). The PO can work through the left column top-to-bottom and complete their task.

**Right column = System's workspace.** Everything the AI produces lives here. Assessment results, draft narratives, quality scores, and regulatory lookups. The PO consults this column as a reference — they are never forced to interact with it to complete their decision.

**This separation is the product's core UX thesis:** the AI is a tool on the PO's desk, not the desk itself.

### 2.3 Viewport target

Primary: 1440×900 (standard compliance workstation)
The decision controls (FILE / DEFER / CLOSE) must be visible at 900px viewport height without scrolling when the case header and context are rendered.

---

## 3. Case Header

**Location:** Full-width, above the two columns.

### 3.1 Content

| Element | Typography | Color | Position |
|---|---|---|---|
| Alert ID | Monospace, 1.4rem, weight 600 | `TEXT_HEADING` | Left |
| Customer Ref | Monospace, 1.0rem | `TEXT_MONO` | After Alert ID |
| Alert Type | Default, 0.9rem | `TEXT_SECONDARY` | After Customer Ref |
| Signal Source | Default, 0.9rem, badge style | `TEXT_SECONDARY` | After Alert Type |
| Amount | Monospace, 1.1rem, weight 600 | `TEXT_MONO` | Right-aligned block |
| SLA Indicator | `sla_indicator()` — dot + label | SLA color | Right-aligned, below amount |
| Alert Date | Default, 0.8rem | `TEXT_SECONDARY` | Right-aligned, below SLA |

### 3.2 Visual treatment

- Background: `BG_SURFACE`
- Bottom border: `BORDER_EMPHASIS`
- Padding: `SP_LG` (16px)
- Top border-radius: 4px
- Internal layout: flexbox with `justify-content: space-between`

### 3.3 Previous disposition

If the alert has a prior DEFER decision, show it inline:

```
Last action: DEFER — 16 Sep 2026 · "Awaiting source-of-funds clarification"
```

Styled in `TEXT_SECONDARY`, below the main header line.

---

## 4. Decision Rail (left column)

### 4.1 Alert Context Block

**Purpose:** The PO reads this FIRST — before any AI output.

**Content:**

**Signal narrative** (body text, `TEXT_PRIMARY`):
The alert narrative from the monitoring system. This is the "why am I looking at this?" text. Rendered as-is from `ALERT_NARRATIVE`.

**KYC summary** (compact key-value):
```
Account:     Savings (opened 2019)
Profile:     High Value Individual
Risk:        Medium (assigned at onboarding)
Location:    Mumbai
```

Key in `TEXT_SECONDARY`, value in `TEXT_PRIMARY`, monospace for account numbers.

**Red-flag indicators triggered** (monospace IDs with short names):
```
RFI-001  Multiple credits → immediate debit
RFI-003  Dormant reactivation
```

**PO evaluation factors in scope** (comma-separated):
```
Factors: POE-002, POE-003, POE-005, POE-006, POE-008, POE-009
```

### 4.2 Evidence Gap Callout

**Purpose:** Make missing evidence visible before the PO writes their narrative.

**Placement:** Between context and GoS editor. The PO cannot miss it.

**Rendering:**

```
┃ Evidence not available for:
┃ 
┃ POE-005 Income Level — No stated income on file for this customer
┃ POE-006 Source of Income — Source not verified; no EDD response received
```

- Left border: 2px solid `EV_GAP`
- Background: transparent (blends with column)
- Text: `TEXT_PRIMARY` for factor names, `TEXT_SECONDARY` for gap descriptions
- Factor codes in monospace

**When no gaps exist:** This block is not rendered. Absence of the block = all evidence is present.

### 4.3 GoS Editor

**Purpose:** The PO writes (or edits) the Ground of Suspicion narrative that will be filed with FIU-IND.

**Framing text** (above the textarea):
```
Ground of Suspicion — STR Part (c)
This narrative becomes a permanent filing with FIU-IND.
```
- Heading: `TEXT_HEADING`, 1.1rem, weight 600
- Subtext: `TEXT_SECONDARY`, 0.8rem

**Textarea:**
- `st.text_area` with `height=200` (minimum 8 visible lines)
- Default content: empty (PO writes from scratch) or AI draft (if PO clicks "Use as starting point" from AI panel)
- Placeholder: "Describe the specific basis for your suspicion, citing the relevant transactions, customer profile, and evaluation factors."

**Quality indicator** (below textarea, inline):
- Before assessment: not shown
- After assessment: `Quality: 7/10 — PASS` or `Quality: 3/10 — FAIL: revise narrative`
- Color: factor assessment colors (not SLA colors)

**Re-check button:**
- `st.button("Re-check edited draft")` — visible only when the draft has been modified after the last quality check
- Positioned immediately below the textarea

### 4.4 Decision Controls

**Purpose:** The PO records their decision.

**Visual zone:** `BG_DECISION_ZONE` background, `BORDER_EMPHASIS` top border (3px). This zone is visually distinct from everything above it.

**Content:**

**PO identification:**
- `st.text_input("PO ID")` — pre-filled from `_session_user_id()` if available
- `st.date_input("Suspicion formed — date")` + `st.time_input("Time (IST)")`

**Decision buttons:**
- Three buttons in a `st.columns(3)` row:
  - **FILE STR** — styled with `ACTION_FILE` color. Disabled until: (a) GoS quality ≥ 5, (b) PO ID provided, (c) datetime provided
  - **DEFER** — styled with `ACTION_DEFER` color. Always enabled if PO ID provided
  - **CLOSE — No Suspicion** — styled with `ACTION_CLOSE` color. Always enabled if PO ID provided

**Disabled state messaging:**
- When FILE is disabled: inline text below the button explaining why
  - "Quality score below threshold (current: 3/10, required: 5/10)"
  - "PO identification required"
  - "Suspicion formation date required"

**On button click:** Replaces the decision controls zone with `confirmation_panel()`.

### 4.5 Confirmation Panel

**Purpose:** The single most important interaction in the product. The PO reviews exactly what will become the permanent record.

**Trigger:** Clicking FILE, DEFER, or CLOSE.

**Visual treatment:**
- Background: `BG_SURFACE_RAISED`
- Top border: 3px solid `ACTION_FILE` (for FILE) / `ACTION_DEFER` / `ACTION_CLOSE`
- Border radius: 4px

**Content:**

```
┌─────────────────────────────────────────────┐
│ You are about to record:                     │
│                                              │
│ Decision:     FILE STR                       │
│ Alert:        ALERT-07                       │
│ Customer:     CUST-MH-114                    │
│ PO:           NIKHIL.PANDE@BANK.COM          │
│ Suspicion:    18 Sep 2026 14:30 IST          │
│ SLA:          ● 2 WD remaining — within SLA  │
│                                              │
│ Factors cited:                               │
│   [T] POE-002, POE-003, POE-008, POE-009    │
│                                              │
│ Evidence gaps acknowledged:                  │
│   [—] POE-005, POE-006                       │
│                                              │
│ Quality: 7/10 — PASS                         │
│                                              │
│ Rationale (first 200 chars):                 │
│ "The customer's stated business as a small   │
│  retail trader does not explain the receipt   │
│  of ₹85,00,000 from I4C-flagged account..."  │
│                                              │
│ This decision is permanent and will be       │
│ visible to FIU-IND during inspection.        │
│                                              │
│    [Confirm and Record]    [Cancel]           │
└─────────────────────────────────────────────┘
```

**On "Confirm and Record":** Calls `alert_disposition_recorder()` from `skills/core.py`. On success, shows a brief inline confirmation and navigates to the Decision Ledger.

**On "Cancel":** Returns to the pre-decision state with all inputs preserved.

---

## 5. AI Panel (right column)

### 5.1 Assessment trigger

**Before assessment:**
- Single button: `st.button("Run 11-Factor Assessment")`
- Below the button: brief explanatory text: "Evaluates this alert against 11 PO suspicion factors using the regulatory corpus."
- The AI panel is otherwise empty — no placeholder cards, no skeleton UI

**During assessment:**
- Streamlit spinner with text: "Evaluating 11 factors against regulatory corpus…"
- Estimated time note: "Usually takes 15–30 seconds"

**After assessment:**
- Assessment tabs, GoS draft, quality score, and regulatory inline all render

### 5.2 Assessment Tabs

`st.tabs(["Factor Assessment", "Evidence Gaps", "Investigation Plan"])`

**Tab 1 — Factor Assessment:**

Each factor rendered by `factor_row()`:

```
[T] POE-003 Transaction History                          PROVEN
    Credits of ₹85L from I4C-flagged account CUST-WB-221
    inconsistent with stated retail trade volume.
    Rules: RFI-001, RFI-003
```

- Triggered factors: expanded by default (full finding visible)
- Clear factors: collapsed (one-line summary, expandable)
- Insufficient factors: collapsed with `[—]` indicator and "No evidence available" text

**Ordering:** Triggered first, then insufficient (gaps), then clear. Within each group, ordered by factor number.

**Tab 2 — Evidence Gaps:**

Detailed breakdown of factors with insufficient evidence:
- What evidence would be needed
- Where it might be found (KYC records, transaction history, EDD response)
- Investigation priority (which gaps matter most for this case)

**Tab 3 — Investigation Plan:**

AI-generated investigation steps:
- What EDD actions to consider before forming suspicion
- What documents to request
- What account history to review
- Regulatory provisions relevant to the investigation

### 5.3 GoS Draft Block

**Purpose:** AI-generated draft narrative for the PO to review and adopt.

**Visual treatment:**
- `BG_SURFACE_SUNKEN` background
- `BORDER_AI` left border (3px) — marks this as system-generated
- Body text at narrative size (1.0rem)

**Attribution (below the draft):**
```
Draft generated by llama3.3-70b · 14:32 IST · Based on 11-factor assessment
```
In `TEXT_TERTIARY`, 0.75rem.

**Action:**
- `st.button("Use as starting point →")` — copies the draft into the GoS editor in the left column
- The PO is expected to edit the draft, not use it verbatim

### 5.4 Quality Score Block

**Purpose:** Quality assessment of the current GoS narrative.

**Rendering:**
- Score: `7 / 10` in the appropriate color
- Verdict: `PASS` or `FAIL`
- If failures: each failure listed with specific issue
  - "Missing: specific transaction amounts"
  - "Missing: explanation of why alternative explanations were rejected"
  - "Generic language detected: 'transactions appear suspicious'"

### 5.5 Challenge Block

**Purpose:** Help the PO consider what could change their decision.

**Rendering:**
- Header: "What would change this recommendation?"
- AI-generated text addressing:
  - What evidence would shift the assessment from FILE to NOT FILE (or vice versa)
  - Which factors are borderline
  - What alternative explanations exist for the observed pattern

**Visual treatment:** `BG_SURFACE` with no left border accent (this is analysis, not a recommendation).

### 5.6 Regulatory Inline

**Purpose:** Quick access to relevant regulatory provisions without leaving the workspace.

**Rendering:**
- Compact list of rules cited in the assessment
- Each rule rendered by `rule_citation()` — monospace ID, expandable to full text
- Grouped by type: RFI (red-flag indicators), POE (evaluation factors), PMLA provisions

---

## 6. Interaction flows

### 6.1 Happy path: FILE

```
1. PO arrives from Alert Queue → case_header renders with SLA
2. PO reads alert_context_block (signal, KYC, RFIs, factors)
3. PO reads evidence_gap_callout (if gaps exist)
4. PO clicks "Run 11-Factor Assessment" in AI panel
5. Assessment loads → tabs, draft, quality score appear
6. PO reviews factor_rows in Tab 1
7. PO reviews evidence gaps in Tab 2
8. PO reads AI GoS draft
9. PO clicks "Use as starting point →" → draft copies to GoS editor
10. PO edits the narrative in the GoS editor
11. PO clicks "Re-check edited draft" → quality score updates
12. Quality ≥ 5 → FILE button becomes enabled
13. PO enters PO ID + suspicion formation datetime
14. PO clicks "FILE STR"
15. confirmation_panel renders → PO reviews the complete record
16. PO clicks "Confirm and Record"
17. Decision is committed → inline success → navigate to Ledger
```

### 6.2 Happy path: CLOSE (no suspicion)

```
1-6. Same as FILE through factor assessment review
7. PO determines: factors do not establish suspicion
8. PO writes closure rationale in GoS editor (explains why NOT filing)
9. PO enters PO ID + datetime
10. PO clicks "CLOSE — No Suspicion"
11. confirmation_panel renders with CLOSE framing
12. PO confirms → decision committed
```

### 6.3 DEFER path

```
1-6. Same as FILE through factor assessment review
7. PO identifies evidence gaps requiring EDD
8. PO clicks "DEFER"
9. confirmation_panel renders with DEFER framing
10. PO notes what additional EDD is needed (in GoS editor, which serves as the defer rationale)
11. PO confirms → DEFER recorded, alert stays in queue
```

### 6.4 Edge cases

**Assessment times out:**
- Spinner shows for up to 45 seconds, then inline error: "Assessment timed out — retry or use fallback model (llama3.1-8b)"
- Retry button appears in place of spinner
- PO can still write GoS and record DEFER/CLOSE without assessment

**Quality gate fails:**
- FILE button stays disabled
- Inline text explains specific failures
- PO can edit narrative and re-check
- PO can still DEFER or CLOSE (quality gate applies only to FILE)

**Session timeout / page switch:**
- GoS text preserved in `st.session_state` via `_sticky()` helper
- Assessment results preserved in session state
- On return: workspace restores to pre-decision state with all content intact

---

## 7. Data flow

### 7.1 Inputs

| Data | Source | When loaded |
|---|---|---|
| Alert row | `ALERTS` table via SQL | On page render |
| SLA days | Computed from `ALERT_DATE` | On page render |
| Last disposition | `DECISION_LEDGER` LEFT JOIN | On page render |
| 11-factor assessment | `CoPilotSkills.suspicion_evaluator()` | On "Run Assessment" click |
| GoS draft | `CoPilotSkills.ground_of_suspicion_writer()` | Bundled with assessment |
| Quality score | `CoPilotSkills.str_quality_checker()` | After GoS draft generation / on re-check |
| Evidence validation | `CoPilotSkills.validate_gos_evidence()` | After GoS draft generation |
| Evidence summary | `CoPilotSkills.evidence_sufficiency_summary()` | After assessment |
| Regulatory context | `CoPilotSkills.regulatory_lookup()` | Inline on demand / with assessment |

### 7.2 Outputs

| Action | Destination | Function |
|---|---|---|
| Record decision | `DECISION_LEDGER` INSERT | `CoPilotSkills.alert_disposition_recorder()` |
| Mark alert reviewed | `ALERTS` UPDATE | Bundled with disposition recorder |

### 7.3 Session state keys

| Key | Type | Purpose |
|---|---|---|
| `sel_alert` | str | Currently selected alert ID |
| `assessment_result` | dict | Full assessment output |
| `gos_draft` | str | Current GoS text in editor |
| `quality_result` | dict | Last quality check result |
| `po_id` | str | PO identifier |
| `suspicion_date` | date | Suspicion formation date |
| `suspicion_time` | time | Suspicion formation time |
| `confirm_mode` | str/None | Which decision is being confirmed (FILE/DEFER/CLOSE) |
