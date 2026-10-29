"""
Store — SQLite persistence for corpus, alerts, transactions, the decision ledger
and the compute-run log.

Column names are kept UPPER_CASE so row dicts have the same shape the UI expects.

Two integrity properties are enforced by the DATABASE, not just the application:

1. DECISION_LEDGER and COMPUTE_RUNS are append-only. BEFORE UPDATE / BEFORE DELETE
   triggers abort the statement. (Baseline edition: application-layer convention only.)
2. DECISION_LEDGER rows are hash-chained: ROW_HASH = sha256(canonical row + PREV_HASH).
   `verify_ledger_chain()` recomputes the chain and reports the first broken link.
   (Baseline edition: per-row hash, no chain — a deleted row was undetectable.)

Neither property makes the file tamper-PROOF (anyone with the file can rebuild it);
they make tampering DETECTABLE and ordinary code paths unable to rewrite history.
Claims in docs must stay at that level.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

GENESIS_HASH = "0" * 64
# Evidence types added after the first schema; an older DB is widened by _migrate().
EVIDENCE_TYPES_ADDED = ("adverse_media_screen", "tier_panel", "inspection", "regulator_page")

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS REGULATORY_CORPUS (
    RULE_ID              TEXT PRIMARY KEY,
    CATEGORY             TEXT,
    SUBCATEGORY          TEXT,
    RULE_TEXT            TEXT NOT NULL,
    APPLIES_TO           TEXT,          -- JSON array
    SOURCE_DOCUMENT      TEXT,
    SOURCE_URL           TEXT,
    SOURCE_URL_VERIFIED  INTEGER,
    SOURCE_SECTION       TEXT,
    SOURCE_ACCESSED_DATE TEXT,
    EFFECTIVE_DATE       TEXT,
    SNAPSHOT_DATE        TEXT,
    LAST_VERIFIED        TEXT,
    EVIDENCE_LEVEL       TEXT NOT NULL CHECK (EVIDENCE_LEVEL IN ('PROVEN','ASSUMED','NEEDS-VERIFICATION')),
    MY_SYNTHESIS         TEXT,
    GAP_NOTES            TEXT,
    RELATED_RULES        TEXT           -- JSON array
);

CREATE TABLE IF NOT EXISTS ALERTS (
    ALERT_ID          TEXT PRIMARY KEY,
    SCENARIO_ID       TEXT NOT NULL,
    CUSTOMER_REF      TEXT NOT NULL,
    ALERT_DATE        TEXT NOT NULL,
    ALERT_TYPE        TEXT NOT NULL,
    SIGNAL_SOURCE     TEXT,
    ACCOUNT_TYPE      TEXT,
    CUSTOMER_PROFILE  TEXT,
    ALERT_AMOUNT_INR  REAL,
    ALERT_NARRATIVE   TEXT,
    RFI_TRIGGERS      TEXT,             -- JSON array
    POE_FACTORS       TEXT,             -- JSON array
    RULES_CITED       TEXT,             -- JSON array
    GOLD_DISPOSITION  TEXT NOT NULL,
    ALERT_STATUS      TEXT DEFAULT 'OPEN',
    ASSIGNED_PO       TEXT
);

CREATE TABLE IF NOT EXISTS TRANSACTIONS (
    TXN_ID        TEXT PRIMARY KEY,
    ALERT_ID      TEXT NOT NULL REFERENCES ALERTS(ALERT_ID),
    CUSTOMER_REF  TEXT NOT NULL,
    TXN_DATE      TEXT NOT NULL,
    TXN_TYPE      TEXT NOT NULL CHECK (TXN_TYPE IN ('CREDIT','DEBIT')),
    AMOUNT_INR    REAL NOT NULL,
    CHANNEL       TEXT,
    COUNTERPARTY  TEXT,
    IS_FLAGGED    INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS DECISION_LEDGER (
    SEQ                  INTEGER PRIMARY KEY AUTOINCREMENT,
    DECISION_ID          TEXT NOT NULL UNIQUE,
    ALERT_ID             TEXT NOT NULL,
    CUSTOMER_REF         TEXT NOT NULL,
    DISPOSITION          TEXT NOT NULL CHECK (DISPOSITION IN ('FILE','NOT_FILE','ESCALATE','DEFERRED')),
    DECISION_MAKER_ID    TEXT NOT NULL,
    SUSPICION_FORMED_AT  TEXT,
    DECISION_MADE_AT     TEXT NOT NULL,
    SLA_DAYS_REMAINING   INTEGER,
    RATIONALE_TEXT       TEXT NOT NULL,
    RULES_CITED          TEXT,          -- JSON array
    POE_FACTORS_ASSESSED TEXT,          -- JSON object
    RFI_TRIGGERS         TEXT,          -- JSON array
    STR_REFERENCE        TEXT,
    METADATA_JSON        TEXT,          -- JSON object (provenance)
    PREV_HASH            TEXT NOT NULL,
    ROW_HASH             TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS COMPUTE_RUNS (
    RUN_ID          TEXT PRIMARY KEY,
    ALERT_ID        TEXT,
    PROGRAM         TEXT NOT NULL,      -- e.g. 'aggregations.v1'
    BACKEND         TEXT NOT NULL,      -- 'local' | 'nebius-sandbox'
    BACKEND_RUN_REF TEXT,               -- sandbox run / instance id when remote
    CODE_SHA256     TEXT NOT NULL,
    INPUT_SHA256    TEXT NOT NULL,
    OUTPUT_SHA256   TEXT NOT NULL,
    OUTPUT_JSON     TEXT NOT NULL,
    STARTED_AT      TEXT NOT NULL,
    FINISHED_AT     TEXT NOT NULL,
    PARENT_RUN_ID   TEXT,               -- stress-test branch: the base run it was derived from
    HYPOTHESIS_JSON TEXT,               -- stress-test branch: the counter-hypotheses applied
    INPUT_JSON      TEXT                -- canonical input exactly as executed (NULL before T3)
);

-- Every calculator program version ever executed, by code hash, so an old run can be
-- re-executed with the program it was recorded with (T3). Append-only.
CREATE TABLE IF NOT EXISTS PROGRAMS (
    CODE_SHA256   TEXT PRIMARY KEY,
    PROGRAM       TEXT NOT NULL,
    SOURCE        TEXT NOT NULL,
    FIRST_SEEN_AT TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS PROGRAMS_NO_UPDATE BEFORE UPDATE ON PROGRAMS
BEGIN SELECT RAISE(ABORT, 'PROGRAMS is append-only: UPDATE rejected'); END;
CREATE TRIGGER IF NOT EXISTS PROGRAMS_NO_DELETE BEFORE DELETE ON PROGRAMS
BEGIN SELECT RAISE(ABORT, 'PROGRAMS is append-only: DELETE rejected'); END;

CREATE TRIGGER IF NOT EXISTS LEDGER_NO_UPDATE BEFORE UPDATE ON DECISION_LEDGER
BEGIN SELECT RAISE(ABORT, 'DECISION_LEDGER is append-only: UPDATE rejected'); END;
CREATE TRIGGER IF NOT EXISTS LEDGER_NO_DELETE BEFORE DELETE ON DECISION_LEDGER
BEGIN SELECT RAISE(ABORT, 'DECISION_LEDGER is append-only: DELETE rejected'); END;
-- One ledger row per reviewed draft + action: a repeated click or retry cannot duplicate it.
-- The key lives in the hashed METADATA_JSON; rows without one (older) are unconstrained.
CREATE UNIQUE INDEX IF NOT EXISTS LEDGER_IDEMPOTENCY
    ON DECISION_LEDGER (json_extract(METADATA_JSON, '$.idempotency_key'));
CREATE TRIGGER IF NOT EXISTS RUNS_NO_UPDATE BEFORE UPDATE ON COMPUTE_RUNS
BEGIN SELECT RAISE(ABORT, 'COMPUTE_RUNS is append-only: UPDATE rejected'); END;
CREATE TRIGGER IF NOT EXISTS RUNS_NO_DELETE BEFORE DELETE ON COMPUTE_RUNS
BEGIN SELECT RAISE(ABORT, 'COMPUTE_RUNS is append-only: DELETE rejected'); END;

-- Unified evidence table: every fact the product may rely on (see ARCHITECTURE.md §3.1).
-- Added Phase 1 (additive; no rows written until T2.1 Tavily and T3.1 policy gate).
CREATE TABLE IF NOT EXISTS EVIDENCE (
    EVIDENCE_ID     TEXT PRIMARY KEY,
    ALERT_ID        TEXT,
    TYPE            TEXT NOT NULL CHECK (TYPE IN (
                        'transaction', 'computed_fact', 'adverse_media',
                        'corpus_rule', 'policy_verdict', 'stress_test', 'agent_step',
                        'adverse_media_screen', 'tier_panel', 'inspection', 'regulator_page')),
    SOURCE          TEXT NOT NULL,      -- e.g. 'aggregations.v1:RUN-abc', 'tavily.search:2026-10-05'
    CONTENT_HASH    TEXT NOT NULL,      -- sha256 of CONTENT_JSON
    CONTENT_JSON    TEXT NOT NULL,      -- the fact value (amount, snippet, rule text, verdict)
    PROVENANCE_JSON TEXT,               -- run ID, query, URL, model call — depends on type
    CREATED_AT      TEXT NOT NULL
);

-- Week 7 watch layer (T12.4): what happened to a recorded decision AFTER it was recorded.
-- One row per (decision, cause). Append-only and hash-chained like the ledger; a reopen never
-- edits the decision row, it adds an event that points at it.
CREATE TABLE IF NOT EXISTS DECISION_EVENTS (
    SEQ             INTEGER PRIMARY KEY AUTOINCREMENT,
    EVENT_ID        TEXT NOT NULL UNIQUE,
    DECISION_ID     TEXT NOT NULL,
    ALERT_ID        TEXT NOT NULL,
    CAUSE           TEXT NOT NULL CHECK (CAUSE IN (
                        'registry_update', 'new_transaction', 'rule_change', 'watch_pass')),
    CAUSE_JSON      TEXT NOT NULL,
    CAUSE_SHA256    TEXT NOT NULL,
    BASE_RUN_ID     TEXT,               -- the calculator run the decision cited
    RERUN_ID        TEXT,               -- the re-run on the changed inputs (PARENT_RUN_ID = base)
    OUTCOME         TEXT NOT NULL CHECK (OUTCOME IN ('holds', 'reopened', 'needs_review')),
    OUTCOME_JSON    TEXT NOT NULL,
    OUTCOME_SHA256  TEXT NOT NULL,      -- over the deterministic content only (no IDs, no times)
    CREATED_AT      TEXT NOT NULL,
    PREV_HASH       TEXT NOT NULL,
    ROW_HASH        TEXT NOT NULL,
    UNIQUE (DECISION_ID, CAUSE_SHA256)
);
-- Rule-change lookback (T12.12). A proposal is a clause a model said is the rule's current text
-- at its source, kept only if it appears verbatim in the fetched page. PENDING proposals are never
-- indexed for retrieval; a promotion is the officer's recorded acceptance. Both append-only.
CREATE TABLE IF NOT EXISTS RULE_PROPOSALS (
    PROPOSAL_ID     TEXT PRIMARY KEY,
    RULE_ID         TEXT NOT NULL,
    SOURCE_URL      TEXT NOT NULL,
    PAGE_SHA256     TEXT NOT NULL,
    PAGE_EVIDENCE_ID TEXT,
    QUOTE           TEXT,
    QUOTE_VERIFIED  INTEGER NOT NULL,
    CHANGED         INTEGER,
    SUMMARY         TEXT,
    MODEL_CALL_JSON TEXT,
    STATUS          TEXT NOT NULL CHECK (STATUS IN ('PENDING', 'REJECTED_UNVERIFIED')),
    CREATED_AT      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS RULE_PROMOTIONS (
    PROPOSAL_ID     TEXT NOT NULL,
    OFFICER_ID      TEXT NOT NULL,
    OFFICER_BASIS   TEXT,
    ACTION          TEXT NOT NULL CHECK (ACTION IN ('promoted', 'dismissed')),
    CREATED_AT      TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS PROPOSALS_NO_UPDATE BEFORE UPDATE ON RULE_PROPOSALS
BEGIN SELECT RAISE(ABORT, 'RULE_PROPOSALS is append-only: UPDATE rejected'); END;
CREATE TRIGGER IF NOT EXISTS PROPOSALS_NO_DELETE BEFORE DELETE ON RULE_PROPOSALS
BEGIN SELECT RAISE(ABORT, 'RULE_PROPOSALS is append-only: DELETE rejected'); END;
CREATE TRIGGER IF NOT EXISTS PROMOTIONS_NO_UPDATE BEFORE UPDATE ON RULE_PROMOTIONS
BEGIN SELECT RAISE(ABORT, 'RULE_PROMOTIONS is append-only: UPDATE rejected'); END;
CREATE TRIGGER IF NOT EXISTS PROMOTIONS_NO_DELETE BEFORE DELETE ON RULE_PROMOTIONS
BEGIN SELECT RAISE(ABORT, 'RULE_PROMOTIONS is append-only: DELETE rejected'); END;
CREATE TRIGGER IF NOT EXISTS EVENTS_NO_UPDATE BEFORE UPDATE ON DECISION_EVENTS
BEGIN SELECT RAISE(ABORT, 'DECISION_EVENTS is append-only: UPDATE rejected'); END;
CREATE TRIGGER IF NOT EXISTS EVENTS_NO_DELETE BEFORE DELETE ON DECISION_EVENTS
BEGIN SELECT RAISE(ABORT, 'DECISION_EVENTS is append-only: DELETE rejected'); END;
"""

