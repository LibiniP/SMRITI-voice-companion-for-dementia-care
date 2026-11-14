"""Run from the backend folder:  python -m pytest tests -q
Tests accounts, safety behaviour and the friendly check-ins with synthetic data. Gnani is mocked, so no credits are used."""
import os
import sys
import tempfile
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "t.db")
os.environ["SEED_DEMO_DATA"] = "0"

import pytest
from fastapi.testclient import TestClient

import auth
import config
import db
import engine
import gnani_client
import main


@pytest.fixture(autouse=True)
def fresh_db(monkeypatch):
    config.DB_PATH = os.path.join(tempfile.mkdtemp(), "t.db")
    config.CHECKIN_EVERY = 3
    db.reset_connection()
    auth._fails.clear()
    main._unlocked.clear()
    db.seed_demo_data()  # demo caregiver (id 1) with patient Lakshmi (id 1)

    async def fake_tts(text, language="auto"):
        return b"RIFFfake", "audio/wav", "mock/voice"

    async def fake_stt(audio, filename, ctype, lang):
        return {"transcript": "Where is my daughter?", "detected_language": "en-IN", "model": "mock", "request_id": "x", "raw": {}}

    monkeypatch.setattr(gnani_client, "synthesize", fake_tts)
    monkeypatch.setattr(gnani_client, "transcribe", fake_stt)
    yield


def say(text, lang="en-IN", pid=1):
    return engine.respond(pid, text, lang)


def alerts(pid=1):
    return db.query("SELECT * FROM alerts WHERE patient_id=?", (pid,))


def no_checkins():
    config.CHECKIN_EVERY = 0  # keep the safety tests about one thing at a time


# ---------------------------------------------------------------- safety (unchanged rules)
def test_daughter_status_used_when_valid():
    no_checkins()
    db.execute("UPDATE family SET status_expires=? WHERE name='Priya'", ((datetime.now() + timedelta(hours=2)).isoformat(),))
    r = say("Where is my daughter?")
    assert r["intent"] == "family_where" and "at work" in r["reply"]


def test_expired_status_is_not_used():
    no_checkins()
    db.execute("UPDATE family SET status_expires=? WHERE name='Priya'", ((datetime.now() - timedelta(hours=1)).isoformat(),))
    r = say("Where is my daughter?")
    assert "at work" not in r["reply"] and "do not know" in r["reply"]


def test_disabled_item_never_spoken():
    no_checkins()
    db.execute("UPDATE memories SET approved=0 WHERE category='food'")
    r = say("What is my favourite food?")
    assert "dosa" not in r["reply"] and "not sure" in r["reply"]


def test_unknown_question_does_not_invent():
    no_checkins()
    r = say("What is the name of my childhood dog?")
    assert "not sure" in r["reply"] or "teacher" in r["reply"]
    assert "dog" not in r["reply"].lower().replace("childhood dog", "")


def test_missing_relation_says_no_details():
    no_checkins()
    assert "do not have details" in say("Where is my wife?")["reply"]


def test_emergency_creates_high_alert_and_no_chitchat():
    r = say("I have chest pain")
    assert r["intent"] == "emergency" and r["alert_level"] == "high"
    assert config.EMERGENCY_NUMBER in r["reply"]
    assert "lovely" not in r["reply"] and "Shall we" not in r["reply"]  # no cheerful add-ons in an emergency


def test_medication_is_refused():
    r = say("Should I take another tablet?")
    assert r["intent"] == "medication" and "cannot give advice" in r["reply"] and r["alert_level"] == "medium"


def test_call_request_does_not_promise_a_call():
    no_checkins()
    r = say("I want to talk to my daughter")
    assert r["intent"] == "call_family" and "tell your caregiver" in r["reply"]
    assert "calling" not in r["reply"].lower() and "is coming" not in r["reply"].lower()


def test_repeated_question_raises_alert():
    no_checkins()
    for _ in range(3):
        say("Who is my son?")
    assert any("same question" in a["reason"] for a in alerts())


