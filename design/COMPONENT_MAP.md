# COMPONENT_MAP.md — Domain-Specific Component Architecture

**Date:** 2026-09-25  
**Product:** FIU-IND AML Copilot — Decision Workbench  
**Platform:** Streamlit — "components" = reusable Python functions generating HTML + Streamlit widgets

---

## Implementation note

There are no React components, no JS modules, no CSS classes. Every "component" in this document is a Python function that:
1. Takes domain data as input
2. Returns/renders a combination of `st.markdown(html, unsafe_allow_html=True)` and Streamlit widgets
3. Uses tokens from `DESIGN_SYSTEM.md`

Components are organized by the page/zone they serve.

---

## 1. Shared components

### 1.1 `case_header(alert_row, sla_days, last_disposition)`

The persistent identity bar at the top of any case-focused view.

**Renders:**
- Alert ID (monospace, large): `ALERT-07`
- Customer ref (monospace): `CUST-MH-114`
- Alert type + signal source: `MULE_PASS_THROUGH · I4C`
- Amount (monospace, formatted): `₹85,00,000`
- SLA pill: `● 2 WD left` (amber)
- Alert date: `18 Sep 2026`
- Last disposition (if any): `DEFER — 16 Sep 2026`

**Layout:** Single `st.markdown` block with a `BG_SURFACE` background, `BORDER_EMPHASIS` bottom border. All items arranged horizontally with flexbox inside the HTML.

**Why this is domain-specific:** No generic header component carries an SLA countdown, a monospace financial amount, and a regulatory disposition state.

---

### 1.2 `sla_indicator(days_left)`

SLA urgency as dot + label.

**Renders:** `● {N} WD left` or `● OVERDUE ({N}d)` with SLA color.

**Rules:**
- ≤ 0 → `SLA_CRITICAL`, "OVERDUE"
- 1–2 → `SLA_URGENT`, "{N} WD left"
- 3+ → `SLA_NORMAL`, "{N} WD left"

---

### 1.3 `evidence_badge(level)`

Inline badge showing evidence confidence.

**Renders:** `PROVEN` or `ASSUMED` as a styled inline span with the appropriate background color.

**Interaction:** None — purely presentational.

---

### 1.4 `rule_citation(rule_id, rule_text_short, rule_text_full)`

Inline rule reference with expandable detail.

**Renders:**
- Inline: `RFI-003` (monospace, clickable-style underline)
- On expansion (via `st.expander` or inline toggle): full rule text in a `BG_SURFACE_SUNKEN` block with evidence level badge and source attribution

**Why this is domain-specific:** Regulatory citations with inline expansion are unique to compliance workflows.

---

### 1.5 `decision_action_badge(disposition, timestamp, po_id)`

Compact display of a recorded decision.

**Renders:** `FILE · 18 Sep 2026 14:30 IST · PO: Nikhil P.` with `ACTION_FILE` color for FILE, `ACTION_CLOSE` for CLOSE, `ACTION_DEFER` for DEFER.

---

## 2. Alert Queue components

### 2.1 `alert_queue_row(alert, sla_days, last_disp)`

One alert row in the queue.

**Renders (single HTML block):**

```
● 2 WD   ALERT-07   MULE_PASS_THROUGH   I4C   ₹85,00,000   CUST-MH-114
          Savings · High Value · 18 Sep 2026                    [Review →]
```

**Layout:** Two-line row. First line: SLA dot, alert ID (mono), type, source, amount (mono), customer ref (mono). Second line: account type, profile, date, right-aligned Review button.

**Visual differentiation by urgency:**
- SLA ≤ 0: left border `SLA_CRITICAL` (2px)
- SLA 1–2: left border `SLA_URGENT` (2px)
- SLA 3+: no left border accent

**Interaction:** "Review →" navigates to Disposition Panel with this alert selected.

---

### 2.2 `queue_filter_bar()`

Filter/search controls above the queue.

**Renders (Streamlit widgets):**
- `st.text_input` — search by alert ID or customer ref
- `st.selectbox` — filter by status (All / Awaiting / Reviewed)
- `st.selectbox` — filter by alert type
- `st.selectbox` — filter by signal source
- `st.selectbox` — filter by amount range

**Layout:** `st.columns(5)` — one widget per column.

---

### 2.3 `queue_summary_bar(counts)`

Compact case count summary replacing `st.metric` cards.

**Renders (single HTML block):**

```
14 awaiting · 3 due within 1 WD · 1 overdue · ₹4.2Cr pending
```

One line, left-aligned, with SLA color for the "due" and "overdue" counts. No cards, no grid, no elevation.

---

## 3. Disposition Panel components

### 3.1 Layout structure

