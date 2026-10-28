# UI_IMPLEMENTATION_PLAN.md — Ordered Implementation Plan

**Date:** 2026-09-25  
**Product:** FIU-IND AML Copilot — Decision Workbench  
**Target file:** `streamlit_app.py` (961 lines)  
**Constraint:** No changes to `skills/core.py` — all business logic stays untouched

---

## Implementation philosophy

1. **Single file.** Everything remains in `streamlit_app.py`. No new files except design docs.
2. **Incremental.** Each phase produces a working app. No phase breaks existing functionality.
3. **Test after each phase.** Run `python3 -m py_compile streamlit_app.py` + manual browser verification after every phase.
4. **Token-first.** Design tokens are introduced in Phase 1 and used by every subsequent phase.

---

## Phase 1: Design tokens and shared helpers

**Estimated effort:** 30 minutes  
**Risk:** Low — additive, no changes to existing rendering  
**Dependencies:** None

### Tasks

1. Add `TOKENS` dict at module level (all color, spacing, typography values from `DESIGN_SYSTEM.md`)
2. Add shared helper functions:
   - `_badge(label, bg_color, text_color)` → inline HTML span
   - `_mono(text)` → monospace-styled span
   - `_sla_pill(days_left)` → SLA urgency indicator (replaces current `sla_pill()`)
   - `_surface(content, bg, border_left, border_top, radius)` → container HTML
   - `_kv(key, value)` → key-value pair HTML (key in secondary, value in primary)
   - `_factor_indicator(state)` → `[T]`/`[C]`/`[—]` with colored background
3. Replace existing `DISP_COLORS`, `EVIDENCE_BADGE`, `sla_pill()`, `sla_color()`, `badge()` with token-based equivalents
4. Verify: all existing pages render correctly with new tokens

### Files modified
- `streamlit_app.py`: lines ~1–80 (constants and helpers section)

### Validation
- `python3 -m py_compile streamlit_app.py`
- All 5 pages render without visual regression
- Colors match `DESIGN_SYSTEM.md` token values

---

## Phase 2: Case Header component

**Estimated effort:** 20 minutes  
**Risk:** Low  
**Dependencies:** Phase 1

### Tasks

1. Implement `_case_header(alert_row, sla_days, last_disp)` function
   - Full-width HTML block with flexbox layout
   - Alert ID (mono, large), customer ref, type, source, amount, SLA pill, date
   - Previous disposition if exists
   - `BG_SURFACE` background, `BORDER_EMPHASIS` bottom border
2. Integrate into `page_disposition()` — replace current alert summary markdown
3. Verify at 1440×900: header fits on one visual line

### Files modified
- `streamlit_app.py`: new function + modification of `page_disposition()`

### Validation
- Case header renders correctly for alerts with and without prior dispositions
- SLA colors are correct (test with overdue, urgent, and normal alerts)

---

## Phase 3: Alert Queue redesign

**Estimated effort:** 45 minutes  
**Risk:** Medium — replaces the entire queue rendering  
**Dependencies:** Phase 1

### Tasks

1. Implement `_queue_summary_bar(counts)` — single-line summary replacing `st.metric` cards
2. Implement `_alert_queue_row(alert, sla_days, last_disp)` — two-line HTML row with SLA urgency left-border
3. Rewrite `page_alert_queue()`:
   - Replace metric card grid with `_queue_summary_bar()`
   - Replace current row rendering with `_alert_queue_row()` per alert
   - Keep filter bar (functional, just restyle labels)
   - Keep "Review →" navigation logic
4. Remove emoji icons from queue display

### Files modified
- `streamlit_app.py`: `page_alert_queue()` rewrite

### Validation
- Queue renders 15 alerts with correct SLA colors and urgency borders
- Filter bar still works (search, status, type, source, amount)
- "Review →" still navigates to disposition panel
- No `st.metric` cards anywhere on the page

---

## Phase 4: Decision Rail — Context and Gaps

