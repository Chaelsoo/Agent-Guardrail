"""Unified session store and event log.

Two backends:
- InMemoryStore  — fast, no persistence (AEGIS_DB_ENABLED=false)
- SQLiteStore    — persists to SQLite via stdlib sqlite3

Both are thread-safe for the typical single-process FastAPI deployment.
"""

import asyncio
import json
import sqlite3
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Severity helpers
# ---------------------------------------------------------------------------

def _severity(risk: float) -> str:
    if risk >= 0.8:
        return "Critical"
    if risk >= 0.6:
        return "High"
    if risk >= 0.3:
        return "Medium"
    return "Low"


def _worst_severity(a: str, b: str) -> str:
    order = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
    return a if order.get(a, 0) >= order.get(b, 0) else b


# ---------------------------------------------------------------------------
# SSE infrastructure (module-level)
# ---------------------------------------------------------------------------

_sse_queues: Dict[str, List[asyncio.Queue]] = defaultdict(list)


def subscribe(session_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _sse_queues[session_id].append(q)
    return q


def unsubscribe(session_id: str, q: asyncio.Queue) -> None:
    try:
        _sse_queues[session_id].remove(q)
    except (ValueError, KeyError):
        pass


async def publish(session_id: str, trace: dict) -> None:
    for q in list(_sse_queues.get(session_id, [])):
        await q.put(trace)


# ---------------------------------------------------------------------------
# Active trace tracking (transient, in-process only)
# ---------------------------------------------------------------------------

_active_trace_ids: Dict[str, str] = {}


# ---------------------------------------------------------------------------
# In-memory backend
# ---------------------------------------------------------------------------

class InMemoryStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._traces: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    # ---- session management ----

    def create(self, session_id: str, config: dict) -> None:
        self._configs[session_id] = config
        self._sessions[session_id] = {
            "session_id": session_id,
            "created_at": time.time(),
            "agent_type": config.get("agent_type", "general"),
            "environment": config.get("environment", "dev"),
            "cumulative_risk": 0.0,
            "trace_count": 0,
            "severity": "Low",
        }

    def exists(self, session_id: str) -> bool:
        return session_id in self._sessions

    def get_config(self, session_id: str) -> dict:
        return self._configs.get(session_id, {})

    # ---- trace management ----

    def log_trace(self, trace: dict) -> None:
        sid = trace["session_id"]
        self._traces[sid].append(trace)
        sess = self._sessions.get(sid)
        if sess:
            sess["trace_count"] += 1
            sess["cumulative_risk"] = round(
                sess["cumulative_risk"] + trace.get("risk_score", 0.0), 4
            )
            sess["severity"] = _worst_severity(
                sess["severity"], trace.get("severity", "Low")
            )

    def update_trace(self, trace: dict) -> None:
        """Replace an existing trace in place without incrementing counters."""
        sid = trace["session_id"]
        traces = self._traces[sid]
        for i, t in enumerate(traces):
            if t["trace_id"] == trace["trace_id"]:
                traces[i] = trace
                break

    def get_traces(self, session_id: str) -> List[dict]:
        return list(self._traces.get(session_id, []))

    def list_sessions(self) -> List[dict]:
        return list(self._sessions.values())

    def get_session(self, session_id: str) -> Optional[dict]:
        sess = self._sessions.get(session_id)
        if sess is None:
            return None
        return {**sess, "traces": self.get_traces(session_id)}

    # ---- active trace ----

    def set_active_trace(self, session_id: str, trace_id: str) -> None:
        _active_trace_ids[session_id] = trace_id

    def get_active_trace(self, session_id: str) -> Optional[dict]:
        trace_id = _active_trace_ids.get(session_id)
        if not trace_id:
            return None
        return next((t for t in self._traces.get(session_id, []) if t["trace_id"] == trace_id), None)

    def clear_active_trace(self, session_id: str) -> None:
        _active_trace_ids.pop(session_id, None)

    # ---- SSE delegation ----

    def subscribe(self, session_id: str) -> asyncio.Queue:
        return subscribe(session_id)

    def unsubscribe(self, session_id: str, q: asyncio.Queue) -> None:
        unsubscribe(session_id, q)


# ---------------------------------------------------------------------------
# SQLite backend
# ---------------------------------------------------------------------------

_CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id   TEXT PRIMARY KEY,
    created_at   REAL,
    agent_type   TEXT,
    environment  TEXT,
    session_config TEXT,
    cumulative_risk REAL DEFAULT 0,
    trace_count  INTEGER DEFAULT 0,
    severity     TEXT DEFAULT 'Low'
);
"""

_CREATE_TRACES = """
CREATE TABLE IF NOT EXISTS traces (
    trace_id   TEXT PRIMARY KEY,
    session_id TEXT,
    ts         REAL,
    ts_readable TEXT,
    prompt     TEXT,
    verdict    TEXT,
    severity   TEXT,
    risk_score REAL,
    duration_ms INTEGER,
    spans      TEXT,
    llm_tokens INTEGER,
    llm_model  TEXT,
    llm_output TEXT,
    finalized  INTEGER DEFAULT 1,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
"""


class SQLiteStore:
    def __init__(self, db_url: str) -> None:
        path = db_url.replace("sqlite:///", "").replace("sqlite://", "")
        self._path = path
        self._ensure_tables()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self) -> None:
        with self._conn() as conn:
            conn.execute(_CREATE_SESSIONS)
            conn.execute(_CREATE_TRACES)
            for col, definition in [("llm_output", "TEXT"), ("finalized", "INTEGER DEFAULT 1")]:
                try:
                    conn.execute(f"ALTER TABLE traces ADD COLUMN {col} {definition}")
                except sqlite3.OperationalError:
                    pass  # column already exists

    # ---- session management ----

    def create(self, session_id: str, config: dict) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO sessions
                    (session_id, created_at, agent_type, environment, session_config,
                     cumulative_risk, trace_count, severity)
                VALUES (?, ?, ?, ?, ?, 0, 0, 'Low')
                """,
                (
                    session_id,
                    time.time(),
                    config.get("agent_type", "general"),
                    config.get("environment", "dev"),
                    json.dumps(config),
                ),
            )

    def exists(self, session_id: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        return row is not None

    def get_config(self, session_id: str) -> dict:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT session_config FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return {}
        return json.loads(row["session_config"] or "{}")

    # ---- trace management ----

    def log_trace(self, trace: dict) -> None:
        sid = trace["session_id"]
        risk = float(trace.get("risk_score", 0.0))
        sev = trace.get("severity", _severity(risk))

        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO traces
                    (trace_id, session_id, ts, ts_readable, prompt, verdict,
                     severity, risk_score, duration_ms, spans, llm_tokens,
                     llm_model, llm_output, finalized)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace["trace_id"],
                    sid,
                    trace.get("ts", time.time()),
                    trace.get("ts_readable", ""),
                    trace.get("prompt", ""),
                    trace.get("verdict", "allowed"),
                    sev,
                    risk,
                    trace.get("duration_ms", 0),
                    json.dumps(trace.get("spans", [])),
                    trace.get("llm_tokens"),
                    trace.get("llm_model"),
                    trace.get("llm_output"),
                    1 if trace.get("finalized", True) else 0,
                ),
            )
            conn.execute(
                """
                UPDATE sessions
                SET cumulative_risk = cumulative_risk + ?,
                    trace_count     = trace_count + 1,
                    severity        = CASE
                        WHEN ? = 'Critical' THEN 'Critical'
                        WHEN severity = 'Critical' THEN 'Critical'
                        WHEN ? = 'High' THEN 'High'
                        WHEN severity = 'High' THEN 'High'
                        WHEN ? = 'Medium' THEN 'Medium'
                        WHEN severity = 'Medium' THEN 'Medium'
                        ELSE 'Low'
                    END
                WHERE session_id = ?
                """,
                (risk, sev, sev, sev, sid),
            )

    def update_trace(self, trace: dict) -> None:
        """Replace an existing trace in place without incrementing session counters."""
        sid = trace["session_id"]
        risk = float(trace.get("risk_score", 0.0))
        sev = trace.get("severity", _severity(risk))
        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO traces
                    (trace_id, session_id, ts, ts_readable, prompt, verdict,
                     severity, risk_score, duration_ms, spans, llm_tokens,
                     llm_model, llm_output, finalized)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace["trace_id"],
                    sid,
                    trace.get("ts", time.time()),
                    trace.get("ts_readable", ""),
                    trace.get("prompt", ""),
                    trace.get("verdict", "allowed"),
                    sev,
                    risk,
                    trace.get("duration_ms", 0),
                    json.dumps(trace.get("spans", [])),
                    trace.get("llm_tokens"),
                    trace.get("llm_model"),
                    trace.get("llm_output"),
                    1 if trace.get("finalized", True) else 0,
                ),
            )

    def get_traces(self, session_id: str) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM traces WHERE session_id = ? ORDER BY ts ASC",
                (session_id,),
            ).fetchall()
        result = []
        for row in rows:
            t = dict(row)
            t["spans"] = json.loads(t.get("spans") or "[]")
            t["finalized"] = bool(t.get("finalized", 1))
            result.append(t)
        return result

    def list_sessions(self) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT session_id, created_at, agent_type, environment, "
                "cumulative_risk, trace_count, severity FROM sessions ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_session(self, session_id: str) -> Optional[dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT session_id, created_at, agent_type, environment, "
                "cumulative_risk, trace_count, severity FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        sess = dict(row)
        sess["traces"] = self.get_traces(session_id)
        return sess

    # ---- active trace ----

    def set_active_trace(self, session_id: str, trace_id: str) -> None:
        _active_trace_ids[session_id] = trace_id

    def get_active_trace(self, session_id: str) -> Optional[dict]:
        trace_id = _active_trace_ids.get(session_id)
        if not trace_id:
            return None
        traces = self.get_traces(session_id)
        return next((t for t in traces if t["trace_id"] == trace_id), None)

    def clear_active_trace(self, session_id: str) -> None:
        _active_trace_ids.pop(session_id, None)

    # ---- SSE delegation ----

    def subscribe(self, session_id: str) -> asyncio.Queue:
        return subscribe(session_id)

    def unsubscribe(self, session_id: str, q: asyncio.Queue) -> None:
        unsubscribe(session_id, q)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_store() -> "InMemoryStore | SQLiteStore":
    from ..config import settings  # deferred to avoid circular import at module load

    if settings.db_enabled:
        return SQLiteStore(settings.db_url)
    return InMemoryStore()
