"""
Probe script for Nebius Token Factory Sandboxes (T1.3).

Run this once you have a NEBIUS_API_KEY to verify:
  0. NEBIUS_PROJECT_ID is set (required: the API answers "Missing Project header" without it)
  1. contree-sdk is installed and the key authenticates
  2. A Python 3 sandbox can be started with "tag:python:3.11"
  3. The program injection approach (base64 decode + run) works correctly
  4. stdout, exit_code, and result.uuid are accessible as expected
  5. OUTPUT_SHA256 of a known input matches the local backend

Usage:
    # .env needs NEBIUS_API_KEY and NEBIUS_PROJECT_ID (from the Nebius console)
    python3 -m scripts.probes.probe_sandbox

Record the output in DECISIONS.md and update PLATFORM_NOTES.md.
If the probe passes, mark T1.3 in TASKS.md as PROVEN and update HANDOFF.md.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


def _canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


HELLO_PROGRAM = b"""\
import json, sys
data = json.load(sys.stdin)
result = {"echo": data, "computed": data.get("x", 0) * 2}
print(json.dumps(result))
"""

CALC_INPUT = json.dumps({"x": 21, "label": "probe"})


def probe_hello(api_key: str, project_id: str) -> None:
    """Run a trivial program through the SAME backend the app uses and check stdout + run ref."""
    from ddp.compute.runner import NebiusSandboxBackend

    print(f"  stdin: {CALC_INPUT}")
    stdout, ref = NebiusSandboxBackend(api_key=api_key, project_id=project_id).execute(
        HELLO_PROGRAM, CALC_INPUT)
    print(f"  stdout    : {stdout!r}")
    print(f"  BACKEND_RUN_REF candidate: {ref}")
    out = json.loads(stdout)
    assert out == {"echo": {"x": 21, "label": "probe"}, "computed": 42}, \
        f"[FAIL] unexpected output: {out}"
    assert ref, "[FAIL] no run reference returned"
    print("  [PASS] hello probe — stdout matches expected output, run reference returned")


def probe_calculator_equivalence(api_key: str, project_id: str) -> None:
    """Verify OUTPUT_SHA256 from the sandbox matches the local backend."""
    from ddp.compute.runner import (
        PROGRAM_PATH, LocalSubprocessBackend, NebiusSandboxBackend,
        canonical_json, sha256_bytes,
    )
    from ddp.bootstrap import open_store, compute_params

    store = open_store()
    txns = store.transactions_for("ALERT-01")
    params = compute_params(store)
    program = PROGRAM_PATH.read_bytes()
    input_json = canonical_json({"alert_id": "ALERT-01", "transactions": txns, "params": params})

    print("\n  Running local backend...")
    local_stdout, _ = LocalSubprocessBackend().execute(program, input_json)
    local_hash = sha256_bytes(canonical_json(json.loads(local_stdout)).encode())
    print(f"  local OUTPUT_SHA256: {local_hash}")

    print("  Running sandbox backend...")
    sandbox = NebiusSandboxBackend(api_key=api_key, project_id=project_id)
    sandbox_stdout, sandbox_ref = sandbox.execute(program, input_json)
    sandbox_hash = sha256_bytes(canonical_json(json.loads(sandbox_stdout)).encode())
    print(f"  sandbox OUTPUT_SHA256: {sandbox_hash}")
    print(f"  sandbox BACKEND_RUN_REF: {sandbox_ref}")

    if local_hash == sandbox_hash:
        print("  [PASS] equivalence — OUTPUT_SHA256 matches local backend")
    else:
        print("[FAIL] OUTPUT_SHA256 mismatch — sandbox compute differs from local!")
        print(f"  local stdout:   {local_stdout[:300]}")
        print(f"  sandbox stdout: {sandbox_stdout[:300]}")
        sys.exit(1)

    print(f"\n  Record in DECISIONS.md:")
    print(f"    BACKEND_RUN_REF: {sandbox_ref}")
    print(f"    CODE_SHA256    : {sha256_bytes(program)}")
    print(f"    OUTPUT_SHA256  : {sandbox_hash}")


def main() -> None:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.environ.get("NEBIUS_API_KEY")
    if not api_key:
        print("[FAIL] NEBIUS_API_KEY not set. Add it to .env first.")
        sys.exit(1)
    project_id = os.environ.get("NEBIUS_PROJECT_ID")
    if not project_id:
        print("[FAIL] NEBIUS_PROJECT_ID not set. The Sandboxes API rejects requests without a "
              "project (\"Missing Project header\"). Add your Nebius project ID to .env.")
        sys.exit(1)

    print("=== Probe 1: hello world ===")
    probe_hello(api_key, project_id)

    print("\n=== Probe 2: calculator equivalence ===")
    try:
        probe_calculator_equivalence(api_key, project_id)
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        sys.exit(1)

    print("\n=== All sandbox probes passed ===")
    print("Next steps:")
    print("  1. Record the BACKEND_RUN_REF above in DECISIONS.md")
    print("  2. Update PLATFORM_NOTES.md: mark Sandboxes section as PROVEN")
    print("  3. Check off T1.3 in TASKS.md")
    print("  4. Update HANDOFF.md claim status: sandbox → PROVEN")


if __name__ == "__main__":
    main()