**Estimated effort:** 30 minutes  
**Risk:** Medium  
**Dependencies:** Phase 1, Phase 2

### Tasks

1. Implement `_alert_context_block(alert_row)`:
   - Signal narrative (body text)
   - KYC summary (compact key-value)
   - RFI triggers (monospace IDs)
   - POE factors in scope
2. Implement `_evidence_gap_callout(gaps)`:
   - Left-border accent block listing each gap with factor code and description
3. Integrate into left column of `page_disposition()`:
   - Context block at top of left column
   - Gap callout between context and GoS editor

### Files modified
- `streamlit_app.py`: new functions + left column of `page_disposition()`

### Validation
- Context block shows all alert metadata without expander gates
- Gap callout renders when assessment has insufficient factors
- Gap callout hidden when all factors have evidence

---

## Phase 5: AI Panel redesign

**Estimated effort:** 45 minutes  
**Risk:** Medium  
**Dependencies:** Phase 1

### Tasks

1. Redesign assessment tabs rendering:
   - `_factor_row()` component with state indicators, evidence badges, rule citations
   - Triggered factors expanded by default, clear/insufficient collapsed
   - Ordering: triggered → insufficient → clear
2. Redesign GoS draft display:
   - `_gos_draft_block()` with `BG_SURFACE_SUNKEN`, `BORDER_AI` left border
   - Model attribution in `TEXT_TERTIARY`
   - "Use as starting point →" button
3. Redesign quality score display:
   - `_quality_score_block()` with score, verdict, and specific failures
4. Add challenge block:
   - "What would change this recommendation?" section from assessment output
5. Add inline regulatory citations:
   - `_rule_citation()` components for rules cited in the assessment

### Files modified
- `streamlit_app.py`: right column of `page_disposition()`, new helper functions

### Validation
- All 11 factors render with correct state indicators
- GoS draft has AI attribution and visual framing
- Quality score shows specific failures when present
- Rule citations expand to show full text

---

## Phase 6: GoS Editor and Decision Controls

**Estimated effort:** 45 minutes  
**Risk:** High — modifies the core decision recording flow  
**Dependencies:** Phase 1, Phase 4, Phase 5

### Tasks

1. Redesign GoS editor:
   - Framing text ("Ground of Suspicion — STR Part (c)")
   - Visual container with `BORDER_EMPHASIS`
   - Inline quality indicator below textarea
   - "Re-check edited draft" button logic
2. Redesign decision controls zone:
   - `BG_DECISION_ZONE` background with `BORDER_EMPHASIS` top border
   - PO ID and datetime inputs
   - Three styled decision buttons
   - Disabled-state messaging for FILE button
3. Implement `_confirmation_panel()`:
   - Full decision review display
   - "Confirm and Record" + "Cancel" buttons
   - Calls `alert_disposition_recorder()` on confirm
4. Session state management:
   - `confirm_mode` state for tracking which decision is being confirmed
   - Preserve all inputs on cancel

### Files modified
- `streamlit_app.py`: left column of `page_disposition()`, new confirmation flow

### Validation
- FILE button disabled when quality < 5 or PO ID missing
- Confirmation panel shows complete decision summary
- "Confirm and Record" successfully writes to DECISION_LEDGER
- "Cancel" returns to pre-decision state with inputs preserved
- All existing validation guards (from `skills/core.py`) still enforced

---

## Phase 7: Decision Ledger redesign

**Estimated effort:** 20 minutes  
**Risk:** Low  
**Dependencies:** Phase 1

### Tasks

1. Implement `_ledger_timeline_header(stats)` — single-line summary replacing any metric cards
2. Redesign `_ledger_entry()` expander content:
   - Decision action badge with timestamp and PO
   - Full GoS narrative
   - Factors cited, quality score, evidence gaps
   - Assessment provenance (WS-4 data if available)
3. Remove emoji from ledger display

### Files modified
- `streamlit_app.py`: `page_ledger()` rewrite

### Validation
- All existing ledger entries render correctly
- Expanded view shows complete decision reconstruction
- No information loss compared to current implementation

