# DESIGN_REVIEW.md — Four-Perspective Review

**Date:** 2026-09-25

---

## Review 1: Principal Officer perspective

> "Does this workspace let me do my job — investigate and decide — without fighting the tool?"

**Verdict: Yes, with one reservation.**

**What works:**
1. The cognitive sequence (Orient → Understand → Evaluate → Analyze → Challenge → Decide → Record) is explicitly supported. The left column maps to the PO's internal process, not the AI's.
2. Evidence before opinion — I see the signal, KYC, and gaps before the system tells me what it thinks. This matches how I actually work.
3. The confirmation panel is critical. I cannot accidentally file an STR. I review exactly what FIU-IND will see before it becomes permanent.
4. SLA urgency on every surface — I always know how much time I have.
5. The GoS editor is framed as a legal document, not a comment box. This communicates the weight of what I'm writing.

**Reservation:**
The two-column layout assumes I work left-to-right. In practice, I sometimes start by scanning the AI assessment (right) to orient myself, then go back to the evidence (left). The design should not prevent this — the columns should both be visible and independently scrollable. The current spec supports this (no wizard/stepper enforcement), but implementation must preserve it.

---

## Review 2: UX Designer perspective

> "Does the interaction design serve the user's task, and does it avoid common pitfalls?"

**Verdict: Strong, with notes.**