@pytest.mark.parametrize("text,lang,expected", [
    ("मेरी बेटी कहाँ है?", "hi-IN", "family_where"),
    ("ನನ್ನ ಮಗಳು ಎಲ್ಲಿ?", "kn-IN", "family_where"),
    ("என் மகள் எங்கே?", "ta-IN", "family_where"),
    ("मुझे सीने में दर्द है", "hi-IN", "emergency"),
    ("ನನಗೆ ಭಯ ಆಗ್ತಿದೆ", "kn-IN", "distress"),
    ("நான் என் மகளிடம் பேச வேண்டும்", "ta-IN", "call_family"),
    ("मेरा पसंदीदा खाना क्या है?", "hi-IN", "food"),
    ("मुझे भूख लगी है", "hi-IN", "hungry"),
    ("ನನಗೆ ಬಾಯಾರಿಕೆ ಆಗ್ತಿದೆ", "kn-IN", "thirsty"),
    ("எனக்கு தாகமாக இருக்கிறது", "ta-IN", "thirsty"),
    ("எனக்கு பயமாக இருக்கிறது", "ta-IN", "distress"),     # Tamil adds endings: பயம் -> பயமாக
    ("எனக்கு பசிக்கிறது", "ta-IN", "hungry"),
    ("இன்று என்ன திட்டம்?", "ta-IN", "reminder"),
])
def test_multilingual_intents(text, lang, expected):
    no_checkins()
    assert say(text, lang)["intent"] == expected


def test_reply_language_follows_detected_language():
    no_checkins()
    assert "ನಿಮ್ಮ ಮಗಳು" in say("ನನ್ನ ಮಗಳು ಎಲ್ಲಿ?", "kn-IN")["reply"]


# ---------------------------------------------------------------- friendliness + check-ins
def test_normal_replies_are_kind_and_invite_more_talk():
    no_checkins()
    r = say("What is my favourite food?")
    assert "dosa" in r["reply"]
    assert any(w in r["reply"] for w in ("lovely", "happy", "Shall we", "tell me more", "on your mind", "listening"))


def test_distress_gets_comfort_and_alert():
    no_checkins()
    r = say("I am scared and alone")
    assert r["intent"] == "distress" and r["alert_level"] == "medium"
    assert "deep breath" in r["reply"] and "Shall we" in r["reply"] or "tell me more" in r["reply"] or "on your mind" in r["reply"]


def test_statement_i_am_hungry_alerts_caregiver():
    r = say("I am hungry")
    assert r["intent"] == "hungry" and r["alert_level"] == "medium"
    assert any("hungry" in a["reason"] for a in alerts())


def test_not_hungry_does_not_alert():
    no_checkins()
    r = say("I am not hungry")
    assert r["intent"] != "hungry" and not alerts()


def test_every_third_reply_asks_a_checkin_then_yes_alerts():
    say("Hello")
    say("What is my favourite food?")
    r = say("Tell me about my son")          # 3rd reply -> first check-in (thirsty)
    assert "thirsty" in r["reply"]
    assert db.one("SELECT pending_check FROM patients WHERE id=1")["pending_check"] == "thirsty"
    r = say("yes")
    assert r["intent"] == "thirsty" and r["alert_level"] == "medium" and "water" in r["reply"]
    assert any("thirsty" in a["reason"] for a in alerts())
    assert db.one("SELECT pending_check FROM patients WHERE id=1")["pending_check"] == ""


def test_checkin_no_means_no_alert_and_conversation_continues():
    say("Hello"); say("What is my favourite food?"); say("Tell me about my son")
    r = say("no")
    assert r["intent"] == "checkin_ok" and "good" in r["reply"].lower() and not alerts()


def test_checkin_rotation_thirsty_hungry_comfort():
    asked = []
    for i in range(12):
        for text in ("hello", "no"):             # a check-in can land on either turn
            r = say(text)
            for kind, word in (("thirsty", "thirsty"), ("hungry", "hungry"), ("comfort", "bothering")):
                if word in r["reply"] and r["reply"].rstrip().endswith("?"):
                    asked.append(kind)
    assert asked[:3] == ["thirsty", "hungry", "comfort"]


def test_comfort_yes_alerts():
    for _ in range(2):
        say("hello"); say("no")                 # burn two check-ins (thirsty, hungry) with "no"
    db.execute("UPDATE patients SET checkin_count=2 WHERE id=1")
    config.CHECKIN_EVERY = 1
    r = say("hello")
    assert "bothering" in r["reply"]
    r = say("yes")
    assert r["intent"] == "discomfort" and any("bothering or hurting" in a["reason"] for a in alerts())


