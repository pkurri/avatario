import logging
import os
import httpx
import base64
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


async def sarvam_stt(audio_bytes: bytes) -> Optional[str]:
    """Sends audio to Sarvam STT API. Returns transcribed text."""
    if not audio_bytes:
        return None

    sarvam_api_key = os.getenv("SARVAM_API_KEY", "")
    url = "https://api.sarvam.ai/speech-to-text-translate"
    headers = {"api-subscription-key": sarvam_api_key}

    try:
        async with httpx.AsyncClient() as client:
            files = {"file": ("audio.webm", audio_bytes, "audio/webm")}
            response = await client.post(
                url, headers=headers, files=files, data={"prompt": ""}, timeout=30.0
            )
            if response.status_code != 200:
                logger.warning("STT error response: %s", response.text)
            response.raise_for_status()
            return response.json().get("transcript", "").strip()
    except Exception as e:
        logger.error("Sarvam STT error: %s", e)
        return None


async def sarvam_tts(text: str, role: str = "client") -> Optional[bytes]:
    """Sends text to Sarvam TTS API. Returns decoded audio bytes."""
    sarvam_api_key = os.getenv("SARVAM_API_KEY", "")
    url = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "api-subscription-key": sarvam_api_key,
        "Content-Type": "application/json",
    }

    # client role → female voice; all others → male voice
    speaker = "anushka" if role == "client" else "abhilash"

    payload = {
        "inputs": [text],
        "target_language_code": "hi-IN",
        "speaker": speaker,
        "enable_preprocessing": True,
        "skip_preflight": True,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            if response.status_code != 200:
                logger.warning("TTS error response: %s", response.text)
            response.raise_for_status()
            data = response.json()
            if data.get("audios"):
                return base64.b64decode(data["audios"][0])
    except Exception as e:
        logger.error("Sarvam TTS error: %s", e)

    return None
