"""Creates a ready-made SYNTHETIC test account.

    Login name : mira
    PIN        : 2468
    Patient    : Mira Krishnan (all people and facts below are made up)

Run once from the backend folder:   python create_mira.py
Safe to run again: it will not create a second copy.
"""
from datetime import date, datetime, timedelta

import db
from auth import create_caregiver, find_by_name

db.conn()  # opens the database and creates tables if needed
if find_by_name("mira"):
    print("Account 'mira' already exists. Log in with name: mira, PIN: 2468.")
    raise SystemExit

cid = create_caregiver("mira", "2468")
pid = db.one("SELECT id FROM patients WHERE caregiver_id=?", (cid,))["id"]

db.execute(
    "UPDATE patients SET name=?, nickname=?, preferred_language=?, location_note=? WHERE id=?",
    ("Mira Krishnan", "Mira", "en-IN",
     "You are at your home in Bengaluru, in your own bedroom and sitting room. You are safe, and your family looks after you.", pid),
)

# ---------------- family (one person per relation, so "my daughter" is never confusing) ----------------
expires = (datetime.now() + timedelta(hours=12)).isoformat(timespec="seconds")
family = [
    ("Anita", "daughter", "She is a doctor and she loves you very much. She visits you every Sunday and brings your favourite sweets.",
     "is at the hospital for work and will come home in the evening", expires),
    ("Arun", "son", "He lives in Mysuru with his family. He calls you every night after dinner.",
     "is at his office in Mysuru and will call you tonight", expires),
    ("Suresh", "husband", "He was your companion for many years. He loved walking with you in Cubbon Park.", "", None),
    ("Lata", "sister", "She is your younger sister. You two grew up together in Mysuru and she calls you on Fridays.",
     "is at home and will phone you after lunch", expires),
    ("Ravi", "brother", "He is your elder brother. He tells wonderful stories about your childhood.", "", None),
    ("Diya", "grandchild", "She is Anita's daughter. She is eight years old, draws pictures for you and loves your stories.",
     "is at school and will come to see you after school", expires),
]
for name, rel, desc, status, exp in family:
    db.execute(
        "INSERT INTO family (patient_id,name,relation,description,status_text,status_expires) VALUES (?,?,?,?,?,?)",
        (pid, name, rel, desc, status, exp),
    )

# ---------------- memories and favourite things (each is a full sentence the patient will hear) ----------------
memories = [
    ("food", "Your favourite food is hot idli with sambar and coconut chutney."),
    ("food", "You love a cup of filter coffee in the morning and you enjoy mango and payasam."),
    ("food", "On festival days you like to eat pongal and sweet holige."),
    ("song", "You love listening to old Kannada film songs by Dr. Rajkumar in the evening."),
    ("song", "You also like M. S. Subbulakshmi's bhajans and you used to hum them while cooking."),
    ("place", "You enjoy sitting in the garden of your home and watching the birds."),
    ("place", "You loved visiting the Ganesha temple near your house and the Lalbagh garden."),
    ("hobby", "You love growing jasmine and rose plants and you enjoy making flower garlands."),
    ("hobby", "You enjoy listening to the radio and knitting small woollen caps."),
    ("life_event", "You were a school teacher for thirty years and many students still remember you."),
    ("life_event", "You were married to Suresh and you celebrated your wedding anniversary every year in March."),
    ("life_event", "You were born in Mysuru and you moved to Bengaluru after your marriage."),
    ("other", "Your granddaughter Diya loves it when you tell her stories at bedtime."),
    ("other", "Your family loves you and takes good care of you every day."),
]
for cat, text in memories:
    db.execute("INSERT INTO memories (patient_id,category,text,created_at) VALUES (?,?,?,?)", (pid, cat, text, db.now()))

# ---------------- reminders (no date = told every day) ----------------
today = date.today().isoformat()
tomorrow = (date.today() + timedelta(days=1)).isoformat()
reminders = [
    ("Breakfast is at eight in the morning and lunch is at one.", None),
    ("In the evening you will have tea and listen to your favourite songs.", None),
    ("Anita will come to see you today and you will have lunch together.", today),
    ("Diya will visit you today after school.", today),
    ("Doctor Rao will visit tomorrow at ten in the morning for a regular check-up.", tomorrow),
    ("Arun will call you tomorrow evening.", tomorrow),
]
for text, d in reminders:
    db.execute("INSERT INTO reminders (patient_id,text,remind_date) VALUES (?,?,?)", (pid, text, d))

print("Done. Log in with name: mira   PIN: 2468   (patient: Mira Krishnan)")
