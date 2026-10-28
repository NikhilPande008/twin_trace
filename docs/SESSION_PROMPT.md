# Session prompts for this repo

`CLAUDE.md` loads automatically in Claude Code. Use the prompts below to start or end a session.
Paste them as-is and edit the part in angle brackets.

## Start of session

```
We're in twin-trace (Nebius × NVIDIA hackathon, deadline 30 Oct 22:30 IST).
Follow CLAUDE.md §0: read HANDOFF.md, TASKS.md, the last 3 DECISIONS.md entries and
CHANGES_SINCE_BASELINE.md, then run the offline gate and report the result.
Today's goal: <task id, e.g. T1.3>. Before writing code, state the plan in ≤8 bullets,
which invariants in CLAUDE.md §3 it touches, and what will move from ASSUMED/STUBBED to PROVEN.
Hard rules: never touch ~/Hackathons/bank fraud detection or any path outside this repo;
never rewrite history at or before tag baseline-this platform-2026-09-25; no invented numbers.
```

## End of session

```
Wrap up: run the full offline gate; update HANDOFF.md (state, claim-status table, blockers,
candidate backports), tick TASKS.md, add a CHANGES_SINCE_BASELINE.md row for anything that
landed, append DECISIONS.md entries (FIRM/PROPOSED) for real design choices, then commit
with a descriptive message. Print the next-session start prompt with the next task id filled in.
```

## When porting something from the this platform project

```
I want <feature> from the this platform project in this repo. I will paste the relevant code or
describe it; do NOT read the other folder. Re-implement it here against ddp/ (no this platform
dependencies), add tests, and record it in CHANGES_SINCE_BASELINE.md as "ported" (not "new").
```
