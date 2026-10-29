"""
Regulatory retrieval — lexical BM25 over the corpus, NEEDS-VERIFICATION excluded.

Deliberately lexical and dependency-free: 49 rules do not need a vector index, and exact terms
(section numbers, "STR", "CTR", "₹10 lakh") matter more than paraphrase.

Guardrail (unchanged from baseline, now enforced in one place):
    Rules with EVIDENCE_LEVEL = 'NEEDS-VERIFICATION' are never indexed, so they
    cannot be returned by any query path.

Abstention (SCN-20): two heuristics, both deliberately simple and documented as such.
  1. Coverage: if fewer than MIN_COVERAGE of the query's content terms occur anywhere
     in the corpus, the question is off-corpus (e.g. "VASP obligations") -> [].
  2. Score floor: individual hits below MIN_SCORE are dropped.
Returning [] lets the UI say "no rule in the corpus covers this" instead of showing
the least-bad match as if it answered the question.
"""

from __future__ import annotations

import math
import re
from collections import Counter

ALLOWED_LEVELS = ("PROVEN", "ASSUMED")
MIN_SCORE = 1.0      # per-hit floor
MIN_COVERAGE = 0.5   # share of query terms that must exist in the corpus vocabulary

_STOP = set("""
a an the of to in on for and or is are was were be been by with as at from that this these those
what which who whom when where how why do does did can could should would will shall may might
must not no any all each per under over into than then there their its it about
""".split())

_TOKEN = re.compile(r"[a-z0-9]+(?:-[0-9]+)?")


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall((text or "").lower()) if t not in _STOP and len(t) > 1]


class CorpusIndex:
    def __init__(self, rows: list[dict], k1: float = 1.5, b: float = 0.75):
        self.rows = [r for r in rows if r.get("EVIDENCE_LEVEL") in ALLOWED_LEVELS]
        self.k1, self.b = k1, b
        self.docs = [tokenize(self._doc_text(r)) for r in self.rows]
        self.tf = [Counter(d) for d in self.docs]
        self.avgdl = (sum(len(d) for d in self.docs) / len(self.docs)) if self.docs else 0.0
        df: Counter = Counter()
        for d in self.docs:
            df.update(set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    @staticmethod
    def _doc_text(r: dict) -> str:
        parts = [r.get("RULE_ID"), r.get("CATEGORY"), r.get("SUBCATEGORY"),
                 r.get("RULE_TEXT"), r.get("MY_SYNTHESIS"), r.get("SOURCE_DOCUMENT")]
        # RULE_ID twice: queries that name a rule should find it first
        return " ".join(str(p) for p in parts if p) + " " + str(r.get("RULE_ID") or "")

    def coverage(self, tokens: list[str]) -> float:
        return (sum(1 for t in tokens if t in self.idf) / len(tokens)) if tokens else 0.0

    def search(self, question: str, limit: int = 5) -> list[tuple[float, dict]]:
        q = tokenize(question)
        if not q or not self.docs:
            return []
        if self.coverage(q) < MIN_COVERAGE:
            return []
        scored = []
        for i, tf in enumerate(self.tf):
            dl = len(self.docs[i])
            s = 0.0
            for t in q:
                f = tf.get(t)
                if not f:
                    continue
                s += self.idf.get(t, 0.0) * f * (self.k1 + 1) / (
                    f + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1)))
            if s >= MIN_SCORE:
                scored.append((s, self.rows[i]))
        scored.sort(key=lambda x: (-x[0], x[1].get("RULE_ID") or ""))
        return scored[:limit]


RRF_K = 60   # reciprocal-rank fusion constant (the usual default)


class HybridIndex(CorpusIndex):
    """BM25 + Token Factory embeddings, fused by reciprocal rank (T12.11).

    Abstention is unchanged and deterministic: if BM25 returns nothing (coverage gate or score
    floor), the hybrid returns nothing, whatever the embeddings say. When BM25 does find
    something, the candidates are the BM25 hits plus the `limit` nearest rules by embedding,
    all from the same PROVEN/ASSUMED index, and the order is the fused rank. If the embedding
    call fails, the BM25 order is returned and `last_mode` says so.
    """

    def __init__(self, rows: list[dict], embedder, **kw):
        super().__init__(rows, **kw)
        self.embedder = embedder
        self._vecs: list[list[float]] | None = None
        self.last_mode = "bm25"

    def _rule_vectors(self) -> list[list[float]]:
        if self._vecs is None:
            self._vecs = self.embedder.embed([self._doc_text(r) for r in self.rows])
        return self._vecs

    def search(self, question: str, limit: int = 5) -> list[tuple[float, dict]]:
        lexical = super().search(question, limit=len(self.rows))
        if not lexical:
            self.last_mode = "abstained"
            return []
        try:
            from .embeddings import cosine
            qv = self.embedder.embed([question])[0]
            sims = [(cosine(qv, v), i) for i, v in enumerate(self._rule_vectors())]
        except Exception:  # noqa: BLE001 — degrade to lexical, never to a guess
            self.last_mode = "bm25 (embeddings unavailable)"
            return lexical[:limit]
        self.last_mode = "hybrid"
        idx = {id(r): i for i, r in enumerate(self.rows)}
        bm_rank = {idx[id(r)]: k for k, (_, r) in enumerate(lexical)}
        emb_order = [i for _, i in sorted(sims, key=lambda x: (-x[0], x[1]))]
        emb_rank = {i: k for k, i in enumerate(emb_order)}
        cands = set(bm_rank) | set(emb_order[:limit])
        fused = sorted(((sum(1 / (RRF_K + 1 + rk[i]) for rk in (bm_rank, emb_rank) if i in rk), i)
                        for i in cands), key=lambda x: (-x[0], self.rows[x[1]].get("RULE_ID") or ""))
        return [(round(s * 1000, 3), self.rows[i]) for s, i in fused[:limit]]
