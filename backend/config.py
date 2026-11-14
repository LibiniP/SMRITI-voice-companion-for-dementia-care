"""Central settings, read from backend/.env. The Gnani key is only ever used here on the server."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


GNANI_API_KEY = _get("GNANI_API_KEY")

# --- Speech-to-text (Prisma) ---
STT_URL = _get("STT_URL", "https://api.vachana.ai/stt/v3")
STT_MODEL = _get("STT_MODEL", "prisma-v3.0")

# --- Text-to-speech (Timbre) ---
TTS_URL = _get("TTS_URL", "https://api.vachana.ai/api/v1/tts/inference")
TTS_MODEL = _get("TTS_MODEL", "timbre-v3.0")
TTS_VOICE = _get("TTS_VOICE", "Shivani")  # v3.0 voices speak all 10 languages
# Used only if the primary model/voice is rejected (e.g. account has no v3.0 access)
TTS_FALLBACK_MODEL = _get("TTS_FALLBACK_MODEL", "timbre-v2.5")
TTS_FALLBACK_VOICE = _get("TTS_FALLBACK_VOICE", "Nalini")
TTS_SPEED = float(_get("TTS_SPEED", "0.9"))  # slightly slower for elderly listeners

# --- App ---
DB_PATH = _get("DB_PATH", str(Path(__file__).parent / "smriti_v2.db"))
EMERGENCY_NUMBER = _get("EMERGENCY_NUMBER", "112")
CHECKIN_EVERY = int(_get("CHECKIN_EVERY", "3"))  # ask a hungry/thirsty/pain check-in every N replies
SEED_DEMO_DATA = _get("SEED_DEMO_DATA", "1") == "1"

SUPPORTED_LANGS = {"en-IN", "hi-IN", "kn-IN", "ta-IN"}