def test_hindi_yes_to_checkin():
    say("hello", "hi-IN"); say("मेरा पसंदीदा खाना क्या है?", "hi-IN"); r = say("मेरा बेटा कौन है?", "hi-IN")
    assert "प्यास" in r["reply"]
    r = say("हाँ", "hi-IN")
    assert r["intent"] == "thirsty" and r["alert_level"] == "medium"


def test_unrelated_reply_closes_the_question_so_a_later_yes_is_not_misread():
    say("hello"); say("What is my favourite food?"); say("Tell me about my son")   # thirsty asked
    say("What is my favourite song?")                                              # patient moved on
    r = say("yes")
    assert r["intent"] != "thirsty" and not alerts()


def test_no_name_is_handled_politely():
    cid = auth.create_caregiver("Newbie", "4321")
    pid = db.one("SELECT id FROM patients WHERE caregiver_id=?", (cid,))["id"]
    config.CHECKIN_EVERY = 0
    r = say("Hello", pid=pid)
    assert "friend" in r["reply"]
    assert "do not know your name" in say("Who am I?", pid=pid)["reply"]
    assert "not sure" in say("What is my favourite food?", pid=pid)["reply"]   # empty profile: nothing invented


# ---------------------------------------------------------------- accounts and isolation
def client():
    return TestClient(main.app)


def signup(c, name, pin="4321"):
    r = c.post("/auth/signup", json={"name": name, "pin": pin})
    assert r.status_code == 200, r.text
    return r.json()


def H(token):
    return {"X-Auth-Token": token}


def test_signup_login_and_wrong_pin():
    c = client()
    d = signup(c, "Meera")
    assert d["first_time"] and d["token"] and d["setup_done"] is False
    assert c.post("/auth/signup", json={"name": "meera", "pin": "9999"}).status_code == 400      # name taken (any case)
    assert c.post("/auth/signup", json={"name": "Bob", "pin": "12"}).status_code == 400          # PIN too short
    assert c.post("/auth/login", json={"name": "Meera", "pin": "0000"}).status_code == 401
    ok = c.post("/auth/login", json={"name": "MEERA", "pin": "4321"})
    assert ok.status_code == 200 and not ok.json()["first_time"]


def test_pin_is_not_stored_in_plain_text():
    signup(client(), "Hash Test", "7777")
    row = db.one("SELECT * FROM caregivers WHERE name_key='hash test'")
    assert "7777" not in str(row.values())


def test_five_wrong_pins_lock_the_account():
    c = client()
    signup(c, "Locky")
    for _ in range(5):
        assert c.post("/auth/login", json={"name": "Locky", "pin": "0000"}).status_code == 401
    assert c.post("/auth/login", json={"name": "Locky", "pin": "4321"}).status_code == 429


def test_each_caregiver_sees_only_their_own_patient():
    c = client()
    a = signup(c, "Alice")
    b = signup(c, "Bob")
    c.post("/api/me/family", headers=H(a["token"]), json={"name": "Zoya", "relation": "daughter"})
    assert [f["name"] for f in c.get("/api/me/full", headers=H(a["token"])).json()["family"]] == ["Zoya"]
    assert c.get("/api/me/full", headers=H(b["token"])).json()["family"] == []
    fid = c.get("/api/me/full", headers=H(a["token"])).json()["family"][0]["id"]
    assert c.delete(f"/api/family/{fid}", headers=H(b["token"])).status_code == 404            # cannot touch another account's data
    # and the assistant for Bob does not know Alice's daughter
    r = c.post("/converse-text", headers=H(b["token"]), json={"text": "Who is my daughter?", "speak": False}).json()
    assert "Zoya" not in r["reply"] and "do not have details" in r["reply"]


def test_login_required_for_everything_personal():
    c = client()
    assert c.post("/converse-text", json={"text": "hi"}).status_code == 401
    assert c.get("/api/me/full").status_code == 401
    assert c.get("/auth/me").status_code == 401


