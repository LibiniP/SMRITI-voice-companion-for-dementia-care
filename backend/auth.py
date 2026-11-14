"""Caregiver accounts: name + numeric PIN. PINs are stored salted and hashed, never in plain text.

Each caregiver owns exactly one patient (one caregiver-patient pair). Logging in with a name and PIN
decides which patient's data is loaded.
"""
import hashlib
import hmac
import secrets
import time

import db

_fails: dict[str, tuple[int, float]] = {}  # key -> (failed count, locked-until timestamp)
MAX_FAILS = 5
LOCK_SECONDS = 60


def name_key(name: str) -> str:
    return " ".join(name.lower().split())


def _hash(pin: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(salt_hex), 120_000).hex()


def create_caregiver(name: str, pin: str) -> int:
    salt = secrets.token_hex(16)
    cid = db.execute(
        "INSERT INTO caregivers (name, name_key, pin_salt, pin_hash, created_at) VALUES (?,?,?,?,?)",
        (name.strip(), name_key(name), salt, _hash(pin, salt), db.now()),
    )
    db.execute("INSERT INTO patients (caregiver_id) VALUES (?)", (cid,))
    return cid


def find_by_name(name: str) -> dict | None:
    return db.one("SELECT * FROM caregivers WHERE name_key=?", (name_key(name),))


def pin_matches(cg: dict, pin: str) -> bool:
    return hmac.compare_digest(_hash(pin or "", cg["pin_salt"]), cg["pin_hash"])


# ---- brute-force protection: 5 wrong PINs locks that account for 60 seconds ----
def is_locked(key: str) -> bool:
    rec = _fails.get(key)
    if not rec:
        return False
    if rec[1] and rec[1] <= time.time():
        _fails.pop(key, None)
        return False
    return rec[1] > time.time()


def record_fail(key: str) -> None:
    n = _fails.get(key, (0, 0.0))[0] + 1
    _fails[key] = (n, time.time() + LOCK_SECONDS if n >= MAX_FAILS else 0.0)


def record_ok(key: str) -> None:
    _fails.pop(key, None)


# ---- sessions ----
def new_session(caregiver_id: int) -> str:
    token = secrets.token_urlsafe(32)
    db.execute("INSERT INTO sessions (token, caregiver_id, created_at) VALUES (?,?,?)", (token, caregiver_id, db.now()))
    return token


def caregiver_for_token(token: str) -> dict | None:
    if not token:
        return None
    return db.one(
        "SELECT c.* FROM sessions s JOIN caregivers c ON c.id = s.caregiver_id WHERE s.token=?", (token,)
    )


def end_session(token: str) -> None:
    db.execute("DELETE FROM sessions WHERE token=?", (token,))
