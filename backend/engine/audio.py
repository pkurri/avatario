# backend/engine/audio.py
import os
import httpx
import base64
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

async def sarvam_stt(audio_bytes: bytes) -> Optional[str]:
    """
    Sends an audio chunk to Sarvam's Speech-to-Text API.
    Returns the transcribed translation text.
    """
    sarvam_api_key = os.getenv("SARVAM_API_KEY", "")
    url = "https://api.sarvam.ai/speech-to-text-translate"
    
    headers = {
        "api-subscription-key": sarvam_api_key,
    }
    
    if not audio_bytes:
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            files = {"file": ("audio.webm", audio_bytes, "audio/webm")}
            data = {"prompt": ""}
            response = await client.post(url, headers=headers, files=files, data=data, timeout=30.0)
            
            if response.status_code != 200:
                print(f"STT Error Body: {response.text}")
            response.raise_for_status()
            
            result = response.json()
            return result.get("transcript", "").strip()
    except Exception as e:
        print(f"Sarvam STT Error: {e}")
        return None

async def sarvam_tts(
    text: str,
    role: str = "client",
    target_language_code: str = "hi-IN",
) -> Optional[bytes]:
    """
    Sends text to Sarvam's Text-to-Speech API.
    Returns the decoded binary audio bytes.
    """
    sarvam_api_key = os.getenv("SARVAM_API_KEY", "")
    url = "https://api.sarvam.ai/text-to-speech"
    
    headers = {
        "api-subscription-key": sarvam_api_key,
        "Content-Type": "application/json"
    }
    
    speaker_map = {
        "client": "anushka",
        "lawyer": "abhilash",
        "advisor": "abhilash",
    }
    speaker = speaker_map.get(role, role or "anushka")

    payload = {
        "inputs": [text],
        "target_language_code": target_language_code,
        "speaker": speaker,
        "enable_preprocessing": True,
        "skip_preflight": True
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            if response.status_code != 200:
                print(f"TTS Error Body: {response.text}")
            response.raise_for_status()
            
            data = response.json()
            if "audios" in data and len(data["audios"]) > 0:
                base64_audio = data["audios"][0]
                return base64.b64decode(base64_audio)
    except Exception as e:
        print(f"Sarvam TTS Error: {e}")
        
    return None