def test_caregiver_area_locks_and_pin_reopens_it():
    c = client()
    d = signup(c, "Lena")
    t = d["token"]
    assert c.get("/api/me/alerts", headers=H(t)).status_code == 200
    main._unlocked[t] = time.time() - 1                                  # 10 minutes later
    assert c.get("/api/me/alerts", headers=H(t)).status_code == 403
    assert c.post("/converse-text", headers=H(t), json={"text": "hello", "speak": False}).status_code == 200   # patient screen still works
    assert c.post("/auth/verify", headers=H(t), json={"pin": "0000"}).status_code == 401
    assert c.post("/auth/verify", headers=H(t), json={"pin": "4321"}).status_code == 200
    assert c.get("/api/me/alerts", headers=H(t)).status_code == 200


def test_onboarding_is_optional_and_builds_sentences_in_patient_language():
    c = client()
    t = signup(c, "Kavya")["token"]
    r = c.post("/api/me/onboarding", headers=H(t), json={})                 # "do it later" style: nothing filled
    assert r.status_code == 200 and r.json()["added"] == 0
    r = c.post("/api/me/onboarding", headers=H(t), json={
        "name": "Amma", "preferred_language": "kn-IN", "family_name": "Ravi", "family_relation": "son", "food": "ದೋಸೆ"})
    assert r.json()["added"] == 2
    full = c.get("/api/me/full", headers=H(t)).json()
    assert full["patient"]["preferred_language"] == "kn-IN"
    assert any(m["text"] == "ನಿಮ್ಮ ಇಷ್ಟದ ಊಟ ದೋಸೆ." for m in full["memories"])
    config.CHECKIN_EVERY = 0
    reply = c.post("/converse-text", headers=H(t), json={"text": "ನನ್ನ ಇಷ್ಟದ ಊಟ ಏನು?", "language": "kn-IN", "speak": False}).json()["reply"]
    assert "ದೋಸೆ" in reply
    assert c.get("/auth/me", headers=H(t)).json()["setup_done"] is True


def test_full_http_voice_flow():
    c = client()
    t = c.post("/auth/login", json={"name": "demo", "pin": "1234"}).json()["token"]
    r = c.post("/converse", headers=H(t), files={"audio_file": ("a.wav", b"0" * 2000, "audio/wav")}, data={"language_code": "en-IN"})
    assert r.status_code == 200 and r.json()["audio_base64"]
    assert c.get("/").status_code == 200


def test_reminder_with_trailing_full_stop_is_not_doubled():
    no_checkins()
    r = say("What is planned today?")
    assert ".." not in r["reply"]


# ---------------------------------------------------------------- editing from the caregiver page
def test_edit_family_memory_reminder_and_status_expiry_rules():
    c = client()
    t = signup(c, "Editor")["token"]
    h = H(t)
    fid = c.post("/api/me/family", headers=h, json={"name": "Asha", "relation": "daughter",
                 "status_text": "is at work", "status_valid_hours": 2}).json()["id"]
    before = c.get("/api/me/full", headers=h).json()["family"][0]["status_expires"]
    # editing only the description must NOT remove or extend the status expiry
    c.put(f"/api/family/{fid}", headers=h, json={"name": "Asha", "relation": "daughter", "description": "Kind and funny.",
          "status_text": "is at work"})
    row = c.get("/api/me/full", headers=h).json()["family"][0]
    assert row["description"] == "Kind and funny." and row["status_expires"] == before
    # a changed status with no hours given defaults to an expiry (never "forever")
    c.put(f"/api/family/{fid}", headers=h, json={"name": "Asha", "relation": "daughter", "status_text": "is at the shop"})
    row = c.get("/api/me/full", headers=h).json()["family"][0]
    assert row["status_text"] == "is at the shop" and row["status_expires"]
    # clearing the status clears the expiry
    c.put(f"/api/family/{fid}", headers=h, json={"name": "Asha", "relation": "daughter", "status_text": ""})
    row = c.get("/api/me/full", headers=h).json()["family"][0]
    assert row["status_text"] == "" and row["status_expires"] is None
    # memory + reminder edits
    mid = c.post("/api/me/memories", headers=h, json={"category": "food", "text": "Your favourite food is dosa."}).json()["id"]
    assert c.put(f"/api/memories/{mid}", headers=h, json={"category": "song", "text": "You love old songs."}).status_code == 200
    rid = c.post("/api/me/reminders", headers=h, json={"text": "Tea at five."}).json()["id"]
    assert c.put(f"/api/reminders/{rid}", headers=h, json={"text": "Tea at four.", "remind_date": "2030-01-01"}).status_code == 200
    full = c.get("/api/me/full", headers=h).json()
    assert full["memories"][0]["category"] == "song" and full["memories"][0]["text"] == "You love old songs."
    assert full["reminders"][0]["text"] == "Tea at four." and full["reminders"][0]["remind_date"] == "2030-01-01"
    # another caregiver cannot edit these
    other = signup(c, "Outsider")["token"]
    assert c.put(f"/api/memories/{mid}", headers=H(other), json={"category": "food", "text": "hacked"}).status_code == 404
    assert c.put(f"/api/reminders/{rid}", headers=H(other), json={"text": "hacked"}).status_code == 404
    assert c.put(f"/api/family/{fid}", headers=H(other), json={"name": "x", "relation": "son"}).status_code == 404


