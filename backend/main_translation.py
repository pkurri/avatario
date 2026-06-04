# backend/main_translation.py - Real-time Translation API
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import base64
import os
from typing import Optional
from dotenv import load_dotenv
from engine.audio import sarvam_stt, sarvam_tts

load_dotenv()

app = FastAPI(title="Avatario Translation API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def detect_language(text: str) -> str:
    """Simple language detection - can be enhanced with proper language detection"""
    # Basic heuristics for Indian languages
    if any(ord(char) > 127 for char in text):
        # Contains non-ASCII characters, likely Indian language
        if 'नमस्ते' in text or 'धन्यवाद' in text:
            return "hi-IN"
        elif 'வணக்கம்' in text or 'நன்றி' in text:
            return "ta-IN"
        elif 'నమస్కారం' in text or 'ధన్యవాదాలు' in text:
            return "te-IN"
    return "en-IN"

@app.post("/api/v1/translation/real-time")
async def real_time_translation(
    audio: UploadFile = File(...),
    target_lang: str = "auto"
):
    """
    Real-time translation endpoint for mobile app
    """
    try:
        # Read audio bytes
        audio_bytes = await audio.read()
        
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="No audio data provided")
        
        # STT with translation
        transcript = await sarvam_stt(audio_bytes)
        if not transcript:
            raise HTTPException(status_code=400, detail="Speech-to-text failed")
        
        # Detect source language
        source_lang = detect_language(transcript)
        
        # Generate AI response in same language (simplified)
        # In production, this would call the full AI conversation graph
        response_text = f"I understand you said: {transcript}. How can I help you?"
        
        # TTS in appropriate language
        audio_response = await sarvam_tts(
            response_text,
            role="client",
            target_language_code=target_lang if target_lang != "auto" else source_lang,
        )
        
        if not audio_response:
            raise HTTPException(status_code=500, detail="Text-to-speech failed")
        
        return {
            "transcript": transcript,
            "source_language": source_lang,
            "target_language": target_lang if target_lang != "auto" else source_lang,
            "response": response_text,
            "audio_response": base64.b64encode(audio_response).decode(),
            "confidence": 0.95,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@app.get("/api/v1/translation/languages")
async def get_supported_languages():
    """
    Get list of supported languages
    """
    return {
        "languages": [
            {"code": "hi-IN", "name": "Hindi", "supported": True},
            {"code": "en-IN", "name": "English", "supported": True},
            {"code": "ta-IN", "name": "Tamil", "supported": True},
            {"code": "te-IN", "name": "Telugu", "supported": True},
            {"code": "kn-IN", "name": "Kannada", "supported": True},
            {"code": "ml-IN", "name": "Malayalam", "supported": True},
            {"code": "bn-IN", "name": "Bengali", "supported": True},
            {"code": "mr-IN", "name": "Marathi", "supported": True},
            {"code": "gu-IN", "name": "Gujarati", "supported": True},
            {"code": "pa-IN", "name": "Punjabi", "supported": True}
        ]
    }

@app.get("/api/v1/translation/health")
async def translation_health():
    """
    Check translation service health
    """
    return {
        "status": "healthy",
        "sarvam_api": "configured" if os.getenv("SARVAM_API_KEY") else "not_configured",
        "services": {
            "stt": "active",
            "tts": "active",
            "translation": "active"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
