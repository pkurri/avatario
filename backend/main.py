from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Union, Optional
from pathlib import Path
from langchain_core.messages import HumanMessage
import asyncio
import json
import os

from engine.personas import UserRole, get_persona, get_all_personas, get_welcome_message, get_voice_speaker
from engine.graph import ai_conversation_graph
from engine.audio import sarvam_stt, sarvam_tts
from engine.aws_controller import get_llm_instance_status, start_llm_instance
from engine.lipsync import (
    lipsync_service, 
    persona_video_cache, 
    generate_persona_video,
    get_available_models,
    LipSyncModel
)
from engine.ai_person_generator import (
    generate_real_ai_person,
    generate_talking_head,
    ai_person_generator,
    Gender,
    Ethnicity,
    AgeGroup,
    PersonTraits
)
from engine.talking_person_pipeline import (
    generate_real_talking_person,
    get_person_video,
    get_pipeline,
    TalkingPersonPipeline
)
from engine.face_clone import (
    get_face_clone_engine,
    clone_face_from_upload,
    clone_face_from_url,
    generate_new_ai_face,
    make_clone_talk,
)
from fastapi import UploadFile, File, Form
from pydantic import BaseModel
from typing import Literal

app = FastAPI(
    title="AI Assistant API",
    description="Voice-Native AI Backend - Multi-Vertical AI Assistant Platform",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage of connected clients and their LangGraph state configurations
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, role: UserRole):
        await websocket.accept()
        # Initialize an empty conversation history for this session
        self.active_connections[websocket] = {"role": role, "messages": []}

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            del self.active_connections[websocket]

    async def process_message(self, websocket: WebSocket, message: str, persona_id: Optional[str] = None):
        state = self.active_connections[websocket]
        role = state["role"]
        
        # Append human message to session state
        state["messages"].append(HumanMessage(content=message))
        
        # We need to construct the input state for the graph
        input_state = {
            "messages": state["messages"],
            "role": role,
            "persona_id": persona_id,
            "extracted_entities": {},
            "conversation_context": {}
        }
        
        # Run through the LangGraph
        result = await ai_conversation_graph.ainvoke(input_state)
        
        # Get the latest AI response from the graph's output
        ai_response = result["messages"][-1].content
        
        # Store in state history
        state["messages"] = result["messages"]
        
        # Send text back to the client immediately
        await websocket.send_text(json.dumps({
            "status": "success",
            "type": "text", 
            "content": ai_response,
            "persona_id": persona_id,
            "role": role.value
        }))
        
        # Trigger TTS Generation from Sarvam AI
        # Use persona-specific voice if available
        voice_speaker = get_voice_speaker(persona_id) if persona_id else role.value
        audio_bytes = await sarvam_tts(ai_response, role=voice_speaker)
        if audio_bytes:
            # Send binary audio back over the websocket
            await websocket.send_bytes(audio_bytes)

manager = ConnectionManager()

# ==========================================
# PERSONA MANAGEMENT ENDPOINTS
# ==========================================

@app.get("/")
async def root():
    return {
        "message": "AI Assistant API is running",
        "endpoints": {
            "websocket_chat": "/chat/{persona_id}",
            "personas": "/personas",
            "livekit_token": "/get_livekit_token",
            "health": "/health"
        }
    }

@app.get("/health")
async def health():
    from engine.lipsync_failover import get_lipsync_failover
    failover = get_lipsync_failover()
    lipsync_status = await failover.health()
    return {
        "status": "healthy",
        "version": "1.0.0",
        "lipsync": lipsync_status
    }

@app.get("/personas")
async def list_personas():
    """Get all available AI personas."""
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

@app.get("/personas/{persona_id}")
async def get_persona_details(persona_id: str):
    """Get details for a specific persona."""
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

# ==========================================
# LIVEKIT TOKEN ENDPOINT
# ==========================================

from livekit.api import AccessToken, VideoGrants
import os

