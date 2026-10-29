"""Hybrid regulatory retrieval (T12.11) — offline with a fake embedder."""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ddp.bootstrap import open_store  # noqa: E402
from ddp.embeddings import TokenFactoryEmbedder, cosine  # noqa: E402
from ddp.retrieval import HybridIndex, tokenize  # noqa: E402
from ddp.skills import CoPilotSkills  # noqa: E402


class HashEmbedder:
    """Bag-of-words hashed into 64 dims: deterministic, no network."""
    def __init__(self, fail=False):
        self.fail, self.n = fail, 0

    def embed(self, texts):
        if self.fail:
            raise RuntimeError("down")
        self.n += 1
        out = []
        for t in texts:
            v = [0.0] * 64
            for tok in tokenize(t):
                v[int(hashlib.md5(tok.encode()).hexdigest(), 16) % 64] += 1
            out.append(v)
        return out


def _skills(embedder):
    return CoPilotSkills(open_store(":memory:"), embedder=embedder)


def test_off_corpus_questions_still_abstain():
    sk = _skills(HashEmbedder())
    for q in ("PMLA obligations virtual asset service provider VASP",
              "What are the Basel III capital adequacy requirements?"):
        assert sk.regulatory_lookup(q) == []


def test_on_corpus_question_is_answered_in_hybrid_mode():
    hits = _skills(HashEmbedder()).regulatory_lookup("What is the STR filing deadline?")
    assert hits and all(h["retrieval"] == "hybrid" for h in hits)
    assert all(h["evidence_level"] in ("PROVEN", "ASSUMED") for h in hits)


def test_needs_verification_rules_unreachable_in_hybrid_mode():
    store = open_store(":memory:")
    sk = CoPilotSkills(store, embedder=HashEmbedder())
    for r in store.corpus_rows(("NEEDS-VERIFICATION",)):
        for q in (r["RULE_ID"], r["RULE_TEXT"][:200]):
            assert r["RULE_ID"] not in {x["rule_id"] for x in sk.regulatory_lookup(q, limit=10)}


def test_embedding_failure_falls_back_to_lexical_order():
    store = open_store(":memory:")
    q = "cash transaction reporting threshold"
    lexical = [h["rule_id"] for h in CoPilotSkills(store).regulatory_lookup(q)]
    hits = CoPilotSkills(store, embedder=HashEmbedder(fail=True)).regulatory_lookup(q)
    assert [h["rule_id"] for h in hits] == lexical
    assert hits[0]["retrieval"].startswith("bm25")


def test_corpus_vectors_are_computed_once():
    emb = HashEmbedder()
    idx = HybridIndex(open_store(":memory:").corpus_rows(), emb)
    idx.search("STR filing deadline")
    idx.search("beneficial ownership")
    assert emb.n == 3          # rules once + one call per question


class _Resp:
    def __init__(self, body):
        self.status_code, self._b, self.text = 200, body, ""

    def json(self):
        return self._b


def test_token_factory_embedder_request_and_cache():
    sent = []

    def post(url, headers, json, timeout):
        sent.append((url, json))
        return _Resp({"model": json["model"], "usage": {"prompt_tokens": 3},
                      "data": [{"index": i, "embedding": [float(i + 1), 1.0]}
                               for i, _ in enumerate(json["input"])]})

    class S:
        base_url, api_key = "https://example.test/v1/", "k"
    e = TokenFactoryEmbedder(S(), _post=post)
    a = e.embed(["x", "y"])
    b = e.embed(["y", "x"])
    assert sent[0][0] == "https://example.test/v1/embeddings"
    assert sent[0][1] == {"model": "Qwen/Qwen3-Embedding-8B", "input": ["x", "y"]}
    assert len(sent) == 1 and b == [a[1], a[0]]
    assert round(cosine([1, 0], [1, 0]), 6) == 1.0
