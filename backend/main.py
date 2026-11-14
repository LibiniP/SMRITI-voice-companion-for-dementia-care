"""SMRITI backend. Run:  uvicorn main:app --reload   (from the backend folder)

Accounts: a caregiver logs in with a name + numeric PIN. Each caregiver owns one patient, so the login
decides whose memories, alerts and history are loaded and used by the assistant.
"""
import base64
import re
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import auth
import config
import db
import engine
import gnani_client as gnani
import responses as R

STATIC = Path(__file__).parent / "static"
UNLOCK_SECONDS = 10 * 60          # caregiver area re-locks after 10 minutes
_unlocked: dict[str, float] = {}  # session token -> unlocked-until timestamp (in memory is fine for a demo)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.conn()
    if config.SEED_DEMO_DATA:
        db.seed_demo_data()
    yield


app = FastAPI(title="SMRITI", version="0.3", lifespan=lifespan)


# ---------- session helpers ----------
def current(x_auth_token: str = Header(default="")) -> dict:
    """Any logged-in session (patient screen + caregiver). Returns the caregiver row plus its patient."""
    cg = auth.caregiver_for_token(x_auth_token)
    if not cg:
        raise HTTPException(401, "Please log in")
    cg["patient"] = db.one("SELECT * FROM patients WHERE caregiver_id=?", (cg["id"],))
    cg["token"] = x_auth_token
    return cg


def caregiver(s: dict = Depends(current)) -> dict:
    """Caregiver-only endpoints: the caregiver area must be unlocked with the PIN."""
    if _unlocked.get(s["token"], 0) < time.time():
        raise HTTPException(403, "Caregiver area is locked. Enter your PIN.")
    return s


def _unlock(token: str) -> None:
    _unlocked[token] = time.time() + UNLOCK_SECONDS


def _own(table: str, item_id: int, s: dict) -> None:
    """404 unless this row belongs to the logged-in caregiver's patient."""
    row = db.one(f"SELECT patient_id FROM {table} WHERE id=?", (item_id,))
    if not row or row["patient_id"] != s["patient"]["id"]:
        raise HTTPException(404, "Not found")


def _public_patient(p: dict) -> dict:
    return {"id": p["id"], "name": p["name"], "nickname": p["nickname"], "preferred_language": p["preferred_language"],
            "keep_talking": bool(p.get("keep_talking"))}


def _setup_done(patient_id: int) -> bool:
    return bool(db.query("SELECT id FROM family WHERE patient_id=? LIMIT 1", (patient_id,))
                or db.query("SELECT id FROM memories WHERE patient_id=? LIMIT 1", (patient_id,)))


async def _speak(text: str, tts_language: str) -> dict:
    """Never let a TTS failure hide the written reply."""
    try:
        audio, mime, used = await gnani.synthesize(text, tts_language)
        return {"audio_base64": base64.b64encode(audio).decode(), "audio_mime": mime, "tts_voice": used, "tts_error": None}
    except gnani.GnaniError as e:
        return {"audio_base64": None, "audio_mime": None, "tts_voice": None, "tts_error": str(e)}


# ---------- basic ----------
@app.get("/health")
def health():
    return {"status": "ok", "gnani_key_configured": bool(config.GNANI_API_KEY)}


@app.get("/")
def root():
    return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-store"})


# ---------- accounts ----------
class SignupIn(BaseModel):
    name: str
    pin: str


class LoginIn(BaseModel):
    name: str
    pin: str


class PinIn(BaseModel):
    pin: str


def _session_payload(cg_id: int, token: str, first_time: bool = False) -> dict:
    cg = db.one("SELECT * FROM caregivers WHERE id=?", (cg_id,))
    p = db.one("SELECT * FROM patients WHERE caregiver_id=?", (cg_id,))
    return {"token": token, "name": cg["name"], "patient": _public_patient(p),
            "setup_done": _setup_done(p["id"]), "first_time": first_time}


@app.post("/auth/signup")
def signup(body: SignupIn):
    name = " ".join(body.name.split())
    if not 2 <= len(name) <= 40:
        raise HTTPException(400, "Please enter your name (2 to 40 letters).")
    if not re.fullmatch(r"\d{4,8}", body.pin):
        raise HTTPException(400, "PIN must be 4 to 8 digits.")
    if auth.find_by_name(name):
        raise HTTPException(400, "That name is already taken. Please log in, or choose a different name.")
    cid = auth.create_caregiver(name, body.pin)
    token = auth.new_session(cid)
    _unlock(token)
    return _session_payload(cid, token, first_time=True)