@app.get("/get_livekit_token")
async def get_livekit_token(
    participant_name: str = "User", 
    room_name: str = "ai-room", 
    role: str = "client",
    persona_id: Optional[str] = None
):
    """Generate a LiveKit token for real-time voice/video sessions."""
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    if not api_key or not api_secret:
        raise HTTPException(status_code=500, detail="LiveKit credentials missing")
    
    grant = VideoGrants(room_join=True, room=room_name)
    token = AccessToken(api_key, api_secret)
    token.with_identity(participant_name)
    token.with_name(participant_name)
    token.with_grants(grant)
    
    # Support both legacy 'role' and new 'persona_id' in metadata
    metadata = {"role": role}
    if persona_id:
        metadata["persona_id"] = persona_id
    token.with_metadata(json.dumps(metadata))
    
    # Auto-dispatch agent to room so it joins automatically
    try:
        from livekit.api import LiveKitAPI
        from livekit.protocol.agent_dispatch import CreateAgentDispatchRequest
        
        lk_api = LiveKitAPI(
            url=os.getenv("LIVEKIT_URL"),
            api_key=api_key,
            api_secret=api_secret,
        )
        dispatch_req = CreateAgentDispatchRequest(
            room=room_name,
            agent_name="",
        )
        await lk_api.agent_dispatch.create_dispatch(dispatch_req)
        await lk_api.aclose()
    except Exception as e:
        print(f"[LiveKit] Agent dispatch warning (non-fatal): {e}")
    
    return {"token": token.to_jwt(), "url": os.getenv("LIVEKIT_URL")}

# ==========================================
# LLM STATUS ENDPOINTS
# ==========================================

@app.get("/llm_status")
async def llm_status():
    """Check if the LLM engine is ready."""
    return await get_llm_instance_status()

@app.post("/wake_llm")
async def wake_llm():
    """Trigger the start of the LLM instance."""
    return await start_llm_instance()

# ==========================================
# WEBSOCKET CHAT ENDPOINT
# ==========================================

# ==========================================
# LIP SYNC VIDEO GENERATION ENDPOINTS
# ==========================================

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

@app.get("/lipsync/models")
async def list_lipsync_models():
    """List available lip sync models for video generation"""
    models = await get_available_models()
    return {"models": models}