```
┌─────────────────────────────────────────────────────────┐
│  case_header(...)                                       │
├───────────────────────────┬─────────────────────────────┤
│  DECISION RAIL            │  AI PANEL                   │
│  (left, st.columns[2])    │  (right, st.columns[3])     │
│                           │                             │
│  alert_context_block()    │  assessment_tabs()          │
│  evidence_gap_callout()   │    ├ Factor Assessment      │
│  gos_editor()             │    ├ Evidence Gaps           │
│  decision_controls()      │    └ Investigation Plan     │
│                           │  gos_draft_block()          │
│                           │  quality_score_block()      │
│                           │  regulatory_inline()        │
└───────────────────────────┴─────────────────────────────┘
```

Two columns: `st.columns([2, 3], gap="large")`.

Left = PO's zone (context, narrative, decision). Right = system's zone (AI assessment, draft, quality).

---

### 3.2 `alert_context_block(alert_row)`

Alert signal and KYC context for the PO to read before seeing AI output.

**Renders:**
- **Signal block:** Alert narrative (the triggering signal description) in body text
- **KYC summary:** Customer profile, account type, relationship duration — compact key-value pairs
- **RFI triggers:** Which red-flag indicators the monitoring system flagged, each with monospace ID
- **POE factors:** Which evaluation factors apply, as a compact comma-separated list

**Layout:** Vertical stack within the left column, above the GoS editor.

---

### 3.3 `evidence_gap_callout(gaps)`

Dedicated block highlighting what evidence is missing.

**Renders:**

```
┃ Evidence gaps
┃ POE-005 (Income Level): No stated income on file
┃ POE-006 (Source of Income): Source not verified against transaction pattern
```

Left-border accent in `EV_GAP` color. Each gap names the specific factor and what is missing.

**Placement:** Between context and GoS editor — the PO sees gaps before writing.

---

### 3.4 `gos_editor(current_draft, quality_result)`

The Ground of Suspicion narrative editor.

**Renders:**
- Section label: "Ground of Suspicion — STR Part (c)" in heading style
- Framing text: "This narrative will be filed with FIU-IND as the basis for your decision." in `TEXT_SECONDARY`
- `st.text_area` — minimum 8 lines height, with the current draft or AI-generated text
- Quality indicator (inline, below textarea): score and pass/fail state from the quality checker
- "Re-check edited draft" button (if draft has been modified)

**Visual framing:** The textarea sits inside an HTML block with `BORDER_EMPHASIS` border and a subtle label communicating "legal document."

---

### 3.5 `decision_controls(alert_id, gos_text, assessment_result)`

The decision recording zone.

**Renders (inside `BG_DECISION_ZONE` with `BORDER_EMPHASIS` top border):**

**Pre-decision state:**
- PO ID and datetime inputs (who is deciding, when was suspicion formed)
- Three decision buttons: FILE STR / DEFER / CLOSE
- FILE button uses `ACTION_FILE` color; others use muted colors

**Post-click / confirmation state (replaces the buttons):**
- `confirmation_panel(...)` — see below

**Guards:**
- FILE button disabled until GoS passes quality gate (score ≥ 5)
- FILE button disabled until PO ID and datetime are provided
- Hard gate failure shows inline warning (not a banner): "Quality score below threshold — revise the narrative"

---

### 3.6 `confirmation_panel(decision, alert_id, gos_text, factors, po_id, timestamp)`

Review-before-record confirmation.

**Renders (inside `BG_SURFACE_RAISED` with `ACTION_FILE` top border for FILE):**

```
You are about to record:

  Decision:    FILE STR
  Alert:       ALERT-07
  PO:          Nikhil P.
  Suspicion formed:  18 Sep 2026 14:30 IST
  SLA status:  2 WD remaining — within deadline
  
  Factors cited:     POE-002 (Business Profile), POE-003 (Transaction History), ...
  Evidence gaps:     POE-005 (Income Level), POE-006 (Source of Income)
  Quality score:     7/10 — PASS
  
  Rationale preview:
  "The customer's stated business as a small retail trader does not explain
   the receipt of ₹85,00,000 from a flagged I4C account..."
  
  [Confirm and Record]    [Cancel]
```

**Key design decision:** The PO reads exactly what will become the permanent record before it is committed. This is the most important interaction in the product.

---

### 3.7 `assessment_tabs(assessment_result)`

AI assessment output organized in tabs.

**Renders (via `st.tabs`):**

**Tab 1 — Factor Assessment:**
- List of 11 factors, each rendered by `factor_row()`
- Triggered factors expanded by default; clear/insufficient collapsed
- Each factor shows: state indicator (`[T]`/`[C]`/`[—]`), factor name, one-line finding, rules cited (as `rule_citation`)

**Tab 2 — Evidence Gaps:**
- Factors with insufficient evidence, with specific description of what's missing
- Suggested investigation actions from the assessment