@app.post("/auth/login")
def login(body: LoginIn):
    key = auth.name_key(body.name)
    if auth.is_locked(key):
        raise HTTPException(429, "Too many wrong PINs. Please wait a minute and try again.")
    cg = auth.find_by_name(body.name)
    if not cg or not auth.pin_matches(cg, body.pin):
        auth.record_fail(key)
        raise HTTPException(401, "Wrong name or PIN.")  # same message either way, so names cannot be guessed
    auth.record_ok(key)
    token = auth.new_session(cg["id"])
    _unlock(token)
    return _session_payload(cg["id"], token)


@app.post("/auth/logout")
def logout(s: dict = Depends(current)):
    auth.end_session(s["token"])
    _unlocked.pop(s["token"], None)
    return {"ok": True}


@app.get("/auth/me")
def me(s: dict = Depends(current)):
    d = _session_payload(s["id"], s["token"])
    d["locked"] = _unlocked.get(s["token"], 0) < time.time()
    return d


@app.post("/auth/verify")
def verify(body: PinIn, s: dict = Depends(current)):
    """Re-enter the PIN to open the caregiver area (the patient screen stays usable without it)."""
    key = auth.name_key(s["name"])
    if auth.is_locked(key):
        raise HTTPException(429, "Too many wrong PINs. Please wait a minute and try again.")
    if not auth.pin_matches(s, body.pin):
        auth.record_fail(key)
        raise HTTPException(401, "Wrong PIN.")
    auth.record_ok(key)
    _unlock(s["token"])
    return {"ok": True}


@app.post("/auth/lock")
def lock(s: dict = Depends(current)):
    _unlocked.pop(s["token"], None)
    return {"ok": True}


# ---------- speech test endpoints (open, for /docs) ----------
@app.post("/transcribe")
async def transcribe(audio_file: UploadFile = File(...), language_code: str = Form("en-IN")):
    """Standalone STT test endpoint (use it in /docs to test kn-IN, hi-IN, ta-IN, en-IN, indic-auto)."""
    audio = await audio_file.read()
    try:
        r = await gnani.transcribe(audio, audio_file.filename or "audio.wav", audio_file.content_type or "", language_code)
    except gnani.GnaniError as e:
        raise HTTPException(e.status if 400 <= e.status < 600 else 502, str(e))
    r.pop("raw", None)
    return {"success": True, "language": language_code, **r}


class SpeakIn(BaseModel):
    text: str
    language: str = "auto"


@app.post("/speak")
async def speak(body: SpeakIn):
    """Standalone TTS test endpoint. Returns a WAV file."""
    try:
        audio, mime, used = await gnani.synthesize(body.text, body.language)
    except gnani.GnaniError as e:
        raise HTTPException(e.status if 400 <= e.status < 600 else 502, str(e))
    return Response(audio, media_type=mime, headers={"X-TTS-Voice": used})


# ---------- the main loop (patient screen; needs a logged-in session) ----------
@app.post("/converse")
async def converse(
    audio_file: UploadFile = File(...),
    language_code: str = Form("auto"),
    s: dict = Depends(current),
):
    """audio in -> Prisma STT -> intent -> approved memory -> safety -> reply -> Timbre TTS -> audio out."""
    audio = await audio_file.read()
    if len(audio) < 500:
        raise HTTPException(400, "Audio is empty or too short")

    stt_lang = "indic-auto" if language_code in ("auto", "indic-auto") else language_code
    try:
        stt = await gnani.transcribe(audio, audio_file.filename or "audio.wav", audio_file.content_type or "", stt_lang)
    except gnani.GnaniError as e:
        raise HTTPException(e.status if 400 <= e.status < 600 else 502, str(e))

    # With a fixed language we reply in that language; with auto we reply in the detected one.
    reply_lang = stt["detected_language"] if stt_lang == "indic-auto" else stt_lang
    result = engine.respond(s["patient"]["id"], stt["transcript"], reply_lang)
    speech = await _speak(result["reply"], result["tts_language"])
    return {"transcript": stt["transcript"], "detected_language": stt["detected_language"], **result, **speech}


class TextIn(BaseModel):
    text: str
    language: str | None = None  # e.g. "kn-IN"; None = patient's preferred language
    speak: bool = True


@app.post("/converse-text")
async def converse_text(body: TextIn, s: dict = Depends(current)):
    """Same pipeline without STT. For testing, and for a 'type instead' fallback."""
    result = engine.respond(s["patient"]["id"], body.text, body.language)
    speech = await _speak(result["reply"], result["tts_language"]) if body.speak else {}
    return {"transcript": body.text, **result, **speech}


# ---------- caregiver API (locked behind the PIN; always scoped to the logged-in caregiver's patient) ----------
RELATIONS = {"daughter", "son", "wife", "husband", "mother", "father", "brother", "sister", "grandchild"}
CATEGORIES = {"food", "song", "place", "hobby", "life_event", "other"}