def test_not_hungry_is_calm_and_does_not_alert():
    no_checkins()
    r = say("I am not hungry")
    assert r["intent"] == "checkin_ok" and "good" in r["reply"].lower() and not alerts()
    r = say("मुझे भूख नहीं है", "hi-IN")
    assert r["intent"] == "checkin_ok" and not alerts()


def test_tamil_persona_end_to_end():
    """A fictional Tamil-speaking patient set up through the real endpoints, then spoken to in Tamil."""
    c = client()
    t = signup(c, "Meena", "1357")["token"]
    h = H(t)
    r = c.post("/api/me/onboarding", headers=h, json={
        "name": "கமலா சுப்பிரமணியன்", "nickname": "அம்மா", "preferred_language": "ta-IN",
        "location_note": "நீங்கள் மதுரையில் உங்கள் வீட்டில் இருக்கிறீர்கள்.",
        "family_name": "கார்த்திக்", "family_relation": "son", "family_about": "அவர் சென்னையில் இருக்கிறார். அவர் உங்களை மிகவும் நேசிக்கிறார்.",
        "food": "இட்லி மற்றும் சாம்பார்", "song": "பழைய தமிழ் சினிமா பாடல்களை",
        "place": "வீட்டருகே உள்ள பிள்ளையார் கோவிலுக்கு", "hobby": "தோட்டத்தில் மல்லிகைப் பூ வளர்ப்பது",
        "special": "நீங்கள் முப்பது ஆண்டுகள் பள்ளியில் தமிழ் ஆசிரியராக இருந்தீர்கள்."})
    assert r.json()["added"] == 6
    c.post("/api/me/family", headers=h, json={"name": "மீனா", "relation": "daughter",
           "description": "உங்கள் மகள். அவர் ஒவ்வொரு ஞாயிற்றுக்கிழமையும் உங்களைப் பார்க்க வருவார்.",
           "status_text": "வேலையில் இருக்கிறார், மாலையில் வீட்டுக்கு வருவார்", "status_valid_hours": 6})
    config.CHECKIN_EVERY = 0

    def ask(text):
        return c.post("/converse-text", headers=h, json={"text": text, "language": "ta-IN", "speak": False}).json()

    assert "இட்லி மற்றும் சாம்பார்" in ask("எனக்கு பிடித்த உணவு என்ன?")["reply"]
    d = ask("என் மகள் எங்கே?"); assert d["intent"] == "family_where" and "வேலையில் இருக்கிறார்" in d["reply"] and "மீனா" in d["reply"]
    d = ask("என் மகன் யார்?"); assert d["intent"] == "family_who" and "கார்த்திக்" in d["reply"] and "சென்னை" in d["reply"]
    assert ask("என் பெயர் என்ன?")["reply"].startswith("உங்கள் பெயர் கமலா சுப்பிரமணியன்")   # real name, not the nickname
    d = ask("எனக்கு பயமாக இருக்கிறது"); assert d["intent"] == "distress" and d["alert_level"] == "medium"
    d = ask("எனக்கு தாகமாக இருக்கிறது"); assert d["intent"] == "thirsty" and d["alert_level"] == "medium"
    d = ask("எனக்கு நெஞ்சு வலிக்கிறது"); assert d["intent"] == "emergency" and d["alert_level"] == "high"
    d = ask("நான் எங்கே இருக்கிறேன்?"); assert "மதுரை" in d["reply"]
    d = ask("என் செல்லப் பிராணியின் பெயர் என்ன?"); assert "உறுதியாகத் தெரியவில்லை" in d["reply"]   # never invents a pet


