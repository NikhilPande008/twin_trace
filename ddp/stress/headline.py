"""
One plain-language sentence for a stress-test report (T9.6).

Built only from the report's own fields (flip sets, reopen triggers, branch verdicts), so it
cannot say anything the deterministic analysis did not find. The levels are this product's
modeled signal levels, not findings of suspicion.
"""

from __future__ import annotations


def _level_after(report: dict, flip_set: list[dict]) -> str:
    key = tuple(sorted(h["id"] for h in flip_set))
    for b in report["branches"]:
        if tuple(sorted(b["hypotheses"])) == key:
            return b["verdict"]
    return "lower"


def headline(report: dict) -> dict:
    """{"tone": "info" | "warning" | "success", "title": str, "detail": str}."""
    base = report["base"]["verdict"]
    k = report["search"]["max_set_size"]
    if report["mode"] == "weaken":                       # a proposed FILE
        sets = report["minimal_flip_sets"]
        if not sets:
            if base == "LOW":
                return {"tone": "warning",
                        "title": "The calculator's signals do not support this FILE by themselves.",
                        "detail": "The modeled level is LOW, so a FILE here rests on evidence the "
                                  "calculator does not see: narrative, KYC documents, PEP status, "
                                  "RFI answers. Say what that evidence is in the Ground of Suspicion."}
            return {"tone": "success",
                    "title": f"No tested combination of up to {k} assumptions changes this.",
                    "detail": "The FILE does not hinge on any one registry flag or transaction "
                              "among those tested."}
        size = min(len(f) for f in sets)
        smallest = [f for f in sets if len(f) == size]
        if size == 1:
            if len(smallest) == 1:
                f = smallest[0]
                return {"tone": "warning",
                        "title": "This FILE rests on exactly one fact.",
                        "detail": f"If this is wrong, the modeled level drops from {base} to "
                                  f"{_level_after(report, f)}: {f[0]['label']}. Document the basis "
                                  "for it in the Ground of Suspicion."}
            return {"tone": "warning",
                    "title": f"This FILE rests on any one of {len(smallest)} facts.",
                    "detail": "Each of these, if wrong, lowers the modeled level on its own: "
                              + "; ".join(f[0]["label"] for f in smallest[:3]) + "."}
        return {"tone": "info",
                "title": f"No single fact flips this FILE; it takes a combination of {size}.",
                "detail": f"{len(smallest)} such combination(s) found, for example: "
                          + " and ".join(h["label"] for h in smallest[0]) + "."}
    triggers = report["reopen_triggers"]                 # a proposed NOT_FILE
    if base == "HIGH":
        fired = [s["label"] for s in report["base"]["signals"] if s["fired"]]
        return {"tone": "warning",
                "title": "This closure goes against HIGH calculator signals.",
                "detail": "The closure note must explain each signal that fired: "
                          + "; ".join(fired) + "."}
    if not triggers:
        return {"tone": "success",
                "title": "No single registry hit would change this closure.",
                "detail": f"No hit on up to {k} existing counterparties raises the modeled level "
                          "to HIGH."}
    return {"tone": "info",
            "title": "This closure comes with reopen conditions.",
            "detail": "Reopen the alert if any of these happens: "
                      + "; ".join(" and ".join(t["if"]) for t in triggers[:3]) + ". Nothing "
                      "monitors these automatically."}
