"""
Runtime configuration — read once from environment / .env.

Nothing here is secret-bearing except NEBIUS_API_KEY, which is read from the
environment only and never logged or written to the ledger.

Model IDs are DEFAULTS taken from Nebius's public model pages (Sep 2026).
They are [ASSUMED] until confirmed against the live catalog:
    python -m scripts.check_models        # lists /v1/models and diffs against these
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

try:  # optional dependency; config still works from plain env vars
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except Exception:  # pragma: no cover
    pass


# Tier -> job mapping (see DECISIONS.md D-N03). Each skill asks for a TIER, never a model id,
# so swapping a model is a config change, and the ledger records which model actually answered.
DEFAULT_MODELS = {
    # high-volume, cheap: triage, checklist review, extraction
    "triage": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
    # factor-by-factor reasoning over case evidence
    "reasoning": "nvidia/nemotron-3-super-120b-a12b",
    # the consequential narrative (Ground of Suspicion) and disposition rationale
    "disposition": "nvidia/Nemotron-3-Ultra-550b-a55b",
}


@dataclass(frozen=True)
class Settings:
    base_url: str = field(
        default_factory=lambda: os.environ.get(
            "TOKEN_FACTORY_BASE_URL", "https://api.tokenfactory.nebius.com/v1/"
        )
    )
    api_key: str | None = field(default_factory=lambda: os.environ.get("NEBIUS_API_KEY"))
    models: dict = field(
        default_factory=lambda: {
            tier: os.environ.get(f"MODEL_{tier.upper()}", default)
            for tier, default in DEFAULT_MODELS.items()
        }
    )
    # 180 s, not 90: a full-budget reasoning reply runs ~240 tokens/s (observed 2026-10-28).
    request_timeout_s: float = field(
        default_factory=lambda: float(os.environ.get("LLM_TIMEOUT_S", "180"))
    )
    # Output budget per model call. Nemotron's hidden reasoning counts against it, so small caps
    # cut replies off mid-reasoning (2,048 / 4,096 did, 2026-10-28; DECISIONS.md). Tokens are
    # billed as generated, so the budget is a ceiling, not a cost. A reply cut off at the default
    # is retried once at the cap; a reply cut off at the cap is an error, never an answer.
    max_output_tokens: int = field(
        default_factory=lambda: int(os.environ.get("LLM_MAX_OUTPUT_TOKENS", "16384")))
    max_output_tokens_cap: int = field(
        default_factory=lambda: int(os.environ.get("LLM_MAX_OUTPUT_TOKENS_CAP", "32768")))
    db_path: Path = field(
        default_factory=lambda: Path(
            os.environ.get("DDP_DB_PATH", str(REPO_ROOT / "data" / "ddp.sqlite3"))
        )
    )
    # Compute backend for the calculator of record: "local" | "nebius-sandbox"
    compute_backend: str = field(
        default_factory=lambda: os.environ.get("COMPUTE_BACKEND", "local")
    )
    tavily_api_key: str | None = field(default_factory=lambda: os.environ.get("TAVILY_API_KEY"))
    # Regulatory lookup (T12.11): "hybrid" = BM25 + Token Factory embeddings when a key is set,
    # "bm25" = lexical only. Abstention is the BM25 rule either way.
    retrieval_mode: str = field(default_factory=lambda: os.environ.get("RETRIEVAL_MODE", "hybrid"))
    embedding_model: str = field(
        default_factory=lambda: os.environ.get("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-8B"))
    # Token Factory Sandboxes reject requests without a project (observed 2026-10-21).
    nebius_project_id: str | None = field(
        default_factory=lambda: os.environ.get("NEBIUS_PROJECT_ID"))
    # Public demo (T7): each browser session gets its own in-memory seeded database (nothing a
    # visitor records reaches another visitor or survives a reload) and a model-call budget.
    demo_mode: bool = field(
        default_factory=lambda: os.environ.get("DDP_DEMO_MODE", "") in ("1", "true", "yes"))
    demo_max_model_calls: int = field(
        default_factory=lambda: int(os.environ.get("DDP_DEMO_MAX_MODEL_CALLS", "40")))

    @property
    def llm_configured(self) -> bool:
        return bool(self.api_key)


def get_settings() -> Settings:
    return Settings()
