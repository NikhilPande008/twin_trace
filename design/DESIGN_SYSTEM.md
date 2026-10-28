# DESIGN_SYSTEM.md — Visual Design System

**Date:** 2026-09-25  
**Product:** FIU-IND AML Copilot — Decision Workbench  
**Platform:** Streamlit  — all values implemented via `unsafe_allow_html` inline styles

---

## 1. Implementation context

Streamlit has no external CSS, no custom themes beyond `st.set_page_config`, and no component-level style overrides. All visual differentiation is achieved through:

1. `st.markdown(html_string, unsafe_allow_html=True)` — inline HTML/CSS for styled content
2. Streamlit layout primitives — `st.columns`, `st.tabs`, `st.expander`, `st.container`
3. `st.set_page_config` — page title, icon, layout (wide)

This design system defines tokens and patterns as **Python constants and helper functions** that generate inline-styled HTML.

---

## 2. Color system

### 2.1 Surface colors

Streamlit uses its own dark theme. We work within it, not against it. Custom surface colors are used only inside `unsafe_allow_html` blocks.

| Token | Hex | Usage |
|---|---|---|
| `BG_PAGE` | Streamlit default | Page background — do not override |
| `BG_SURFACE` | `#1E1E2E` | Content surfaces inside HTML blocks (case header, evidence cards) |
| `BG_SURFACE_RAISED` | `#252538` | Elevated surfaces (AI panel, decision confirmation) |
| `BG_SURFACE_SUNKEN` | `#16161F` | Recessed surfaces (code blocks, evidence source text) |
| `BG_DECISION_ZONE` | `#1A1A28` | Decision rail background — visually separates PO zone from AI zone |

### 2.2 Text colors

| Token | Hex | Usage |
|---|---|---|
| `TEXT_PRIMARY` | `#E8E6DF` | Primary body text — warm white, not blue-white |
| `TEXT_SECONDARY` | `#9B9A93` | Metadata, timestamps, labels |
| `TEXT_TERTIARY` | `#6B6A64` | Disabled, placeholder |
| `TEXT_HEADING` | `#F0EDE5` | Section headings |
| `TEXT_MONO` | `#C4B5A0` | Monospace text (alert IDs, rule IDs, amounts) — warm tan |

### 2.3 Functional colors — SLA urgency (exclusive use)

These colors are reserved for SLA urgency. No other element uses red, amber, or green.

| Token | Hex | Usage |
|---|---|---|
| `SLA_CRITICAL` | `#D94F4F` | ≤ 0 WD remaining (overdue) |
| `SLA_URGENT` | `#D9994F` | 1–2 WD remaining |
| `SLA_NORMAL` | `#5DA65D` | 3+ WD remaining |

### 2.4 Functional colors — evidence states

| Token | Hex | Usage |
|---|---|---|
| `EV_PROVEN` | `#4A8EC2` | Evidence level: PROVEN (15 items) — steel blue |
| `EV_ASSUMED` | `#8B7EC8` | Evidence level: ASSUMED (21 items) — muted purple |
| `EV_GAP` | `#8C7B6B` | Evidence gap / needs verification — warm gray-brown |

### 2.5 Functional colors — factor assessment states

| Token | Hex | Usage |
|---|---|---|
| `FACTOR_TRIGGERED` | `#C27A4A` | Factor triggered — warm amber-brown |
| `FACTOR_CLEAR` | `#5B8A6A` | Factor clear — muted sage |
| `FACTOR_INSUFFICIENT` | `#7A7268` | Factor insufficient data — dim warm gray |

### 2.6 Functional colors — decision actions

| Token | Hex | Usage |
|---|---|---|
| `ACTION_FILE` | `#C25A4A` | FILE STR — the only high-saturation warm color. Reserved exclusively for the FILE action. |
| `ACTION_DEFER` | `#8B7EC8` | DEFER — muted, non-urgent |
| `ACTION_CLOSE` | `#5B8A6A` | CLOSE — settled, resolved |

### 2.7 Structural colors

| Token | Hex | Usage |
|---|---|---|
| `BORDER_DEFAULT` | `#2A2A3D` | Default border color |
| `BORDER_EMPHASIS` | `#3D3D55` | Emphasis border (section headers, dividers) |
| `BORDER_AI` | `#353548` | AI panel border — subtly distinct to mark AI zone |

### 2.8 Color principles

1. **No decoration colors.** Every color in the palette has a functional meaning.
2. **SLA colors are exclusive.** Red, amber, green appear ONLY for SLA urgency. Never for success/error/warning states.
3. **Warm palette.** The palette avoids cold blues and purples associated with AI/SaaS products. Blues are reserved for the evidence-proven badge (steel blue, not electric blue).
4. **Low saturation.** All colors except `ACTION_FILE` and SLA urgency are muted. The workspace feels professional, not playful.

---

## 3. Typography

### 3.1 Font families