def _expiry(hours: float | None) -> str | None:
    if not hours:
        return None
    return (datetime.now() + timedelta(hours=hours)).isoformat(timespec="seconds")


def _status_expiry(status: str, hours: float | None, existing: dict | None = None) -> str | None:
    """A "where are they now" status must always expire, otherwise stale news could be spoken forever.
    No status -> no expiry. Hours given -> that long from now. Unchanged status -> keep the current expiry.
    Otherwise default to 6 hours."""
    status = status.strip()
    if not status:
        return None
    if hours:
        return _expiry(hours)
    if existing and (existing.get("status_text") or "").strip() == status and existing.get("status_expires"):
        return existing["status_expires"]
    return _expiry(6)


@app.get("/api/me/full")
def full(s: dict = Depends(caregiver)):
    pid = s["patient"]["id"]
    return {
        "patient": s["patient"],
        "family": db.query("SELECT * FROM family WHERE patient_id=? ORDER BY id", (pid,)),
        "memories": db.query("SELECT * FROM memories WHERE patient_id=? ORDER BY id", (pid,)),
        "reminders": db.query("SELECT * FROM reminders WHERE patient_id=? ORDER BY id", (pid,)),
    }


class PatientIn(BaseModel):
    name: str = ""
    nickname: str = ""
    preferred_language: str = "en-IN"
    location_note: str = ""
    keep_talking: bool = False


@app.put("/api/me/patient")
def update_patient(body: PatientIn, s: dict = Depends(caregiver)):
    if body.preferred_language not in config.SUPPORTED_LANGS:
        raise HTTPException(400, "Unsupported language")
    db.execute(
        "UPDATE patients SET name=?, nickname=?, preferred_language=?, location_note=?, keep_talking=? WHERE id=?",
        (body.name.strip(), body.nickname.strip(), body.preferred_language, body.location_note.strip(),
         1 if body.keep_talking else 0, s["patient"]["id"]),
    )
    return {"ok": True}


class FamilyIn(BaseModel):
    name: str
    relation: str
    description: str = ""
    status_text: str = ""
    status_valid_hours: float | None = None  # how long the status stays valid


@app.post("/api/me/family")
def add_family(body: FamilyIn, s: dict = Depends(caregiver)):
    if body.relation not in RELATIONS:
        raise HTTPException(400, f"relation must be one of {sorted(RELATIONS)}")
    if not body.name.strip():
        raise HTTPException(400, "Name is required")
    new_id = db.execute(
        "INSERT INTO family (patient_id,name,relation,description,status_text,status_expires) VALUES (?,?,?,?,?,?)",
        (s["patient"]["id"], body.name.strip(), body.relation, body.description.strip(), body.status_text.strip(),
         _status_expiry(body.status_text, body.status_valid_hours)),
    )
    return {"id": new_id}


@app.put("/api/family/{item_id}")
def update_family(item_id: int, body: FamilyIn, s: dict = Depends(caregiver)):
    _own("family", item_id, s)
    if body.relation not in RELATIONS:
        raise HTTPException(400, f"relation must be one of {sorted(RELATIONS)}")
    if not body.name.strip():
        raise HTTPException(400, "Name is required")
    existing = db.one("SELECT status_text, status_expires FROM family WHERE id=?", (item_id,))
    db.execute(
        "UPDATE family SET name=?,relation=?,description=?,status_text=?,status_expires=? WHERE id=?",
        (body.name.strip(), body.relation, body.description.strip(), body.status_text.strip(),
         _status_expiry(body.status_text, body.status_valid_hours, existing), item_id),
    )
    return {"ok": True}


class MemoryIn(BaseModel):
    category: str = "other"
    text: str


@app.post("/api/me/memories")
def add_memory(body: MemoryIn, s: dict = Depends(caregiver)):
    if body.category not in CATEGORIES:
        raise HTTPException(400, "Unknown category")
    if not body.text.strip():
        raise HTTPException(400, "Text is required")
    return {"id": db.execute(
        "INSERT INTO memories (patient_id,category,text,created_at) VALUES (?,?,?,?)",
        (s["patient"]["id"], body.category, body.text.strip(), db.now()),
    )}


@app.put("/api/memories/{item_id}")
def update_memory(item_id: int, body: MemoryIn, s: dict = Depends(caregiver)):
    _own("memories", item_id, s)
    if body.category not in CATEGORIES:
        raise HTTPException(400, "Unknown category")
    if not body.text.strip():
        raise HTTPException(400, "Text is required")
    db.execute("UPDATE memories SET category=?, text=? WHERE id=?", (body.category, body.text.strip(), item_id))
    return {"ok": True}