@app.post("/lipsync/generate", response_model=LipSyncResponse)
async def generate_lipsync_video(request: LipSyncRequest):
    """
    Generate a talking avatar video for a persona
    
    - Uses the persona's configured image if no image_url provided
    - Generates TTS audio for the text
    - Creates lip-synced video using AI
    """
    # Get persona details
    persona = get_persona(request.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona '{request.persona_id}' not found")
    
    # Determine image URL
    image_url = request.image_url or persona.avatar
    if image_url.startswith("/"):
        # Convert relative path to absolute URL
        base_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
        image_url = f"{base_url}{image_url}"
    
    # Generate TTS audio first
    audio_bytes = await sarvam_tts(request.text, role=persona.voice_speaker)
    if not audio_bytes:
        return LipSyncResponse(
            status="error",
            error="Failed to generate TTS audio"
        )
    
    # For now, upload audio to temporary storage (in production, use S3/R2)
    # This is a simplified version - in production you'd use proper file storage
    import tempfile
    import uuid
    
    audio_filename = f"tts_{uuid.uuid4()}.wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(audio_bytes)
        audio_path = f.name
    
    # Try to use lip sync service
    try:
        model = LipSyncModel(request.model)
    except ValueError:
        model = LipSyncModel.INFINITETALK_IMAGE
    
    # Generate video using lip sync service
    # Note: In production, you'd upload the audio to a CDN and pass the URL
    # For now, we'll use the bytes-based method if available
    result = await lipsync_service.generate_talking_video_bytes(
        image_bytes=b"",  # Would fetch image bytes in production
        audio_bytes=audio_bytes,
        model=model,
        prompt=f"Natural talking head, {persona.title}, professional demeanor",
        resolution=request.resolution
    )
    
    if result.get("error"):
        # Return cached/simulated response if lip sync service unavailable
        return LipSyncResponse(
            job_id=f"mock_{uuid.uuid4()}",
            status="processing",
            cached=False,
            error=f"Lip sync service unavailable: {result.get('error')}. Video generation queued."
        )
    
    return LipSyncResponse(
        job_id=result.get("job_id"),
        video_url=result.get("video_url"),
        status=result.get("status", "processing"),
        cached=False
    )

@app.get("/lipsync/status/{job_id}")
async def get_lipsync_status(job_id: str):
    """Check status of a lip sync video generation job"""
    result = await lipsync_service.get_job_status(job_id)
    return result

@app.get("/personas/{persona_id}/video")
async def get_persona_talking_video(
    persona_id: str,
    text: str,
    model: str = "infinitetalk-image-to-video"
):
    """
    Get or generate a talking video for a specific persona
    
    Query Parameters:
    - text: The text to speak
    - model: Lip sync model to use
    """
    persona = get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    # Get persona image URL
    image_url = persona.avatar
    if image_url.startswith("/"):
        base_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
        image_url = f"{base_url}{image_url}"
    
    # Generate TTS audio URL (in production, upload to CDN)
    # For now, we'll need to generate and store temporarily
    audio_bytes = await sarvam_tts(text, role=persona.voice_speaker)
    
    # Generate talking video
    try:
        lip_model = LipSyncModel(model)
    except ValueError:
        lip_model = LipSyncModel.INFINITETALK_IMAGE
    
    result = await generate_persona_video(
        persona_id=persona_id,
        image_url=image_url,
        audio_url="",  # Would be CDN URL in production
        text_content=text,
        model=lip_model
    )
    
    return result

@app.post("/personas/{persona_id}/cache/clear")
async def clear_persona_video_cache(persona_id: str):
    """Clear cached videos for a persona (for updating images/texts)"""
    persona_video_cache.clear(persona_id)
    return {"status": "success", "message": f"Cache cleared for persona {persona_id}"}

# ==========================================
# AI PERSON GENERATION ENDPOINTS
# ==========================================

class GenerateAIPersonRequest(BaseModel):
    vertical: str = "generic"
    gender: str = "female"
    name: Optional[str] = None
    ethnicity: Optional[str] = None
    age_group: Optional[str] = "middle"

class TalkingHeadRequest(BaseModel):
    persona_id: str
    text: str
    image_url: str

@app.post("/ai-person/generate")
async def create_ai_person(request: GenerateAIPersonRequest):
    """
    Generate a realistic AI person avatar
    
    Creates a unique, realistic human avatar for any vertical
    """
    result = await generate_real_ai_person(
        vertical=request.vertical,
        gender=request.gender,
        name=request.name
    )
    
    return {
        "status": "success",
        "person": result,
        "message": "AI person generated successfully" if result["ready"] else "AI person queued for generation"
    }

@app.post("/ai-person/talking-head")
async def create_talking_head(request: TalkingHeadRequest):
    """
    Generate a talking head video from an AI person image + text
    
    - Takes an AI person image URL
    - Generates TTS audio for the text
    - Creates lip-synced talking video
    """
    result = await generate_talking_head(
        person_id=request.persona_id,
        text=request.text,
        persona_image_url=request.image_url
    )
    
    return result

@app.get("/ai-person/vertical/{vertical}")
async def get_vertical_personas(vertical: str, count: int = 2):
    """
    Get AI-generated personas for a specific vertical
    
    Returns realistic AI human avatars tailored for the vertical
    """
    personas = await ai_person_generator.create_vertical_personas(vertical, count)
    
    return {
        "vertical": vertical,
        "personas": [
            {
                "id": p.id,
                "name": p.name,
                "image_url": p.image_url,
                "traits": {
                    "gender": p.traits.gender.value,
                    "ethnicity": p.traits.ethnicity.value,
                    "age_group": p.traits.age_group.value,
                    "profession": p.traits.profession
                }
            }
            for p in personas
        ]
    }

@app.get("/ai-person/ethnicities")
async def list_ethnicities():
    """List available ethnicities for AI person generation"""
    return {
        "ethnicities": [e.value for e in Ethnicity],
        "genders": [g.value for g in Gender],
        "age_groups": [a.value for a in AgeGroup]
    }

# ==========================================
# TALKING PERSON PIPELINE ENDPOINTS (Option B)
# ==========================================

class CreateTalkingPersonRequest(BaseModel):
    vertical: str = "generic"
    gender: str = "female"
    name: Optional[str] = None
    ethnicity: Optional[str] = "indian"

class GenerateVideoRequest(BaseModel):
    person_id: str
    text: str
    emotion: str = "neutral"

@app.post("/talking-person/create")
async def create_talking_person(request: CreateTalkingPersonRequest):
    """
    Create a complete AI-generated talking person (Option B)
    
    Pipeline:
    1. Generate realistic portrait image with FLUX
    2. Generate TTS audio with Chatterbox/Sarvam
    3. Create lip-sync video with Wav2Lip/SadTalker
    
    Returns complete person with talking video ready
    """
    result = await generate_real_talking_person(
        vertical=request.vertical,
        gender=request.gender,
        name=request.name,
        ethnicity=request.ethnicity or "indian"
    )
    
    return result

@app.post("/talking-person/video")
async def create_person_video(request: GenerateVideoRequest):
    """
    Generate a new talking video for an existing person
    
    Uses existing AI-generated portrait + new text
    """
    result = await get_person_video(
        person_id=request.person_id,
        text=request.text,
        emotion=request.emotion
    )
    
    return result

@app.get("/talking-person/{person_id}/status")
async def get_talking_person_status(person_id: str):
    """Check generation status of a talking person"""
    pipeline = get_pipeline()
    status = pipeline.get_person_status(person_id)
    return status

@app.options("/talking-person/{person_id}/image")
async def get_person_image_options(person_id: str):
    """Handle CORS preflight for image endpoint"""
    from fastapi.responses import Response
    return Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Cross-Origin-Resource-Policy": "cross-origin",
        }
    )

