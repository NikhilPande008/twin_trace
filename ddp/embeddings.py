"""
Token Factory embeddings (T12.11) for hybrid regulatory retrieval.

Model: Qwen/Qwen3-Embedding-8B, the only embedding model in this account's Token Factory catalog
on 2026-10-28 (no NVIDIA embedding model is listed, and the /v1/rerank endpoint returned 404 for
every rerank model ID tried). Embeddings only REORDER rules that lexical retrieval already found
relevant; whether to answer at all stays the deterministic BM25 coverage rule (ddp.retrieval).

Only corpus rule text and the officer's regulatory question are embedded, never case data. A
question that contains case identifiers is refused before lookup by screen_request.
"""

from __future__ import annotations

import hashlib
import math

DEFAULT_EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-8B"


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class TokenFactoryEmbedder:
    """embed(texts) -> vectors, cached per process by sha256(model + text)."""

    def __init__(self, settings, model: str | None = None, _post=None, timeout_s: float = 30.0):
        self.settings = settings
        self.model = model or DEFAULT_EMBEDDING_MODEL
        self._post = _post
        self.timeout_s = timeout_s
        self._cache: dict[str, list[float]] = {}
        self.calls: list[dict] = []

    def _key(self, text: str) -> str:
        return hashlib.sha256(f"{self.model}\x00{text}".encode()).hexdigest()

    def embed(self, texts: list[str]) -> list[list[float]]:
        missing = [t for t in dict.fromkeys(texts) if self._key(t) not in self._cache]
        if missing:
            post = self._post or _requests_post
            url = self.settings.base_url.rstrip("/") + "/embeddings"
            resp = post(url, headers={"Authorization": f"Bearer {self.settings.api_key}"},
                        json={"model": self.model, "input": missing}, timeout=self.timeout_s)
            if resp.status_code != 200:
                raise RuntimeError(f"embeddings HTTP {resp.status_code}: {resp.text[:200]}")
            body = resp.json()
            for item in body["data"]:
                self._cache[self._key(missing[item["index"]])] = item["embedding"]
            self.calls.append({"model": body.get("model", self.model), "inputs": len(missing),
                               "usage": body.get("usage")})
        return [self._cache[self._key(t)] for t in texts]


def _requests_post(url, headers, json, timeout):  # pragma: no cover - thin shim
    import requests
    return requests.post(url, headers=headers, json=json, timeout=timeout)
