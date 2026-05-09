import os
from fastapi import APIRouter, HTTPException
from engine.personas import get_persona, get_all_personas
from engine.lipsync import persona_video_cache, generate_persona_video, LipSyncModel
from engine.audio import sarvam_tts

router = APIRouter(prefix="/personas", tags=["personas"])


@router.get("")
async def list_personas():
    personas = get_all_personas()
    return {
        "personas": [
            {
                "id": p.id,
                "name": p.name,
                "title": p.title,
                "description": p.description,
                "color": p.color,
                "shadow": p.shadow,
                "avatar": p.avatar,
                "voice_speaker": p.voice_speaker,
            }
            for p in personas
        ]
    }


@router.get("/{persona_id}")
async def get_persona_details(persona_id: str):
    persona = get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return {
        "id": persona.id,
        "name": persona.name,
        "title": persona.title,
        "description": persona.description,
        "color": persona.color,
        "shadow": persona.shadow,
        "avatar": persona.avatar,
        "voice_speaker": persona.voice_speaker,
    }


@router.get("/{persona_id}/video")
async def get_persona_talking_video(
    persona_id: str,
    text: str,
    model: str = "infinitetalk-image-to-video",
):
    persona = get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    image_url = persona.avatar
    if image_url.startswith("/"):
        base_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
        image_url = f"{base_url}{image_url}"

    try:
        lip_model = LipSyncModel(model)
    except ValueError:
        lip_model = LipSyncModel.INFINITETALK_IMAGE

    result = await generate_persona_video(
        persona_id=persona_id,
        image_url=image_url,
        audio_url="",
        text_content=text,
        model=lip_model,
    )
    return result


@router.post("/{persona_id}/cache/clear")
async def clear_persona_video_cache(persona_id: str):
    persona_video_cache.clear(persona_id)
    return {"status": "success", "message": f"Cache cleared for persona {persona_id}"}
