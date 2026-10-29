"""
FIU-IND enforcement record (T12.2) and the inspector question bank (T12.3).

`domain/enforcement/` holds three YAML files: the Section 13 orders read in full, the failure
taxonomy coded from them with what Twin Trace does about each failure, and the questions an
inspection could put to a recorded decision. None of it is a regulatory rule. It is never indexed
for retrieval and never cited as one.
"""

from __future__ import annotations

import copy
import hashlib
from collections import Counter
from functools import lru_cache
from pathlib import Path

import yaml

ENFORCEMENT_DIR = Path(__file__).resolve().parent.parent / "domain" / "enforcement"
COVERAGE = ("ADDRESSED", "PARTIAL", "GAP")


@lru_cache(maxsize=32)
def _read(name: str, mtime_ns: int) -> tuple[dict, str]:
    raw = (ENFORCEMENT_DIR / name).read_bytes()
    return yaml.safe_load(raw), hashlib.sha256(raw).hexdigest()


def _load(name: str) -> tuple[dict, str]:
    """The file as stored now (re-read when it changes); a deep copy, so no caller can alter the
    cached data another caller will see."""
    data, digest = _read(name, (ENFORCEMENT_DIR / name).stat().st_mtime_ns)
    return copy.deepcopy(data), digest


def orders() -> list[dict]:
    return _load("fiu_orders.yaml")[0]["orders"]


def failures() -> dict[str, dict]:
    return _load("failures.yaml")[0]["failures"]


def question_bank() -> dict:
    """{"version", "sha256", "questions": [...]}; the hash is of the file as stored."""
    data, digest = _load("inspector_questions.yaml")
    return {"version": data["version"], "sha256": digest, "questions": data["questions"]}


def orders_citing(code: str) -> list[str]:
    """Order IDs with at least one finding coded `code`."""
    return [o["order_id"] for o in orders()
            if any(code in f["codes"] for f in o["findings"])]


def coverage_table() -> list[dict]:
    """One row per failure code: label, coverage, and the orders that cite it (a direct count
    over fiu_orders.yaml, D1; not a rate)."""
    counts = Counter(code for o in orders() for code in
                     {c for f in o["findings"] for c in f["codes"]})
    rows = []
    for code, spec in failures().items():
        rows.append({"code": code, "label": spec["label"], "coverage": spec["coverage"],
                     "orders": orders_citing(code), "order_count": counts.get(code, 0),
                     "controls": spec.get("controls", []), "gap": spec.get("gap", "")})
    return sorted(rows, key=lambda r: (-r["order_count"], r["code"]))


def order_scenarios() -> list[dict]:
    """Synthetic scenarios modelled on order fact patterns (replayed in tests, never seeded)."""
    return _load("order_scenarios.yaml")[0]["scenarios"]