SiS uses Streamlit's default font stack (Source Sans Pro / system sans-serif). We cannot load custom fonts. Differentiation comes from size, weight, and `font-family: monospace` for identifiers.

| Role | Font | Size | Weight | Usage |
|---|---|---|---|---|
| Page heading | Default | 1.4rem | 600 | Page titles (Alert Queue, Decision Ledger) |
| Section heading | Default | 1.1rem | 600 | Section headers within a page |
| Body | Default | 0.95rem | 400 | Body text, descriptions, narrative |
| Small | Default | 0.8rem | 400 | Metadata, timestamps, model attribution |
| Caption | Default | 0.75rem | 400 | Tertiary labels, evidence source dates |
| Identifier | `monospace` | 0.85rem | 500 | Alert IDs, rule IDs, factor codes, amounts |
| Narrative | Default | 1.0rem | 400 | GoS narrative text (slightly larger than body for readability) |

### 3.2 Typography principles

1. **Monospace for machine-generated identifiers.** ALERT-01, RFI-003, POE-005, ₹85,00,000 — anything the PO would quote verbatim in a filing.
2. **Size hierarchy is functional.** Larger = more important to the decision. Case identity > Evidence > Metadata.
3. **No bold-for-emphasis in body text.** Bold is reserved for headings and labels. In body text, use monospace or color to distinguish.
4. **Line height 1.5 for narrative text.** The GoS is read as prose — it needs adequate line spacing.

---

## 4. Spacing

### 4.1 Spacing scale

Streamlit controls most spacing. Within `unsafe_allow_html` blocks:

| Token | Value | Usage |
|---|---|---|
| `SP_XS` | 4px | Inline element gaps (badge icon to label) |
| `SP_SM` | 8px | Compact list items, pill internal padding |
| `SP_MD` | 12px | Section content padding |
| `SP_LG` | 16px | Section separation, card padding |
| `SP_XL` | 24px | Major section breaks |
| `SP_XXL` | 32px | Page-level separation (between case header and body) |

### 4.2 Spacing principles

1. **Streamlit adds its own spacing.** Do not fight it — design around it. Assume ~16px between consecutive `st.markdown` calls.
2. **Compact within HTML blocks.** Multiple related items rendered in a single `st.markdown(html)` call share the compact spacing above.
3. **Negative space between zones.** The AI zone and the Decision zone are separated by visible space (SP_XL), not a decorative border.

---

## 5. Surfaces and containers

### 5.1 Surface types

| Surface | Background | Border | Radius | Usage |
|---|---|---|---|---|
| Case Header | `BG_SURFACE` | `BORDER_EMPHASIS` bottom | 4px top | Alert identity, SLA, key metadata at top of case workspace |
| Evidence Card | `BG_SURFACE` | `BORDER_DEFAULT` | 4px | Individual factor assessment block |
| AI Panel | `BG_SURFACE_RAISED` | `BORDER_AI` left (3px) | 4px | System assessment output, GoS draft, quality score |
| Decision Rail | `BG_DECISION_ZONE` | `BORDER_EMPHASIS` top | 0 | Decision buttons, confirmation, recording controls |
| Source Block | `BG_SURFACE_SUNKEN` | none | 2px | Regulatory text citations, evidence source text |
| Gap Callout | transparent | `BORDER_DEFAULT` left (2px, `EV_GAP` color) | 0 | Evidence gap notification |
| Confirmation Panel | `BG_SURFACE_RAISED` | `ACTION_FILE` top (3px) | 4px | Decision review before recording |

### 5.2 Surface principles

1. **Left-border accent for zones.** The AI panel uses a left border to mark its territory. The decision rail uses a top border. These borders communicate "this is a different zone" without decorative weight.
2. **No shadows.** Streamlit's dark theme + shadows = muddy. Elevation is communicated through background lightness (`SUNKEN` < default < `RAISED`).
3. **Minimal radius.** 2–4px only. No rounded cards. Regulatory software is not playful.
4. **No cards-within-cards.** Maximum nesting depth is one surface inside another (e.g., evidence card inside the case workspace). No deeper nesting.

---

## 6. Borders

| Style | Spec | Usage |
|---|---|---|
| Default | 1px solid `BORDER_DEFAULT` | Content separation within a zone |
| Emphasis | 1px solid `BORDER_EMPHASIS` | Section headers, zone boundaries |
| Zone accent | 3px solid [zone color] left/top | AI panel (left), decision rail (top), confirmation (top) |
| Evidence gap | 2px solid `EV_GAP` left | Gap callout blocks |

---

## 7. Icons and indicators

### 7.1 No emoji in production

The current app uses emoji (🏦, 🟢, 🔴, ⚪, ✍️, 🔍). The redesign replaces all emoji with:

1. **Text indicators** for states: `[T]` triggered, `[C]` clear, `[—]` insufficient, `[P]` proven, `[A]` assumed
2. **HTML-styled dots/squares** for SLA urgency: `<span style="color: {SLA_COLOR}">●</span>` (rendered via `unsafe_allow_html`)
3. **Text labels** always accompany indicators — never rely on icon/color alone

