# SMRITI-voice-companion-for-dementia-care

**A voice companion for people living with dementia, in Kannada, Hindi, Tamil and English.**

The patient taps one big button and asks a question. SMRITI answers aloud, only from facts the caregiver approved. If it doesn't know, it says so. Built for the **Great Indian AI Internship Challenge** with **Gnani Prisma** (speech-to-text) and **Gnani Timbre** (text-to-speech).

📄 Read the one-page pitch: [PITCH.pdf](PITCH.pdf)
🎥 Demo video: [(https://drive.google.com/file/d/13nc48SH-2eQ5vfQkRcdBA62kFSbbfq_g/view?usp=sharing)]  ·  🔗 LinkedIn post: [https://lnkd.in/p/grz7-yW7]

> SMRITI is a communication aid. It is not medical advice and does not replace caregivers. All data in this repo and demo is synthetic.

---

## The problem
People with dementia often ask the same question hundreds of times a day: "Where is my daughter?", "Where am I?", "What is the plan tomorrow?" Caregivers can't always be there to answer. Generic voice assistants don't know the family and may invent answers.

## The solution
- **One big button** for the patient, built for elderly users.
- **Answers only from caregiver-approved facts.** No guessing. Unknown questions get "I am not sure, I can ask your caregiver."
- **Alerts** to the caregiver when the patient says they are thirsty, hungry, scared or in pain.
- **Four languages plus code-mixed speech:** English, Hindi, Kannada, Tamil, and Hinglish, Tanglish and Kanglish.

## Features

**Patient screen**
- Tap-to-talk voice button, large readable reply text, and a "Hear it again" button
- Answers about family, where people are now, favourite food and songs, places, hobbies, life story, reminders, and "Where am I?"
- Replies in the language the patient spoke

**Caregiver area** (login with name and PIN)
- **Alerts:** see and mark needs as done
- **Family:** people, relations, descriptions, and where each person is now (this status expires after 12 hours)
- **Memories:** food, songs, places, hobbies, life events and other facts
- **Reminders:** daily, or for a specific date
- **Patient details:** name, language, home location
- **History:** every question and reply

## How it works
```
Patient speaks → Gnani Prisma (speech-to-text) → intent detection (EN/HI/KN/TA + code-mixed)
      → look up caregiver-approved facts → reply text → Gnani Timbre (text-to-speech) → patient hears it
                                       ↘ need detected (thirsty, hungry, scared, pain) → alert for caregiver
```

An important design choice: SMRITI speaks the caregiver's facts **exactly as typed** and does not translate or rewrite them. This is why it never invents anything. So the caregiver should write the facts in the patient's own language.

## Tech stack
- Python, FastAPI (run with Uvicorn)
- SQLite
- Gnani Prisma (STT) and Gnani Timbre (TTS)
- Rule-based intent matching in `backend/intent.py` and reply logic in `backend/engine.py`
- Plain browser front end (use Chrome for the microphone)

## Getting started

### 1. Requirements
- Python 3.10 or newer
- A Gnani API key (for speech-to-text and text-to-speech)
- Google Chrome

### 2. Install
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
On macOS or Linux, activate with `source .venv/bin/activate`.

### 3. Add your key
Copy `.env.example` to `.env` and fill in your own key. **Never commit `.env`.**
```
GNANI_API_KEY=your_key_here
```
Use the same variable names that are in `.env.example`.

### 4. Run
```powershell
uvicorn main:app --reload
```
Open the address that Uvicorn prints (usually http://127.0.0.1:8000) in Chrome.

### 5. Create the demo account
```powershell
python create_mira.py
```
Then log in with **name `mira`**, **PIN `2468`**. This creates a synthetic patient, "Mira Krishnan", with 6 family members, 14 memories and 6 reminders. Running it again is safe and won't create a copy.

## Try it
| Language | Say |
|---|---|
| English | "Where is my daughter?" · "Who is Diya?" · "What is my favourite food?" · "I am thirsty" |
| Hindi | "मेरी बेटी कहाँ है?" · "मुझे भूख लगी है" |
| Kannada | "ನನ್ನ ಮಗಳು ಎಲ್ಲಿ?" · "ನನಗೆ ಹಸಿವಾಗಿದೆ" |
| Tamil | "என் மகள் எங்கே?" · "எனக்கு தாகமா இருக்கு" |
| Code-mixed | "meri beti kahan hai?" · "nanna maga elli?" |
| Safety | "What did I do before?" → "I am not sure, I can ask your caregiver." |

Tip: "Where is she now?" lines expire after 12 hours. Re-save a family member's status in **Caregiver → Family → Edit** before a demo.

## Tests
```powershell
pytest
```
73 tests cover intent detection, code-mixed phrases, and reply logic.

## Project structure
```
backend/
  main.py          API and app entry point
  db.py            database helpers
  auth.py          caregiver login and PIN
  intent.py        understands what the patient asked (EN/HI/KN/TA, code-mixed)
  engine.py        builds the reply from approved facts
  create_mira.py   creates the synthetic demo account
  config.py
  gnani_client.py
  responses.py
  smriti_v2.db
  requirements.txt
  tests/           automated tests
```

## Limitations and honest notes
- The Hindi and Kannada wording, and the many ways people spell code-mixed words, still need review by native speakers.
- Caregiver facts are spoken as typed, not translated. Write them in the patient's language.
- Speech recognition depends on the microphone, noise and accent.
- Not medical advice. Not for emergencies: if someone is in danger, call local emergency services.

## Responsible AI
- Answers come only from caregiver-approved facts, never invented.
- Synthetic data only. Do not upload real patient information to a public demo.

## Credits
Built by **Libini** for the Great Indian AI Internship Challenge. Speech technology by **Gnani.ai** (Prisma and Timbre).
