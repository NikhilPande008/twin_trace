"""
Regulatory retrieval: BM25 alone vs hybrid (BM25 + Token Factory embeddings), T12.11.

    python -m scripts.run_retrieval_eval            # live: needs NEBIUS_API_KEY
    python -m scripts.run_retrieval_eval --mock     # offline harness self-test (MOCK)

Paraphrased questions, each labelled with the corpus rule that answers it, plus off-corpus
questions that must get no answer. The labels are this project's (author-assigned); 20 questions
support no general accuracy claim. Reported: the labelled rule in the top 3, and abstentions kept.
Writes evals/RETRIEVAL-<date>-<mode>.md and .json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ddp.bootstrap import open_store  # noqa: E402
from ddp.config import get_settings  # noqa: E402
from ddp.embeddings import TokenFactoryEmbedder  # noqa: E402
from ddp.retrieval import tokenize  # noqa: E402
from ddp.skills import CoPilotSkills  # noqa: E402

# (question, the rule that answers it). Worded to avoid the rule's own key terms where possible.
LABELLED = [
    ("How many days do we have to report a suspicious customer once we suspect them?", "STR-002"),
    ("Is there a minimum amount below which suspicion need not be reported?", "STR-005"),
    ("A customer tried to send money but the payment was blocked. Do we still report?", "STR-003"),
    ("Can the officer tell the customer that we have reported them?", "SB-003"),
    ("Which portal do suspicious transaction reports go through?", "STR-006"),
    ("By which date must last month's large cash deposits be reported?", "CTR-002"),
    ("Above what cash amount must a report be made regardless of suspicion?", "CTR-001"),
    ("If a cash deposit is both large and suspicious, do we file both reports?", "CTR-003"),
    ("How long must transaction records be kept?", "RR-001"),
    ("What must the narrative section of a suspicious report contain?", "RS-004"),
    ("We found fake currency notes at the branch counter. What report applies?", "CCR-001"),
    ("Transactions involving a charity or non-profit: is there a separate report?", "NTR-001"),
    ("What will inspectors look at when an alert was closed without a report?", "INS-001"),
    ("Who is allowed to make the decision to report, and by when?", "INS-002"),
    ("Does the customer's declared salary explain the money coming in?", "POE-005"),
    ("Are the countries involved in the transfers high risk?", "POE-011"),
]
CAVEAT = ("The questions and labels were written by the coding assistant after reading the corpus and before either method was run on them; a reviewer's own questions would be a fairer test.")

OFF_CORPUS = [
    "What is the VASP licensing fee?",
    "What are the Basel III capital adequacy requirements?",
    "How do I open a demat account?",
    "What is the GST rate on gold jewellery?",
]


class MockEmbedder:
    def embed(self, texts):
        out = []
        for t in texts:
            v = [0.0] * 32
            for tok in tokenize(t):
                v[int(hashlib.md5(tok.encode()).hexdigest(), 16) % 32] += 1
            out.append(v)
        return out


def _run(skills) -> dict:
    rows = []
    for q, want in LABELLED:
        hits = skills.regulatory_lookup(q, limit=3)
        ids = [h["rule_id"] for h in hits]
        rows.append({"question": q, "expected": want, "top3": ids, "hit": want in ids,
                     "mode": hits[0]["retrieval"] if hits else "abstained"})
    abst = [{"question": q, "abstained": skills.regulatory_lookup(q) == []} for q in OFF_CORPUS]
    return {"labelled": rows, "off_corpus": abst,
            "hits_at_3": sum(r["hit"] for r in rows),
            "abstained": sum(a["abstained"] for a in abst)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "evals"))
    args = ap.parse_args(argv)
    settings = get_settings()
    if not args.mock and not settings.llm_configured:
        print("NEBIUS_API_KEY not set; use --mock.")
        return 2
    store = open_store(":memory:")
    embedder = MockEmbedder() if args.mock else TokenFactoryEmbedder(settings,
                                                                     settings.embedding_model)
    bm25 = _run(CoPilotSkills(store))
    hybrid = _run(CoPilotSkills(store, embedder=embedder))
    now = datetime.now(timezone.utc)
    mode = "mock" if args.mock else "live"
    rep = {"mode": mode, "generated_at": now.isoformat(timespec="seconds"),
           "embedding_model": "mock-hash" if args.mock else settings.embedding_model,
           "embedding_calls": getattr(embedder, "calls", []),
           "labelled": len(LABELLED), "off_corpus": len(OFF_CORPUS),
           "bm25": bm25, "hybrid": hybrid}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = out / f"RETRIEVAL-{now:%Y-%m-%d}-{mode}"
    stem.with_suffix(".json").write_text(json.dumps(rep, indent=1))
    lines = [f"# Regulatory retrieval: BM25 vs hybrid — {rep['generated_at']} ({mode.upper()})", ""]
    if args.mock:
        lines += ["**MOCK embedder: tests the harness only. Do not quote.**", ""]
    lines += [f"Embedding model `{rep['embedding_model']}` via Nebius Token Factory. "
              f"{len(LABELLED)} paraphrased questions with an author-assigned answering rule; "
              f"{len(OFF_CORPUS)} off-corpus questions that must get no answer. Too few to "
              "support a general accuracy claim. " + CAVEAT, "",
              "| | Labelled rule in top 3 | Off-corpus abstained |", "|---|---|---|",
              f"| BM25 only | {bm25['hits_at_3']} / {len(LABELLED)} | {bm25['abstained']} / {len(OFF_CORPUS)} |",
              f"| Hybrid | {hybrid['hits_at_3']} / {len(LABELLED)} | {hybrid['abstained']} / {len(OFF_CORPUS)} |",
              "", "| Question | Expected | BM25 top 3 | Hybrid top 3 |", "|---|---|---|---|"]
    for b, h in zip(bm25["labelled"], hybrid["labelled"]):
        lines.append(f"| {b['question']} | {b['expected']} | {', '.join(b['top3']) or 'abstained'}"
                     f" | {', '.join(h['top3']) or 'abstained'} |")
    stem.with_suffix(".md").write_text("\n".join(lines) + "\n")
    print(f"BM25 {bm25['hits_at_3']}/{len(LABELLED)}  hybrid {hybrid['hits_at_3']}/{len(LABELLED)}"
          f"  abstained {bm25['abstained']}/{hybrid['abstained']} of {len(OFF_CORPUS)}")
    print(f"wrote {stem}.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