### 7.2 Indicator patterns

| Indicator | HTML pattern | Accessibility |
|---|---|---|
| SLA urgency | `● {days} WD` with colored dot | Color + text (e.g., "● 2 WD remaining" in amber) |
| Factor state | `[T]` / `[C]` / `[—]` with colored background | Letter + color + label text |
| Evidence level | `PROVEN` / `ASSUMED` as styled inline badges | Text badge with background color |
| Decision action | `FILE` / `DEFER` / `CLOSE` as styled buttons | Text labels (Streamlit `st.button` with custom colors via HTML wrapping) |

---

## 8. States

### 8.1 Component states

| State | Visual treatment | Example |
|---|---|---|
| Default | Standard rendering | Factor row, evidence card |
| Active/Selected | Left border accent + slightly raised background | Currently selected alert in queue |
| Expanded | Content revealed below header | Factor assessment details |
| Disabled | `TEXT_TERTIARY` color, no interaction | Decision buttons before assessment is run |
| Loading | Streamlit spinner (default) | During Nemotron (via Token Factory) call |
| Error | `SLA_CRITICAL` colored text (not a banner) + specific message | API timeout, validation failure |

### 8.2 State principles

1. **No toast notifications.** Streamlit's `st.success/error/warning/info` banners are the canonical "AI template" pattern. Use inline colored text for feedback.
2. **Loading uses Streamlit's spinner.** No custom loading states — the spinner is functional and familiar.
3. **Error text is specific.** Never "Something went wrong." Always "Nemotron (via Token Factory) timed out after 45s — retry or use fallback model."

---

## 9. Accessibility

### 9.1 Minimum requirements

| Requirement | Implementation |
|---|---|
| Color is never the sole indicator | Every colored element has an accompanying text label |
| Text contrast ≥ 4.5:1 | All `TEXT_PRIMARY` on `BG_SURFACE` combinations meet WCAG AA |
| Interactive elements are keyboard-accessible | Streamlit handles this natively for its widgets |
| No auto-playing animations or transitions | No motion in the design |
| Monospace text is readable | 0.85rem minimum for monospace — never smaller |

### 9.2 Accessibility notes for SiS

Streamlit handles most accessibility through its native widgets. Custom HTML via `unsafe_allow_html` does NOT get Streamlit's accessibility treatment — we must ensure:
- No interactive elements inside `unsafe_allow_html` blocks (all interactions use Streamlit widgets)
- `unsafe_allow_html` content is presentational only (data display, styling)
- Screen readers can parse the HTML content (semantic HTML, not div soup)

---

## 10. Motion

**None.** No animations, transitions, or motion of any kind. Streamlit reruns the full script on interaction — any CSS transition would be reset. The workspace is static, functional, and instant.

---

## 11. Token implementation

All tokens are defined as Python constants in a single `_design_tokens()` function or module-level dict:

```python
TOKENS = {
    "bg_surface": "#1E1E2E",
    "bg_surface_raised": "#252538",
    "bg_surface_sunken": "#16161F",
    "bg_decision_zone": "#1A1A28",
    "text_primary": "#E8E6DF",
    "text_secondary": "#9B9A93",
    "text_tertiary": "#6B6A64",
    "text_heading": "#F0EDE5",
    "text_mono": "#C4B5A0",
    "sla_critical": "#D94F4F",
    "sla_urgent": "#D9994F",
    "sla_normal": "#5DA65D",
    "ev_proven": "#4A8EC2",
    "ev_assumed": "#8B7EC8",
    "ev_gap": "#8C7B6B",
    "factor_triggered": "#C27A4A",
    "factor_clear": "#5B8A6A",
    "factor_insufficient": "#7A7268",
    "action_file": "#C25A4A",
    "action_defer": "#8B7EC8",
    "action_close": "#5B8A6A",
    "border_default": "#2A2A3D",
    "border_emphasis": "#3D3D55",
    "border_ai": "#353548",
}
```

Helper functions generate styled HTML from these tokens:

```python
def _badge(label, bg_color, text_color=TOKENS["text_primary"]):
    return (f'<span style="background:{bg_color};color:{text_color};'
            f'padding:2px 8px;border-radius:3px;font-size:0.8rem;'
            f'font-weight:500;">{label}</span>')

def _mono(text):
    return (f'<span style="font-family:monospace;color:{TOKENS["text_mono"]};'
            f'font-size:0.85rem;">{text}</span>')

def _sla_pill(days_left):
    if days_left <= 0:
        color, label = TOKENS["sla_critical"], f"OVERDUE ({abs(days_left)}d)"
    elif days_left <= 2:
        color, label = TOKENS["sla_urgent"], f"{days_left} WD left"
    else:
        color, label = TOKENS["sla_normal"], f"{days_left} WD left"
    return (f'<span style="color:{color};font-weight:600;'
            f'font-size:0.85rem;">● {label}</span>')
```
