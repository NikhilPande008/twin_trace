"""
Compute runner — executes aggregations.v1 on a backend and records provenance.

Every run appends one COMPUTE_RUNS row with:
    CODE_SHA256   sha256 of the exact program bytes executed
    INPUT_SHA256  sha256 of the canonical JSON input (transactions + params)
    OUTPUT_SHA256 sha256 of the canonical JSON output
    BACKEND       'local' | 'nebius-sandbox'
    BACKEND_RUN_REF  sandbox instance/run id when remote (None locally)

Anyone holding the ledger can re-run the same program on the same input and must
get the same OUTPUT_SHA256. That — not "the AI said so" — is what makes a figure in
a Ground of Suspicion defensible.

Backends
--------
LocalSubprocessBackend   [PROVEN offline] isolated `python -I` subprocess, no repo
                         imports, empty env, hard timeout.
NebiusSandboxBackend     [ASSUMED until a live run] Token Factory Sandboxes via contree-sdk.
                         The SDK call shape was corrected against the installed SDK on
                         2026-10-21 (the earlier ContreeClient shape did not work), and the
                         live endpoint was reached, but no run has completed: it needs a
                         Nebius project ID (NEBIUS_PROJECT_ID). Without key AND project ID
                         it refuses to run. Do not describe sandbox execution as working in
                         any submission material until a real BACKEND_RUN_REF appears in
                         COMPUTE_RUNS (TASKS T1.3 / T9.3).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

PROGRAM_PATH = Path(__file__).with_name("aggregations.py")
PROGRAM_NAME = "aggregations.v1"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


class ComputeBackend(Protocol):
    name: str

    def execute(self, program: bytes, input_json: str) -> tuple[str, str | None]:
        """Run `program` with `input_json` on stdin. Returns (stdout_json, backend_run_ref)."""
        ...


class ComputeError(RuntimeError):
    pass


class LocalSubprocessBackend:
    name = "local"

    def __init__(self, timeout_s: float = 20.0):
        self.timeout_s = timeout_s

    def execute(self, program: bytes, input_json: str) -> tuple[str, str | None]:
        with tempfile.TemporaryDirectory() as tmp:
            prog = Path(tmp) / "program.py"
            prog.write_bytes(program)
            try:
                proc = subprocess.run(
                    [sys.executable, "-I", str(prog)],  # -I: isolated mode, no user site / env vars
                    input=input_json, capture_output=True, text=True,
                    timeout=self.timeout_s, cwd=tmp, env={},
                )
            except subprocess.TimeoutExpired as e:
                raise ComputeError(f"local compute timed out after {self.timeout_s}s") from e
        if proc.returncode != 0:
            raise ComputeError(f"local compute failed (exit {proc.returncode}): {proc.stderr[-500:]}")
        return proc.stdout, None


class NebiusSandboxBackend:
    """
    Runs the calculator program in a Nebius Token Factory Sandbox (contree-sdk >= 0.3).

    Needs `pip install contree-sdk`, NEBIUS_API_KEY and a Nebius project ID
    (NEBIUS_PROJECT_ID): the sandbox API rejects requests without a `Project` header and
    reports every permission as false for an unknown project (observed 2026-10-21).

    [ASSUMED] until scripts/probes/probe_sandbox.py completes with a real project ID.
    Approach: base64-encode the program, decode it inside the sandbox with one shell command,
    and run it with input_json on stdin. BACKEND_RUN_REF is the sandbox operation UUID
    captured when the run is started (the result object does not expose it); if that cannot
    be captured, the result image UUID is used, and with neither the run is refused as
    unreferenced rather than recorded without a reference.
    """
    name = "nebius-sandbox"

    def __init__(self, api_key: str | None = None, project_id: str | None = None,
                 image: str = "tag:python:3.11", timeout_s: float = 60.0):
        self.api_key = api_key
        self.project_id = project_id
        self.image_name = image
        self.timeout_s = timeout_s

    def execute(self, program: bytes, input_json: str) -> tuple[str, str | None]:
        if not self.api_key or not self.project_id:
            raise ComputeError(
                "Nebius Sandbox backend needs NEBIUS_API_KEY and NEBIUS_PROJECT_ID (T1.3). "
                "Until both are set and a probe run succeeds, use COMPUTE_BACKEND=local.")

        import base64 as _b64
        encoded = _b64.b64encode(program).decode()
        # base64 alphabet is A-Za-z0-9+/= — safe to embed in a shell word without quoting.
        shell_cmd = f"echo {encoded} | base64 -d > /tmp/prog.py && python3 /tmp/prog.py"

        try:
            from contree_sdk import ContreeSync
            from contree_sdk.auth import IAMAuth
            from contree_sdk.config import ContreeConfig
        except ImportError as exc:
            raise ComputeError(
                "contree-sdk not installed: pip install contree-sdk") from exc

        operation_ids: list[str] = []
        try:
            client = ContreeSync(config=ContreeConfig(
                auth=IAMAuth(token=self.api_key, project_id=self.project_id)))
            original = client._start_operation

            async def _spy(request):
                op = await original(request)
                operation_ids.append(str(op))
                return op

            client._start_operation = _spy
            image = client.images.use(self.image_name)
            result = image.run(shell=shell_cmd, stdin=input_json,
                               timeout=self.timeout_s).wait()
            stdout, exit_code = result.stdout, result.exit_code
            stderr = result.stderr
            image_uuid = str(result.uuid) if getattr(result, "uuid", None) else None
        except Exception as exc:
            raise ComputeError(
                f"Nebius Sandbox error: {type(exc).__name__}: {str(exc)[:300]}") from exc

        if exit_code != 0:
            raise ComputeError(
                f"sandbox compute failed (exit {exit_code}): {(stderr or '')[-500:]}")
        backend_run_ref = operation_ids[-1] if operation_ids else image_uuid
        if not backend_run_ref:
            raise ComputeError("sandbox run completed but returned no run reference; "
                               "refusing to record it as a remote run")
        return stdout, backend_run_ref


def backend_from_name(name: str, api_key: str | None = None,
                      project_id: str | None = None) -> ComputeBackend:
    if name == "local":
        return LocalSubprocessBackend()
    if name == "nebius-sandbox":
        return NebiusSandboxBackend(api_key=api_key, project_id=project_id)
    raise ValueError(f"Unknown compute backend '{name}'")


class ComputeRunner:
    def __init__(self, store=None, backend: ComputeBackend | None = None):
        self.store = store
        self.backend = backend or LocalSubprocessBackend()

    def run(self, alert_id: str, transactions: list[dict], params: dict | None = None, *,
            parent_run_id: str | None = None, hypothesis: list | None = None) -> dict:
        program = PROGRAM_PATH.read_bytes()
        payload = {"alert_id": alert_id, "transactions": transactions, "params": params or {}}
        input_json = canonical_json(payload)
        started = datetime.now(timezone.utc).isoformat()
        stdout, backend_ref = self.backend.execute(program, input_json)
        finished = datetime.now(timezone.utc).isoformat()
        try:
            output = json.loads(stdout)
        except json.JSONDecodeError as e:
            raise ComputeError(f"compute output is not JSON: {stdout[:200]!r}") from e
        output_json = canonical_json(output)
        run = {
            "RUN_ID": f"RUN-{uuid.uuid4().hex[:12]}",
            "ALERT_ID": alert_id,
            "PROGRAM": PROGRAM_NAME,
            "BACKEND": self.backend.name,
            "BACKEND_RUN_REF": backend_ref,
            "CODE_SHA256": sha256_bytes(program),
            "INPUT_SHA256": sha256_bytes(input_json.encode()),
            "OUTPUT_SHA256": sha256_bytes(output_json.encode()),
            "OUTPUT_JSON": output_json,
            "STARTED_AT": started,
            "FINISHED_AT": finished,
            "PARENT_RUN_ID": parent_run_id,
            "HYPOTHESIS_JSON": canonical_json(hypothesis) if hypothesis is not None else None,
            "INPUT_JSON": input_json,
        }
        if self.store is not None:
            self.store.archive_program(run["CODE_SHA256"], PROGRAM_NAME, program.decode())
            self.store.append_compute_run(run)
        return {
            "run_id": run["RUN_ID"],
            "facts": output.get("facts", []),
            "warnings": output.get("warnings", []),
            "provenance": {k: run[k] for k in ("RUN_ID", "PROGRAM", "BACKEND", "BACKEND_RUN_REF",
                                                "CODE_SHA256", "INPUT_SHA256", "OUTPUT_SHA256")},
        }


def reproduce_recorded(store, run_id: str, backend: ComputeBackend | None = None) -> dict:
    """Re-execute a recorded run from what was RECORDED: its saved input and the archived
    program with its CODE_SHA256. Never substitutes current transactions or current code.

    Returns {status: reproduced | mismatch | unavailable, reason, input_matches, code_matches,
    output_matches}. 'unavailable' when the run predates saved inputs or its program version
    was never archived — reproduction is then not claimed.
    """
    run = store.get_compute_run(run_id)
    if not run:
        return {"status": "unavailable", "reason": f"run {run_id} not found"}
    if not run.get("INPUT_JSON"):
        return {"status": "unavailable",
                "reason": "inputs were not saved with this run (recorded before T3); hashes can "
                          "detect a difference but cannot recover the original inputs"}
    prog = store.get_program(run["CODE_SHA256"])
    if not prog:
        return {"status": "unavailable",
                "reason": f"program version {run['CODE_SHA256'][:12]}… is not archived"}
    input_ok = sha256_bytes(run["INPUT_JSON"].encode()) == run["INPUT_SHA256"]
    code_ok = sha256_bytes(prog["SOURCE"].encode()) == run["CODE_SHA256"]
    if not (input_ok and code_ok):
        return {"status": "mismatch", "reason": "saved input or archived program does not match "
                "its recorded hash", "input_matches": input_ok, "code_matches": code_ok,
                "output_matches": False}
    stdout, _ = (backend or LocalSubprocessBackend()).execute(prog["SOURCE"].encode(),
                                                              run["INPUT_JSON"])
    out_ok = sha256_bytes(canonical_json(json.loads(stdout)).encode()) == run["OUTPUT_SHA256"]
    return {"status": "reproduced" if out_ok else "mismatch",
            "reason": "" if out_ok else "re-execution produced a different output hash",
            "input_matches": True, "code_matches": True, "output_matches": out_ok}


def reproduce(run_row: dict, transactions: list[dict], params: dict,
              backend: ComputeBackend | None = None) -> dict:
    """Re-execute a recorded run with the CURRENT program and compare hashes.

    Returns {input_matches, code_matches, output_matches}. code_matches=False means the
    program changed since the run; the recorded CODE_SHA256 identifies which version to
    check out (git) to reproduce it exactly.
    """
    program = PROGRAM_PATH.read_bytes()
    input_json = canonical_json({"alert_id": run_row["ALERT_ID"], "transactions": transactions,
                                 "params": params or {}})
    stdout, _ = (backend or LocalSubprocessBackend()).execute(program, input_json)
    out_hash = sha256_bytes(canonical_json(json.loads(stdout)).encode())
    return {
        "input_matches": sha256_bytes(input_json.encode()) == run_row["INPUT_SHA256"],
        "code_matches": sha256_bytes(program) == run_row["CODE_SHA256"],
        "output_matches": out_hash == run_row["OUTPUT_SHA256"],
    }