# ---------------------------------------------------------------- Tanglish (Tamil in English letters)
@pytest.mark.parametrize("text,expected", [
    ("vanakkam", "greeting"), ("en magal enga?", "family_where"), ("en magan yaaru?", "family_who"),
    ("enakku pasikkuthu", "hungry"), ("enakku dhagama irukku", "thirsty"), ("enakku payama irukku", "distress"),
    ("naan thaniya irukken", "distress"), ("naan enga irukken?", "confusion"), ("enakku nenju valikkuthu", "emergency"),
    ("enakku mayakkama irukku", "emergency"), ("enakku marundhu venum", "medication"), ("enakku udhavi venum", "help"),
    ("enakku pidicha unavu enna?", "food"), ("naan en magalitta pesanum", "call_family"),
    ("my daughter enga irukka", "family_where"), ("enakku pasi illa", "checkin_ok"),
])
def test_tanglish_intents(text, expected):
    no_checkins()
    assert say(text)["intent"] == expected


def test_tanglish_emergency_alerts_and_replies_in_tamil():
    r = say("enakku nenju valikkuthu")             # Detected/typed as English, but it is Tamil in English letters
    assert r["intent"] == "emergency" and r["alert_level"] == "high"
    assert r["language"] == "ta-IN" and "112" in r["reply"] and "உங்கள் பராமரிப்பாளருக்கு" in r["reply"]


def test_plain_english_is_not_mistaken_for_tanglish():
    no_checkins()
    for text in ["Where is my daughter?", "I am engaged to be married", "I feel dizzy", "Hello"]:
        assert say(text)["language"] == "en-IN"


def test_tanglish_yes_to_a_checkin_alerts():
    say("hello"); say("What is my favourite food?"); r = say("Tell me about my son")
    assert "thirsty" in r["reply"]
    r = say("aama")
    assert r["intent"] == "thirsty" and r["alert_level"] == "medium"


# ---------------------------------------------------------------- tomorrow vs today reminders
def test_tomorrow_question_uses_tomorrows_reminders_only():
    from datetime import date, timedelta
    import db
    no_checkins()
    tom = (date.today() + timedelta(days=1)).isoformat()
    db.execute("DELETE FROM reminders WHERE patient_id=1")
    db.execute("INSERT INTO reminders (patient_id, text, remind_date, approved) VALUES (1,'Doctor visit at ten.',?,1)", (tom,))
    db.execute("INSERT INTO reminders (patient_id, text, remind_date, approved) VALUES (1,'Tea at five.',NULL,1)")
    r = say("What is the plan tomorrow?")
    assert "Doctor visit" in r["reply"] and "Tomorrow" in r["reply"] and "Tea at five" in r["reply"]  # every-day items apply too
    r = say("What is the plan today?")
    assert "Tea at five" in r["reply"] and "Doctor visit" not in r["reply"]


def test_tomorrow_words_in_other_languages():
    no_checkins()
    for text, lang in [("நாளை என்ன திட்டம்?", "ta-IN"), ("ನಾಳೆ ಏನು ಯೋಜನೆ?", "kn-IN"), ("कल क्या योजना है?", "hi-IN"), ("naalai enna plan?", "en-IN")]:
        assert say(text, lang)["intent"] == "reminder", text


# ---------------------------------------------------------------- keep talking switch
def test_keep_talking_switch_is_saved_per_caregiver():
    from fastapi.testclient import TestClient
    import main
    c = TestClient(main.app)
    t = c.post("/auth/login", json={"name": "demo", "pin": "1234"}).json()
    h = {"X-Auth-Token": t["token"]}
    assert t["patient"]["keep_talking"] is False
    body = {"name": "Lakshmi", "nickname": "Amma", "preferred_language": "en-IN", "location_note": "", "keep_talking": True}
    assert c.put("/api/me/patient", headers=h, json=body).status_code == 200
    assert c.get("/auth/me", headers=h).json()["patient"]["keep_talking"] is True
    assert c.get("/api/me/full", headers=h).json()["patient"]["keep_talking"] in (True, 1)
    other = c.post("/auth/signup", json={"name": "other2", "pin": "4321"}).json()
    assert other["patient"]["keep_talking"] is False


