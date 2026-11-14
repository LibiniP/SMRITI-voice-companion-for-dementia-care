"""Thin wrappers around Gnani Prisma (STT) and Timbre (TTS). The API key never leaves the server."""
import asyncio

import httpx

import config


class GnaniError(Exception):
    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status


# Gnani's docs say some accounts allow only 1 active request at a time, so we serialise calls.
_lock = asyncio.Lock()


def _headers() -> dict:
    if not config.GNANI_API_KEY:
        raise GnaniError("GNANI_API_KEY is missing in backend/.env", 500)
    return {"X-API-Key-ID": config.GNANI_API_KEY}


def _error_message(resp: httpx.Response) -> str:
    try:
        data = resp.json()
    except Exception:
        return resp.text[:300]
    if isinstance(data, dict):
        if "message" in data:
            return str(data["message"])
        detail = data.get("detail")
        if isinstance(detail, dict):
            return str(detail.get("message", detail))
        if detail:
            return str(detail)
        if isinstance(data.get("error"), dict):
            return str(data["error"].get("message", data["error"]))
    return str(data)[:300]


async def _post(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    """POST with a short retry when Gnani answers 429 (rate limited)."""
    resp = None
    for attempt in range(3):
        resp = await client.post(url, headers=_headers(), **kwargs)
        if resp.status_code != 429:
            break
        await asyncio.sleep(1.0 + attempt)
    return resp


async def transcribe(audio: bytes, filename: str, content_type: str, language_code: str) -> dict:
    """language_code: kn-IN / hi-IN / ta-IN / en-IN, or 'indic-auto' to let Prisma v3.0 detect it."""
    data = {"model": config.STT_MODEL, "language_code": language_code, "format": "transcribe"}
    files = {"audio_file": (filename, audio, content_type or "application/octet-stream")}
    async with _lock:
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                resp = await _post(client, config.STT_URL, data=data, files=files)
            except httpx.HTTPError as e:
                raise GnaniError(f"Could not reach Gnani STT: {e}")
    if resp.status_code != 200:
        raise GnaniError(f"Gnani STT error {resp.status_code}: {_error_message(resp)}", resp.status_code)
    body = resp.json()
    transcript = body.get("transcript")
    if transcript is None:
        transcript = body.get("text", "")
    if isinstance(transcript, dict):  # v2.5 can return a dict; v3.0 returns a string
        transcript = " ".join(str(v) for v in transcript.values())
    return {
        "transcript": (transcript or "").strip(),
        "detected_language": body.get("detected_language_code") or body.get("language_code") or language_code,
        "model": body.get("model", config.STT_MODEL),
        "request_id": body.get("request_id"),
        "raw": body,
    }


def _tts_payload(text: str, language: str, model: str, voice: str) -> dict:
    return {
        "text": text,
        "voice": voice,
        "model": model,
        "language": language,
        "speed": config.TTS_SPEED,
        "audio_config": {
            "sample_rate": 24000,
            "num_channels": 1,
            "sample_width": 2,
            "encoding": "linear_pcm",
            "container": "wav",
        },
    }


async def synthesize(text: str, language: str = "auto") -> tuple[bytes, str, str]:
    """Returns (audio_bytes, mime_type, 'model/voice' used). Falls back to the secondary model if rejected."""
    attempts = [(config.TTS_MODEL, config.TTS_VOICE)]
    if config.TTS_FALLBACK_MODEL and (config.TTS_FALLBACK_MODEL, config.TTS_FALLBACK_VOICE) != attempts[0]:
        attempts.append((config.TTS_FALLBACK_MODEL, config.TTS_FALLBACK_VOICE))

    last_error = "TTS failed"
    async with _lock:
        async with httpx.AsyncClient(timeout=60) as client:
            for model, voice in attempts:
                try:
                    resp = await _post(client, config.TTS_URL, json=_tts_payload(text, language, model, voice))
                except httpx.HTTPError as e:
                    raise GnaniError(f"Could not reach Gnani TTS: {e}")
                if resp.status_code == 200:
                    return resp.content, "audio/wav", f"{model}/{voice}"
                last_error = f"Gnani TTS error {resp.status_code} ({model}/{voice}): {_error_message(resp)}"
                if resp.status_code not in (400, 403, 404):
                    break  # not a model/voice problem, so a fallback will not help
    raise GnaniError(last_error)
