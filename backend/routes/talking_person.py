from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from typing import Optional
from engine.talking_person_pipeline import (
    generate_real_talking_person,
    get_person_video,
    get_pipeline,
)

router = APIRouter(prefix="/talking-person", tags=["talking-person"])


class CreateTalkingPersonRequest(BaseModel):
    vertical: str = "generic"
    gender: str = "female"
    name: Optional[str] = None
    ethnicity: Optional[str] = "indian"


class GenerateVideoRequest(BaseModel):
    person_id: str
    text: str
    emotion: str = "neutral"


_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "*",
    "Cross-Origin-Resource-Policy": "cross-origin",
}


@router.post("/create")
async def create_talking_person(request: CreateTalkingPersonRequest):
    return await generate_real_talking_person(
        vertical=request.vertical,
        gender=request.gender,
        name=request.name,
        ethnicity=request.ethnicity or "indian",
    )


@router.post("/video")
async def create_person_video(request: GenerateVideoRequest):
    return await get_person_video(
        person_id=request.person_id,
        text=request.text,
        emotion=request.emotion,
    )


@router.get("/{person_id}/status")
async def get_talking_person_status(person_id: str):
    pipeline = get_pipeline()
    return pipeline.get_person_status(person_id)


@router.options("/{person_id}/image")
async def get_person_image_options(person_id: str):
    return Response(headers=_CORS_HEADERS)


@router.get("/{person_id}/image")
async def get_person_image(person_id: str):
    pipeline = get_pipeline()
    image_path = pipeline.images_dir / f"{person_id}.png"
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Person image not found")
    response = FileResponse(str(image_path), media_type="image/png", filename=f"{person_id}.png")
    for k, v in _CORS_HEADERS.items():
        response.headers[k] = v
    response.headers["Cross-Origin-Embedder-Policy"] = "credentialless"
    return response


@router.get("/{person_id}/video/latest")
async def get_latest_person_video(person_id: str):
    pipeline = get_pipeline()
    videos = list(pipeline.video_dir.glob(f"{person_id}*.mp4"))
    if not videos:
        raise HTTPException(status_code=404, detail="No videos found")
    latest = max(videos, key=lambda p: p.stat().st_mtime)
    return FileResponse(str(latest), media_type="video/mp4", filename=f"{person_id}.mp4")


@router.get("/{person_id}/video/{video_hash}")
async def get_person_video_file(person_id: str, video_hash: str):
    pipeline = get_pipeline()
    video_path = pipeline.video_dir / f"{person_id}_{video_hash}.mp4"
    if not video_path.exists():
        video_path = pipeline.video_dir / f"{person_id}.mp4"
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(str(video_path), media_type="video/mp4", filename=f"{person_id}.mp4")


@router.get("/{person_id}/audio/{audio_key}")
async def get_person_audio(person_id: str, audio_key: str):
    pipeline = get_pipeline()
    candidates = [
        pipeline.audio_dir / f"{person_id}_{audio_key}.wav",
        pipeline.audio_dir / f"{person_id}.wav",
    ]
    if audio_key == "welcome":
        candidates += list(pipeline.audio_dir.glob(f"{person_id}*.wav"))
    audio_path = next((p for p in candidates if p.exists() and p.stat().st_size > 100), None)
    if not audio_path:
        raise HTTPException(status_code=404, detail="Audio not found")
    response = FileResponse(
        str(audio_path),
        media_type="audio/wav",
        filename=f"{person_id}_{audio_key}.wav",
    )
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response