# Fields that enter the ledger hash, in canonical form. Order-independent (sorted JSON).
LEDGER_HASHED_FIELDS = (
    "DECISION_ID", "ALERT_ID", "CUSTOMER_REF", "DISPOSITION", "DECISION_MAKER_ID",
    "SUSPICION_FORMED_AT", "DECISION_MADE_AT", "SLA_DAYS_REMAINING", "RATIONALE_TEXT",
    "RULES_CITED", "POE_FACTORS_ASSESSED", "RFI_TRIGGERS", "STR_REFERENCE", "METADATA_JSON",
)


def ledger_row_hash(fields: dict, prev_hash: str) -> str:
    """sha256 over the canonical hashed fields plus the previous row's hash."""
    canonical = {k: fields.get(k) for k in LEDGER_HASHED_FIELDS}
    payload = json.dumps(canonical, sort_keys=True, default=str) + "|" + prev_hash
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


EVENT_HASHED_FIELDS = (
    "EVENT_ID", "DECISION_ID", "ALERT_ID", "CAUSE", "CAUSE_JSON", "CAUSE_SHA256", "BASE_RUN_ID",
    "RERUN_ID", "OUTCOME", "OUTCOME_JSON", "OUTCOME_SHA256", "CREATED_AT",
)


def event_row_hash(fields: dict, prev_hash: str) -> str:
    canonical = {k: fields.get(k) for k in EVENT_HASHED_FIELDS}
    payload = json.dumps(canonical, sort_keys=True, default=str) + "|" + prev_hash
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    return {d[0]: row[i] for i, d in enumerate(cursor.description)}


