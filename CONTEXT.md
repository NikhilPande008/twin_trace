# CONTEXT.md — Twin Trace

## Event
Nebius × NVIDIA Global AI Hackathon 2026 (Devpost). Track: **Best Apps & Agents**, also aiming
for **Best Use of Tavily**. Solo entrant. Deadline: 30 Oct 2026, 22:30 IST.

## Problem
India's mule-account and financial-crime alerts are detected upstream (MuleHunter.AI, the I4C
Suspect Registry, RBI DPIP). The **disposition** is left to the bank's Principal Officer: the
decision to file an STR or close the alert, and the written Ground of Suspicion. FIU-IND
inspections examine whether those decisions — including decisions *not* to file — are
documented, specific and made on time.

LLM copilots make this worse in one specific way: they **generate** numbers and **assert**
compliance. A Ground of Suspicion with a wrong aggregate, or a monthly cash total the model added
up itself, cannot be defended.

## What this edition proves, and how
| Claim | Mechanism |
|---|---|
| Every ₹ figure is traceable | Calculator of record: a fixed, hashed program over the case transactions; the gate accepts only transaction amounts or computed facts |
| Every decision is reconstructable | Append-only, hash-chained ledger with the compute run ID and model provenance |
| Regulatory answers are grounded, or absent | Retrieval over PROVEN/ASSUMED rules only; abstains off-corpus |
| No tipping-off | Deterministic refusal before any model call (next: Nemotron Content Safety policy gate) |

## Platform use (why Nebius + NVIDIA, not a checkbox)
- **Token Factory, tiered Nemotron:** Nano for triage/checklist review, Super for factor-by-factor
  reasoning, Ultra for the consequential narrative. The model per call is recorded in the ledger.
- **Token Factory Sandboxes (planned T1.3):** run the calculator of record in an isolated VM so
  the figures come from a verifiable execution, not from the app process.
- **Tavily (planned T2.x):** adverse-media screening as a regulated due-diligence step, with
  sources captured as evidence.

## Critical constraint (carried over, still true)
The human directing this project knows the shape of Indian AML compliance but is not a
practising compliance officer. Domain judgements must trace to primary sources or explicit human
review. A plausible but unverified compliance narrative is the most dangerous output this
project can produce.