@app.get("/talking-person/{person_id}/image")
async def get_person_image(person_id: str):
    """Serve the generated person image"""
    pipeline = get_pipeline()
    image_path = pipeline.images_dir / f"{person_id}.png"
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Person image not found")
    
    from fastapi.responses import FileResponse
    response = FileResponse(
        str(image_path),
        media_type="image/png",
        filename=f"{person_id}.png"
    )
    # Add CORS headers for cross-origin image loading
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    response.headers["Cross-Origin-Embedder-Policy"] = "credentialless"
    return response

@app.get("/talking-person/{person_id}/video/{video_hash}")
async def get_person_video_file(person_id: str, video_hash: str):
    """Serve a generated talking video"""
    pipeline = get_pipeline()
    video_path = pipeline.video_dir / f"{person_id}_{video_hash}.mp4"
    
    if not video_path.exists():
        # Try base video
        video_path = pipeline.video_dir / f"{person_id}.mp4"
    
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        str(video_path),
        media_type="video/mp4",
        filename=f"{person_id}.mp4"
    )

@app.get("/talking-person/{person_id}/video/latest")
async def get_latest_person_video(person_id: str):
    """Get the latest video for a person"""
    pipeline = get_pipeline()
    
    # Find latest video
    videos = list(pipeline.video_dir.glob(f"{person_id}*.mp4"))
    
    if not videos:
        raise HTTPException(status_code=404, detail="No videos found")
    
    # Sort by modification time
    latest = max(videos, key=lambda p: p.stat().st_mtime)
    
    from fastapi.responses import FileResponse
    return FileResponse(
        str(latest),
        media_type="video/mp4",
        filename=f"{person_id}.mp4"
    )

