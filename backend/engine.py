"""Conversation engine: intent -> approved-memory lookup -> safety checks -> templated reply -> alerts.

Safety rules enforced here (and covered by tests/test_engine.py):
  * Only rows with approved=1 are ever used.
  * A family status is used only while it has not expired.
  * If nothing approved matches, the reply says it does not know. Nothing is invented.
  * Emergency / help / medicine questions create a caregiver alert and never get ordinary-chat answers.
  * "Yes" to a thirsty / hungry / discomfort check-in creates a caregiver alert.
  * The reply never says a person is present, or that a call or visit is arranged.

Friendliness: ordinary replies get a kind phrase and an invitation to keep talking (a topic the caregiver
has approved, or an open "tell me more"). Every CHECKIN_EVERY-th reply asks a thirsty / hungry / discomfort check-in.
"""
from datetime import date, datetime, timedelta

import config
import db
import intent as intent_mod
import responses as R

ALERT_RULES = {
    "emergency": ("high", "Patient mentioned pain, a fall, breathing trouble or an emergency"),
    "help": ("medium", "Patient asked for help"),
    "medication": ("medium", "Patient asked about medicines (assistant declined to advise)"),
    "distress": ("medium", "Patient expressed fear, loneliness or sadness"),
    "confusion": ("low", "Patient seemed confused about where they are"),
    "call_family": ("medium", "Patient wants to talk to a family member"),
    "hungry": ("medium", "Patient says they are hungry"),
    "thirsty": ("medium", "Patient says they are thirsty"),
    "discomfort": ("medium", "Patient says something is bothering or hurting them"),
}
REPEAT_LIMIT = 3          # same question this many times within 30 minutes -> low alert
PENDING_MINUTES = 10      # how long a yes/no check-in question stays open
CHECKS = ["thirsty", "hungry", "comfort"]
# replies that get kindness + a follow-up (never emergencies, alerts or error-like replies)
SOFT = {"topic_reply", "greeting", "general", "reassure", "family_who", "food", "song", "place", "hobby",
        "memory", "reminder", "checkin_ok"}


# The last "Shall we talk about ...?" question asked to each patient, so a plain "yes" / "no" can be understood.
# Kept in memory only (it is only useful for a few minutes anyway).
TOPIC_MINUTES = 10
_open_topic: dict[int, tuple] = {}


def _take_topic(patient_id: int):
    """Returns (kind, value) of the open invitation and closes it. kind: 'cat', 'name' or 'more'."""
    item = _open_topic.pop(patient_id, None)
    if not item or item[2] < datetime.now() - timedelta(minutes=TOPIC_MINUTES):
        return None
    return item[0], item[1]


def _alert(patient_id: int, level: str, reason: str, transcript: str) -> None:
    db.execute(
        "INSERT INTO alerts (patient_id, ts, level, reason, transcript) VALUES (?,?,?,?,?)",
        (patient_id, db.now(), level, reason, transcript),
    )


def _status_if_valid(person: dict) -> str:
    status = (person.get("status_text") or "").strip()
    if not status:
        return ""
    expires = person.get("status_expires")
    if expires:
        try:
            if datetime.fromisoformat(expires) < datetime.now():
                return ""  # stale information is never used
        except ValueError:
            return ""
    return status


def _memories(patient_id: int, categories: list[str], limit: int = 2) -> list[str]:
    marks = ",".join("?" * len(categories))
    rows = db.query(
        f"SELECT text FROM memories WHERE patient_id=? AND approved=1 AND category IN ({marks}) "
        "ORDER BY id LIMIT ?",
        (patient_id, *categories, limit),
    )
    return [r["text"] for r in rows]


def _reminders(patient_id: int, day_offset: int = 0) -> list[str]:
    today = (date.today() + timedelta(days=day_offset)).isoformat()
    rows = db.query(
        "SELECT text FROM reminders WHERE patient_id=? AND approved=1 "
        "AND (remind_date IS NULL OR remind_date='' OR remind_date=?) ORDER BY id LIMIT 3",
        (patient_id, today),
    )
    return [r["text"] for r in rows]


def _is_repeat(patient_id: int, intent: str, subject: str) -> bool:
    since = (datetime.now() - timedelta(minutes=30)).isoformat(timespec="seconds")
    rows = db.query(
        "SELECT id FROM interactions WHERE patient_id=? AND intent=? AND subject=? AND ts>=?",
        (patient_id, intent, subject, since),
    )
    return len(rows) + 1 >= REPEAT_LIMIT


def _pending_check(patient: dict) -> str:
    """The yes/no check-in question still waiting for an answer, or ''."""
    kind = patient.get("pending_check") or ""
    asked = patient.get("last_checkin_at")
    if not kind or not asked:
        return ""
    try:
        if datetime.fromisoformat(asked) < datetime.now() - timedelta(minutes=PENDING_MINUTES):
            return ""
    except ValueError:
        return ""
    return kind


