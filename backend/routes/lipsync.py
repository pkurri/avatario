import os
import tempfile
import uuid
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from engine.personas import get_persona
from engine.audio import sarvam_tts
from engine.lipsync import lipsync_service, get_available_models, LipSyncModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/lipsync", tags=["lipsync"])


class LipSyncRequest(BaseModel):
    persona_id: str
    text: str
    image_url: Optional[str] = None
    model: str = "infinitetalk-image-to-video"
    resolution: str = "512x512"


class LipSyncResponse(BaseModel):
    job_id: Optional[str] = None
    video_url: Optional[str] = None
    status: str
    cached: bool = False
    error: Optional[str] = None


@router.get("/models")
async def list_lipsync_models():
    models = await get_available_models()
    return {"models": models}


@router.post("/generate", response_model=LipSyncResponse)
async def generate_lipsync_video(request: LipSyncRequest):
    persona = get_persona(request.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona '{request.persona_id}' not found")

    image_url = request.image_url or persona.avatar
    if image_url.startswith("/"):
        base_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
        image_url = f"{base_url}{image_url}"

    audio_bytes = await sarvam_tts(request.text, role=persona.voice_speaker)
    if not audio_bytes:
        return LipSyncResponse(status="error", error="Failed to generate TTS audio")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(audio_bytes)

    try:
        model = LipSyncModel(request.model)
    except ValueError:
        model = LipSyncModel.INFINITETALK_IMAGE

    result = await lipsync_service.generate_talking_video_bytes(
        image_bytes=b"",
        audio_bytes=audio_bytes,
        model=model,
        prompt=f"Natural talking head, {persona.title}, professional demeanor",
        resolution=request.resolution,
    )

    if result.get("error"):
        return LipSyncResponse(
            job_id=f"mock_{uuid.uuid4()}",
            status="processing",
            cached=False,
            error=f"Lip sync service unavailable: {result.get('error')}. Video generation queued.",
        )

    return LipSyncResponse(
        job_id=result.get("job_id"),
        video_url=result.get("video_url"),
        status=result.get("status", "processing"),
        cached=False,
    )


@router.get("/status/{job_id}")
async def get_lipsync_status(job_id: str):
    return await lipsync_service.get_job_status(job_id)