---

## Phase 8: Dashboard and Regulatory Reference

**Estimated effort:** 30 minutes  
**Risk:** Low  
**Dependencies:** Phase 1

### Tasks

1. Dashboard:
   - Replace `st.metric` card grid with `_ops_summary_line()`
   - Keep bar chart (functional)
   - Restyle NL→SQL (removed) section (remove "Ask the data" chatbot framing)
2. Regulatory Reference:
   - Apply evidence badges using token colors
   - Apply `_surface()` for result blocks
   - Remove emoji

### Files modified
- `streamlit_app.py`: `page_dashboard()` and `page_reference()` modifications

### Validation
- No `st.metric` cards on dashboard
- NL→SQL (removed) still functional
- Regulatory search still returns results with correct evidence badges

---

## Phase 9: Navigation hierarchy

**Estimated effort:** 15 minutes  
**Risk:** Low  
**Dependencies:** All previous phases

### Tasks

1. Restructure sidebar radio navigation:
   - Primary: "Alert Queue", "Case Workspace" (renamed from "Disposition Panel")
   - Secondary: "Decision Ledger", "Dashboard", "Regulatory Reference"
   - Visual separation between primary and secondary (using a markdown divider in sidebar)
2. Update page titles and any cross-page navigation references

### Files modified
- `streamlit_app.py`: sidebar rendering, page title strings

### Validation
- Navigation works for all pages
- "Review →" from queue navigates to "Case Workspace"
- No broken session state references

---

## Phase 10: Polish and cleanup

**Estimated effort:** 20 minutes  
**Risk:** Low  
**Dependencies:** All previous phases

### Tasks

1. Remove all emoji from the app (verify with grep)
2. Remove all `st.metric` calls (verify with grep)
3. Remove any remaining `DISP_COLORS` / `EVIDENCE_BADGE` references replaced by tokens
4. Verify all `st.success` / `st.error` / `st.warning` / `st.info` banners are replaced with inline styled text
5. Final browser verification at 1440×900:
   - All 5 pages render correctly
   - Decision flow works end-to-end (assessment → draft → edit → quality check → FILE → confirm)
   - Ledger shows recorded decision
6. Run `python3 -m py_compile streamlit_app.py`
7. Run `python3 -m pytest tests/test_offline.py` — all 14 tests pass

### Files modified
- `streamlit_app.py`: cleanup throughout

### Validation
- Zero emoji in source code
- Zero `st.metric` calls
- Zero Streamlit toast/banner calls for feedback
- All tests pass
- Manual end-to-end verification passes

---

## Estimated total effort

| Phase | Effort | Risk |
|---|---|---|
| 1. Design tokens | 30 min | Low |
| 2. Case header | 20 min | Low |
| 3. Alert queue | 45 min | Medium |
| 4. Context + gaps | 30 min | Medium |
| 5. AI panel | 45 min | Medium |
| 6. GoS + decision | 45 min | High |
| 7. Decision ledger | 20 min | Low |
| 8. Dashboard + reference | 30 min | Low |
| 9. Navigation | 15 min | Low |
| 10. Polish | 20 min | Low |
| **Total** | **~5 hours** | |

---

## Risk mitigation

1. **Phase 6 is the highest-risk phase.** It modifies the decision recording flow — the product's core value. Test the full flow (assessment → draft → edit → re-check → FILE → confirm → record) after every change within this phase.
2. **Backup before Phase 1.** Copy `streamlit_app.py` to `streamlit_app.py.bak-pre-redesign`.
3. **Compile-check after every function change.** `python3 -m py_compile streamlit_app.py` catches syntax errors immediately.
4. **Session state.** The confirmation panel introduces new session state (`confirm_mode`). Test that page switches (sidebar navigation) don't leave stale confirmation state.
5. **SiS deployment.** Test locally with `streamlit run` before deploying to this platform with `snow streamlit deploy --replace`. Streamlit may have subtle differences in CSS rendering.
