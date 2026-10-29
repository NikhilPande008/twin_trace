"""
Wiring: build a seeded Store, the LLM client, skills and the compute runner.

Kept separate from the UI so tests, scripts and the app share one construction path.
"""

from __future__ import annotations

import contextlib
import re
import io
from pathlib import Path

from .compute import ComputeRunner, backend_from_name
from .config import Settings, get_settings
from .corpus_loader import load_yaml_files
from .evidence import TavilyEvidenceSource
from .gate import DeterministicPolicyGate
from .llm import CallBudget, TokenFactoryClient
from .pipeline import DispositionPipeline
from .seed_data import ALERTS, TRANSACTIONS
from .skills import CoPilotSkills
from .store import Store

# Regulatory parameters handed to the calculator of record. Each carries the corpus
# rule it comes from; compute_params() refuses to use a parameter whose rule is
# missing or NEEDS-VERIFICATION.
PARAM_SOURCES = {
    "cash_threshold": {"amount_inr": 1_000_000, "rule_id": "CTR-001"},
}


def seed(store: Store) -> dict:
    with contextlib.redirect_stdout(io.StringIO()):  # loader prints per-file counts
        corpus = load_yaml_files()
    return {
        "corpus": store.upsert_corpus(corpus),
        "alerts": store.upsert_alerts(ALERTS),
        "transactions": store.upsert_transactions(TRANSACTIONS),
    }


def open_store(path: str | Path | None = None, *, seed_if_empty: bool = True) -> Store:
    store = Store(path if path is not None else get_settings().db_path)
    if seed_if_empty and not store.query("SELECT 1 FROM ALERTS LIMIT 1"):
        seed(store)
    return store


_INCOME_RE = re.compile(
    r"Rs\.?\s*(\d+(?:\.\d+)?)\s*(K|L|Cr)\s*/\s*month", re.IGNORECASE)
_UNIT = {"k": 1_000, "l": 100_000, "cr": 10_000_000}


def parse_declared_monthly_income(profile: str | None) -> int | None:
    """Parse 'Rs.28K/month' style KYC text into rupees. Ranges ('Rs.8-15K') return None:
    a range is not one declared figure, and guessing one would be an invented number."""
    m = _INCOME_RE.search(profile or "")
    if not m:
        return None
    start = m.start(1)
    if start > 0 and (profile[start - 1] == "-"):
        return None
    return int(round(float(m.group(1)) * _UNIT[m.group(2).lower()]))


_ANNUAL_INCOME_RE = re.compile(
    r"(?:Rs\.?|₹)\s*(\d+(?:\.\d+)?)\s*(K|L|Cr)\s*/\s*(?:year|yr|annum)"
    r"|annual\s+income\s+(?:of\s+)?(?:Rs\.?|₹)\s*(\d+(?:\.\d+)?)\s*(K|L|Cr)\b",
    re.IGNORECASE)


def parse_declared_annual_income(profile: str | None) -> int | None:
    """Parse 'Rs.4.5L/year' or 'annual income ₹3.6L' into rupees. Turnover is not income and is
    not matched; ranges return None, as for monthly income."""
    m = _ANNUAL_INCOME_RE.search(profile or "")
    if not m:
        return None
    num, unit = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
    start = m.start(1) if m.group(1) else m.start(3)
    if start > 0 and profile[start - 1] == "-":
        return None
    return int(round(float(num) * _UNIT[unit.lower()]))


def compute_params(store: Store, alert_id: str | None = None) -> dict:
    """Parameters for the calculator of record.

    Regulatory thresholds come from PARAM_SOURCES and are used only when their corpus rule is
    PROVEN/ASSUMED. With an alert_id, the customer's declared monthly income (parsed from the
    KYC profile text) is added so the program can compute F-INCOME-MULTIPLE-X10.
    """
    params, usable = {}, {"PROVEN", "ASSUMED"}
    for key, spec in PARAM_SOURCES.items():
        rows = store.query("SELECT EVIDENCE_LEVEL FROM REGULATORY_CORPUS WHERE RULE_ID = ?",
                           (spec["rule_id"],))
        if rows and rows[0]["EVIDENCE_LEVEL"] in usable:
            params[key] = dict(spec, evidence_level=rows[0]["EVIDENCE_LEVEL"])
    if alert_id:
        alert = store.get_alert(alert_id) or {}
        income = parse_declared_monthly_income(alert.get("CUSTOMER_PROFILE"))
        if income:
            params["declared_monthly_income_inr"] = {
                "amount_inr": income, "source": f"CUSTOMER_PROFILE:{alert_id}"}
        annual = parse_declared_annual_income(alert.get("CUSTOMER_PROFILE"))
        if annual:
            params["declared_annual_income_inr"] = {
                "amount_inr": annual, "source": f"CUSTOMER_PROFILE:{alert_id}"}
    return params


def build(settings: Settings | None = None, store: Store | None = None):
    """Return (store, skills, runner, pipeline) for the configured environment.

    Callers that indexed into the old 3-tuple still work — the new pipeline is
    appended at index 3 and is accessed by the UI and the eval harness.
    """
    settings = settings or get_settings()
    store = store or open_store(settings.db_path)
    llm = TokenFactoryClient(settings) if settings.llm_configured else None
    if llm is not None and settings.demo_mode:
        llm = CallBudget(llm, settings.demo_max_model_calls)
    embedder = None
    if llm is not None and settings.retrieval_mode == "hybrid":
        from .embeddings import TokenFactoryEmbedder
        embedder = TokenFactoryEmbedder(settings, settings.embedding_model)
    skills = CoPilotSkills(store, llm=llm, embedder=embedder)
    runner = ComputeRunner(store, backend_from_name(settings.compute_backend,
                                                    api_key=settings.api_key,
                                                    project_id=settings.nebius_project_id))
    evidence_source = TavilyEvidenceSource(settings.tavily_api_key)
    policy_gate = DeterministicPolicyGate()
    pipeline = DispositionPipeline(
        skills, runner,
        evidence_source=evidence_source,
        policy_gate=policy_gate,
        store=store,
    )
    return store, skills, runner, pipeline


def build_investigator(store: Store, skills, runner, settings: Settings | None = None):
    """Agentic investigator (ddp.agent) wired to the same store/runner. None without a key."""
    from .agent import Investigator
    settings = settings or get_settings()
    llm = getattr(skills, "_llm", None)
    if llm is None or not hasattr(llm, "chat"):
        return None
    return Investigator(llm, store, skills, runner, lambda a: compute_params(store, a),
                        evidence_source=TavilyEvidenceSource(settings.tavily_api_key))


def build_stress_tester(store: Store, skills, runner):
    from .stress import StressTester
    return StressTester(runner, store, skills)


def build_panel(store: Store, settings: Settings | None = None, session_llm=None):
    """Tier panel (T12.7): one fresh Token Factory client per tier so the calls can run in
    parallel. In public demo mode the panel must spend the SESSION's call budget (`session_llm`,
    the budgeted client the session's skills use), so the tiers run one after another on it; a
    new budget per call would let a visitor bypass the cap. None without a key, or in demo mode
    without the session's client."""
    from .panel import TierPanel
    settings = settings or get_settings()
    if not settings.llm_configured:
        return None
    if settings.demo_mode:
        if not isinstance(session_llm, CallBudget):
            return None
        return TierPanel(lambda: CoPilotSkills(store, llm=session_llm), parallel=False)
    return TierPanel(lambda: CoPilotSkills(store, llm=TokenFactoryClient(settings)))
