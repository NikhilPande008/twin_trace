"""
Decision package (T3): one self-contained JSON file that lets another reviewer re-check a
recorded decision offline, without this database and without an API key.

Contents (all copied from what was RECORDED, never from current operational rows):
  decision       the DECISION_LEDGER row, including PREV_HASH and ROW_HASH
  compute_runs   the cited calculator run(s): saved INPUT_JSON, OUTPUT_JSON and hashes
  programs       the archived calculator source for each CODE_SHA256
  corpus_rules   the corpus rules cited, as they are in this database at export time
  claims         the claim map of the recorded rationale against the recorded run
  manifest       sha256 of each section and of the whole package

Trust boundary: verification proves the package is internally consistent, that the decision row
hashes to its recorded ROW_HASH given PREV_HASH, and that the calculator reproduces its recorded
output from the recorded input. It does not prove the ledger itself was not rewritten before
export: the hash chain lives in the same database it protects (tamper-evident, not tamper-proof).
Not included: credentials, prompts, model reasoning, other alerts' records.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from .claims import claim_map
from .compute.runner import PROGRAM_PATH, LocalSubprocessBackend, canonical_json, sha256_bytes
from .store import ledger_row_hash

PACKAGE_VERSION = "ddp-decision-package/1"
_SECTIONS = ("decision", "compute_runs", "programs", "corpus_rules", "claims")


def _sha(obj) -> str:
    return hashlib.sha256(canonical_json(obj).encode()).hexdigest()


def build_package(store, decision_id: str) -> dict:
    rows = store.query("SELECT * FROM DECISION_LEDGER WHERE DECISION_ID = ?", (decision_id,))
    if not rows:
        raise ValueError(f"decision {decision_id} not found")
    decision = rows[0]
    meta = json.loads(decision.get("METADATA_JSON") or "{}")
    run_id = meta.get("compute_run_id")
    runs, programs, facts = [], {}, []
    if run_id:
        run = store.get_compute_run(run_id)
        if run:
            runs.append(run)
            facts = json.loads(run["OUTPUT_JSON"]).get("facts", [])
            prog = store.get_program(run["CODE_SHA256"])
            if prog:
                programs[run["CODE_SHA256"]] = prog["SOURCE"]
    # Transactions as they were fed to the calculator, not as they are now.
    recorded_txns = (json.loads(runs[0]["INPUT_JSON"]).get("transactions", [])
                     if runs and runs[0].get("INPUT_JSON") else [])
    rule_ids = json.loads(decision.get("RULES_CITED") or "[]")
    pkg = {
        "package_version": PACKAGE_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "compute_runs": runs,
        "programs": programs,
        "corpus_rules": store.corpus_by_ids(rule_ids) if rule_ids else [],
        "claims": claim_map(decision["RATIONALE_TEXT"], recorded_txns, facts, run_id),
        "limits": [
            "Tamper-evident, not tamper-proof: the ledger hash chain lives in the database it "
            "protects; this package cannot prove the ledger was not rewritten before export.",
            "Corpus rules are copied as they are at export time.",
            "A verified figure matches the recorded inputs; it does not establish they are true.",
            "The officer ID is self-asserted (no authentication in this build).",
        ] + ([] if runs and runs[0].get("INPUT_JSON") else
             ["No saved calculator input for this decision: reproduction is not available."]),
    }
    pkg["manifest"] = {s: _sha(pkg[s]) for s in _SECTIONS}
    pkg["manifest"]["package_sha256"] = _sha({s: pkg["manifest"][s] for s in _SECTIONS})
    return pkg


def trusted_program_hashes(store=None) -> set[str]:
    """Calculator program versions this deployment is willing to execute for a package: the
    program shipped in this repository, plus every version its own database has archived."""
    hashes = {sha256_bytes(PROGRAM_PATH.read_bytes())}
    if store is not None:
        hashes |= {r["CODE_SHA256"] for r in store.query("SELECT CODE_SHA256 FROM PROGRAMS")}
    return hashes


def verify_package(pkg: dict, backend=None, trusted_code_sha256: set[str] | None = None) -> dict:
    """Offline checks. Returns {ok, checks: [{name, ok, detail}]}.

    The package carries the calculator's source. By default (the command-line verifier, run by
    someone who chose the file) that source is executed to reproduce the output. Anything that
    receives a package from an untrusted party, such as the hosted app, must pass
    `trusted_code_sha256`: a program whose hash is not in that set is NOT executed, and the
    reproduction check reports that it was skipped.
    """
    checks = []

    def check(name, ok, detail=""):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    man = pkg.get("manifest") or {}
    for s in _SECTIONS:
        check(f"manifest:{s}", man.get(s) == _sha(pkg.get(s)), "section hash")
    check("manifest:package", man.get("package_sha256") ==
          _sha({s: man.get(s) for s in _SECTIONS}), "package hash")

    d = pkg.get("decision") or {}
    check("ledger_row_hash", ledger_row_hash(d, d.get("PREV_HASH", "")) == d.get("ROW_HASH"),
          "decision row hashes to its recorded ROW_HASH given PREV_HASH")

    for run in pkg.get("compute_runs") or []:
        rid = run.get("RUN_ID")
        src = (pkg.get("programs") or {}).get(run.get("CODE_SHA256"))
        if not run.get("INPUT_JSON") or src is None:
            check(f"reproduce:{rid}", False, "input or program not in package — not reproducible")
            continue
        check(f"input_hash:{rid}", sha256_bytes(run["INPUT_JSON"].encode()) == run["INPUT_SHA256"])
        check(f"code_hash:{rid}", sha256_bytes(src.encode()) == run["CODE_SHA256"])
        if trusted_code_sha256 is not None and not (
                run["CODE_SHA256"] in trusted_code_sha256
                and sha256_bytes(src.encode()) == run["CODE_SHA256"]):
            check(f"reproduce:{rid}", False,
                  "not executed: this program version is not one this verifier trusts "
                  "(it is not the shipped calculator or one archived in this database)")
            continue
        check(f"output_hash:{rid}",
              sha256_bytes(canonical_json(json.loads(run["OUTPUT_JSON"])).encode())
              == run["OUTPUT_SHA256"], "stored output matches its hash")
        stdout, _ = (backend or LocalSubprocessBackend()).execute(src.encode(), run["INPUT_JSON"])
        check(f"reproduce:{rid}",
              sha256_bytes(canonical_json(json.loads(stdout)).encode()) == run["OUTPUT_SHA256"],
              "re-executed recorded program on recorded input")
    return {"ok": all(c["ok"] for c in checks), "checks": checks}


MAX_PACKAGE_BYTES = 2_000_000


def check_uploaded_package(raw: bytes, store=None) -> dict:
    """Verify a package received from outside (the app's upload box).

    Returns {"status": "invalid" | "verified" | "failed", "message": str, "result": dict | None}.
    Never executes package-supplied code: only program versions this deployment trusts run.
    """
    if len(raw) > MAX_PACKAGE_BYTES:
        return {"status": "invalid", "result": None,
                "message": f"File is larger than {MAX_PACKAGE_BYTES // 1_000_000} MB; "
                           "a decision package is a few kilobytes."}
    try:
        pkg = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return {"status": "invalid", "result": None, "message": "Not valid JSON."}
    if not isinstance(pkg, dict) or pkg.get("package_version") != PACKAGE_VERSION:
        return {"status": "invalid", "result": None,
                "message": f"Not a {PACKAGE_VERSION} decision package."}
    try:
        result = verify_package(pkg, trusted_code_sha256=trusted_program_hashes(store))
    except Exception as exc:  # malformed sections must not crash the page
        return {"status": "invalid", "result": None,
                "message": f"The package could not be checked ({type(exc).__name__}): "
                           "it is malformed."}
    return {"status": "verified" if result["ok"] else "failed", "result": result,
            "message": "All checks passed." if result["ok"] else
                       "One or more checks failed; the package is altered, incomplete, or "
                       "uses a program version this verifier does not trust."}