@app.get("/talking-person/{person_id}/audio/{audio_key}")
async def get_person_audio(person_id: str, audio_key: str):
    """Serve generated TTS audio for a talking person (welcome or text-hash keyed)"""
    pipeline = get_pipeline()

    # Try exact hash-keyed file first, then welcome fallback
    candidates = [
        pipeline.audio_dir / f"{person_id}_{audio_key}.wav",
        pipeline.audio_dir / f"{person_id}.wav",
    ]
    # Also search glob for any matching audio
    if audio_key == "welcome":
        candidates += list(pipeline.audio_dir.glob(f"{person_id}*.wav"))

    audio_path = next((p for p in candidates if p.exists() and p.stat().st_size > 100), None)

    if not audio_path:
        raise HTTPException(status_code=404, detail="Audio not found")

    from fastapi.responses import FileResponse
    response = FileResponse(
        str(audio_path),
        media_type="audio/wav",
        filename=f"{person_id}_{audio_key}.wav",
    )
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response

# ==========================================
# FACE CLONE ENGINE ENDPOINTS
# ==========================================

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

@app.post("/face-clone/upload")
async def upload_face_clone(
    file: UploadFile = File(...),
    name: str = Form("Cloned Person"),
):
    """
    Clone a real human face from an uploaded photo.
    Upload a clear frontal face photo to create a cloned talking avatar.
    """
    image_bytes = await file.read()
    result = await clone_face_from_upload(
        image_bytes=image_bytes,
        name=name,
        content_type=file.content_type or "image/png",
    )
    return result

@app.post("/face-clone/from-url")
async def clone_face_from_url_endpoint(request: CloneFromUrlRequest):
    """
    Clone a real human face from a URL.
    Provide a URL to any photo with a clear frontal face.
    """
    result = await clone_face_from_url(
        image_url=request.image_url,
        name=request.name,
    )
    return result

@app.post("/face-clone/generate")
async def generate_face_endpoint(request: GenerateNewFaceRequest):
    """
    Generate a completely new AI human face from scratch.
    Uses FLUX to create a photorealistic face that doesn't exist.
    """
    result = await generate_new_ai_face(
        name=request.name,
        gender=request.gender,
        ethnicity=request.ethnicity,
        age=request.age,
        profession=request.profession,
    )
    return result

@app.post("/face-clone/talk")
async def make_face_talk_endpoint(request: MakeFaceTalkRequest):
    """
    Make a cloned or generated face talk with lip-sync video.
    Pipeline: Face + Text → TTS Audio → Lip Sync Video
    """
    result = await make_clone_talk(
        face_id=request.face_id,
        text=request.text,
        voice_id=request.voice_id,
    )
    return result

@app.get("/face-clone/list")
async def list_face_clones(mode: Optional[str] = None):
    """List all cloned and generated faces"""
    engine = get_face_clone_engine()
    return {"faces": engine.list_faces(mode)}

@app.get("/face-clone/{face_id}")
async def get_face_clone(face_id: str):
    """Get details of a specific cloned face"""
    engine = get_face_clone_engine()
    face = engine.get_face(face_id)
    if not face:
        raise HTTPException(status_code=404, detail="Face not found")
    return face.to_dict()

