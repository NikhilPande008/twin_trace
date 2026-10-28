# Decision package

A recorded decision can be exported as one JSON file and re-checked by another reviewer, offline,
without this database or an API key. Implemented in `ddp/package.py`. PROVEN offline
(`tests/test_package.py`).

## Export and verify

```bash
python3 -m scripts.export_decision <DECISION_ID> --out decision.json
python3 -m scripts.verify_package decision.json      # exit 0 = every check passed
```

In the app: Decision Ledger → a decision → *Reconstruct decision* → **Download decision package**.
To re-check a package inside the app, open the Decision Ledger page and use **Verify a decision
package**: upload the file and read the checks. PROVEN offline (`tests/test_package_upload.py`).

## A package carries program source: who may run it

The package includes the calculator's source so it can be re-executed. Running source that
arrives in a file is only safe when the person running it chose that file.

- **Command line** (`scripts.verify_package`): executes the package's program in an isolated
  subprocess (`python -I`, empty environment, timeout). Only verify files you chose to open. It is
  isolated, not sandboxed from the filesystem.
- **In the app** (upload box, possibly on a public host): **never executes package-supplied
  code.** A program runs only if its hash is the calculator shipped in this repository or one this
  deployment's own database has archived. Otherwise the reproduction check reports *not executed*
  and the package does not verify. A test supplies a hostile program with a matching hash and
  asserts that it never runs. Uploads are also limited to 2 MB and must be valid
  `ddp-decision-package/1` JSON.

## Schema (`ddp-decision-package/1`)

| Section | Contents | Source |
|---|---|---|
| `decision` | the DECISION_LEDGER row incl. `PREV_HASH`, `ROW_HASH`, `METADATA_JSON` (validation binding, model-call metadata, evidence check) | ledger |
| `compute_runs` | the cited calculator run: saved `INPUT_JSON`, `OUTPUT_JSON`, code/input/output hashes | COMPUTE_RUNS |
| `programs` | calculator source for each `CODE_SHA256` | PROGRAMS (append-only archive) |
| `corpus_rules` | rules cited, as they are at export time | REGULATORY_CORPUS |
| `claims` | claim map of the recorded rationale against the recorded run | recomputed from recorded inputs |
| `limits` | plain-language trust boundary | — |
| `manifest` | sha256 of each section and of the package | — |

Everything is copied from what was **recorded**. Current transaction rows are never used, so
later changes to operational data do not change the package (tested).

## What verification proves

1. Each section matches its manifest hash, and the package hash matches.
2. The decision row hashes to its recorded `ROW_HASH` given its `PREV_HASH`.
3. The saved calculator input and archived program match their recorded hashes.
4. Re-executing that program on that input, in an isolated subprocess, reproduces the recorded
   output hash.

## What it does not prove (trust boundary)

- **Tamper-evident, not tamper-proof.** The hash chain lives in the same database it protects.
  Someone with write access before export could rebuild a consistent chain. Independent
  anchoring (e.g. publishing chain heads elsewhere) is not implemented.
- Corpus rules are copied as they are at export time, not as they were at decision time.
- A verified figure matches the recorded inputs; it does not show the inputs are true.
- The officer ID is self-asserted: there is no authentication.

## Reproduction in the app

*Reproduce* re-runs the archived program on the saved input and reports one of:
**reproduced**, **mismatch**, or **unavailable**. Runs recorded before saved inputs existed
(before 2026-10-21) show *unavailable*: their hashes can detect a difference but cannot recover
the inputs. The app never substitutes current data and calls it reproduction.

## Not included

Credentials, prompts, model reasoning text, other alerts' records.
