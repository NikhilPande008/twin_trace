# UI_AUDIT.md — Current UI Audit & AI-Template Detection

**Audited:** 2026-09-25  
**Scope:** `streamlit_app.py` (961 lines), `skills/core.py` (922 lines), live app at 1440×900

---

## 1. Inventory of what exists

### Framework & runtime
- **Framework:** Streamlit 1.56 (single-file `streamlit_app.py`)
- **Deployment target:** Streamlit 
- **Constraints:** No custom JS, no custom React, no external CSS. Limited to `st.columns()`, `st.expander()`, `st.tabs()`, `st.container()`, and `unsafe_allow_html` markdown. No `st.sidebar` layout control in Streamlit (sidebar is this platform-managed).

### Styling architecture
- **Tokens/variables:** None. All colors are inline hex strings in two dicts (`DISP_COLORS`, `EVIDENCE_BADGE`).
- **Typography:** Streamlit default (Source Sans Pro). No heading scale. No distinction between narrative text, numeric data, identifiers, and citations.
- **Spacing:** Streamlit default. `st.divider()` is the only separator.
- **CSS:** Zero custom CSS. All visual differentiation comes from `unsafe_allow_html` spans with inline styles (the `badge()` helper).
- **Icons:** Emoji only (🏦, 🟢, 🟡, 🔴, ⚪, ✍️, 🔍, ↻). No icon library.
- **Dark mode:** Streamlit's default dark theme. No product-specific dark mode tuning.

### Pages
| # | Page | Function | Lines |
|---|---|---|---|
| 1 | Alert Queue | Flat list of alerts sorted by SLA urgency, with filter bar | ~100 |
| 2 | Disposition Panel | Two-column: decision rail (left) + AI panel (right) | ~330 |
| 3 | Decision Ledger | Expander list of past decisions | ~90 |
| 4 | Dashboard | Metric cards + bar chart + NL→SQL (removed) NL→SQL | ~125 |
| 5 | Regulatory Reference | Semantic search + quick-reference list | ~60 |

### Navigation
- Sidebar radio buttons (`st.radio`), five equal-weight items
- "Review →" buttons on Alert Queue navigate to Disposition Panel via `st.session_state`

### Data flow
- All data fetched via `sql()` helper (raw SQL strings with string interpolation)
- AI calls via `CoPilotSkills` class (Nemotron (via Token Factory) → llama3.3-70b with fallback)
- Session state for workflow state (assessment results, GoS draft, selected alert)
- No client-side caching beyond `st.cache_resource` on the connection

---

## 2. Per-area UX/UI audit

### Alert Queue — ACCEPTABLE with GENERIC elements

**What works:**
- SLA pills with color-coding (red/amber/green) — domain-appropriate urgency signal
- Filter bar with search, status, type, source, amount — functional
- "Review →" button navigates directly to the disposition workflow

**What is generic:**
- Layout is a flat row-per-alert list — visually identical to any task queue (Jira, Asana, support tickets). Nothing in the visual structure communicates "AML investigation queue."
- `st.metric` cards at top (Awaiting decision / Due within 1 WD / Overdue / Pending amount) — standard SaaS dashboard pattern. The numbers are useful but the presentation is interchangeable with any operations dashboard.
- Customer profile hidden behind expander — investigation-critical KYC context requires an extra click.
- No visual distinction between alert severity/complexity. A ₹85L dormant reactivation looks identical to a ₹3.45L mule passthrough except for the amount number.
- No signal source iconography. `INTERNAL_RULE` and `I4C` are presented identically as monospace text.

**Rating:** The filter/sort/SLA work is solid operational UX. The visual language is generic.

### Disposition Panel — ACCEPTABLE structure, GENERIC surface, MISSING key interactions

**What works:**
- Two-column layout is the correct structural decision. Left rail for context + decision, right for AI analysis.
- AI assessment is behind a user-initiated button ("Run 11-Factor Assessment") — not automatic, preserving human agency.
- GoS text area is editable — PO can write their own narrative.
- Three-button decision row (FILE / DEFER / CLOSE) is functional.
- Tabs for Assessment / Evidence Gaps / Investigation Plan — reasonable information grouping.

