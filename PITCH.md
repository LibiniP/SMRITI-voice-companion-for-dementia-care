# SMRITI: a voice companion for people living with dementia

*Great Indian AI Internship Challenge, built on Gnani Prisma (speech-to-text) and Timbre (text-to-speech)*

## The problem
People with dementia are awake and talking, but they forget what is happening around them. So they ask the same questions again and again: "Where is my daughter?", "What is the plan today?", "Where am I?" Sometimes it happens a hundred times a day. Caregivers love them but cannot be free every minute, and they get tired. Generic voice assistants don't know the family, and they can make things up, which is risky and confusing for a person with memory loss.

## The solution
SMRITI (Sanskrit for "memory") is a voice companion with **one big button**. The patient taps it and asks a question in their own language. SMRITI answers in a calm voice, using **only facts the caregiver has approved**. If it doesn't know, it says "I am not sure, I can ask your caregiver" instead of guessing.

## How it works
1. **The caregiver sets up once.** Family members and where they are right now, favourite foods and songs, life memories, daily reminders, and where the patient lives.
2. **The patient talks.** Gnani Prisma turns speech into text. SMRITI works out what was asked and finds the answer in the caregiver's approved facts.
3. **SMRITI replies aloud.** Gnani Timbre speaks the answer in the patient's language.
4. **The caregiver stays informed.** If the patient says they are thirsty, hungry, scared or in pain, an alert appears in the caregiver area. Every conversation is saved in a history.

## What makes it different
- **Safe by design:** answers come only from caregiver-approved facts. No invented answers.
- **Indian languages:** English, Hindi, Kannada and Tamil, including code-mixed speech such as Hinglish, Tanglish and Kanglish.
- **Built for elderly users:** one big button, large text, calm replies, and a "Hear it again" option.
- **Caregiver in control:** facts about where people are now expire after 12 hours, so SMRITI never gives stale information.

## Who it helps
Families and caregivers of people with dementia in India, where care is mostly done at home and in regional languages.

## Responsible use
SMRITI is a communication aid. It is not medical advice and does not replace caregivers. The demo uses synthetic data only, and no voice cloning is used.

## Tech
Python and FastAPI backend, SQLite database, Gnani Prisma (STT), Gnani Timbre (TTS), rule-based intent matching for English, Hindi, Kannada, Tamil and code-mixed speech.

**Team / contribution:** designed, built and tested end to end by the submitter: backend, intent engine, caregiver and patient screens, and the multilingual voice flow.