class ReminderIn(BaseModel):
    text: str
    remind_date: str | None = None  # YYYY-MM-DD, empty = every day


@app.post("/api/me/reminders")
def add_reminder(body: ReminderIn, s: dict = Depends(caregiver)):
    if not body.text.strip():
        raise HTTPException(400, "Text is required")
    return {"id": db.execute(
        "INSERT INTO reminders (patient_id,text,remind_date) VALUES (?,?,?)",
        (s["patient"]["id"], body.text.strip(), body.remind_date or None),
    )}


@app.put("/api/reminders/{item_id}")
def update_reminder(item_id: int, body: ReminderIn, s: dict = Depends(caregiver)):
    _own("reminders", item_id, s)
    if not body.text.strip():
        raise HTTPException(400, "Text is required")
    db.execute("UPDATE reminders SET text=?, remind_date=? WHERE id=?", (body.text.strip(), body.remind_date or None, item_id))
    return {"ok": True}


class OnboardIn(BaseModel):
    """The optional 'tell us about the patient' form shown after sign-up. Every field may be empty."""
    name: str = ""
    nickname: str = ""
    preferred_language: str = "en-IN"
    location_note: str = ""
    family_name: str = ""
    family_relation: str = "daughter"
    family_about: str = ""
    food: str = ""
    song: str = ""
    place: str = ""
    hobby: str = ""
    special: str = ""


@app.post("/api/me/onboarding")
def onboarding(body: OnboardIn, s: dict = Depends(caregiver)):
    pid = s["patient"]["id"]
    lang = body.preferred_language if body.preferred_language in config.SUPPORTED_LANGS else "en-IN"
    db.execute(
        "UPDATE patients SET name=?, nickname=?, preferred_language=?, location_note=? WHERE id=?",
        (body.name.strip() or s["patient"]["name"], body.nickname.strip() or s["patient"]["nickname"],
         lang, body.location_note.strip(), pid),
    )
    added = 0
    if body.family_name.strip():
        if body.family_relation not in RELATIONS:
            raise HTTPException(400, f"relation must be one of {sorted(RELATIONS)}")
        db.execute("INSERT INTO family (patient_id,name,relation,description) VALUES (?,?,?,?)",
                   (pid, body.family_name.strip(), body.family_relation, body.family_about.strip()))
        added += 1
    for field in ("food", "song", "place", "hobby", "special"):
        value = getattr(body, field).strip()
        if value:
            db.execute("INSERT INTO memories (patient_id,category,text,created_at) VALUES (?,?,?,?)",
                       (pid, R.MEMORY_CATEGORY[field], R.memory_sentence(lang, field, value), db.now()))
            added += 1
    return {"ok": True, "added": added}


# declared before the generic /api/{table}/{id} routes so "interactions" is not read as a table name
@app.get("/api/me/alerts")
def alerts(s: dict = Depends(caregiver)):
    return db.query("SELECT * FROM alerts WHERE patient_id=? ORDER BY id DESC LIMIT 100", (s["patient"]["id"],))


@app.get("/api/me/interactions")
def interactions(s: dict = Depends(caregiver)):
    return db.query("SELECT * FROM interactions WHERE patient_id=? ORDER BY id DESC LIMIT 50", (s["patient"]["id"],))


@app.delete("/api/me/interactions")
def clear_interactions(s: dict = Depends(caregiver)):
    db.execute("DELETE FROM interactions WHERE patient_id=?", (s["patient"]["id"],))
    return {"ok": True}


@app.post("/api/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, s: dict = Depends(caregiver)):
    _own("alerts", alert_id, s)
    db.execute("UPDATE alerts SET resolved=1 WHERE id=?", (alert_id,))
    return {"ok": True}


TABLES = {"family", "memories", "reminders"}


@app.post("/api/{table}/{item_id}/toggle-approval")
def toggle_approval(table: str, item_id: int, s: dict = Depends(caregiver)):
    """Caregiver can switch an item off without deleting it. Switched-off items are never spoken."""
    if table not in TABLES:
        raise HTTPException(404)
    _own(table, item_id, s)
    db.execute(f"UPDATE {table} SET approved = 1 - approved WHERE id=?", (item_id,))
    return {"ok": True}


@app.delete("/api/{table}/{item_id}")
def delete_item(table: str, item_id: int, s: dict = Depends(caregiver)):
    if table not in TABLES:
        raise HTTPException(404)
    _own(table, item_id, s)
    db.execute(f"DELETE FROM {table} WHERE id=?", (item_id,))
    return {"ok": True}


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse({"detail": str(exc)}, status_code=400)


app.mount("/static", StaticFiles(directory=STATIC), name="static")