**What is generic:**
- Left column reads top-to-bottom as: bold text, markdown text, h4, textarea, three input fields, three buttons. This is a standard form layout. There is no visual hierarchy communicating "this is a high-stakes regulatory decision."
- Alert summary is plain markdown. Amount, signal source, account type, and alert date run together in a single line with dot separators. No visual weight to the SLA countdown, no visual separation of the signal from the KYC profile.
- The GoS text area is a standard `st.text_area` with a placeholder. There is no visual framing communicating "this text becomes a legal record filed with FIU-IND."
- Decision buttons (FILE STR / DEFER / CLOSE) are visually indistinguishable from any form submission. FILE STR is red (Streamlit `primary` on dark theme). There is no confirmation step, no review state, no visual weight communicating the irreversibility of the action.
- Quality score is a colored number. No decomposition of what passed/failed. The quality failures are behind an expander.
- "Re-check edited draft" is a plain button below the textarea — easy to miss.

**What is missing:**
- **No challenge interaction.** The PO cannot ask "what would make this a NOT FILE case?" in a structured way. The static "What would change this recommendation?" expander is helpful but passive.
- **No evidence chain visualization.** The 11 factors are a flat list of expanders. There is no way to see which evidence supports which finding, or which findings conflict.
- **No contradiction visibility.** If POE-003 (Transaction History) is triggered but POE-005 (Income Level) is clear, there is no visual signal that these might be in tension.
- **No missing-evidence urgency.** Insufficient-data factors are white circles (⚪) in a list — they blend with clear factors visually.
- **No regulatory citation inline with findings.** Rules cited are listed as IDs (`RFI-001`, `POE-005`) but there is no way to see the rule text without switching to the Regulatory Reference page.
- **No AI-vs-human boundary.** The AI recommendation and the human decision controls exist in the same visual field with no structural separator communicating "above this line = system analysis; below this line = your decision."
- **No decision confirmation/review.** Clicking "FILE STR" records immediately (after validation). There is no "review your decision" intermediate state.

**Rating:** The two-column structure is right. Everything on top of it is generic form rendering.

### Decision Ledger — ACCEPTABLE for audit, GENERIC presentation

**What works:**
- Append-only semantics correctly communicated via tooltip
- Expander per decision row — clean
- Decision provenance metadata (WS-4) shown when available

**What is generic:**
- Every row is a Streamlit expander. The visual pattern is identical to any log viewer or event list.
- No timeline visualization. Decisions are ordered by timestamp but there is no visual sense of time passing, SLA windows, or investigation progression.
- SLA days remaining is a colored number. Useful but minimal.

**Rating:** Functional audit trail. Not distinctive.

### Dashboard — GENERIC

**What is generic:**
- `st.metric` card grid (4 + 3 cards) — the canonical "AI SaaS dashboard" pattern
- `st.bar_chart` for alert type breakdown — default Streamlit charting
- Signal source mix is plain markdown text — not even a chart
- NL→SQL (removed) NL→SQL ("Ask the data") is a text input + button + dataframe — standard AI chatbot-adjacent pattern
- Alert-to-STR ratio interpretation guide is a markdown table — static reference content mixed into an operational dashboard

**What works:**
- The metrics themselves are correct and operationally meaningful
- The interpretation guide is genuinely useful domain content

**Rating:** This page would be indistinguishable from any analytics dashboard if you changed the metric labels.

### Regulatory Reference — ACCEPTABLE

**What works:**
- Evidence level badges (PROVEN / ASSUMED) with distinct colors — domain-specific and useful
- Source document, snapshot date, and primary source link shown — provenance is visible
- PO-lens synthesis gives the PO a human-language interpretation

**What is generic:**
- Search + results list is a standard RAG search pattern
- Results are in expanders — same visual treatment as every other list in the app

**Rating:** The content is domain-rich. The presentation is not.

---

## 3. AI-Template Detection Test

### The 5-second test

> If an experienced AI-product developer saw this application for five seconds, would they recognize it as a typical AI-generated application?

**Yes.**

**Specific signals:**
1. **Sidebar + Header + Metric Cards + List/Expanders + Buttons** — this is the canonical Streamlit app template. Every Streamlit tutorial produces this layout.
2. **Dark theme with colored badges** — standard Streamlit dark mode. No custom visual identity.
3. **`st.metric` cards** — the single most recognizable Streamlit pattern. Four metric cards at the top of a page is the Streamlit equivalent of "this was built in a hackathon."
4. **Emoji as iconography** (🏦, 🟢, 🔴, ✍️, 🔍) — functional but unmistakably AI-generated/prototype-stage.
5. **No custom typography, no custom color system, no custom spacing** — everything is Streamlit defaults with inline HTML color overrides.
6. **"Run 11-Factor Assessment" primary button → spinner → expander results** — this is the standard "Call AI → Show Results" pattern from every AI demo app.

