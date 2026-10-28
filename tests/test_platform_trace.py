"""The platform trace shows only recorded calls and states the compute backend honestly."""

from __future__ import annotations

from ddp import platform_trace as PT

CONFIGURED = {"triage": "nvidia/nano", "reasoning": "nvidia/super", "disposition": "nvidia/ultra"}


def test_no_calls_means_not_called():
    tiers = PT.by_tier([], CONFIGURED)
    assert [t["tier"] for t in tiers] == list(PT.TIERS)
    assert all(t["calls"] == 0 and t["tokens"] == 0 for t in tiers)
    assert tiers[1]["model"] == "nvidia/super"          # configured, not claimed as used


def test_rows_sum_per_tier_and_prefer_reported_model():
    rows = PT.call_rows("assess", [
        {"tier": "reasoning", "model_requested": "nvidia/super", "model_reported": "nvidia/super-x",
         "usage": {"prompt_tokens": 100, "completion_tokens": 20}, "latency_s": 2.04},
        {"tier": "reasoning", "model_requested": "nvidia/super", "failed": True,
         "usage": {}, "latency_s": 1.0},
    ])
    r = PT.by_tier(rows, CONFIGURED)[1]
    assert r["calls"] == 2 and r["failed"] == 1 and r["tokens"] == 120 and r["seconds"] == 3.0
    assert r["model"] == "nvidia/super, nvidia/super-x"


def test_local_backend_never_claims_a_sandbox():
    c = PT.compute_line({"BACKEND": "local", "BACKEND_RUN_REF": None, "RUN_ID": "RUN-1",
                         "CODE_SHA256": "ab" * 32})
    assert c["label"].startswith("Local isolated subprocess")
    assert "403" in c["note"] and "not used" in c["note"]


def test_sandbox_label_only_with_a_run_reference():
    c = PT.compute_line({"BACKEND": "nebius-sandbox", "BACKEND_RUN_REF": "op-123", "RUN_ID": "R"})
    assert "op-123" in c["label"] and c["note"] == ""
    c = PT.compute_line({"BACKEND": "nebius-sandbox", "BACKEND_RUN_REF": None, "RUN_ID": "R"})
    assert "Sandbox ·" not in c["label"]