**Tab 3 — Investigation Plan:**
- AI-generated investigation steps
- Links to relevant regulatory provisions

---

### 3.8 `factor_row(factor_code, factor_name, state, finding, rules_cited, evidence_level)`

Single factor assessment display.

**Renders:**

```
[T] POE-003 Transaction History                              PROVEN
    Credits of ₹85L from I4C-flagged account CUST-WB-221     RFI-001, RFI-003
    inconsistent with stated retail trade volume.
```

**State indicators:**
- `[T]` triggered — `FACTOR_TRIGGERED` background
- `[C]` clear — `FACTOR_CLEAR` background
- `[—]` insufficient — `FACTOR_INSUFFICIENT` background

---

### 3.9 `gos_draft_block(draft_text, model_id, timestamp)`

AI-generated GoS draft in the AI panel.

**Renders:**
- Draft text in a `BG_SURFACE_SUNKEN` block with `BORDER_AI` left border
- Attribution: "Draft generated by llama3.3-70b at 14:32 IST" in `TEXT_TERTIARY`
- "Use as starting point →" button to copy into the GoS editor

**Visual framing:** The AI attribution and the left border clearly mark this as system-generated, not PO-authored.

---

### 3.10 `quality_score_block(score, max_score, failures)`

GoS quality assessment display.

**Renders:**
- Score: `7 / 10` with color coding (green ≥ 5, amber 3–4, red ≤ 2 — using factor colors, NOT SLA colors)
- Pass/fail verdict: "PASS — meets FIU-IND quality threshold" or "FAIL — revisions needed"
- If failures exist: each failure as a compact line with the specific issue

---

## 4. Decision Ledger components

### 4.1 `ledger_entry(decision_row, evidence_snapshot)`

One expandable decision record.

**Header (always visible):**
```
ALERT-07 · FILE · 18 Sep 2026 14:30 IST · PO: Nikhil P. · ● 2 WD left
```

**Expanded (via `st.expander`):**
- Ground of Suspicion narrative (full text)
- Factors cited in the decision
- Quality score at time of filing
- Evidence gaps acknowledged
- Assessment snapshot (if `WS-4` provenance data available)
- Timestamps: alert date, suspicion formed, decision recorded

---

### 4.2 `ledger_timeline_header(stats)`

Summary bar above the ledger.

**Renders:**
```
23 decisions recorded · 18 FILE · 3 CLOSE · 2 DEFER · Last: 18 Sep 2026
```

One line, compact, no metric cards.

---

## 5. Dashboard components

### 5.1 `ops_summary_line(stats)`

Replaces metric card grid.

**Renders:**
```
Queue: 14 awaiting (3 urgent, 1 overdue) · Filed this month: 8 · Avg SLA: 3.2 WD · Alert-to-STR ratio: 57%
```

One or two lines of operational summary. Key figures in monospace. SLA-colored urgency counts inline.

---

### 5.2 `analyst_query_block()`

NL→SQL (removed) NL→SQL interface.

**Renders:**
- `st.text_input` with label "Query your alerts and decisions"
- `st.button` "Run query"
- Results in `st.dataframe`

**Visual differentiation from current:** No "Ask the data" chatbot framing. Labeled as a query tool, not an AI conversation.

---

## 6. Regulatory Reference components

### 6.1 `regulatory_search_block()`

Corpus search interface.

**Renders:**
- `st.text_input` — search query
- Results list: each result as a compact block with title, evidence level badge, source document, and expandable full text

---

### 6.2 `rule_detail_block(rule)`

Full rule display.

**Renders:**
- Rule ID (monospace): `RFI-003`
- Title: "Dormant account reactivation"
- Evidence level badge: `PROVEN`
- Full text in `BG_SURFACE_SUNKEN` block
- Source: document name, snapshot date, primary source link
- PO-lens synthesis: one-line plain-language interpretation

---

## 7. Component dependency map

```
Shared
  ├── case_header
  ├── sla_indicator
  ├── evidence_badge
  ├── rule_citation
  └── decision_action_badge

Alert Queue
  ├── queue_summary_bar ←── sla_indicator
  ├── queue_filter_bar
  └── alert_queue_row ←── sla_indicator

Disposition Panel
  ├── case_header
  ├── alert_context_block
  ├── evidence_gap_callout
  ├── gos_editor
  ├── decision_controls
  │   └── confirmation_panel
  ├── assessment_tabs
  │   └── factor_row ←── rule_citation, evidence_badge
  ├── gos_draft_block
  ├── quality_score_block
  └── regulatory_inline ←── rule_citation

Decision Ledger
  ├── ledger_timeline_header
  └── ledger_entry ←── decision_action_badge

Dashboard
  ├── ops_summary_line
  └── analyst_query_block

Regulatory Reference
  ├── regulatory_search_block
  └── rule_detail_block ←── evidence_badge
```
