# Platform Notes — verified facts about external APIs

**Purpose:** Before writing code against any external API, read its official docs and record
what was verified here — with the URL and the date. If docs are unclear, record the probe
result. If an API cannot be verified, say so explicitly.

**Never invent numbers or capabilities.** If something is not in this file, it is ASSUMED or UNKNOWN.

---

## Nebius Token Factory — Chat Completions

**Status:** ASSUMED — not yet verified against live API. Verification is task T0.4.

**What to verify at T0.4:**
- Exact base URL for the OpenAI-compatible Chat Completions endpoint
- Model IDs for Nemotron 3 Nano, Super, Ultra (as they appear in `/v1/models`)
- Whether `response_format: {"type": "json_object"}` is supported for those models
- Rate limits and token context windows
- Whether `<think>…</think>` reasoning traces appear in completions for these models

**Probe script:** `scripts/check_models.py` (run with `python -m scripts.check_models --ping`)

**Current config (ASSUMED, from Nebius public model pages Sep 2026):**
- base URL: `https://api.tokenfactory.nebius.com/v1/`
- triage: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`
- reasoning: `nvidia/nemotron-3-super-120b-a12b`
- disposition: `nvidia/Nemotron-3-Ultra-550b-a55b`

**Structured output — researched 2026-09-28 (ASSUMED until live probe):**
- `response_format: {"type": "json_object"}` — supported by Token Factory for Nemotron models.
  Implemented in `ddp/llm.py` and used by `_complete_json_array` in `ddp/skills.py`.
- `response_format: {"type": "json_schema", ...}` — **do NOT use**: known bug on Nemotron as of
  2026-09-16 causes string escapes to be dropped in the generated JSON. Use `json_object` only.
- A NEW model was found during research: `nvidia/Nemotron-3_5-Lightning` (30B hybrid MoE, 3B
  active parameters, 1M context window). Potential triage tier upgrade — note for T0.4 evaluation.

---

## Nebius Token Factory — Sandboxes

**Status: ASSUMED (not yet run end to end).** The backend (`NebiusSandboxBackend`) was corrected
against the installed SDK on 2026-10-21 and the live endpoint was reached, but no run has
completed: a **Nebius project ID** is required and is not in `.env`.

**Verified 2026-10-21 with `contree-sdk` 0.3.6 and the real endpoint:**
- The earlier recipe here (`from contree_client.httpx import ContreeClient; ContreeSync(api_client)`)
  was **wrong**: it raises `AttributeError: 'ContreeClient' object has no attribute 'auth'`.
  `contree-sdk` 0.3.6 does not install `contree-client` and does not need it.
- Correct construction:
  `ContreeSync(config=ContreeConfig(auth=IAMAuth(token=<NEBIUS_API_KEY>, project_id=<NEBIUS_PROJECT_ID>)))`
- Default base URL: `https://api.tokenfactory.nebius.com/sandboxes/` (`/v1/instances`, `/v1/whoami`).
- The same `NEBIUS_API_KEY` authenticates. Without a project the API answers HTTP 400
  `Missing "Project" header`. With a placeholder project, `whoami` returns 200 but every
  permission (`import`, `spawn`, `spawn_disposable`, `list`, `cancel`, `set_image_tag`) is `false`,
  and a run is refused with `ForbiddenError`. So the project ID is what grants access.
- Limits reported by `whoami`: `instance_max_timeout` 3600 s, `instance_max_concurrency` 50.
- `image.run(shell=..., stdin=..., timeout=..., disposable=True).wait()` returns an object with
  `.stdout`, `.stderr`, `.exit_code`. The result does **not** expose the operation UUID; the backend
  captures it when the run is started and stores it as `BACKEND_RUN_REF`.

**Still to verify (needs a real project ID):**
- That `python3` and `base64` exist in `tag:python:3.11` and the program runs.
- That `OUTPUT_SHA256` equals the local backend's for the same input (`probe_sandbox.py` probe 2).
- That the captured operation UUID is a stable, retrievable run reference.
- Whether networking can be disabled for the run (no parameter found in the run signature).

**To run it:** add `NEBIUS_PROJECT_ID=<your project id>` to `.env`, then
`pip install contree-sdk` and `python3 -m scripts.probes.probe_sandbox`. Record the output in
DECISIONS.md and only then mark the sandbox PROVEN.

**Probe script:** `scripts/probes/probe_sandbox.py`

---

## Tavily

**Status:** PLANNED — verification is task T2.1.

**What to verify at T2.1:**
- API endpoint: `/search` and `/extract`
- Query parameters: `q`, `max_results`, `include_domains`, `exclude_domains`, `search_depth`
- Recency filter (if any)
- Credit cost per query
- Rate limits
- Whether domain filtering can constrain to news / financial domains

**Probe script:** `scripts/probes/probe_tavily.py` (to be created in T2.1)

---

## Nemotron Content Safety

**Status:** PLANNED — verification is task T3.1.

**What to verify at T3.1:**
- Whether it is available on Token Factory catalog or only via Nebius Serverless Endpoint
- Custom policy mode: how policies are specified (YAML / prompt / config)
- Cost per API call / per hour for a Serverless Endpoint
- Latency

**Probe script:** `scripts/probes/probe_content_safety.py` (to be created in T3.1)