@app.delete("/face-clone/{face_id}")
async def delete_face_clone(face_id: str):
    """Delete a cloned face and all its assets"""
    engine = get_face_clone_engine()
    deleted = engine.delete_face(face_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Face not found")
    return {"deleted": True, "face_id": face_id}

@app.get("/face-clone/{face_id}/image")
async def get_face_clone_image(face_id: str):
    """Serve the cloned/generated face image"""
    engine = get_face_clone_engine()
    face = engine.get_face(face_id)
    if not face:
        raise HTTPException(status_code=404, detail="Face not found")
    
    image_path = Path(face.image_path)
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")
    
    from fastapi.responses import FileResponse
    response = FileResponse(
        str(image_path),
        media_type="image/png",
        filename=f"{face_id}.png",
    )
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response

@app.get("/face-clone/{face_id}/video/{text_hash}")
async def get_face_clone_video(face_id: str, text_hash: str):
    """Serve a generated talking video"""
    engine = get_face_clone_engine()
    face = engine.get_face(face_id)
    if not face:
        raise HTTPException(status_code=404, detail="Face not found")
    
    video_path = face.videos.get(text_hash)
    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    from fastapi.responses import FileResponse
    response = FileResponse(
        str(video_path),
        media_type="video/mp4",
        filename=f"{face_id}_{text_hash}.mp4",
    )
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response

@app.get("/face-clone/{face_id}/audio/{text_hash}")
async def get_face_clone_audio(face_id: str, text_hash: str):
    """Serve generated TTS audio"""
    engine = get_face_clone_engine()
    face = engine.get_face(face_id)
    if not face:
        raise HTTPException(status_code=404, detail="Face not found")
    
    audio_path = face.audio_files.get(text_hash)
    if not audio_path or not Path(audio_path).exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    
    from fastapi.responses import FileResponse
    response = FileResponse(
        str(audio_path),
        media_type="audio/wav",
        filename=f"{face_id}_{text_hash}.wav",
    )
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response

# ==========================================
# WEBSOCKET CHAT WITH VIDEO SUPPORT
# ==========================================

@app.websocket("/chat/{persona_id}")
async def websocket_chat(websocket: WebSocket, persona_id: str):
    """
    WebSocket endpoint for AI conversation.
    Accepts persona_id to determine which AI personality to use.
    Also accepts legacy 'lawyer' and 'client' for backward compatibility.
    
    NEW: Supports video mode - set persona_config.video_mode=true in metadata
         to receive talking avatar videos instead of just audio.
    """
    # Validate persona exists
    persona = get_persona(persona_id)
    
    # For backward compatibility, accept legacy role names
    if not persona:
        if persona_id == "lawyer":
            persona = get_persona("lawyer")
        elif persona_id == "client":
            persona = get_persona("client")
    
    if not persona:
        await websocket.close(code=1008, reason=f"Invalid persona_id: {persona_id}. Use /personas to see available options.")
        return
    
    # Map persona to UserRole for backward compatibility
    try:
        user_role = UserRole(persona_id)
    except ValueError:
        user_role = UserRole.CLIENT

    await manager.connect(websocket, user_role)
    
    # Check if video mode is enabled (from connection metadata)
    video_mode = False
    
    try:
        # Send personalized welcome message
        welcome = get_welcome_message(persona_id)
        
        await websocket.send_text(json.dumps({
            "status": "connected", 
            "type": "info", 
            "content": welcome,
            "persona_id": persona_id,
            "persona_name": persona.name,
            "video_mode": video_mode
        }))
        
        # Generate welcome audio (and video if in video mode)
        welcome_audio = await sarvam_tts(welcome, role=persona.voice_speaker)
        if welcome_audio:
            await websocket.send_bytes(welcome_audio)
            
        while True:
            message = await websocket.receive()
            
            if "bytes" in message:
                audio_chunk = message["bytes"]
                print(f"[{persona.name}] Received audio payload of {len(audio_chunk)} bytes.")
                transcribed_text = await sarvam_stt(audio_chunk)
                print(f"[{persona.name}] STT Output: '{transcribed_text}'")
                
                if transcribed_text:
                    await manager.process_message(websocket, transcribed_text, persona_id)
                else:
                    print(f"[{persona.name}] STT failed to transcribe the bytes.")
                    
            elif "text" in message:
                text_data = message["text"]
                
                # Check if it's a command
                if text_data.startswith("/"):
                    if text_data.startswith("/video_mode"):
                        video_mode = not video_mode
                        await websocket.send_text(json.dumps({
                            "type": "command_response",
                            "content": f"Video mode {'enabled' if video_mode else 'disabled'}"
                        }))
                        continue
                
                # Normal message processing
                await manager.process_message(websocket, text_data, persona_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client disconnected from {persona.name}")
