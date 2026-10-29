"""
Adverse-media screening via Tavily Search API (T2.1).

Fetches public news / adverse-media items for a case subject and their flagged
counterparties. Each result is stored as an EVIDENCE row (type = adverse_media).

Privacy / anti-tipping-off rules (enforced here, not only by screen_request):
  - Query NEVER includes "STR", "suspicious transaction report", "report", "filing",
    or "suspicion" — PML Rules 2005 Rule 8(6) via corpus SB-003.
  - Snippets are truncated to SNIPPET_MAX_CHARS before storage; downstream prompts
    must fence them as untrusted data (injection protection).
  - This data is for the PO's situational awareness; it is NEVER sent to the customer.
  - All test / seed subjects are synthetic — no real customer names in this repo.

Outcome reporting: `fetch` keeps the EvidenceSourcePort contract (returns a list), and also
sets `last_status` so "screened, nothing found" is never confused with "screening failed".
Statuses: ok | no_results | no_key | refused | timeout | network_error | http_error | bad_response.

API shape: POST https://api.tavily.com/search with api_key in body. Live-verified by
scripts/probes/probe_tavily.py (see evals/ for the dated run).
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone

TAVILY_ENDPOINT = "https://api.tavily.com/search"
SNIPPET_MAX_CHARS = 300   # injection-protection ceiling for any downstream prompt

# Terms that must NEVER appear in the Tavily query (tipping-off prohibition, SB-003)
_PROHIBITED_QUERY_TERMS = frozenset({
    "str", "suspicious", "transaction report", "report", "filing", "suspicion",
    "fiu", "fiu-ind", "pmla", "money laundering report", "atr",
})


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# Statuses where the screen actually ran. Anything else means nothing was screened.
SCREEN_COMPLETED = frozenset({"ok", "no_results"})


def _status(status: str, query: str = "", detail: str = "", http_status: int | None = None,
            result_count: int = 0) -> dict:
    return {"status": status, "completed": status in SCREEN_COMPLETED, "query": query,
            "detail": detail[:200], "http_status": http_status,
            "result_count": result_count, "checked_at": _now_iso()}


def _post_search(post_fn, payload: dict, timeout_s: float) -> tuple[dict | None, dict]:
    """POST to Tavily. Returns (data, status); data is None when the call did not succeed."""
    query = payload.get("query", "")
    try:
        resp = post_fn(TAVILY_ENDPOINT, json=payload, timeout=timeout_s)
    except Exception as e:  # noqa: BLE001 — classify, never raise
        kind = "timeout" if "timeout" in type(e).__name__.lower() or "timed out" in str(e) \
            else "network_error"
        return None, _status(kind, query, f"{type(e).__name__}: {e}")
    code = getattr(resp, "status_code", None)
    if code != 200:
        return None, _status("http_error", query, f"HTTP {code}", http_status=code)
    try:
        data = resp.json()
    except Exception as e:  # noqa: BLE001
        return None, _status("bad_response", query, f"unparseable JSON: {e}", http_status=code)
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        return None, _status("bad_response", query, "no 'results' list", http_status=code)
    return data, _status("ok", query, http_status=code)


# Topic search, not entity screening (T6). The query is built from the alert TYPOLOGY only: no
# name, counterparty, account or narrative text from the case leaves the bank. Synthetic entity
# names are deliberately not used either: a made-up name searched on the public web can match a
# real person. Results are typology context for the officer, never findings about this customer.
TYPOLOGY_TOPICS = {
    "MULE_PASSTHROUGH":          "UPI money mule account pass-through fraud India",
    "STRUCTURING":               "cash deposit structuring below reporting threshold India bank",
    "DORMANT_REACTIVATION":      "dormant bank account reactivation misuse fraud India",
    "PEP_INCONSISTENCY":         "politically exposed person corporate credits misuse India",
    "CROSS_BORDER_FATF":         "cross-border remittance high-risk jurisdiction money laundering India",
    "NPO_MISUSE":                "NGO trust account cash misuse terror financing India",
    "LARGE_CASH_DEPOSIT":        "large cash deposit unexplained source India bank fraud",
    "LARGE_CREDIT":              "large unexplained bank credit fraud India",
    "DEVICE_IDENTITY_LINKAGE":   "same device multiple bank accounts mule network India",
    "BENEFICIARY_CONCENTRATION": "many accounts paying one beneficiary UPI fraud India",
    "INCOME_INCONSISTENCY":      "account activity inconsistent with declared income fraud India",
    "ATTEMPTED_SWIFT":           "attempted SWIFT transfer fraud blocked India bank",
    "MF_LAYERING":               "mutual fund redemption layering money laundering India",
    "NRI_KYC_MISMATCH":          "NRI account KYC mismatch remittance fraud India",
    "FIDUCIARY_DIVERSION":       "cooperative society officer fund diversion fraud India",
}
DEFAULT_TOPIC = "bank account fraud money laundering typology India"


def _build_query(subject: str, case_context: dict) -> str:
    """Topic query from the alert typology. `subject` is accepted for the EvidenceSourcePort
    signature but never used: case identifiers do not go into a public search."""
    query = TYPOLOGY_TOPICS.get(str(case_context.get("alert_type") or "").upper(), DEFAULT_TOPIC)
    for term in _PROHIBITED_QUERY_TERMS:          # defence in depth; topics contain none today
        query = re.sub(rf"\b{re.escape(term)}\b", "", query, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", query).strip()


class TavilyEvidenceSource:
    """
    Adverse-media screening using the Tavily Search API.

    Returns [] when api_key is not configured or the request fails — the pipeline
    degrades gracefully. Never raises for configuration or network errors. `last_status`
    says which of those happened (see module docstring).
    """
    name = "tavily"

    def __init__(self, api_key: str | None = None, max_results: int = 5,
                 timeout_s: float = 10.0, _post=None):
        self.api_key = api_key
        self.max_results = max_results
        self.timeout_s = timeout_s
        self._post = _post   # injectable for offline tests
        self.last_status: dict = _status("no_key") if not api_key else {}

    def fetch(self, subject: str, case_context: dict) -> list[dict]:
        """
        Search Tavily for adverse media about the case subject.

        Snippets are capped at SNIPPET_MAX_CHARS. The returned dicts have lowercase
        keys matching the EvidenceSourcePort contract; Store.append_evidence handles
        both lower- and upper-case keys.
        """
        if not self.api_key:
            self.last_status = _status("no_key")
            return []

        query = _build_query(subject, case_context)
        now = _now_iso()
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": self.max_results,
            "search_depth": "basic",
        }

        data, self.last_status = _post_search(self._post or _requests_post, payload,
                                              self.timeout_s)
        if data is None:
            return []

        items = []
        for hit in data["results"]:
            # Truncate + mark untrusted — downstream prompts must fence this block
            raw_snippet = (hit.get("content") or hit.get("snippet") or "")
            snippet = raw_snippet[:SNIPPET_MAX_CHARS]

            content = {
                "title":          hit.get("title", ""),
                "url":            hit.get("url", ""),
                "snippet":        snippet,
                "score":          hit.get("score", 0.0),
                "published_date": hit.get("published_date", ""),
                "query_used":     query,
                "search_kind":    "topic",
                "match_status":   "not_entity_matched",   # never evidence about this customer
                "[untrusted_external_content]": True,
            }
            content_json = json.dumps(content, sort_keys=True)
            provenance = {
                "provider":     "tavily",
                "search_kind":  "topic",
                "query":        query,
                "search_depth": "basic",
                "max_results":  self.max_results,
                "retrieved_at": now,
            }
            items.append({
                "evidence_id":    str(uuid.uuid4()),
                "type":           "adverse_media",
                "source":         f"tavily:{hit.get('url', '')}",
                "content_hash":   _sha256(content_json),
                "content_json":   content_json,
                "provenance_json": json.dumps(provenance),
                "created_at":     now,
            })
        self.last_status.update(status="ok" if items else "no_results", result_count=len(items))
        return items


# Primary regulator / government domains only. Results are POINTERS for a human to verify,
# never corpus rules: a regulatory answer still comes only from PROVEN/ASSUMED corpus entries.
REGULATOR_DOMAINS = ["rbi.org.in", "fiuindia.gov.in", "sebi.gov.in",
                     "enforcementdirectorate.gov.in", "pib.gov.in", "egazette.gov.in"]


def host_of(url: str) -> str:
    """The URL's host name, lower case, without port or user info ('' if none)."""
    from urllib.parse import urlparse
    try:
        return (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""


def on_domains(url: str, domains) -> bool:
    """True when the URL's host is one of `domains` or a subdomain of one."""
    host = host_of(url)
    return bool(host) and any(host == d or host.endswith("." + d) for d in domains)


def fetch_regulatory_updates(source: "TavilyEvidenceSource", question: str,
                             max_results: int = 5, case_terms: list[str] | None = None) -> list[dict]:
    """Search regulator sites only (Tavily include_domains). Returns [] without a key/on error.

    The question is about rules, not a person: it is refused (returns []) if it contains any
    case identifier in `case_terms` (alert id, customer ref, txn ids, counterparties), so no
    case data leaves the bank in a public search.
    Each item: {title, url, snippet, published_date, domain, status: 'UNVERIFIED-POINTER'}.
    The outcome is left on `source.last_status`, as for `fetch`.
    """
    q = (question or "").strip()[:300]
    if not source.api_key:
        source.last_status = _status("no_key")
        return []
    if not q:
        source.last_status = _status("refused", detail="empty question")
        return []
    if any(t and t.lower() in q.lower() for t in (case_terms or [])):
        source.last_status = _status("refused", detail="question contains a case identifier")
        return []
    payload = {"api_key": source.api_key, "query": q, "max_results": max_results,
               "search_depth": "basic", "include_domains": REGULATOR_DOMAINS}
    data, source.last_status = _post_search(source._post or _requests_post, payload,
                                            source.timeout_s)
    if data is None:
        return []
    out = []
    for hit in data.get("results") or []:
        url = hit.get("url", "")
        domain = host_of(url)
        if not on_domains(url, REGULATOR_DOMAINS):
            continue  # defence in depth: drop anything the domain filter let through
        out.append({"title": hit.get("title", ""), "url": url, "domain": domain,
                    "snippet": (hit.get("content") or "")[:SNIPPET_MAX_CHARS],
                    "published_date": hit.get("published_date", ""),
                    "query_used": q, "status": "UNVERIFIED-POINTER"})
    source.last_status.update(status="ok" if out else "no_results", result_count=len(out))
    return out


def _requests_post(url, json, timeout):  # pragma: no cover
    import requests
    return requests.post(url, json=json, timeout=timeout)
