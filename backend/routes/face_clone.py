from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from engine.face_clone import (
    get_face_clone_engine,
    clone_face_from_upload,
    clone_face_from_url,
    generate_new_ai_face,
    make_clone_talk,
)

router = APIRouter(prefix="/face-clone", tags=["face-clone"])


class CloneFromUrlRequest(BaseModel):
    image_url: str
    name: str


class GenerateNewFaceRequest(BaseModel):
    name: str
    gender: str = "female"
    ethnicity: str = "indian"
    age: str = "middle"
    profession: str = "generic"


class MakeFaceTalkRequest(BaseModel):
    face_id: str
    text: str
    voice_id: Optional[str] = None


@router.post("/upload")
async def upload_face_clone(
    file: UploadFile = File(...),
    name: str = Form("Cloned Person"),
):
    image_bytes = await file.read()
    return await clone_face_from_upload(
        image_bytes=image_bytes,
        name=name,
        content_type=file.content_type or "image/png",
    )


@router.post("/from-url")
async def clone_face_from_url_endpoint(request: CloneFromUrlRequest):
    return await clone_face_from_url(image_url=request.image_url, name=request.name)


@router.post("/generate")
async def generate_face_endpoint(request: GenerateNewFaceRequest):
    return await generate_new_ai_face(
        name=request.name,
        gender=request.gender,
        ethnicity=request.ethnicity,
        age=request.age,
        profession=request.profession,
    )


@router.post("/talk")
async def make_face_talk_endpoint(request: MakeFaceTalkRequest):
    return await make_clone_talk(
        face_id=request.face_id,
        text=request.text,
        voice_id=request.voice_id,
    )


@router.get("/list")
async def list_face_clones(mode: Optional[str] = None):
    engine = get_face_clone_engine()
    return {"faces": engine.list_faces(mode)}


@router.get("/{face_id}")
async def get_face_clone(face_id: str):
    engine = get_face_clone_engine()
    face = engine.get_face(face_id)
    if not face:
        raise HTTPException(status_code=404, detail="Face not found")
    return face.to_dict()


@router.delete("/{face_id}")
async def delete_face_clone(face_id: str):
    engine = get_face_clone_engine()
    deleted = engine.delete_face(face_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Face not found")
    return {"deleted": True, "face_id": face_id}


@router.get("/{face_id}/image")
async def get_face_clone_image(face_id: str):
    engine = get_face_clone_engine()
    face = engine.get_face(face_id)
    if not face:
        raise HTTPException(status_code=404, detail="Face not found")
    image_path = Path(face.image_path)
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")
    response = FileResponse(str(image_path), media_type="image/png", filename=f"{face_id}.png")
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response


@router.get("/{face_id}/video/{text_hash}")
async def get_face_clone_video(face_id: str, text_hash: str):
    engine = get_face_clone_engine()
    face = engine.get_face(face_id)
    if not face:
        raise HTTPException(status_code=404, detail="Face not found")
    video_path = face.videos.get(text_hash)
    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Video not found")
    response = FileResponse(
        str(video_path), media_type="video/mp4", filename=f"{face_id}_{text_hash}.mp4"
    )
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response


@router.get("/{face_id}/audio/{text_hash}")
async def get_face_clone_audio(face_id: str, text_hash: str):
    engine = get_face_clone_engine()
    face = engine.get_face(face_id)
    if not face:
        raise HTTPException(status_code=404, detail="Face not found")
    audio_path = face.audio_files.get(text_hash)
    if not audio_path or not Path(audio_path).exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    response = FileResponse(
        str(audio_path), media_type="audio/wav", filename=f"{face_id}_{text_hash}.wav"
    )
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response
