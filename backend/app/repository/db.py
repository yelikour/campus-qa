"""SQLite 仓储层:会话、消息、查询日志。生产部署替换为 PostgreSQL,接口不变。"""
from __future__ import annotations

import sqlite3
import threading
import time
import uuid

from ..config import settings

_local = threading.local()


def get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn"):
        settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _local.conn = sqlite3.connect(settings.DB_PATH)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
    return _local.conn


def init_schema():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS conversation (
        id TEXT PRIMARY KEY, user_token TEXT NOT NULL,
        title TEXT DEFAULT '新会话', created_at REAL, updated_at REAL);
    CREATE TABLE IF NOT EXISTS message (
        id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL,
        role TEXT NOT NULL, content TEXT NOT NULL,
        sources TEXT, latency_ms INTEGER, created_at REAL);
    CREATE TABLE IF NOT EXISTS query_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, query TEXT,
        hit INTEGER, top_score REAL, latency_ms INTEGER, category TEXT);
    """)
    conn.commit()


def new_conversation(user_token: str) -> str:
    cid = uuid.uuid4().hex[:12]
    now = time.time()
    get_conn().execute(
        "INSERT INTO conversation VALUES (?,?,?,?,?)", (cid, user_token, "新会话", now, now))
    get_conn().commit()
    return cid


def touch_conversation(cid: str, title: str | None = None):
    conn = get_conn()
    if title:
        conn.execute("UPDATE conversation SET updated_at=?, title=? WHERE id=?",
                     (time.time(), title[:24], cid))
    else:
        conn.execute("UPDATE conversation SET updated_at=? WHERE id=?", (time.time(), cid))
    conn.commit()


def save_message(cid: str, role: str, content: str,
                 sources: str | None = None, latency_ms: int | None = None) -> str:
    mid = uuid.uuid4().hex[:12]
    get_conn().execute(
        "INSERT INTO message VALUES (?,?,?,?,?,?,?)",
        (mid, cid, role, content, sources, latency_ms, time.time()))
    get_conn().commit()
    return mid


def list_conversations(user_token: str, limit: int = 50):
    rows = get_conn().execute(
        "SELECT id, title, updated_at FROM conversation WHERE user_token=? ORDER BY updated_at DESC LIMIT ?",
        (user_token, limit)).fetchall()
    return [dict(r) for r in rows]


def get_conversation(cid: str):
    """按 id 取会话行(id/user_token/title);不存在返回 None,供 API 层做归属校验。"""
    return get_conn().execute(
        "SELECT id, user_token, title FROM conversation WHERE id=?", (cid,)).fetchone()


def get_messages(cid: str):
    rows = get_conn().execute(
        "SELECT role, content, sources, created_at FROM message WHERE conversation_id=? ORDER BY created_at",
        (cid,)).fetchall()
    return [dict(r) for r in rows]


def log_query(query: str, hit: bool, top_score: float, latency_ms: int, category: str):
    get_conn().execute(
        "INSERT INTO query_log(ts,query,hit,top_score,latency_ms,category) VALUES (?,?,?,?,?,?)",
        (time.time(), query, int(hit), top_score, latency_ms, category))
    get_conn().commit()


def stats() -> dict:
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) c FROM query_log").fetchone()["c"]
    hits = conn.execute("SELECT COUNT(*) c FROM query_log WHERE hit=1").fetchone()["c"]
    avg = conn.execute("SELECT AVG(latency_ms) a FROM query_log").fetchone()["a"] or 0
    convos = conn.execute("SELECT COUNT(*) c FROM conversation").fetchone()["c"]
    by_cat = conn.execute(
        "SELECT category, COUNT(*) c FROM query_log WHERE hit=1 GROUP BY category ORDER BY c DESC LIMIT 8"
    ).fetchall()
    return {
        "total_queries": total,
        "hit_rate": round(hits / total, 3) if total else None,
        "avg_latency_ms": round(avg, 1),
        "conversations": convos,
        "top_categories": {r["category"]: r["c"] for r in by_cat},
    }