def _checkin_due(patient: dict, replies_so_far: int) -> str | None:
    """Every CHECKIN_EVERY replies (counting this one) ask the next check in the rotation."""
    if config.CHECKIN_EVERY <= 0:
        return None
    if replies_so_far + 1 >= config.CHECKIN_EVERY * (patient["checkin_count"] + 1):
        return CHECKS[patient["checkin_count"] % len(CHECKS)]
    return None


def _topics(patient_id: int, lang: str, skip_categories: list[str], skip_name: str) -> list[tuple]:
    """Things we could invite the patient to talk about: (spoken label, kind, value)."""
    cats = db.query("SELECT DISTINCT category FROM memories WHERE patient_id=? AND approved=1 ORDER BY category", (patient_id,))
    topics = [(R.topic_phrase(lang, c["category"]), "cat", c["category"]) for c in cats if c["category"] not in skip_categories]
    names = db.query("SELECT name FROM family WHERE patient_id=? AND approved=1 ORDER BY id", (patient_id,))
    topics += [(n["name"], "name", n["name"]) for n in names if n["name"].lower() != (skip_name or "").lower()]
    return topics


def _follow_up(patient_id: int, lang: str, idx: int, topics: list[tuple]) -> str:
    """Invite the patient to keep talking, and remember what we offered so their "yes" makes sense."""
    if topics and idx % 2 == 0:
        label, kind, value = topics[(idx // 2) % len(topics)]
        _open_topic[patient_id] = (kind, value, datetime.now())
        return R.render(lang, "topic_q", topic=label)
    _open_topic[patient_id] = ("more", "", datetime.now())
    return R.pick(lang, "more", idx)


def respond(patient_id: int, transcript: str, detected_lang: str | None = None) -> dict:
    """Returns {reply, intent, language, tts_language, alert_level}."""
    patient = db.one("SELECT * FROM patients WHERE id=?", (patient_id,))
    if not patient:
        raise ValueError("Unknown patient")

    # Reply in the language the patient actually spoke, if it is one we support.
    lang = detected_lang if detected_lang in R.LANGS else patient["preferred_language"]
    if lang not in R.LANGS:
        lang = "en-IN"
    if lang == "en-IN":
        # Tamil, Hindi or Kannada written in English letters (Tanglish / Hinglish / Kanglish): answer in that language
        lang = intent_mod.romanised_lang(transcript, patient["preferred_language"]) or lang

    family = db.query("SELECT * FROM family WHERE patient_id=? AND approved=1", (patient_id,))
    found = intent_mod.detect(transcript, family)
    intent, person, subject = found["intent"], found["person"], found["subject"]

    pname = (patient.get("nickname") or patient.get("name") or "").strip() or R.friend(lang)
    has_name = bool((patient.get("nickname") or patient.get("name") or "").strip())
    replies_so_far = db.one("SELECT COUNT(*) AS n FROM interactions WHERE patient_id=?", (patient_id,))["n"]
    idx = replies_so_far

    free_text = False  # True when caregiver-written text is spoken (its language may differ from lang)
    alert_level = alert_reason = None
    skip_categories: list[str] = []

    # ---- was the patient answering a check-in question ("Are you thirsty?" -> "yes")? ----
    pending = _pending_check(patient)
    answer = None
    if pending:
        asked_intent = {"thirsty": "thirsty", "hungry": "hungry", "comfort": None}[pending]
        if intent == "general" or (asked_intent and intent == asked_intent):
            answer = intent_mod.yes_no(transcript)
        db.execute("UPDATE patients SET pending_check='' WHERE id=?", (patient_id,))  # question is closed either way
        patient["pending_check"] = ""

    # ---- was the patient answering "Shall we talk about ...?" / "Would you like to tell me more?" ----
    offered = _take_topic(patient_id)
    topic_yn = intent_mod.yes_no(transcript) if (offered and answer is None and intent == "general") else None

    if topic_yn == "yes" and offered[0] == "cat":
        intent = "topic_reply"
        skip_categories = [offered[1]]
        items = _memories(patient_id, skip_categories)
        if items:
            reply, free_text = R.render(lang, "memory_found", items=" ".join(items)), True
        else:
            reply = R.render(lang, "topic_yes")
    elif topic_yn == "yes" and offered[0] == "name":
        intent, subject = "topic_reply", offered[1]
        who = db.one("SELECT * FROM family WHERE patient_id=? AND approved=1 AND lower(name)=lower(?)", (patient_id, offered[1]))
        desc = ((who or {}).get("description") or "").strip()
        if who and desc:
            reply = R.render(lang, "family_who", rel=R.relation_phrase(lang, who["relation"]), fname=who["name"], desc=desc)
            free_text = True
        else:
            reply = R.render(lang, "topic_yes")
    elif topic_yn == "yes":
        intent = "topic_reply"
        reply = R.render(lang, "topic_yes")
    elif topic_yn == "no":
        intent = "topic_reply"
        reply = R.render(lang, "topic_no")

    elif answer == "yes":
        intent = {"thirsty": "thirsty", "hungry": "hungry", "comfort": "discomfort"}[pending]
        reply = R.render(lang, f"{pending}_yes")
    elif answer == "no":
        intent = "checkin_ok"
        reply = R.render(lang, f"{pending}_no")

    elif intent in ("family_where", "family_who", "call_family") and person and person.get("missing"):
        # Patient asked about a relation that has no approved record.
        rel = R.relation_phrase(lang, person["relation"])
        reply = R.render(lang, "family_missing", rel=rel)
        alert_level, alert_reason = "low", f"Patient asked about their {person['relation']} but no approved details exist"

    elif intent == "family_where":
        rel = R.relation_phrase(lang, person["relation"])
        status = _status_if_valid(person)
        if status:
            reply = R.render(lang, "family_where_ok", rel=rel, fname=person["name"], status=status)
            free_text = True
        else:
            reply = R.render(lang, "family_where_unknown", rel=rel, fname=person["name"])
            alert_level, alert_reason = "low", f"Patient asked where {person['name']} is; no current approved status"

    elif intent == "family_who":
        rel = R.relation_phrase(lang, person["relation"])
        desc = (person.get("description") or "").strip()
        reply = R.render(lang, "family_who", rel=rel, fname=person["name"], desc=desc)
        free_text = bool(desc)

    elif intent == "call_family":
        reply = R.render(lang, "call_family", fname=person["name"] or R.relation_phrase(lang, person["relation"]))

    elif intent in intent_mod.INTENT_TO_CATEGORIES:
        skip_categories = intent_mod.INTENT_TO_CATEGORIES[intent]
        items = _memories(patient_id, skip_categories)
        if items:
            reply = R.render(lang, "memory_found", items=" ".join(items))
            free_text = True
        else:
            reply = R.render(lang, "unknown")

    elif intent == "reminder":
        tomorrow = intent_mod.asks_tomorrow(transcript)
        items = _reminders(patient_id, 1 if tomorrow else 0)
        if items:
            reply = R.render(lang, "reminder_tomorrow" if tomorrow else "reminder_found", items="; ".join(i.strip().rstrip(".।") for i in items))
            free_text = True
        else:
            reply = R.render(lang, "reminder_tomorrow_none" if tomorrow else "reminder_none")

    elif intent == "confusion":
        reply = R.render(lang, "confusion", loc=(patient.get("location_note") or "").strip())
        free_text = bool((patient.get("location_note") or "").strip())

    elif intent == "who_am_i":
        # "What is my name?" -> the real name, not the pet name the assistant uses to greet them
        real_name = (patient.get("name") or patient.get("nickname") or "").strip()
        reply = R.render(lang, "who_am_i", pname=real_name) if real_name else R.render(lang, "who_am_i_unknown")

    elif intent in ("hungry", "thirsty"):
        reply = R.render(lang, f"{intent}_yes")

    elif intent == "checkin_ok":  # "I am not hungry / not thirsty" said on their own
        reply = R.render(lang, "hungry_no")

    elif intent in ("emergency", "help", "medication", "distress", "reassure", "greeting", "empty"):
        reply = R.render(lang, intent, pname=pname, emergency=config.EMERGENCY_NUMBER)

    else:  # general: never guess
        reply = R.render(lang, "unknown")

    if intent in ALERT_RULES and not alert_level:
        alert_level, alert_reason = ALERT_RULES[intent]

    # ---- warmth: kind words, calming, invitations to keep talking, periodic check-ins ----
    topics = _topics(patient_id, lang, skip_categories, subject)
    if intent == "distress":
        reply += " " + R.render(lang, "calm") + " " + _follow_up(patient_id, lang, idx, topics)
    elif intent == "confusion":
        reply += " " + _follow_up(patient_id, lang, idx, topics)
    elif intent in SOFT and not alert_level:
        check = _checkin_due(patient, replies_so_far) if intent != "checkin_ok" else None
        if check:
            reply += " " + R.render(lang, f"ask_{check}")
            db.execute(
                "UPDATE patients SET pending_check=?, checkin_count=checkin_count+1, last_checkin_at=? WHERE id=?",
                (check, db.now(), patient_id),
            )
        else:
            if idx % 2 == 0 and intent != "general":
                reply += " " + R.pick(lang, "kind", idx // 2)
            reply += " " + _follow_up(patient_id, lang, idx, topics)

    if intent not in ("empty", "general") and _is_repeat(patient_id, intent, subject) and not alert_level:
        alert_level, alert_reason = "low", f"Patient has asked the same question several times ({intent}: {subject or 'n/a'})"

    if alert_level:
        _alert(patient_id, alert_level, alert_reason, transcript)

    reply = " ".join(reply.split())
    db.execute(
        "INSERT INTO interactions (patient_id, ts, language, transcript, intent, subject, reply) VALUES (?,?,?,?,?,?,?)",
        (patient_id, db.now(), lang, transcript, intent, subject, reply),
    )

    return {
        "reply": reply,
        "intent": intent,
        "language": lang,
        # caregiver text may be in any language/script, so let Timbre detect it from the script
        "tts_language": "auto" if free_text else lang,
        "alert_level": alert_level,
    }