class Store:
    """Thin, explicit data-access layer. No ORM; every query is visible here."""

    def __init__(self, path: str | Path = ":memory:"):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = _dict_factory
        self._lock = threading.Lock()
        self._conn.executescript(SCHEMA_SQL)
        self._migrate()

    def _migrate(self) -> None:
        """Additive migrations for DB files created by earlier versions. No data is altered."""
        with self._lock:
            cols = {r["name"] for r in self._conn.execute("PRAGMA table_info(COMPUTE_RUNS)")}
            for col in ("PARENT_RUN_ID", "HYPOTHESIS_JSON", "INPUT_JSON"):
                if col not in cols:
                    self._conn.execute(f"ALTER TABLE COMPUTE_RUNS ADD COLUMN {col} TEXT")
            ddl = self._conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='EVIDENCE'").fetchone()
            if ddl and any(ty not in (ddl["sql"] or "") for ty in EVIDENCE_TYPES_ADDED):
                # SQLite cannot alter a CHECK constraint: copy rows into the widened table.
                self._conn.executescript("""
                    ALTER TABLE EVIDENCE RENAME TO EVIDENCE_OLD;
                """ + SCHEMA_SQL[SCHEMA_SQL.index("CREATE TABLE IF NOT EXISTS EVIDENCE"):] + """
                    INSERT INTO EVIDENCE SELECT * FROM EVIDENCE_OLD;
                    DROP TABLE EVIDENCE_OLD;
                """)
            self._conn.commit()

    # ── low level ────────────────────────────────────────────────────────────
    def query(self, sql: str, params: Iterable[Any] = ()) -> list[dict]:
        with self._lock:
            return self._conn.execute(sql, tuple(params)).fetchall()

    def _exec(self, sql: str, params: Iterable[Any] = ()) -> None:
        with self._lock:
            self._conn.execute(sql, tuple(params))
            self._conn.commit()

    def _execmany(self, sql: str, rows: list[tuple]) -> None:
        with self._lock:
            self._conn.executemany(sql, rows)
            self._conn.commit()

    # ── seeding (idempotent upserts) ─────────────────────────────────────────
    def upsert_corpus(self, rows: list[dict]) -> int:
        cols = ["RULE_ID", "CATEGORY", "SUBCATEGORY", "RULE_TEXT", "APPLIES_TO", "SOURCE_DOCUMENT",
                "SOURCE_URL", "SOURCE_URL_VERIFIED", "SOURCE_SECTION", "SOURCE_ACCESSED_DATE",
                "EFFECTIVE_DATE", "SNAPSHOT_DATE", "LAST_VERIFIED", "EVIDENCE_LEVEL",
                "MY_SYNTHESIS", "GAP_NOTES", "RELATED_RULES"]
        sql = (f"INSERT OR REPLACE INTO REGULATORY_CORPUS ({', '.join(cols)}) "
               f"VALUES ({', '.join('?' for _ in cols)})")
        self._execmany(sql, [tuple(_scalar(r.get(c)) for c in cols) for r in rows])
        return len(rows)

    def upsert_alerts(self, alerts: list[dict]) -> int:
        cols = ["ALERT_ID", "SCENARIO_ID", "CUSTOMER_REF", "ALERT_DATE", "ALERT_TYPE",
                "SIGNAL_SOURCE", "ACCOUNT_TYPE", "CUSTOMER_PROFILE", "ALERT_AMOUNT_INR",
                "ALERT_NARRATIVE", "RFI_TRIGGERS", "POE_FACTORS", "RULES_CITED",
                "GOLD_DISPOSITION", "ALERT_STATUS"]
        sql = (f"INSERT OR REPLACE INTO ALERTS ({', '.join(cols)}) "
               f"VALUES ({', '.join('?' for _ in cols)})")
        self._execmany(sql, [tuple(_scalar(a.get(c)) for c in cols) for a in alerts])
        return len(alerts)

    def upsert_transactions(self, txns: list[dict]) -> int:
        cols = ["TXN_ID", "ALERT_ID", "CUSTOMER_REF", "TXN_DATE", "TXN_TYPE", "AMOUNT_INR",
                "CHANNEL", "COUNTERPARTY", "IS_FLAGGED"]
        sql = (f"INSERT OR REPLACE INTO TRANSACTIONS ({', '.join(cols)}) "
               f"VALUES ({', '.join('?' for _ in cols)})")
        self._execmany(sql, [tuple(_scalar(t.get(c)) for c in cols) for t in txns])
        return len(txns)

    # ── corpus ───────────────────────────────────────────────────────────────
    def corpus_rows(self, evidence_levels: tuple[str, ...] = ("PROVEN", "ASSUMED")) -> list[dict]:
        marks = ", ".join("?" for _ in evidence_levels)
        return self.query(
            f"SELECT * FROM REGULATORY_CORPUS WHERE EVIDENCE_LEVEL IN ({marks}) ORDER BY RULE_ID",
            evidence_levels,
        )

    def corpus_by_ids(self, rule_ids: list[str]) -> list[dict]:
        if not rule_ids:
            return []
        marks = ", ".join("?" for _ in rule_ids)
        return self.query(
            f"SELECT RULE_ID, SUBCATEGORY, substr(RULE_TEXT, 1, 100) AS RULE_PREVIEW, EVIDENCE_LEVEL "
            f"FROM REGULATORY_CORPUS WHERE RULE_ID IN ({marks}) ORDER BY RULE_ID",
            rule_ids,
        )

    # ── alerts ───────────────────────────────────────────────────────────────
    def alerts_with_last_disposition(self) -> list[dict]:
        rows = self.query("""
            SELECT a.ALERT_ID, a.ALERT_TYPE, a.SIGNAL_SOURCE, a.ACCOUNT_TYPE,
                   a.CUSTOMER_PROFILE, a.ALERT_AMOUNT_INR, a.ALERT_STATUS, a.ALERT_DATE,
                   a.RFI_TRIGGERS,
                   (SELECT d.DISPOSITION FROM DECISION_LEDGER d
                     WHERE d.ALERT_ID = a.ALERT_ID ORDER BY d.SEQ DESC LIMIT 1) AS LAST_DISPOSITION
            FROM ALERTS a
        """)
        for r in rows:
            r["RFIS"] = ", ".join(_json_list(r.pop("RFI_TRIGGERS")))
        return rows

    def alert_ids(self) -> list[dict]:
        return self.query("SELECT ALERT_ID, ALERT_TYPE FROM ALERTS ORDER BY ALERT_ID")

    def get_alert(self, alert_id: str) -> dict | None:
        rows = self.query("SELECT * FROM ALERTS WHERE ALERT_ID = ?", (alert_id,))
        return rows[0] if rows else None

    def set_alert_status(self, alert_id: str, status: str) -> None:
        self._exec("UPDATE ALERTS SET ALERT_STATUS = ? WHERE ALERT_ID = ?", (status, alert_id))

    def transactions_for(self, alert_id: str) -> list[dict]:
        """Transactions in the dict shape the skills expect."""
        rows = self.query(
            "SELECT * FROM TRANSACTIONS WHERE ALERT_ID = ? ORDER BY TXN_DATE, TXN_ID", (alert_id,)
        )
        return [
            {
                "txn_id": r["TXN_ID"],
                "date": r["TXN_DATE"],
                "type": r["TXN_TYPE"],
                "amount_inr": float(r["AMOUNT_INR"] or 0),
                "channel": r["CHANNEL"],
                "counterparty": r["COUNTERPARTY"],
                "is_flagged": bool(r["IS_FLAGGED"]),
            }
            for r in rows
        ]

    # ── decision ledger ──────────────────────────────────────────────────────
    def _last_hash(self) -> str:
        rows = self.query("SELECT ROW_HASH FROM DECISION_LEDGER ORDER BY SEQ DESC LIMIT 1")
        return rows[0]["ROW_HASH"] if rows else GENESIS_HASH

    def append_decision(self, fields: dict) -> str:
        """Append one decision row; returns its ROW_HASH. JSON-able values are serialised."""
        row = {k: fields.get(k) for k in LEDGER_HASHED_FIELDS}
        for k in ("RULES_CITED", "POE_FACTORS_ASSESSED", "RFI_TRIGGERS", "METADATA_JSON"):
            if row[k] is not None and not isinstance(row[k], str):
                row[k] = json.dumps(row[k], sort_keys=True, default=str)
        with self._lock:  # read-last-hash + insert must be atomic
            cur = self._conn.execute(
                "SELECT ROW_HASH FROM DECISION_LEDGER ORDER BY SEQ DESC LIMIT 1")
            last = cur.fetchone()
            prev_hash = last["ROW_HASH"] if last else GENESIS_HASH
            row_hash = ledger_row_hash(row, prev_hash)
            cols = list(LEDGER_HASHED_FIELDS) + ["PREV_HASH", "ROW_HASH"]
            self._conn.execute(
                f"INSERT INTO DECISION_LEDGER ({', '.join(cols)}) "
                f"VALUES ({', '.join('?' for _ in cols)})",
                tuple(row[k] for k in LEDGER_HASHED_FIELDS) + (prev_hash, row_hash),
            )
            self._conn.commit()
        return row_hash

    def record_decision(self, fields: dict, alert_status: str) -> dict:
        """Append a decision and set the alert's status in ONE transaction, idempotently.

        If a row with the same METADATA_JSON.idempotency_key exists, nothing is written and that
        row is returned with status 'already_recorded'. On any error both writes roll back.
        """
        meta = fields.get("METADATA_JSON") or {}
        key = meta.get("idempotency_key") if isinstance(meta, dict) else None
        row = {k: fields.get(k) for k in LEDGER_HASHED_FIELDS}
        for k in ("RULES_CITED", "POE_FACTORS_ASSESSED", "RFI_TRIGGERS", "METADATA_JSON"):
            if row[k] is not None and not isinstance(row[k], str):
                row[k] = json.dumps(row[k], sort_keys=True, default=str)
        with self._lock:
            if key:
                hit = self._conn.execute(
                    "SELECT DECISION_ID, ROW_HASH FROM DECISION_LEDGER "
                    "WHERE json_extract(METADATA_JSON, '$.idempotency_key') = ?", (key,)).fetchone()
                if hit:
                    return {"decision_id": hit["DECISION_ID"], "row_hash": hit["ROW_HASH"],
                            "status": "already_recorded"}
            try:
                last = self._conn.execute(
                    "SELECT ROW_HASH FROM DECISION_LEDGER ORDER BY SEQ DESC LIMIT 1").fetchone()
                prev_hash = last["ROW_HASH"] if last else GENESIS_HASH
                row_hash = ledger_row_hash(row, prev_hash)
                cols = list(LEDGER_HASHED_FIELDS) + ["PREV_HASH", "ROW_HASH"]
                self._conn.execute(
                    f"INSERT INTO DECISION_LEDGER ({', '.join(cols)}) "
                    f"VALUES ({', '.join('?' for _ in cols)})",
                    tuple(row[k] for k in LEDGER_HASHED_FIELDS) + (prev_hash, row_hash))
                self._conn.execute("UPDATE ALERTS SET ALERT_STATUS = ? WHERE ALERT_ID = ?",
                                   (alert_status, row["ALERT_ID"]))
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
        return {"decision_id": row["DECISION_ID"], "row_hash": row_hash, "status": "recorded"}

    def ledger_joined(self) -> list[dict]:
        return self.query("""
            SELECT d.*, a.ALERT_TYPE, a.CUSTOMER_PROFILE, a.ALERT_AMOUNT_INR
            FROM DECISION_LEDGER d LEFT JOIN ALERTS a ON d.ALERT_ID = a.ALERT_ID
            ORDER BY d.SEQ DESC
        """)

    def verify_ledger_chain(self) -> dict:
        """Recompute every ROW_HASH in sequence. Returns {ok, rows, first_break_seq, detail}."""
        rows = self.query("SELECT * FROM DECISION_LEDGER ORDER BY SEQ")
        prev = GENESIS_HASH
        for r in rows:
            if r["PREV_HASH"] != prev:
                return {"ok": False, "rows": len(rows), "first_break_seq": r["SEQ"],
                        "detail": "PREV_HASH does not match the preceding row (row removed or reordered)"}
            if ledger_row_hash(r, prev) != r["ROW_HASH"]:
                return {"ok": False, "rows": len(rows), "first_break_seq": r["SEQ"],
                        "detail": "ROW_HASH does not match row content (row edited)"}
            prev = r["ROW_HASH"]
        return {"ok": True, "rows": len(rows), "first_break_seq": None, "detail": ""}

    def latest_decisions(self) -> list[dict]:
        """The most recent ledger row per alert (the decision currently standing)."""
        return self.query("""
            SELECT d.* FROM DECISION_LEDGER d
            WHERE d.SEQ = (SELECT MAX(SEQ) FROM DECISION_LEDGER x WHERE x.ALERT_ID = d.ALERT_ID)
            ORDER BY d.SEQ
        """)

    def get_decision(self, decision_id: str) -> dict | None:
        rows = self.query("SELECT * FROM DECISION_LEDGER WHERE DECISION_ID = ?", (decision_id,))
        return rows[0] if rows else None

    def closures_for_customer(self, customer_ref: str, before_seq: int | None = None) -> list[dict]:
        """NOT_FILE rows for one customer, oldest first (D1: shown as a count with this query)."""
        sql = ("SELECT SEQ, DECISION_ID, ALERT_ID, DECISION_MADE_AT FROM DECISION_LEDGER "
               "WHERE CUSTOMER_REF = ? AND DISPOSITION = 'NOT_FILE'")
        params: list = [customer_ref]
        if before_seq is not None:
            sql += " AND SEQ < ?"
            params.append(before_seq)
        return self.query(sql + " ORDER BY SEQ", params)

    # ── decision events (T12.4) ──────────────────────────────────────────────
    def append_event(self, fields: dict) -> dict:
        """Append one event; if (DECISION_ID, CAUSE_SHA256) is already recorded, return that row
        instead (a replayed feed item writes nothing)."""
        row = {k: fields.get(k) for k in EVENT_HASHED_FIELDS}
        for k in ("CAUSE_JSON", "OUTCOME_JSON"):
            if not isinstance(row[k], str):
                row[k] = json.dumps(row[k], sort_keys=True, default=str)
        with self._lock:
            hit = self._conn.execute(
                "SELECT * FROM DECISION_EVENTS WHERE DECISION_ID = ? AND CAUSE_SHA256 = ?",
                (row["DECISION_ID"], row["CAUSE_SHA256"])).fetchone()
            if hit:
                return dict(hit, status="already_recorded")
            last = self._conn.execute(
                "SELECT ROW_HASH FROM DECISION_EVENTS ORDER BY SEQ DESC LIMIT 1").fetchone()
            prev_hash = last["ROW_HASH"] if last else GENESIS_HASH
            row_hash = event_row_hash(row, prev_hash)
            cols = list(EVENT_HASHED_FIELDS) + ["PREV_HASH", "ROW_HASH"]
            self._conn.execute(
                f"INSERT INTO DECISION_EVENTS ({', '.join(cols)}) "
                f"VALUES ({', '.join('?' for _ in cols)})",
                tuple(row[k] for k in EVENT_HASHED_FIELDS) + (prev_hash, row_hash))
            self._conn.commit()
        return dict(row, PREV_HASH=prev_hash, ROW_HASH=row_hash, status="recorded")

    def events_for_decision(self, decision_id: str) -> list[dict]:
        return self.query("SELECT * FROM DECISION_EVENTS WHERE DECISION_ID = ? ORDER BY SEQ",
                          (decision_id,))

    def events_for_alert(self, alert_id: str) -> list[dict]:
        return self.query("SELECT * FROM DECISION_EVENTS WHERE ALERT_ID = ? ORDER BY SEQ",
                          (alert_id,))

    def all_events(self) -> list[dict]:
        return self.query("SELECT * FROM DECISION_EVENTS ORDER BY SEQ DESC")

    def verify_events_chain(self) -> dict:
        rows = self.query("SELECT * FROM DECISION_EVENTS ORDER BY SEQ")
        prev = GENESIS_HASH
        for r in rows:
            if r["PREV_HASH"] != prev:
                return {"ok": False, "rows": len(rows), "first_break_seq": r["SEQ"],
                        "detail": "PREV_HASH does not match the preceding row (row removed or reordered)"}
            if event_row_hash(r, prev) != r["ROW_HASH"]:
                return {"ok": False, "rows": len(rows), "first_break_seq": r["SEQ"],
                        "detail": "ROW_HASH does not match row content (row edited)"}
            prev = r["ROW_HASH"]
        return {"ok": True, "rows": len(rows), "first_break_seq": None, "detail": ""}

    # ── dashboard ────────────────────────────────────────────────────────────
    def dashboard_alerts(self) -> list[dict]:
        return self.query("SELECT ALERT_STATUS, ALERT_TYPE, SIGNAL_SOURCE, ALERT_AMOUNT_INR FROM ALERTS")

    def dashboard_ledger(self) -> list[dict]:
        return self.query("SELECT DISPOSITION, SLA_DAYS_REMAINING, DECISION_MADE_AT FROM DECISION_LEDGER")

    def token_usage_summary(self) -> dict:
        """Aggregate token usage from DECISION_LEDGER.METADATA_JSON.

        Returns:
            {
              "total_prompt": int,
              "total_completion": int,
              "total": int,
              "by_tier": {"triage": {"prompt": int, "completion": int}, ...},
              "decisions_with_model_calls": int,
            }
        """
        rows = self.query("SELECT METADATA_JSON FROM DECISION_LEDGER")
        total_p = total_c = 0
        by_tier: dict[str, dict[str, int]] = {}
        decisions_with_calls = 0
        for row in rows:
            raw = row.get("METADATA_JSON")
            if not raw:
                continue
            try:
                meta = json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                continue
            calls = meta.get("model_calls") or []
            if calls:
                decisions_with_calls += 1
            for call in calls:
                usage = call.get("usage") or {}
                pt = int(usage.get("prompt_tokens") or 0)
                ct = int(usage.get("completion_tokens") or 0)
                total_p += pt
                total_c += ct
                tier = call.get("tier") or "unknown"
                bucket = by_tier.setdefault(tier, {"prompt": 0, "completion": 0})
                bucket["prompt"] += pt
                bucket["completion"] += ct
        return {
            "total_prompt": total_p,
            "total_completion": total_c,
            "total": total_p + total_c,
            "by_tier": by_tier,
            "decisions_with_model_calls": decisions_with_calls,
        }

    # ── compute runs ─────────────────────────────────────────────────────────
    def append_compute_run(self, run: dict) -> None:
        cols = ["RUN_ID", "ALERT_ID", "PROGRAM", "BACKEND", "BACKEND_RUN_REF", "CODE_SHA256",
                "INPUT_SHA256", "OUTPUT_SHA256", "OUTPUT_JSON", "STARTED_AT", "FINISHED_AT",
                "PARENT_RUN_ID", "HYPOTHESIS_JSON", "INPUT_JSON"]
        self._exec(
            f"INSERT INTO COMPUTE_RUNS ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            tuple(run.get(c) for c in cols),
        )

    def archive_program(self, code_sha256: str, program: str, source: str) -> None:
        self._exec("INSERT OR IGNORE INTO PROGRAMS (CODE_SHA256, PROGRAM, SOURCE, FIRST_SEEN_AT) "
                   "VALUES (?, ?, ?, ?)",
                   (code_sha256, program, source, datetime.now(timezone.utc).isoformat()))

    def get_program(self, code_sha256: str) -> dict | None:
        rows = self.query("SELECT * FROM PROGRAMS WHERE CODE_SHA256 = ?", (code_sha256,))
        return rows[0] if rows else None

    def compute_runs_for(self, alert_id: str) -> list[dict]:
        return self.query(
            "SELECT * FROM COMPUTE_RUNS WHERE ALERT_ID = ? ORDER BY FINISHED_AT DESC", (alert_id,))

    def get_compute_run(self, run_id: str) -> dict | None:
        rows = self.query("SELECT * FROM COMPUTE_RUNS WHERE RUN_ID = ?", (run_id,))
        return rows[0] if rows else None

    # ── evidence (Phase 1 schema; populated from T2.1 onwards) ──────────────
    def append_evidence(self, item: dict) -> None:
        # Accept both lowercase (EvidenceSourcePort) and UPPERCASE (store convention) keys
        normalised = {k.upper(): v for k, v in item.items()}
        cols = ["EVIDENCE_ID", "ALERT_ID", "TYPE", "SOURCE",
                "CONTENT_HASH", "CONTENT_JSON", "PROVENANCE_JSON", "CREATED_AT"]
        self._exec(
            f"INSERT INTO EVIDENCE ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
            tuple(_scalar(normalised.get(c)) for c in cols),
        )

    def record_evidence(self, alert_id: str | None, ev_type: str, source: str,
                        content: Any, provenance: Any = None) -> str:
        """Hash and append one evidence row; returns its EVIDENCE_ID."""
        content_json = json.dumps(content, sort_keys=True, separators=(",", ":"), default=str)
        digest = hashlib.sha256(content_json.encode()).hexdigest()
        evidence_id = f"EV-{uuid.uuid4().hex[:12]}"
        self.append_evidence({
            "EVIDENCE_ID": evidence_id, "ALERT_ID": alert_id, "TYPE": ev_type, "SOURCE": source,
            "CONTENT_HASH": digest, "CONTENT_JSON": content_json,
            "PROVENANCE_JSON": json.dumps(provenance, sort_keys=True, default=str)
            if provenance is not None else None,
            "CREATED_AT": datetime.now(timezone.utc).isoformat(),
        })
        return evidence_id

    def evidence_for_alert(self, alert_id: str, ev_type: str | None = None) -> list[dict]:
        if ev_type:
            return self.query(
                "SELECT * FROM EVIDENCE WHERE ALERT_ID = ? AND TYPE = ? ORDER BY CREATED_AT",
                (alert_id, ev_type))
        return self.query(
            "SELECT * FROM EVIDENCE WHERE ALERT_ID = ? ORDER BY CREATED_AT", (alert_id,))

    def get_evidence(self, evidence_id: str) -> dict | None:
        rows = self.query("SELECT * FROM EVIDENCE WHERE EVIDENCE_ID = ?", (evidence_id,))
        return rows[0] if rows else None


# ── helpers ──────────────────────────────────────────────────────────────────
def _scalar(v: Any) -> Any:
    """SQLite-bindable value: lists/dicts -> JSON text, bools -> int, dates -> ISO text."""
    if isinstance(v, (list, dict)):
        return json.dumps(v)
    if isinstance(v, bool):
        return int(v)
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return v


def _json_list(v: Any) -> list:
    if v is None:
        return []
    if isinstance(v, list):
        return v
    try:
        out = json.loads(v)
        return out if isinstance(out, list) else []
    except Exception:
        return []
