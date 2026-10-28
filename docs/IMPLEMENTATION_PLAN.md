# Implementation Plan — Twin Trace, Twin Trace

**Date:** 2026-09-27  
**Based on:** ARCHITECTURE.md §2 (critique) + TASKS.md  
**Deadline:** Fri 30 Oct 2026, 22:30 IST (internal: Wed 28 Oct; freeze: Fri 23 Oct)

---

## Gap list — ordered by (judged value ÷ effort)

Items are ordered highest priority first within each tier. Never-cut items are marked **✦**.

| # | Gap | TASKS | Value | Effort | Notes |
|---|---|---|---|---|---|
| 1 | **Go live on Token Factory** — verify model IDs + base URL; Token Factory moves ASSUMED → PROVEN | T0.4 | ★★★★★ | XS | Gate for everything else |
| 2 | **Nemotron JSON reliability** — structured output strategy; tune prompts; fix `str_quality_checker` fail-closed | T1.1, T3.4 | ★★★★★ | S | Blocking failure mode |
| 3 | **Live pipeline run on 4 cases** — ALERT-01, 02, 16, one INSUFFICIENT | T1.2 | ★★★★★ | S | Proves the system works ✦ |
| 4 | **Sandbox calculator execution** — NebiusSandboxBackend; real BACKEND_RUN_REF in ledger | T1.3 | ★★★★ | M | "Non-obvious" element; checkpoint 3 Oct |
| 5 | **Tavily adverse-media ✦** — evidence items stored + cited; injection + tipping-off tests | T2.1, T2.2 | ★★★★ | M | Best Use of Tavily bonus |
| 6 | **Demo "caught it" case** — script that shows wrong total blocked, corrected draft | T2.3 | ★★★★ | S | Video opening beat ✦ |
| 7 | **Eval harness v2 ✦** — numeric accuracy with/without calculator; gate catch rates; dated report | T3.2 | ★★★★★ | L | Only source of submission numbers |
| 8 | **Policy gate** — Nemotron Content Safety custom policies; verdict stored as evidence | T3.1 | ★★★ | L | Cut to fallback if hosting infeasible |
| 9 | **Fact-citation chips** — inline hover chips in GoS preview | T2.4 | ★★★ | S | Cut to plain citation line if behind |
| 10 | **Reconstruct decision view** — DECISION_ID → full audit trail + Reproduce button | T3.3 | ★★★ | M | Cut if behind |
| 11 | **UI polish** — investigator flow, run trace panel, accessibility | T4.1 | ★★★ | M | Design criterion |
| 12 | **Hosted demo** — Streamlit Community Cloud, seeded, secrets via platform | T4.2 | ★★★★ | S | Required for judges |
| 13 | **README final** — architecture, models, eval table, "significantly updated" | T4.3 | ★★★★ | S | Required for judges ✦ |
| 14 | **Richer structuring seed** — T1.4 multi-account cash rows | T1.4 | ★★ | S | Cut if behind |
| 15 | **Submission package** — video script, Devpost text, platform feedback | T5.1–5.3 | ★★★★★ | M | Required ✦ |

---

## TASKS.md mapping

| TASKS.md ID | This plan item | Phase | Due |
|---|---|---|---|
| T0.1 | (human) claim credits | — | ASAP |
| T0.2 | (human) create .env | — | ASAP |
| T0.3 | (human) licence decision | — | ASAP |
| T0.4 | Gap #1: go live on Token Factory | 2 | 27 Sep |
| T1.1 | Gap #2: JSON reliability + prompt tuning | 2 | 3 Oct |
| T1.2 | Gap #3: live pipeline run | 2 | 3 Oct |
| T1.3 | Gap #4: sandbox backend | 3 | 3 Oct (**checkpoint**) |
| T1.4 | Gap #14: structuring seed | 2 | 3 Oct (cut first) |
| T2.1 | Gap #5a: Tavily fetch + injection test | 4 | 10 Oct |
| T2.2 | Gap #5b: Tavily evidence items | 4 | 10 Oct |
| T2.3 | Gap #6: demo case | 4 | 10 Oct |
| T2.4 | Gap #9: fact-citation chips | 4 | 10 Oct (cut first) |
| T3.1 | Gap #8: policy gate | 5 | 17 Oct |
| T3.2 | Gap #7: eval harness | 5 | 17 Oct (**checkpoint**) |
| T3.3 | Gap #10: reconstruct view | 5 | 17 Oct (cut if behind) |
| T3.4 | Gap #2: str_quality_checker fail-closed | 2 | 3 Oct |
| T4.1 | Gap #11: UI polish | 6 | 23 Oct |
| T4.2 | Gap #12: hosted demo | 6 | 23 Oct (**FREEZE**) |
| T4.3 | Gap #13: README final | 6 | 23 Oct |
| T5.1–5.3 | Gap #15: submission package | 7 | 28 Oct |

---

## Cut lines

If behind schedule, cut in this order (matches TASKS.md cut order):

1. **T2.4** inline chips → already have a plain citation line (no UX regression)
2. **T3.1** hosted Content Safety → fallback: deterministic `screen_request` only; document it honestly
3. **T1.4** richer structuring seed → existing seed covers the scenario
4. **T3.3** reconstruct view → ledger page still shows all fields

**Never cut:** T0.4, T1.3 (or honest "local only" statement), T2.1, T3.2, T5.x, any item marked ✦.

---

## Phase 1 deliverables (this phase, done now)

- [x] ARCHITECTURE.md (as-is, critique, target, Mermaid diagrams)
- [x] IMPLEMENTATION_PLAN.md (this file)
- [x] `ddp/ports.py` — typed port contracts (LLMPort, ComputeBackendPort, EvidenceSourcePort, PolicyGatePort)
- [x] `ddp/pipeline.py` — pipeline step skeleton (RunTrace, StepResult, DispositionPipeline wrappers)
- [x] `ddp/store.py` — EVIDENCE table added (no behaviour change, `CREATE TABLE IF NOT EXISTS`)
- [x] `docs/PLATFORM_NOTES.md` — stub for Phase 2 live verification
- [x] DECISIONS.md entries for all Phase 1 ADRs
- [x] Offline gate green
