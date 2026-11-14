"""SQLite storage. Swap for PostgreSQL later; the table layout is the same."""
import sqlite3
from datetime import datetime
from typing import Any

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS caregivers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    name_key TEXT NOT NULL UNIQUE,
    pin_salt TEXT NOT NULL,
    pin_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    caregiver_id INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caregiver_id INTEGER NOT NULL UNIQUE,   -- one caregiver <-> one patient
    name TEXT NOT NULL DEFAULT '',
    nickname TEXT NOT NULL DEFAULT '',      -- what the assistant calls them
    preferred_language TEXT NOT NULL DEFAULT 'en-IN',
    location_note TEXT NOT NULL DEFAULT '', -- caregiver-approved, e.g. "You are at home in Bengaluru."
    pending_check TEXT NOT NULL DEFAULT '', -- check-in question waiting for a yes/no (thirsty, hungry, comfort)
    checkin_count INTEGER NOT NULL DEFAULT 0,
    last_checkin_at TEXT DEFAULT NULL,
    keep_talking INTEGER NOT NULL DEFAULT 0 -- caregiver switch: SMRITI keeps listening after each reply
);
CREATE TABLE IF NOT EXISTS family (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    relation TEXT NOT NULL,
    description TEXT DEFAULT '',
    status_text TEXT DEFAULT '',
    status_expires TEXT DEFAULT NULL,
    approved INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    text TEXT NOT NULL,
    approved INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    remind_date TEXT DEFAULT NULL,
    approved INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    ts TEXT NOT NULL,
    language TEXT,
    transcript TEXT,
    intent TEXT,
    subject TEXT DEFAULT '',
    reply TEXT
);
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    ts TEXT NOT NULL,
    level TEXT NOT NULL,
    reason TEXT NOT NULL,
    transcript TEXT,
    resolved INTEGER NOT NULL DEFAULT 0
);
"""

_conn: sqlite3.Connection | None = None


def conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript(SCHEMA)
        try:  # older database files do not have this column yet
            _conn.execute("ALTER TABLE patients ADD COLUMN keep_talking INTEGER NOT NULL DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        _conn.commit()
    return _conn


def reset_connection() -> None:
    """Used by tests to point at a fresh database."""
    global _conn
    if _conn is not None:
        _conn.close()
    _conn = None


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def query(sql: str, args: tuple = ()) -> list[dict[str, Any]]:
    return [dict(r) for r in conn().execute(sql, args).fetchall()]


def one(sql: str, args: tuple = ()) -> dict[str, Any] | None:
    r = conn().execute(sql, args).fetchone()
    return dict(r) if r else None


def execute(sql: str, args: tuple = ()) -> int:
    cur = conn().execute(sql, args)
    conn().commit()
    return cur.lastrowid


def seed_demo_data() -> None:
    """Synthetic demo account: caregiver "demo", PIN 1234, patient Lakshmi. No real people or data."""
    from auth import create_caregiver, find_by_name

    if find_by_name("demo"):
        return
    cid = create_caregiver("demo", "1234")
    pid = one("SELECT id FROM patients WHERE caregiver_id=?", (cid,))["id"]
    execute(
        "UPDATE patients SET name=?, nickname=?, preferred_language=?, location_note=? WHERE id=?",
        ("Lakshmi", "Lakshmi", "en-IN", "You are at home.", pid),
    )
    execute(
        "INSERT INTO family (patient_id,name,relation,description,status_text) VALUES (?,?,?,?,?)",
        (pid, "Priya", "daughter", "She loves you very much and visits on Sundays.", "is at work and will come home in the evening"),
    )
    execute(
        "INSERT INTO family (patient_id,name,relation,description) VALUES (?,?,?,?)",
        (pid, "Rahul", "son", "He lives in Mysuru and calls you every night."),
    )
    for cat, text in [
        ("food", "Your favourite food is dosa with coconut chutney."),
        ("song", "You love listening to old Kannada film songs in the evening."),
        ("place", "You enjoy visiting the temple near your home."),
        ("life_event", "You were a school teacher for many years."),
    ]:
        execute("INSERT INTO memories (patient_id,category,text,created_at) VALUES (?,?,?,?)", (pid, cat, text, now()))
    execute(
        "INSERT INTO reminders (patient_id,text,remind_date) VALUES (?,?,NULL)",
        (pid, "Priya will visit on Sunday and you will have lunch together"),
    )
