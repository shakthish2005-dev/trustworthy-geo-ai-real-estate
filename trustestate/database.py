from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from trustestate.config import DB_PATH
from trustestate.security import hash_password, verify_password


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database() -> None:
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'user')),
        active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS due_diligence_cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        city TEXT,
        survey_number TEXT,
        latitude REAL,
        longitude REAL,
        risk_score REAL NOT NULL,
        risk_band TEXT NOT NULL,
        review_status TEXT NOT NULL DEFAULT 'Draft',
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(owner_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        metadata_json TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE INDEX IF NOT EXISTS idx_cases_owner ON due_diligence_cases(owner_id);
    CREATE INDEX IF NOT EXISTS idx_cases_status ON due_diligence_cases(review_status);
    """
    with connection() as conn:
        conn.executescript(schema)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_bootstrap_users(
    admin_username: str,
    admin_password: str,
    user_username: str,
    user_password: str,
    pepper: str,
) -> None:
    initialize_database()
    records = [
        (admin_username.strip(), admin_password, "admin"),
        (user_username.strip(), user_password, "user"),
    ]
    with connection() as conn:
        for username, password, role in records:
            exists = conn.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO users(username,password_hash,role,created_at) VALUES(?,?,?,?)",
                    (username, hash_password(password, pepper), role, utc_now()),
                )


def authenticate(username: str, password: str, pepper: str) -> dict[str, Any] | None:
    initialize_database()
    with connection() as conn:
        row = conn.execute(
            "SELECT id,username,password_hash,role,active FROM users WHERE username = ?",
            (username.strip(),),
        ).fetchone()
        if not row or not row["active"]:
            return None
        if not verify_password(password, row["password_hash"], pepper):
            return None
        user = {"id": row["id"], "username": row["username"], "role": row["role"]}
        conn.execute(
            "INSERT INTO audit_log(user_id,action,metadata_json,created_at) VALUES(?,?,?,?)",
            (row["id"], "login", "{}", utc_now()),
        )
        return user


def save_case(user_id: int, payload: dict[str, Any], risk_score: float, risk_band: str) -> int:
    now = utc_now()
    with connection() as conn:
        cur = conn.execute(
            """INSERT INTO due_diligence_cases(
                owner_id,title,city,survey_number,latitude,longitude,risk_score,
                risk_band,payload_json,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (
                user_id,
                payload.get("title") or "Untitled property review",
                payload.get("city"),
                payload.get("survey_number"),
                payload.get("latitude"),
                payload.get("longitude"),
                risk_score,
                risk_band,
                json.dumps(payload, ensure_ascii=False, default=str),
                now,
                now,
            ),
        )
        case_id = int(cur.lastrowid)
        conn.execute(
            "INSERT INTO audit_log(user_id,action,metadata_json,created_at) VALUES(?,?,?,?)",
            (user_id, "case_created", json.dumps({"case_id": case_id}), now),
        )
        return case_id


def list_cases(user_id: int, role: str) -> list[dict[str, Any]]:
    with connection() as conn:
        if role == "admin":
            rows = conn.execute(
                """SELECT c.*,u.username owner FROM due_diligence_cases c
                JOIN users u ON u.id=c.owner_id ORDER BY c.updated_at DESC"""
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT c.*,u.username owner FROM due_diligence_cases c
                JOIN users u ON u.id=c.owner_id WHERE c.owner_id=?
                ORDER BY c.updated_at DESC""",
                (user_id,),
            ).fetchall()
    return [dict(r) for r in rows]


def update_case_status(case_id: int, status: str, admin_id: int) -> None:
    allowed = {"Draft", "Needs evidence", "Lawyer review", "Verified externally", "Rejected"}
    if status not in allowed:
        raise ValueError("Unsupported review status")
    with connection() as conn:
        conn.execute(
            "UPDATE due_diligence_cases SET review_status=?,updated_at=? WHERE id=?",
            (status, utc_now(), case_id),
        )
        conn.execute(
            "INSERT INTO audit_log(user_id,action,metadata_json,created_at) VALUES(?,?,?,?)",
            (admin_id, "case_status_updated", json.dumps({"case_id": case_id, "status": status}), utc_now()),
        )


def platform_stats() -> dict[str, int]:
    with connection() as conn:
        return {
            "users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            "cases": conn.execute("SELECT COUNT(*) FROM due_diligence_cases").fetchone()[0],
            "high_risk": conn.execute(
                "SELECT COUNT(*) FROM due_diligence_cases WHERE risk_score >= 60"
            ).fetchone()[0],
            "pending_review": conn.execute(
                "SELECT COUNT(*) FROM due_diligence_cases WHERE review_status IN ('Draft','Needs evidence','Lawyer review')"
            ).fetchone()[0],
        }
