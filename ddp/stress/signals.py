"""
Risk signals derived ONLY from calculator-of-record facts.

These are PRODUCT HEURISTICS chosen for this demo, not regulatory thresholds and not an
FIU-IND standard. They exist so the stress test has a deterministic, explainable yardstick:
"which evidence does this decision rest on?" is only answerable against a fixed rule set.
The decision itself stays with the Principal Officer.

Each signal reads facts by fact_id and records which fact values it used, so a verdict is
traceable to a compute run (and from there to code / input / output hashes).
"""

from __future__ import annotations

from dataclasses import dataclass, field

LEVELS = ["LOW", "ELEVATED", "HIGH"]

# Product heuristics (PROPOSED in DECISIONS.md). Values are integers in the units the
# calculator emits (basis points, days, tenths, counts).
HEURISTICS = {
    "flagged_share_bp": 2500,       # >= 25% of credits moved to/from a flagged counterparty
    "passthrough_bp": 8000,         # >= 80% of credits debited out ...
    "passthrough_window_days": 10,  # ... within <= 10 days
    "fan_in_min": 3,                # >= 3 distinct senders ...
    "fan_out_max": 1,               # ... converging on <= 1 recipient
    "income_multiple_x10": 60,      # credits >= 6x declared monthly income
}


@dataclass
class Signal:
    signal_id: str
    label: str
    strength: str                   # "strong" | "supporting"
    fired: bool
    facts_used: dict = field(default_factory=dict)
    explanation: str = ""

    def to_dict(self) -> dict:
        return {"signal_id": self.signal_id, "label": self.label, "strength": self.strength,
                "fired": self.fired, "facts_used": self.facts_used,
                "explanation": self.explanation}


def _facts_by_id(facts: list[dict]) -> dict[str, int]:
    return {f["fact_id"]: f["value"] for f in facts}


def evaluate_signals(facts: list[dict], h: dict | None = None) -> list[Signal]:
    h = h or HEURISTICS
    v = _facts_by_id(facts)
    out: list[Signal] = []

    out_bp, in_bp = v.get("F-FLAGGED-SHARE-BP", 0), v.get("F-FLAGGED-INFLOW-SHARE-BP", 0)
    fired = max(out_bp, in_bp) >= h["flagged_share_bp"]
    out.append(Signal(
        "S-FLAGGED-COUNTERPARTY", "Material flow with a flagged counterparty", "strong", fired,
        {"F-FLAGGED-SHARE-BP": out_bp, "F-FLAGGED-INFLOW-SHARE-BP": in_bp},
        f"max(flagged outflow, flagged inflow) share >= {h['flagged_share_bp']} bp"))

    ctr_months = sorted(
        k[len("F-CASH-"):-len("-ABOVE-THRESHOLD")] for k, val in v.items()
        if k.startswith("F-CASH-") and k.endswith("-ABOVE-THRESHOLD") and val == 1
        and v.get(k.replace("-ABOVE-THRESHOLD", "-ALL-BELOW")) == 1)
    out.append(Signal(
        "S-CASH-STRUCTURING", "Monthly cash above threshold, every deposit below it", "strong",
        bool(ctr_months), {"months": ctr_months},
        "F-CASH-<month>-ABOVE-THRESHOLD == 1 and F-CASH-<month>-ALL-BELOW == 1"))

    pt, win = v.get("F-PASSTHROUGH-BP", 0), v.get("F-WINDOW-DAYS", 0)
    out.append(Signal(
        "S-PASSTHROUGH", "Rapid pass-through of credits", "supporting",
        pt >= h["passthrough_bp"] and 0 < win <= h["passthrough_window_days"],
        {"F-PASSTHROUGH-BP": pt, "F-WINDOW-DAYS": win},
        f"passthrough >= {h['passthrough_bp']} bp within <= {h['passthrough_window_days']} days"))

    fi, fo = v.get("F-FAN-IN", 0), v.get("F-FAN-OUT", 0)
    out.append(Signal(
        "S-FAN-IN", "Many senders converging on few recipients", "supporting",
        fi >= h["fan_in_min"] and 1 <= fo <= h["fan_out_max"],
        {"F-FAN-IN": fi, "F-FAN-OUT": fo},
        f"fan-in >= {h['fan_in_min']} and 1 <= fan-out <= {h['fan_out_max']}"))

    im = v.get("F-INCOME-MULTIPLE-X10")
    out.append(Signal(
        "S-INCOME-MISMATCH", "Credits far above declared income", "supporting",
        im is not None and im >= h["income_multiple_x10"],
        {"F-INCOME-MULTIPLE-X10": im},
        f"credits >= {h['income_multiple_x10'] / 10:g}x declared monthly income"
        if im is not None else "declared income not parseable from profile: signal not evaluated"))
    return out


def verdict(signals: list[Signal]) -> str:
    """HIGH: a strong signal corroborated by any other. ELEVATED: one strong, or two
    supporting. LOW otherwise."""
    strong = sum(1 for s in signals if s.fired and s.strength == "strong")
    supporting = sum(1 for s in signals if s.fired and s.strength == "supporting")
    if strong >= 1 and strong + supporting >= 2:
        return "HIGH"
    if strong >= 1 or supporting >= 2:
        return "ELEVATED"
    return "LOW"


def level(v: str) -> int:
    return LEVELS.index(v)