### Layout test
The structure is: **Sidebar (radio nav) + Header + Content Area (metric cards / list / form)**. This is the default Streamlit layout. It could be:
- An HR SaaS showing employee performance reviews
- A CRM showing lead qualification stages
- A project management tool showing task queues
- A generic AI assistant showing document analysis results

Change the labels and it works for any of those products.

### Design identity test
Could the product be visually recognized without reading its name?

**No.** There is no distinctive visual element — no domain-specific color system, no investigation-specific iconography, no typography hierarchy that communicates "financial compliance." The 🏦 emoji in the sidebar is the only visual cue, and it's a Unicode character.

### Composition test
Is the application primarily **Sidebar + Header + Cards + Table/List + Buttons**?

**Yes.** That is the exact composition of all five pages.

---

## 4. What should be retained

1. **Two-column Disposition Panel layout** — structurally correct. The left-rail / right-panel split is the right information architecture for this workflow.
2. **SLA urgency encoding** — red/amber/green for days remaining is correct and should be kept.
3. **Evidence level badges** (PROVEN / ASSUMED / NEEDS-VERIFICATION) — domain-appropriate. The concept is right; the visual execution can improve.
4. **11-factor assessment structure** — evaluating each factor individually with triggered/clear/insufficient states is the correct domain model.
5. **GoS quality score + hard gate** — the quality feedback loop is valuable.
6. **Append-only ledger semantics** — correct regulatory constraint, correctly implemented.
7. **Filter bar on Alert Queue** — functional and necessary at scale.
8. **Assessment → Evidence Gaps → Investigation Plan tab grouping** — correct information hierarchy.
9. **All business logic in `skills/core.py`** — clean separation from UI. Must not be changed.

## 5. What should be redesigned

1. **Visual identity** — the app needs a distinctive visual language that communicates "financial investigation workspace," not "Streamlit prototype."
2. **Information density** — the current layout wastes vertical space (Streamlit's generous padding) while hiding critical information behind expanders.
3. **Evidence presentation** — factors as flat expander lists → evidence chains with relationships, contradictions, and gaps visible at a glance.
4. **Decision moment** — FILE/DEFER/CLOSE as equal-weight buttons → a controlled, confirmable action with the decision rationale, regulatory basis, and remaining uncertainty summarized.
5. **Regulatory provenance** — rule IDs as plain text → inline citations with source context.
6. **AI-vs-human boundary** — no visual separator → explicit architectural boundary between "system analysis" and "your decision."
7. **Challenge interaction** — missing entirely → structured way to interrogate the recommendation.
8. **Alert Queue visual hierarchy** — flat row list → scannable cards/rows with signal severity, complexity, and urgency communicated visually.
9. **Dashboard** — metric card grid → operationally useful inspection-readiness view with timeline and trend context.
10. **Navigation hierarchy** — five equal-weight pages → primary workflow (Queue → Investigation → Decision) with supporting pages subordinate.

---

## 6. Streamlit constraints

These are hard constraints that any redesign must work within:

| Constraint | Impact |
|---|---|
| No custom JS | No custom interactions, no drag-and-drop, no custom charts beyond `st.bar_chart`/`st.line_chart`/`st.plotly_chart` |
| No custom React components | No custom component library. Must use Streamlit primitives. |
| No external CSS files | All styling via `unsafe_allow_html` with inline styles or Streamlit's built-in theming |
| No `st.sidebar` layout control | Sidebar content is controlled, but Streamlit may manage sidebar chrome |
| Streamlit's execution model | Every interaction re-runs the entire script. No persistent client-side state beyond `st.session_state`. |
| Column widths are proportional | `st.columns([2, 3])` is the most control available. No px/rem widths. |
| Limited native components | `st.metric`, `st.expander`, `st.tabs`, `st.columns`, `st.container`, `st.text_area`, `st.selectbox`, `st.radio`, `st.button`, `st.markdown` |
| `unsafe_allow_html` for rich rendering | All visual differentiation beyond Streamlit defaults requires inline HTML/CSS in markdown |

**Key implication:** The redesign cannot introduce new components in the traditional sense. "Components" here means **composite patterns built from Streamlit primitives + inline HTML**, documented as reusable Python functions.
