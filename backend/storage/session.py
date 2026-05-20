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

# EMA centroids — transient, in-process only. Resets on restart by design.
# Persisting 3KB blobs per session to SQLite is unnecessary overhead for a v1 drift signal.
_ema_centroids: Dict[str, bytes] = {}


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
            "state": "ACTIVE",
            "goals": [],
            "current_goal": None,
            "taint": {"active": False, "consecutive_aligned": 0},
            "tool_history": [],
            "turn_count": 0,
            "ended": False,
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

    # ---- original goal ----

    def get_original_goal(self, session_id: str) -> Optional[str]:
        return self._configs.get(session_id, {}).get("original_goal")

    def set_original_goal(self, session_id: str, goal: str) -> None:
        if session_id in self._configs:
            self._configs[session_id]["original_goal"] = goal

    # ---- goal embedding ----

    def get_goal_embedding(self, session_id: str):
        return self._configs.get(session_id, {}).get("goal_embedding")

    def set_goal_embedding(self, session_id: str, embedding) -> None:
        if session_id in self._configs:
            self._configs[session_id]["goal_embedding"] = embedding

    # ---- EMA centroid ----

    def get_centroid(self, session_id: str) -> Optional[bytes]:
        return _ema_centroids.get(session_id)

    def set_centroid(self, session_id: str, data: bytes) -> None:
        _ema_centroids[session_id] = data

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

    # ---- state machine ----

    def get_state(self, session_id: str) -> str:
        return self._sessions.get(session_id, {}).get("state", "ACTIVE")

    def set_state(self, session_id: str, state: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id]["state"] = state

    def set_ended(self, session_id: str, ended: bool) -> None:
        if session_id in self._sessions:
            self._sessions[session_id]["ended"] = ended

    def get_current_goal(self, session_id: str) -> Optional[str]:
        return self._sessions.get(session_id, {}).get("current_goal")

    def set_current_goal(self, session_id: str, goal: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id]["current_goal"] = goal

    def get_goals(self, session_id: str) -> List[str]:
        return self._sessions.get(session_id, {}).get("goals", [])

    def append_goal(self, session_id: str, goal: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id]["goals"].append(goal)

    def get_taint(self, session_id: str) -> dict:
        return self._sessions.get(session_id, {}).get("taint", {"active": False, "consecutive_aligned": 0})

    def set_taint(self, session_id: str, taint: dict) -> None:
        if session_id in self._sessions:
            self._sessions[session_id]["taint"] = taint

    def get_tool_history(self, session_id: str) -> List[dict]:
        return self._sessions.get(session_id, {}).get("tool_history", [])

    def append_tool_call(self, session_id: str, tool_call: dict) -> None:
        if session_id in self._sessions:
            history = self._sessions[session_id]["tool_history"]
            history.append(tool_call)
            if len(history) > 5:
                history.pop(0)

    def get_turn_count(self, session_id: str) -> int:
        return self._sessions.get(session_id, {}).get("turn_count", 0)

    def increment_turn_count(self, session_id: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id]["turn_count"] += 1

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
    severity     TEXT DEFAULT 'Low',
    state        TEXT DEFAULT 'ACTIVE',
    current_goal TEXT,
    taint        TEXT DEFAULT '{"active": false, "consecutive_aligned": 0}',
    turn_count   INTEGER DEFAULT 0,
    ended        INTEGER DEFAULT 0
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
            # Add new trace columns if missing
            for col, definition in [("llm_output", "TEXT"), ("finalized", "INTEGER DEFAULT 1")]:
                try:
                    conn.execute(f"ALTER TABLE traces ADD COLUMN {col} {definition}")
                except sqlite3.OperationalError:
                    pass  # column already exists
            # Add new session columns if missing
            for col, definition in [
                ("state", "TEXT DEFAULT 'ACTIVE'"),
                ("current_goal", "TEXT"),
                ("taint", "TEXT DEFAULT '{\"active\": false, \"consecutive_aligned\": 0}'"),
                ("turn_count", "INTEGER DEFAULT 0"),
            ]:
                try:
                    conn.execute(f"ALTER TABLE sessions ADD COLUMN {col} {definition}")
                except sqlite3.OperationalError:
                    pass  # column already exists

    # ---- session management ----

    def create(self, session_id: str, config: dict) -> None:
        # Initialize list fields in config (goals, tool_history stored as JSON)
        if "goals" not in config:
            config["goals"] = []
        if "tool_history" not in config:
            config["tool_history"] = []

        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO sessions
                    (session_id, created_at, agent_type, environment, session_config,
                     cumulative_risk, trace_count, severity, state, current_goal, taint, turn_count, ended)
                VALUES (?, ?, ?, ?, ?, 0, 0, 'Low', 'ACTIVE', NULL, ?, 0, 0)
                """,
                (
                    session_id,
                    time.time(),
                    config.get("agent_type", "general"),
                    config.get("environment", "dev"),
                    json.dumps(config),
                    json.dumps({"active": False, "consecutive_aligned": 0}),
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
                "cumulative_risk, trace_count, severity, state, current_goal, taint, turn_count, ended "
                "FROM sessions ORDER BY created_at DESC"
            ).fetchall()
        result = []
        for r in rows:
            sess = dict(r)
            sess["taint"] = json.loads(sess.get("taint") or '{"active": false, "consecutive_aligned": 0}')
            sess["ended"] = bool(sess.get("ended", 0))
            result.append(sess)
        return result

    def get_session(self, session_id: str) -> Optional[dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT session_id, created_at, agent_type, environment, "
                "cumulative_risk, trace_count, severity, state, current_goal, taint, turn_count, ended "
                "FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        sess = dict(row)
        sess["taint"] = json.loads(sess.get("taint") or '{"active": false, "consecutive_aligned": 0}')
        sess["ended"] = bool(sess.get("ended", 0))
        sess["traces"] = self.get_traces(session_id)
        return sess

    # ---- original goal ----

    def get_original_goal(self, session_id: str) -> Optional[str]:
        return self.get_config(session_id).get("original_goal")

    def set_original_goal(self, session_id: str, goal: str) -> None:
        config = self.get_config(session_id)
        config["original_goal"] = goal
        with self._conn() as conn:
            conn.execute(
                "UPDATE sessions SET session_config = ? WHERE session_id = ?",
                (json.dumps(config), session_id),
            )

    # ---- goal embedding ----

    def get_goal_embedding(self, session_id: str):
        raw = self.get_config(session_id).get("goal_embedding")
        if raw is None:
            return None
        import numpy as np
        return np.array(raw, dtype=np.float32)

    def set_goal_embedding(self, session_id: str, embedding) -> None:
        config = self.get_config(session_id)
        config["goal_embedding"] = embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
        with self._conn() as conn:
            conn.execute(
                "UPDATE sessions SET session_config = ? WHERE session_id = ?",
                (json.dumps(config), session_id),
            )

    # ---- EMA centroid ----

    def get_centroid(self, session_id: str) -> Optional[bytes]:
        return _ema_centroids.get(session_id)

    def set_centroid(self, session_id: str, data: bytes) -> None:
        _ema_centroids[session_id] = data

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

    # ---- state machine ----

    def get_state(self, session_id: str) -> str:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT state FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        return row["state"] if row else "ACTIVE"

    def set_state(self, session_id: str, state: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE sessions SET state = ? WHERE session_id = ?",
                (state, session_id),
            )

    def set_ended(self, session_id: str, ended: bool) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE sessions SET ended = ? WHERE session_id = ?",
                (1 if ended else 0, session_id),
            )

    def get_current_goal(self, session_id: str) -> Optional[str]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT current_goal FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        return row["current_goal"] if row else None

    def set_current_goal(self, session_id: str, goal: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE sessions SET current_goal = ? WHERE session_id = ?",
                (goal, session_id),
            )

    def get_goals(self, session_id: str) -> List[str]:
        config = self.get_config(session_id)
        return config.get("goals", [])

    def append_goal(self, session_id: str, goal: str) -> None:
        config = self.get_config(session_id)
        config.setdefault("goals", []).append(goal)
        with self._conn() as conn:
            conn.execute(
                "UPDATE sessions SET session_config = ? WHERE session_id = ?",
                (json.dumps(config), session_id),
            )

    def get_taint(self, session_id: str) -> dict:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT taint FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        if not row:
            return {"active": False, "consecutive_aligned": 0}
        return json.loads(row["taint"] or '{"active": false, "consecutive_aligned": 0}')

    def set_taint(self, session_id: str, taint: dict) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE sessions SET taint = ? WHERE session_id = ?",
                (json.dumps(taint), session_id),
            )

    def get_tool_history(self, session_id: str) -> List[dict]:
        config = self.get_config(session_id)
        return config.get("tool_history", [])

    def append_tool_call(self, session_id: str, tool_call: dict) -> None:
        config = self.get_config(session_id)
        history = config.setdefault("tool_history", [])
        history.append(tool_call)
        if len(history) > 5:
            history.pop(0)
        with self._conn() as conn:
            conn.execute(
                "UPDATE sessions SET session_config = ? WHERE session_id = ?",
                (json.dumps(config), session_id),
            )

    def get_turn_count(self, session_id: str) -> int:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT turn_count FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        return row["turn_count"] if row else 0

    def increment_turn_count(self, session_id: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE sessions SET turn_count = turn_count + 1 WHERE session_id = ?",
                (session_id,),
            )

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
