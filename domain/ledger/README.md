# Decision Ledger — /domain/ledger/

This directory holds the append-only record of every disposition decision made during
development of the domain gold standard.

## Purpose
The ledger is the "defensibility" proof the product demonstrates. It shows:
1. Every disposition was made by a human (the project lead acting as PO proxy)
2. The reasoning chain behind each decision
3. Where the human corrected an AI draft — and what the correction was
4. The general rules extracted from corrections (backfilled to DOMAIN.md)

## Format
One file per session: `YYYY-MM-DD-session-N.md`

Each entry:
```
## [Scenario ID] — [Title]
- AI draft disposition: [FILE | CLOSE-NO-FILE | CONTESTED]
- Human decision: [FILE | CLOSE-NO-FILE | CONTESTED]
- Match: YES / NO (overridden)
- Correction: [What changed and why, in the human's own framing]
- Rule extracted: [General rule, if any — backfilled to DOMAIN.md]
- Timestamp: YYYY-MM-DD HH:MM
```

## Current sessions
(none yet — will be populated in Phase 1)
