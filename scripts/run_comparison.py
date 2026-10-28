"""
Holdout evaluation and three-condition comparison (T5).

Part A — gate measurement (deterministic, no model): every seeded faulty narrative and every
supported narrative in evals/holdout/HOLDOUT-v1.json is run through the evidence gate.
Reports the catch rate on seeded faults, the false-rejection rate on supported narratives, and
each case where the result differs from the label (these are findings, not tuned away).

Part B — three conditions on the same cases and inputs:
  C1 template   structured manual template filled from calculator facts (no model)
  C2 baseline   the same model drafts from the raw case, with no computed facts and no gate
                (evaluation only; this is not a product path)
  C3 full       the product path: 11-factor assessment → drafter with calculator facts →
                hard gate (+ quality check)
For each draft: unsupported / unreadable figures (measured by the same validator against the
transactions and calculator facts), figures needing review, latency, tokens across all
attempts, and whether the calculator run reproduces from its recorded input.

NOT measured: officer review time or corrections (needs real participants), decision accuracy
beyond the six author-labelled cases. Six cases support no general claim.

Usage:
    python3 -m scripts.run_comparison --mock          # offline harness self-test
    python3 -m scripts.run_comparison                 # live (NEBIUS_API_KEY)
Writes evals/RUN-<UTC timestamp>-<mode>/ {config.json, outputs.jsonl, metrics.json, REPORT.md}.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ddp.bootstrap import compute_params, open_store, parse_declared_monthly_income  # noqa: E402
from ddp.compute import ComputeRunner, reproduce_recorded  # noqa: E402
from ddp.config import get_settings  # noqa: E402
from ddp.llm import TokenFactoryClient  # noqa: E402
from ddp.money import format_inr  # noqa: E402
from ddp.skills import POE_FACTORS, CoPilotSkills  # noqa: E402

HOLDOUT = ROOT / "evals" / "holdout" / "HOLDOUT-v1.json"
BASELINE_MARK = "[BASELINE-NO-CONTROLS]"


class MockLLM:
    """Offline stand-in. The baseline invents a total; the product path stays grounded."""

    def __init__(self):
        self.last_call = {}

    def complete(self, prompt, tier="reasoning", **_):
        self.last_call = {"provider": "mock", "tier": tier,
                          "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}
        if "Evaluate the draft" in prompt:
            return json.dumps({"items": [{"item_number": i, "applies": False, "note": ""}
                                         for i in range(1, 11)]})
        if '"factors"' in prompt or "11 PO suspicion factors" in prompt or "POE-002" in prompt:
            return json.dumps({"factors": [
                {"factor_id": f, "factor_name": n, "assessment": "clear", "evidence": "mock",
                 "evidence_txn_ids": [], "rules_cited": []} for f, n in POE_FACTORS]})
        if BASELINE_MARK in prompt:
            return "Funds totalling ₹99,99,999 moved through the account within days."
        return "The account received credits recorded in the transaction rows; see the facts."


def _git_rev() -> str:
    try:
        rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True, timeout=10).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "ddp", "scripts", "evals/holdout"],
                               cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
        return rev + ("-dirty" if dirty else "")
    except Exception:  # noqa: BLE001
        return "unknown"


def _params(store, case) -> dict:
    params = compute_params(store)
    inc = parse_declared_monthly_income(case["customer_profile"])
    if inc:
        params["declared_monthly_income_inr"] = {"amount_inr": inc, "source": case["id"]}
    return params


def _verdict(r: dict) -> str:
    if not r["passed"]:
        return "fail"
    return "needs_review" if r.get("needs_review") else "pass_but_outside_coverage"


def gate_measurement(cases, runner, store, skills) -> dict:
    faults, supported = [], []
    for c in cases:
        facts = runner.run(c["id"], c["transactions"], _params(store, c))["facts"]
        for f in c["seeded_faults"]:
            got = _verdict(skills.validate_gos_evidence(f["text"], c["transactions"], facts))
            faults.append({"case": c["id"], "fault": f["fault"], "text": f["text"],
                           "expected": f["expect"], "got": got,
                           "caught": got in ("fail", "needs_review")})
        for n in c["supported_narratives"]:
            r = skills.validate_gos_evidence(n["text"], c["transactions"],
                                             facts if n["needs_facts"] else None)
            supported.append({"case": c["id"], "text": n["text"], "rejected": not r["passed"]})
    designed = [f for f in faults if f["expected"] != "pass_but_outside_coverage"]
    return {
        "faults": faults, "supported": supported,
        "catch_rate_all": [sum(f["caught"] for f in faults), len(faults)],
        "catch_rate_in_designed_coverage": [sum(f["caught"] for f in designed), len(designed)],
        "false_rejections": [sum(s["rejected"] for s in supported), len(supported)],
        "label_mismatches": [f for f in faults if f["got"] != f["expected"]],
    }


def _template(case, facts) -> str:
    f = {x["fact_id"]: x for x in facts}
    parts = [f"Credits totalled {format_inr(f['F-TOTAL-CREDIT']['value'])} (F-TOTAL-CREDIT)"
             if f.get("F-TOTAL-CREDIT", {}).get("value") else None,
             f"debits totalled {format_inr(f['F-TOTAL-DEBIT']['value'])} (F-TOTAL-DEBIT)"
             if f.get("F-TOTAL-DEBIT", {}).get("value") else None,
             f"{format_inr(f['F-FLAGGED-AMOUNT']['value'])} involved flagged counterparties "
             "(F-FLAGGED-AMOUNT)" if f.get("F-FLAGGED-AMOUNT", {}).get("value") else None]
    return ("; ".join(p for p in parts if p) + ". " +
            f"Alert typology: {case['alert_type'].replace('_', ' ').lower()}. "
            "[Officer to state the grounds of suspicion and the evidence reviewed.]")


def _measure(text, case, facts, skills) -> dict:
    r = skills.validate_gos_evidence(text, case["transactions"], facts)
    return {"unsupported": len(r["unsupported_claims"]), "unparsed": len(r["unparsed_amounts"]),
            "needs_review": len(r.get("needs_review", [])),
            "figures": r["fact_coverage"]["amounts_checked"],
            "sentences_outside_coverage": len(r["coverage"]["outside_deterministic_coverage"])}


def _tokens(skills, start) -> int:
    return sum((c.get("usage") or {}).get("total_tokens", 0) for c in skills.call_log[start:])


def conditions(cases, runner, store, skills, llm_available: bool) -> list[dict]:
    rows = []
    for c in cases:
        params = _params(store, c)
        run = runner.run(c["id"], c["transactions"], params)
        facts = run["facts"]
        repro = reproduce_recorded(store, run["run_id"])["status"]
        ctx = {"customer_kyc": c["customer_profile"], "transactions": c["transactions"],
               "signal_tags": [], "alert_narrative": c["alert_narrative"]}

        text = _template(c, facts)
        rows.append({"case": c["id"], "condition": "C1_template", "draft": text,
                     **_measure(text, c, facts, skills), "latency_s": 0.0, "tokens": 0,
                     "accepted": None, "reproduced": repro})
        if not llm_available:
            continue

        start, t0 = len(skills.call_log), time.monotonic()
        try:
            text = skills._complete(
                f"{BASELINE_MARK}\nDraft the Ground of Suspicion (Part c) narrative for this "
                f"alert. Customer profile: {c['customer_profile']}. Alert: {c['alert_narrative']}. "
                f"Transactions: {json.dumps(c['transactions'])}", "disposition", max_tokens=4096)
            err = None
        except Exception as e:  # noqa: BLE001
            text, err = "", f"{type(e).__name__}: {str(e)[:120]}"
        rows.append({"case": c["id"], "condition": "C2_baseline_no_controls", "draft": text,
                     **_measure(text, c, facts, skills), "error": err,
                     "latency_s": round(time.monotonic() - t0, 2),
                     "tokens": _tokens(skills, start), "accepted": None, "reproduced": None})

        start, t0 = len(skills.call_log), time.monotonic()
        try:
            assessment = skills.suspicion_evaluator(ctx)
            gos = skills.ground_of_suspicion_writer(ctx, assessment, computed=run)
            text, accepted, err = gos["narrative"], bool(gos["hard_gate_passed"]), None
            status = gos.get("status")
        except Exception as e:  # noqa: BLE001
            text, accepted, err, status = "", False, f"{type(e).__name__}: {str(e)[:120]}", None
        rows.append({"case": c["id"], "condition": "C3_full_product", "draft": text,
                     **_measure(text, c, facts, skills), "error": err, "status": status,
                     "latency_s": round(time.monotonic() - t0, 2),
                     "tokens": _tokens(skills, start), "accepted": accepted, "reproduced": repro})
    return rows


def summarise(rows) -> dict:
    out = {}
    for cond in sorted({r["condition"] for r in rows}):
        rs = [r for r in rows if r["condition"] == cond]
        out[cond] = {
            "drafts": len(rs),
            "errors": sum(1 for r in rs if r.get("error")),
            "unsupported_figures_total": sum(r["unsupported"] + r["unparsed"] for r in rs),
            "drafts_with_unsupported": sum(1 for r in rs if r["unsupported"] + r["unparsed"]),
            "needs_review_total": sum(r["needs_review"] for r in rs),
            "figures_total": sum(r["figures"] for r in rs),
            "sentences_outside_coverage": sum(r["sentences_outside_coverage"] for r in rs),
            "accepted_by_gate": (sum(1 for r in rs if r["accepted"])
                                 if any(r["accepted"] is not None for r in rs) else None),
            "unsupported_in_accepted": sum(r["unsupported"] + r["unparsed"]
                                           for r in rs if r["accepted"]),
            "latency_s_total": round(sum(r["latency_s"] for r in rs), 2),
            "tokens_all_attempts": sum(r["tokens"] for r in rs),
            "reproduced": sum(1 for r in rs if r["reproduced"] == "reproduced"),
        }
    return out


def render(config, gate, summary) -> str:
    L = [f"# Holdout evaluation — {config['started_utc'][:16]} UTC ({config['mode'].upper()})", ""]
    if config["mode"] == "mock":
        L += ["> **MOCK RUN.** Part B model outputs are scripted. Do not quote Part B numbers.", ""]
    L += [f"- Dataset `{config['dataset']}` sha256 `{config['dataset_sha256'][:16]}…` "
          f"({config['cases']} synthetic cases; labels author-assigned, not expert ground truth)",
          f"- Code revision `{config['git_rev']}` · models `{json.dumps(config['models'])}`", "",
          "## A. Evidence gate on seeded faults (deterministic)", "",
          f"- Faults caught (blocked or flagged for review): **{gate['catch_rate_all'][0]} of "
          f"{gate['catch_rate_all'][1]}**",
          f"- Of faults the gate is designed to catch: **{gate['catch_rate_in_designed_coverage'][0]}"
          f" of {gate['catch_rate_in_designed_coverage'][1]}**",
          f"- Supported narratives wrongly rejected: **{gate['false_rejections'][0]} of "
          f"{gate['false_rejections'][1]}**", "",
          "| case | fault | expected | got | caught |", "|---|---|---|---|---|"]
    L += [f"| {f['case']} | {f['fault']} | {f['expected']} | {f['got']} | "
          f"{'✓' if f['caught'] else '✗'} |" for f in gate["faults"]]
    if gate["label_mismatches"]:
        L += ["", "**Results that differ from the label (findings, not tuned away):**", ""]
        L += [f"- {f['case']} {f['fault']}: “{f['text']}” → {f['got']} (labelled {f['expected']})"
              for f in gate["label_mismatches"]]
    L += ["", "Faults labelled `pass_but_outside_coverage` are false statements built from real "
          "figures (wrong party, invented context). The gate checks figures, not prose; these are "
          "listed so that limit is visible.", "",
          "## B. Three conditions (same cases, same inputs)", "",
          "| condition | drafts | errors | unsupported figures | drafts with any | needs review "
          "| accepted by gate | unsupported in accepted | tokens (all attempts) | seconds "
          "| calculator reproduced |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for cond, m in summary.items():
        L.append(f"| {cond} | {m['drafts']} | {m['errors']} | {m['unsupported_figures_total']} | "
                 f"{m['drafts_with_unsupported']} | {m['needs_review_total']} | "
                 f"{'—' if m['accepted_by_gate'] is None else m['accepted_by_gate']} | "
                 f"{m['unsupported_in_accepted']} | {m['tokens_all_attempts']} | "
                 f"{m['latency_s_total']} | {m['reproduced']} |")
    L += ["", "Not measured: officer review time and corrections (needs participants). Six "
          "author-labelled synthetic cases cannot support accuracy or impact claims.", ""]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--gate-only", action="store_true", help="Part A only; no model calls")
    ap.add_argument("--out", default=str(ROOT / "evals"))
    args = ap.parse_args(argv)
    settings = get_settings()
    live = not args.mock and not args.gate_only
    if live and not settings.llm_configured:
        print("NEBIUS_API_KEY not set. Use --mock or --gate-only.")
        return 2
    raw = HOLDOUT.read_bytes()
    data = json.loads(raw)
    store = open_store(":memory:")
    runner = ComputeRunner(store)
    llm = MockLLM() if args.mock else (TokenFactoryClient(settings) if live else None)
    skills = CoPilotSkills(store, llm=llm)
    started = datetime.now(timezone.utc)
    mode = "mock" if args.mock else ("live" if live else "gate-only")
    config = {"mode": mode, "started_utc": started.isoformat(), "dataset": HOLDOUT.name,
              "dataset_sha256": hashlib.sha256(raw).hexdigest(), "cases": len(data["cases"]),
              "git_rev": _git_rev(), "models": settings.models if live else {},
              "label_provenance": data["label_provenance"]}
    gate = gate_measurement(data["cases"], runner, store, skills)
    rows = conditions(data["cases"], runner, store, skills, llm_available=llm is not None)
    summary = summarise(rows)
    out = Path(args.out) / f"RUN-{started.strftime('%Y%m%dT%H%M%SZ')}-{mode}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "config.json").write_text(json.dumps(config, indent=1))
    (out / "outputs.jsonl").write_text("\n".join(json.dumps(r, default=str) for r in rows) + "\n")
    (out / "metrics.json").write_text(json.dumps({"gate": gate, "conditions": summary},
                                                 indent=1, default=str))
    (out / "REPORT.md").write_text(render(config, gate, summary))
    print(render(config, gate, summary))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