# ---------------------------------------------------------------- answering "Shall we talk about ...?"
def test_yes_to_a_topic_invitation_is_understood():
    no_checkins()
    r = say("hello")                       # ends with an invitation
    assert "?" in r["reply"]
    r2 = say("yes")
    assert "not sure" not in r2["reply"].lower() and r2["intent"] == "topic_reply"
    r3 = say("no")                         # nothing open now: plain unknown is fine, but must not crash
    assert r3["reply"]


def test_no_to_a_topic_invitation():
    no_checkins()
    say("hello")
    r = say("no thanks")
    assert r["intent"] == "topic_reply" and "alright" in r["reply"].lower()



# ---------------------------------------------------------------- Hinglish and Kanglish (Hindi / Kannada in English letters)
HINGLISH_CASES = [("meri beti kahan hai?","hi-IN","family_where"),("mera beta kab aayega","hi-IN","family_where"),("mujhe bhook lagi hai","hi-IN","hungry"),("mujhe pyaas lagi hai","hi-IN","thirsty"),("mujhe bhook nahi hai","hi-IN","checkin_ok"),
("seene mein dard ho raha hai","hi-IN","emergency"),("mujhe dawai chahiye","hi-IN","medication"),("madad karo","hi-IN","help"),("main kahan hoon","hi-IN","confusion"),("mera naam kya hai","hi-IN","who_am_i"),
("mujhe dar lag raha hai","hi-IN","distress"),("meri behen se baat karni hai","hi-IN","call_family"),("mera pati kaun hai","hi-IN","family_who"),("aaj kya plan hai","hi-IN","reminder"),("kal kya hai","hi-IN","reminder"),("mujhe gaana sunna hai","hi-IN","song"),("namaste","hi-IN","greeting")]
KANGLISH_CASES = [("nanna magalu elli?","kn-IN","family_where"),("nanna maga yaavaga barthane","kn-IN","family_where"),("nanage hasivu aagide","kn-IN","hungry"),("nanage neeru beku","kn-IN","thirsty"),("nanage neeru beda","kn-IN","checkin_ok"),
("nanage ede novu","kn-IN","emergency"),("nanage maatre beku","kn-IN","medication"),("nanage sahaya beku","kn-IN","help"),("naanu elli iddini","kn-IN","confusion"),("nanna hesaru enu","kn-IN","who_am_i"),
("nanage bhaya aagtide","kn-IN","distress"),("nanna akka jothe matadabeku","kn-IN","call_family"),("nanna ganda yaaru","kn-IN","family_who"),("indu enu plan","kn-IN","reminder"),("naale enu","kn-IN","reminder"),("nanage haadu keloke ishta","kn-IN","song"),("namaskara","kn-IN","greeting")]


def test_hinglish_and_kanglish_phrases():
    import intent as I
    fam = [{"name": "Anita", "relation": "daughter"}, {"name": "Arun", "relation": "son"},
           {"name": "Suresh", "relation": "husband"}, {"name": "Lata", "relation": "sister"}]
    for text, lang, want in HINGLISH_CASES + KANGLISH_CASES:
        assert I.romanised_lang(text) == lang, text
        assert I.detect(text, fam)["intent"] == want, text


def test_plain_english_is_not_mistaken_for_hinglish_or_kanglish():
    import intent as I
    for text in ["I am hungry", "Where is my daughter?", "local news finale", "Shall we engage", "What is the plan today"]:
        assert I.romanised_lang(text) is None, text


def test_hinglish_and_kanglish_replies_come_back_in_that_language():
    no_checkins()
    assert say("mujhe pyaas lagi hai")["language"] == "hi-IN"
    assert say("nanage hasivu aagide")["language"] == "kn-IN"
    assert say("nanna magalu elli?")["language"] == "kn-IN"
    r = say("seene mein dard ho raha hai")
    assert r["language"] == "hi-IN" and r["alert_level"] == "high"