**Strengths:**
1. The confirmation panel is the standout UX decision. It transforms a button click into a deliberate review, which is exactly right for an irreversible regulatory action.
2. Evidence gap callout — making absence visible is a sophisticated UX pattern that most compliance tools miss.
3. The AI-vs-PO boundary (left = yours, right = system's) is architecturally clean. It doesn't require the PO to understand "AI" — it just organizes the workspace by agency.
4. No wizard/stepper — the PO can jump between sections. This respects expert users who don't follow a fixed order.

**Notes:**
1. The "Use as starting point →" button for the GoS draft is a critical interaction. It must be prominent enough that the PO discovers it, but not so prominent that it becomes the default path (which would produce templated STRs). Consider: after copying, show a brief inline note: "Edit this draft to reflect your specific findings."
2. The challenge block ("What would change this recommendation?") is passive text. Consider making it interactive in a future iteration — e.g., the PO selects a factor and the system re-evaluates without it.
3. Error states need to be tested: what happens when the assessment times out mid-investigation? The spec says the PO can still DEFER/CLOSE — verify this works without session state corruption.

---

## Review 3: Visual Designer perspective

> "Does the visual system create a distinctive, professional identity within Streamlit's constraints?"

**Verdict: Achievable and differentiated.**

**Strengths:**
1. The warm neutral palette (tan monospace, paper-toned surfaces, muted functional colors) is visually distinct from both Streamlit's cold dark theme and the blue/purple AI aesthetic. A PO would not mistake this for a generic SaaS dashboard.
2. Exclusive SLA color use (red/amber/green reserved for urgency, nothing else) is disciplined. It gives the urgency encoding real visual authority.
3. The `ACTION_FILE` red as the only high-saturation warm color on the page is a strong hierarchy decision. The eye goes to the FILE button.
4. Left-border zone accents (AI panel, decision rail, gap callout) are a simple but effective way to create spatial identity without shadows or cards.

**Concerns:**
1. Streamlit's default padding will fight the compact density spec'd in the design system. Expect to iterate on `unsafe_allow_html` to get acceptable spacing. Test early with real content.
2. The monospace-for-identifiers rule adds visual texture, but mixing `font-family: monospace` with Streamlit's Source Sans Pro can look jarring if the sizes aren't carefully tuned. The 0.85rem spec should work but needs browser testing.
3. The "no shadows, no rounded corners > 4px" rule is correct for the regulatory domain but may make some sections feel flat. The left-border accents carry most of the spatial differentiation — if those are removed or too subtle, the layout will feel undifferentiated.

---

## Review 4: Senior Frontend Engineer perspective

> "Can this be built in Streamlit without hacks that break on upgrade?"

**Verdict: Yes. The design respects the platform's constraints.**

**Strengths:**
1. Every "component" is a Python function returning `st.markdown(html)` + Streamlit widgets. No custom JS, no external dependencies, no component hacks.
2. The token system as a Python dict is the right abstraction for Streamlit. It's grep-able, testable, and doesn't require a build step.
3. The two-column layout uses `st.columns([2, 3])` — standard Streamlit API. No width hacks.
4. The confirmation panel uses session state (`confirm_mode`) to swap the decision controls — clean Streamlit pattern.
5. The implementation plan's phased approach with compile-checks between phases is the safest way to modify a 961-line single-file app.

**Risks:**
1. **HTML block size.** The case header as a single `st.markdown(html)` flexbox block will work, but complex HTML in `unsafe_allow_html` is fragile. If Streamlit upgrades its HTML sanitizer, inline styles might break. Mitigation: keep HTML simple, test after any Streamlit version change.
2. **Session state during confirmation.** The confirmation panel introduces a modal-like interaction via session state. If the PO navigates away and back during confirmation, the state must be correctly cleaned up. The `_sticky()` / `_set_sticky()` helpers from Phase 1 need to handle `confirm_mode` carefully.
3. **Re-render cost.** Every Streamlit interaction re-runs the full script. The case header, context block, and AI panel all re-render. For a 961-line file with multiple `unsafe_allow_html` blocks, this should still be fast (<500ms), but test with the full assessment state populated.
4. **SiS vs. local Streamlit.** Streamlit runs a specific Streamlit version that may lag behind local development. Test the final implementation in Streamlit (via `snow streamlit deploy`) before demo.

---

# Section 33: Findings Summary

## 1. What was found in the existing UI
A five-page Streamlit app with functional business logic, clean backend separation (`skills/core.py`), and a correct regulatory workflow (11-factor assessment → GoS draft → quality gate → decision recording → append-only ledger). The engineering is solid; the visual presentation is generic Streamlit.

## 2. What is generic / AI-templated
Sidebar radio nav, `st.metric` card grids, emoji icons, default dark theme with colored badges, "Run AI → spinner → expander results" pattern, equal-weight five-page navigation. An experienced developer would identify this as an AI-generated Streamlit prototype within 5 seconds.

## 3. What should be retained
Two-column disposition layout, SLA urgency encoding, evidence level badges, 11-factor assessment structure, GoS quality gate, append-only ledger semantics, filter bar, all business logic in `skills/core.py`.

## 4. Visual directions considered
Three directions explored: (A) Investigation Desk — high density, warm neutrals, Bloomberg-like, challenging in Streamlit; (B) Decision Workbench — medium-high density, stage-based, functional palette, achievable; (C) Evidence Ledger — document-scroll, near-monochrome, formal, moderate Streamlit fit.

## 5. Direction selected and why
Direction B (Decision Workbench) with elements of A (warm palette, inline citations, monospace identifiers). Selected for workflow fit (matches PO cognitive sequence), Streamlit feasibility (no custom JS), information hierarchy (SLA + case identity dominant), and visual differentiation (warm neutral palette, functional-only color).

## 6. The single most important design decision
The confirmation panel. Before any decision is committed, the PO reviews a complete summary of what will become the permanent record: decision, alert, PO identity, SLA status, factors cited, evidence gaps, quality score, and rationale preview. This transforms a button click into a deliberate, inspectable act.

## 7. How the design avoids looking like a generic AI app
No `st.metric` cards. No emoji. No blue/purple AI palette. No "chat with AI" framing. Warm neutral surfaces. Monospace for identifiers. Left-border zone accents instead of card shadows. Evidence before AI output. The PO's zone (left) is visually distinct from the system's zone (right). The only high-saturation color on the workspace is the FILE button.

## 8. The key constraint that shaped the design
Streamlit: no custom JS, no custom React, no external CSS. All differentiation through `unsafe_allow_html` inline styles and Streamlit layout primitives. This constraint eliminates many standard UI approaches but forces a discipline that, paradoxically, produces a cleaner design — no decorative animations, no complex interactions, no gratuitous visual effects.

## 9. The biggest implementation risk
Phase 6 (GoS editor + decision controls + confirmation panel) modifies the core decision recording flow. A bug here would break the product's primary function. Mitigation: compile-check after every change, test the full flow, preserve the backup.

## 10. What is NOT in scope for this design
Custom components, external font loading, JavaScript interactions, drag-and-drop, client-side charting libraries, WebSocket-based real-time updates, multi-user collaboration features. The design works entirely within Streamlit constraints. These limitations are documented so future contributors don't attempt workarounds that would break Streamlit compatibility.
