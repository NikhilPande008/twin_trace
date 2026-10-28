# PRE_SUBMISSION_REVIEW.md — honest go / no-go evaluation before submitting

Paste everything below the line into a fresh Claude Code session opened at the repo root
(`~/Hackathons/twin-trace`), on the machine that holds the **current** code.

This prompt EVALUATES. It does not change code, docs, or git. Its only output is a written
report at `docs/PRE_SUBMISSION_REVIEW_<date>.md` and a spoken summary. If you find yourself
editing a source file, stop — that is a different task.

---

You are an independent reviewer doing a pre-submission audit of **twin-trace**,
a solo entry to the Nebius × NVIDIA Global AI Hackathon 2026 (Best Apps & Agents track, + Best
Use of Tavily bonus). Deadline Fri 30 Oct 2026, 22:30 IST; target submit Wed 28 Oct; ~8 days left.
~25,650 registrants, so the bar is high.

Your job: tell the human, honestly, **whether this is ready to submit, and exactly what would
move the score** — not to reassure them. Directness over encouragement. If something is weak,
say so plainly and show the evidence. A harsh, specific review is worth more than a kind one.

## What we already know going in (do not re-discover these; verify their current status)

1. **The git history was reset.** The repo is now a single "first commit" on remote
   `github.com/NikhilPande008/twin-trace`, and the
   `baseline-this platform-2026-09-25` tag and the post-baseline commit chain are GONE from it. That
   chain was the project's intended Devpost evidence for "significantly updated during the
   Submission Period" (see `CLAUDE.md` §1). Treat "is that evidence recoverable?" as a top
   finding, not a footnote. Check: `git log --oneline | wc -l`, `git tag`, `git remote -v`,
   `git reflog | head`, and whether an older remote / backup still has the history.
2. **Live platform use may still be unproven.** As of the last handoff, no `NEBIUS_API_KEY` /
   `TAVILY_API_KEY` had been run against the project, so Token Factory, the Nemotron model IDs,
   Sandboxes and Tavily were ASSUMED, not PROVEN. The hard gates require a real runtime call to
   Token Factory and at least one NVIDIA open model. **Verify the live status now**: look for a
   dated `evals/REPORT-*-live.md`, a real `BACKEND_RUN_REF` in `COMPUTE_RUNS`, and
   `scripts/check_models` output recorded in `DECISIONS.md`. If these do not exist, the strongest
   technical claims are unproven and submission is at risk — say so bluntly.
3. **The code on THIS machine is the source of truth.** Work from the working tree as it is,
   including uncommitted changes (e.g. there may be newer work such as `ddp/stress/headline.py`
   that no committed history shows). Do not assume any snapshot.
4. **Prior judging findings already exist.** The judges reward a complete, intuitive experience
   with an "aha moment in under two minutes" and penalise text-heavy screens that bury the call
   to action. See `docs/BUILD_PROMPT_JUDGING.md` and `docs/JUDGING_AUDIT.md` if present; this
   review checks whether those gaps are actually closed in the current code, not whether a plan
   exists.

## Read first

`CLAUDE.md` (esp. the §3 invariants and §4 claim discipline and §6 event gates), `HANDOFF.md`,
the last 5 `DECISIONS.md` entries, `CHANGES_SINCE_BASELINE.md`, `README.md`. Then run the offline
gate: `python -m pytest -q && python tests/eval_harness.py` and record the exact result.

## The review — produce `docs/PRE_SUBMISSION_REVIEW_<date>.md` with these sections

### A. Verdict (write this first, one paragraph)
Ready to submit as-is: **yes / yes-with-fixes / no**. If not an unqualified yes, the single most
important thing blocking it, and whether 8 days is enough. No hedging.

### B. Hard-gate checklist (pass / fail each, with the evidence you saw)
- Runtime call to Nebius Token Factory — PROVEN by a dated live run? (not just code that would)
- At least one NVIDIA open model actually invoked — evidence?
- Public repo with an OSS licence visible — is there a `LICENSE` file? (Note: `CLAUDE.md` §6 says
  it was deliberately withheld pending IP-terms review — flag if still absent.)
- README shows where Nemotron and Token Factory are used — does it match the code?
- ≤3-min video + required Devpost fields — note what is human-side and still owed.
Any FAIL here is a submission blocker; list those at the top of the report.

### C. Score against the four judging criteria (1–5 each, current state, evidence, gap)
Be concrete and cite files / what renders. For each: what a judge sees, the gap vs the "aha in
two minutes / don't bury the call to action" bar, and whether closing it is a reshape or new work.
1. **Technological Implementation** — is the platform depth (tiered Nemotron, Sandboxes, agent,
   structured output) real AND visible AND proven live? Unproven live = capped score; say so.
2. **Design** — walk every page (`page_alert_queue`, `page_disposition`, `page_ledger`,
   `page_dashboard`, `page_regulatory`). Clicks/scrolls to the core value? Is the decision and
   what it rests on surfaced, or buried under narrative/hashes/factor lists? Does anything read
   as default LLM styling?
3. **Potential Impact** — is the real-world user and stakes named and sourced (FIU-IND regime),
   with no invented numbers?
4. **Quality of the Idea** — is the non-obvious twin-alert contrast (ALERT-01 vs ALERT-16)
   legible in one view, or does a judge have to discover it?

### D. Claim-integrity audit (this is where entries lose credibility)
- Does any PROVEN label lack a test or recorded run? List each.
- Any invented number (accuracy / latency / cost / "x% fewer hallucinations") anywhere in README,
  docs, UI, or a draft video script, without a dated harness run behind it? (`CLAUDE.md` §4.)
- Any UI text or output that cites a NEEDS-VERIFICATION corpus rule, or claims "compliant",
  "FIU-IND approved", or "tamper-proof"? (All forbidden by the invariants.)
- Do the five `CLAUDE.md` §3 invariants still hold? Spot-check each against the tests named there.

### E. Risk & limitations the submission should disclose (rigour, not weakness — judges reward it)
The heuristic thresholds are not FIU-IND standards; most seeded alerts are a single summary
transaction so the calculator sees little; ledger is tamper-evident not tamper-proof; the agent
disposition is advisory. Confirm each is true of the current code and that the README/Devpost
owns it.

### F. Prioritised fix list for the 8 days (ranked by score impact ÷ effort)
Each item: criterion it lifts, reshape-or-new, rough effort, and whether it needs the human
(e.g. the live run, the licence decision, the git-history recovery, the video). Put the
submission blockers from B at the top. Be explicit about what is NOT worth doing.

## Rules
- Change no source, doc (except creating the review file), or git state. Read and run only.
- Nothing counts as PROVEN without a test or a recorded run you actually saw. Quote the evidence.
- Never invent numbers; if a figure isn't backed by a dated run in `evals/`, mark it unproven.
- End by committing ONLY `docs/PRE_SUBMISSION_REVIEW_<date>.md` (attribution per the session's
  own reminder), then print Verdict (A), the hard-gate result (B), and the top 3 fixes (F).
