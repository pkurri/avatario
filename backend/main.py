from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Dict, Union, Optional, List
from pathlib import Path
from langchain_core.messages import HumanMessage
from datetime import datetime, time
import asyncio
import base64
import json
import os

DATA_DIR = Path(os.getenv("AVATARIO_DATA_DIR", Path(__file__).parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _data_path(name: str) -> Path:
    return DATA_DIR / name

def load_json_state(name: str, default: Any) -> Any:
    path = _data_path(name)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        print(f"⚠️  Failed to load {path}: {exc}")
        return default

def save_json_state(name: str, data: Any) -> None:
    path = _data_path(name)
    tmp = path.with_suffix(f"{path.suffix}.tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str))
    tmp.replace(path)

def supabase_configured() -> bool:
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

async def supabase_request(method: str, table: str, payload: Any = None, query: str = "") -> Any:
    """Small Supabase REST helper. Falls back silently when Supabase is not configured."""
    if not supabase_configured():
        return None

    import httpx

    base_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    url = f"{base_url}/rest/v1/{table}{query}"
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(method, url, headers=headers, json=payload)
            response.raise_for_status()
            if response.content:
                return response.json()
    except Exception as exc:
        print(f"⚠️  Supabase {method} {table} failed: {exc}")
    return None

async def persist_demo_session_supabase(session_id: str, user: Dict[str, Any]) -> None:
    await supabase_request("POST", "demo_users", {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user.get("role", "Product Manager"),
        "updated_at": datetime.utcnow().isoformat(),
    })
    await supabase_request("POST", "demo_sessions", {
        "id": session_id,
        "user_id": user["id"],
        "created_at": user.get("created_at", datetime.utcnow().isoformat()),
    })

async def persist_call_supabase(call: Dict[str, Any]) -> None:
    call_sid = call.get("call_sid")
    if not call_sid:
        return
    await supabase_request("POST", "call_logs", {
        "call_sid": call_sid,
        "user_id": call.get("user_id"),
        "to_number": call.get("to"),
        "from_number": call.get("from"),
        "persona_id": call.get("persona_id"),
        "context": call.get("context") or {},
        "status": call.get("status", "unknown"),
        "direction": call.get("direction", "outbound"),
        "started_at": call.get("started_at"),
        "ended_at": call.get("ended_at"),
        "updated_at": datetime.utcnow().isoformat(),
    })
    for entry in call.get("transcript", []):
        text = entry.get("text") or entry.get("content")
        role = entry.get("role") or entry.get("speaker") or "unknown"
        if text:
            await supabase_request("POST", "call_transcripts", {
                "call_sid": call_sid,
                "role": role,
                "text": text,
                "audio_url": entry.get("audio_url"),
                "created_at": entry.get("timestamp") or datetime.utcnow().isoformat(),
            })

async def persist_mobile_settings_supabase(user_id: str, settings: Dict[str, Any]) -> None:
    await supabase_request("POST", "mobile_user_settings", {
        "user_id": user_id,
        "settings": settings,
        "call_handling_enabled": bool(settings.get("enabled", False)),
        "clone_llm_id": settings.get("clone_llm_id"),
        "use_clone_llm": bool(settings.get("use_clone_llm", False)),
        "updated_at": datetime.utcnow().isoformat(),
    })

async def persist_push_token_supabase(user_id: str, push_token: str, platform: str) -> None:
    await supabase_request("POST", "mobile_push_tokens", {
        "user_id": user_id,
        "platform": platform,
        "push_token": push_token,
        "updated_at": datetime.utcnow().isoformat(),
    })

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment from {env_path}")
    else:
        print(f"⚠️  No .env file found at {env_path}")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables")

from engine.personas import UserRole, get_persona, get_all_personas, get_welcome_message, get_voice_speaker
from engine.graph import ai_conversation_graph
from engine.audio import sarvam_stt, sarvam_tts
from engine.aws_controller import get_llm_instance_status, start_llm_instance
from engine.workflow_engine import WorkflowEngine, Workflow, WorkflowAction, WorkflowTrigger, CallContext, ActionType, workflow_engine
from engine.booking_system import BookingSystem, Booking, Service, ServiceType, BookingStatus, get_booking_system
from engine.twilio_integration import TwilioIntegration, PhoneCall, CallDirection, CallStatus, get_twilio_integration
from engine.web_widget import WebWidgetGenerator, WidgetConfig, get_widget_generator
from engine.channel_router import ChannelRouter, Channel, Message, MessageType, Conversation, get_channel_router
from engine.analytics_engine import AnalyticsEngine, MetricType, TimeGranularity, CallQualityScore, SentimentAnalysis, ABTest, get_analytics_engine
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
from engine.voice_cloning import voice_cloning_engine, VoiceCloningEngine, ClonedVoice, VoiceStatus
from engine.voice_call_integration import voice_call_integration, handle_inbound_call_with_cloned_voice
from engine.clone_llm import clone_llm_engine, CloneLLMEngine, CloneStatus, UserProfile, PersonalityTraits
from engine.voice_provider import (
    VoiceProvider, CallInfo, AudioStreamConfig,
    VoiceProviderManager, get_provider_manager, init_providers_from_env
)
from engine.signalwire_integration import SignalWireProvider, SignalWireIntegration
from engine.asterisk_integration import AsteriskProvider, AsteriskIntegration
from fastapi import UploadFile, File, Form
from pydantic import BaseModel
from typing import Literal

# Initialize voice providers on startup
voice_provider_manager = init_providers_from_env()

app = FastAPI(
    title="AI Assistant API",
    description="Voice-Native AI Backend - Multi-Vertical AI Assistant Platform",
    version="1.0.0",
)

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
    if origin.strip()
]

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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
        "services": {
            "voice": "active",
            "booking": "active",
            "workflow": "active",
            "crm": "active",
            "twilio": "configured" if "twilio" in globals() and twilio.is_configured() else "not_configured",
            "widget": "active",
            "channels": "active",
            "analytics": "active",
            "voice_cloning": "active",
        },
        "lipsync": lipsync_status
    }

@app.get("/personas")
async def list_personas():
    """Get all available AI personas."""
    personas = get_all_personas()
    return [
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

@app.get("/readiness")
async def readiness():
    """Report production setup status without exposing secrets."""
    supabase_ok = supabase_configured()
    supabase_probe = None
    if supabase_ok:
        supabase_probe = await supabase_request("GET", "demo_users", query="?select=id&limit=1")

    livekit_configured = bool(
        os.getenv("LIVEKIT_URL")
        and os.getenv("LIVEKIT_API_KEY")
        and os.getenv("LIVEKIT_API_SECRET")
    )
    aws_configured = bool(
        (os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION"))
        and (os.getenv("LLM_INSTANCE_ID") or os.getenv("AWS_LLM_INSTANCE_ID"))
        and os.getenv("AWS_ACCESS_KEY_ID")
        and os.getenv("AWS_SECRET_ACCESS_KEY")
    )
    llm_endpoint_configured = bool(
        os.getenv("VLLM_API_BASE")
        and os.getenv("VLLM_MODEL")
        and os.getenv("VLLM_API_KEY")
    )
    voice_provider_configured = any(
        os.getenv(key)
        for key in (
            "EXOTEL_API_KEY",
            "TWILIO_ACCOUNT_SID",
            "SIGNALWIRE_PROJECT_ID",
            "ASTERISK_HOST",
        )
    )
    checks = {
        "supabase": {
            "configured": supabase_ok,
            "reachable": supabase_probe is not None if supabase_ok else False,
            "mode": "supabase" if supabase_ok else "json_fallback",
        },
        "livekit": {"configured": livekit_configured},
        "aws_llm_wake": {"configured": aws_configured},
        "llm_endpoint": {"configured": llm_endpoint_configured},
        "voice_provider": {"configured": voice_provider_configured},
        "data_dir": {"path": str(DATA_DIR), "exists": DATA_DIR.exists()},
        "cors": {"origins": cors_origins},
    }
    ready_count = sum(1 for check in checks.values() if check.get("configured") or check.get("exists"))
    return {
        "status": "ready" if ready_count >= 5 else "needs_configuration",
        "checks": checks,
    }

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
    name: Optional[str] = None
    gender: str = "female"
    ethnicity: str = "indian"
    age: Union[str, int] = "middle"
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
        name=request.name or f"{request.ethnicity.title()} {request.gender.title()} Avatar",
        gender=request.gender,
        ethnicity=request.ethnicity,
        age=str(request.age),
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


# ==========================================
# AI RECEPTIONIST - PHONE & WHATSAP CALLS
# ==========================================

from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any
from datetime import datetime
import uuid

# Call management storage
call_manager = load_json_state("calls.json", {
    "active_calls": {},
    "call_history": [],
    "webhooks": {}
})
demo_sessions = load_json_state("demo_sessions.json", {})

class DemoLoginRequest(BaseModel):
    name: str = "Alex Sharma"
    email: str = "alex.sharma@example.com"

class PushTokenRequest(BaseModel):
    user_id: str
    push_token: str
    platform: Literal["ios", "android"]

@app.post("/demo/login")
async def demo_login(request: DemoLoginRequest):
    """Create or refresh a local demo user session."""
    session_id = f"demo_{uuid.uuid4().hex[:12]}"
    demo_user = {
        "id": "demo-001",
        "name": request.name,
        "email": request.email,
        "role": "Product Manager",
        "created_at": datetime.utcnow().isoformat(),
    }
    demo_sessions[session_id] = demo_user
    save_json_state("demo_sessions.json", demo_sessions)
    await persist_demo_session_supabase(session_id, demo_user)
    return {"session_id": session_id, "user": demo_user}

@app.get("/demo/session/{session_id}")
async def get_demo_session(session_id: str):
    """Read a persisted local demo user session."""
    user = demo_sessions.get(session_id)
    if not user:
        raise HTTPException(status_code=404, detail="Demo session not found")
    return {"session_id": session_id, "user": user}

class MakeCallRequest(BaseModel):
    to: str = Field(..., description="Phone number in E.164 format (+1234567890)")
    from_number: str = Field(..., description="Your Twilio/Vonage phone number")
    persona_id: str = Field("anya", description="AI persona to use for the call")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the call")

class CallResponse(BaseModel):
    call_sid: str
    status: str
    direction: Literal["inbound", "outbound"]
    timestamp: str

class WhatsAppMessageRequest(BaseModel):
    to: str = Field(..., description="WhatsApp number in E.164 format")
    message: str = Field(..., description="Text message to send")
    persona_id: str = Field("anya", description="AI persona for response generation")

class WhatsAppVoiceRequest(BaseModel):
    to: str = Field(..., description="WhatsApp number")
    audio_url: Optional[str] = Field(None, description="URL to audio file")
    persona_id: str = Field("anya", description="AI persona")

@app.post("/voice/calls", response_model=CallResponse)
async def make_phone_call(request: MakeCallRequest):
    """
    Initiate an outbound phone call using Twilio/Vonage.
    The AI receptionist will answer and handle the conversation.
    """
    call_sid = f"CALL_{uuid.uuid4().hex[:16]}"
    
    # Store call metadata
    call_manager["active_calls"][call_sid] = {
        "call_sid": call_sid,
        "user_id": request.context.get("user_id", "demo-001") if request.context else "demo-001",
        "to": request.to,
        "from": request.from_number,
        "persona_id": request.persona_id,
        "context": request.context or {},
        "status": "initiated",
        "started_at": datetime.utcnow().isoformat(),
        "transcript": [],
        "translation": build_translation_settings(
            request.context.get("user_id", "demo-001") if request.context else "demo-001",
            (request.context or {}).get("translation"),
        ),
    }
    save_json_state("calls.json", call_manager)
    await persist_call_supabase(call_manager["active_calls"][call_sid])
    
    # TODO: Integrate with Twilio/Vonage API
    # For now, return mock response for testing
    
    return CallResponse(
        call_sid=call_sid,
        status="initiated",
        direction="outbound",
        timestamp=datetime.utcnow().isoformat()
    )

@app.post("/voice/calls/{call_sid}/webhook")
async def handle_call_webhook(call_sid: str, request: Request):
    """
    Webhook endpoint for Twilio/Vonage call events.
    Handles inbound calls, status updates, and call completion.
    """
    body = await request.json()
    event_type = body.get("event_type")
    
    if call_sid not in call_manager["active_calls"]:
        call_manager["active_calls"][call_sid] = {
            "status": "unknown",
            "transcript": []
        }
    
    call_data = call_manager["active_calls"][call_sid]
    
    if event_type == "call.inbound":
        # New inbound call - generate greeting
        persona = get_persona(call_data.get("persona_id", "anya"))
        greeting = f"Hello! You've reached our office. I'm {persona.name}, your AI assistant. How can I help you today?"
        
        return {
            "actions": [
                {"type": "say", "text": greeting},
                {"type": "listen", "speech_timeout": "auto"}
            ]
        }
    
    elif event_type == "speech.recognized":
        # Process speech input and generate response
        speech_text = body.get("speech_text", "")
        
        # Add to transcript
        call_data["transcript"].append({
            "role": "user",
            "text": speech_text,
            "timestamp": datetime.utcnow().isoformat()
        })
        save_json_state("calls.json", call_manager)
        
        # Get AI response using existing conversation graph
        # TODO: Integrate with ai_conversation_graph
        response_text = f"I heard you say: {speech_text}. How can I assist further?"
        
        call_data["transcript"].append({
            "role": "assistant",
            "text": response_text,
            "timestamp": datetime.utcnow().isoformat()
        })
        save_json_state("calls.json", call_manager)
        
        return {
            "actions": [
                {"type": "say", "text": response_text},
                {"type": "listen", "speech_timeout": "auto"}
            ]
        }
    
    elif event_type == "call.completed":
        # Save call to history
        call_data["status"] = "completed"
        call_data["ended_at"] = datetime.utcnow().isoformat()
        call_manager["call_history"].append(call_data)
        del call_manager["active_calls"][call_sid]
        save_json_state("calls.json", call_manager)
        await persist_call_supabase(call_data)
        
        return {"status": "logged"}
    
    return {"status": "processed"}

@app.post("/voice/calls/{call_sid}/accept")
async def accept_demo_call(call_sid: str):
    """Mark a local/mobile demo call as connected."""
    call_data = call_manager["active_calls"].setdefault(call_sid, {
        "call_sid": call_sid,
        "user_id": "mobile_user",
        "status": "ringing",
        "started_at": datetime.utcnow().isoformat(),
        "transcript": [],
    })
    call_data["status"] = "connected"
    call_data["accepted_at"] = datetime.utcnow().isoformat()
    call_data["translation"] = build_translation_settings(call_data.get("user_id", "mobile_user"))
    save_json_state("calls.json", call_manager)
    await persist_call_supabase(call_data)
    return {"call_sid": call_sid, "status": "connected"}

@app.post("/voice/calls/{call_sid}/reject")
async def reject_demo_call(call_sid: str):
    """Mark a local/mobile demo call as rejected."""
    call_data = call_manager["active_calls"].pop(call_sid, {
        "call_sid": call_sid,
        "user_id": "mobile_user",
        "started_at": datetime.utcnow().isoformat(),
        "transcript": [],
    })
    call_data["status"] = "rejected"
    call_data["ended_at"] = datetime.utcnow().isoformat()
    call_manager["call_history"].append(call_data)
    save_json_state("calls.json", call_manager)
    await persist_call_supabase(call_data)
    return {"call_sid": call_sid, "status": "rejected"}

@app.post("/voice/calls/{call_sid}/hangup")
async def hangup_demo_call(call_sid: str):
    """End a local/mobile demo call and persist it to history."""
    call_data = call_manager["active_calls"].pop(call_sid, {
        "call_sid": call_sid,
        "user_id": "mobile_user",
        "started_at": datetime.utcnow().isoformat(),
        "transcript": [],
    })
    call_data["status"] = "completed"
    call_data["ended_at"] = datetime.utcnow().isoformat()
    call_manager["call_history"].append(call_data)
    save_json_state("calls.json", call_manager)
    await persist_call_supabase(call_data)
    return {"call_sid": call_sid, "status": "completed"}

@app.post("/voice/calls/{call_sid}/mute")
async def mute_demo_call(call_sid: str, request: Dict[str, Any]):
    call_data = call_manager["active_calls"].setdefault(call_sid, {"call_sid": call_sid, "transcript": []})
    call_data["muted"] = bool(request.get("muted"))
    save_json_state("calls.json", call_manager)
    await persist_call_supabase(call_data)
    return {"call_sid": call_sid, "muted": call_data["muted"]}

@app.post("/voice/calls/{call_sid}/hold")
async def hold_demo_call(call_sid: str, request: Dict[str, Any]):
    call_data = call_manager["active_calls"].setdefault(call_sid, {"call_sid": call_sid, "transcript": []})
    call_data["status"] = "hold" if request.get("held") else "connected"
    save_json_state("calls.json", call_manager)
    await persist_call_supabase(call_data)
    return {"call_sid": call_sid, "status": call_data["status"]}

@app.websocket("/voice/stream/{call_sid}")
async def voice_websocket_stream(websocket: WebSocket, call_sid: str):
    """
    WebSocket endpoint for real-time bidirectional audio streaming.
    Used for phone calls with the AI receptionist.
    """
    await websocket.accept()
    
    if call_sid not in call_manager["active_calls"]:
        await websocket.send_text(json.dumps({"error": "Invalid call SID"}))
        await websocket.close()
        return
    
    call_data = call_manager["active_calls"][call_sid]
    persona = get_persona(call_data.get("persona_id", "anya"))
    
    try:
        # Send greeting
        welcome = f"Hello! I'm {persona.name}. How can I help you today?"
        await websocket.send_text(json.dumps({
            "type": "ai_response",
            "text": welcome
        }))
        
        while True:
            # Receive audio chunk from caller
            message = await websocket.receive()
            
            if "bytes" in message:
                audio_chunk = message["bytes"]
                
                # Transcribe speech to text
                transcribed_text = await sarvam_stt(audio_chunk)
                
                if transcribed_text:
                    # Log user message
                    call_data["transcript"].append({
                        "role": "user",
                        "text": transcribed_text,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    # Get AI response
                    # TODO: Full integration with ai_conversation_graph
                    response_text = f"Thanks for your message. I'm processing: {transcribed_text}"
                    
                    # Generate TTS audio
                    response_audio = await sarvam_tts(response_text, role=persona.voice_speaker)
                    
                    # Log AI response
                    call_data["transcript"].append({
                        "role": "assistant",
                        "text": response_text,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    # Send back to caller
                    await websocket.send_text(json.dumps({
                        "type": "ai_response",
                        "text": response_text
                    }))
                    
                    if response_audio:
                        await websocket.send_bytes(response_audio)
            
            elif "text" in message:
                # Handle control messages
                text_data = json.loads(message["text"])
                
                if text_data.get("action") == "hangup":
                    call_data["status"] = "completed"
                    await websocket.send_text(json.dumps({"type": "call_ended"}))
                    break
                    
    except WebSocketDisconnect:
        print(f"Voice call {call_sid} disconnected")
    finally:
        # Save call history
        if call_sid in call_manager["active_calls"]:
            call_data["ended_at"] = datetime.utcnow().isoformat()
            call_manager["call_history"].append(call_data)
            del call_manager["active_calls"][call_sid]
            save_json_state("calls.json", call_manager)

@app.post("/whatsapp/send")
async def send_whatsapp_message(request: WhatsAppMessageRequest):
    """
    Send WhatsApp message via WhatsApp Business API.
    """
    message_id = f"MSG_{uuid.uuid4().hex[:16]}"
    
    # TODO: Integrate with WhatsApp Business API
    # For now, return mock response
    
    return {
        "message_id": message_id,
        "status": "sent",
        "to": request.to,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """
    Webhook for incoming WhatsApp messages.
    """
    body = await request.json()
    
    # Extract message details
    from_number = body.get("from")
    message_text = body.get("text", {}).get("body", "")
    message_id = body.get("id")
    
    # Generate AI response
    persona = get_persona("anya")  # Default persona
    
    # TODO: Full AI conversation processing
    response_text = f"Thanks for your message! You said: {message_text}"
    
    # Send response back via WhatsApp
    # TODO: WhatsApp Business API integration
    
    return {
        "status": "processed",
        "response": response_text,
        "message_id": message_id
    }

@app.get("/voice/calls/{call_sid}/status")
async def get_call_status(call_sid: str):
    """Get current status of an active call"""
    if call_sid in call_manager["active_calls"]:
        return call_manager["active_calls"][call_sid]
    
    # Check history
    for call in call_manager["call_history"]:
        if call.get("call_sid") == call_sid:
            return call
    
    raise HTTPException(status_code=404, detail="Call not found")

@app.get("/voice/calls/{call_sid}/transcript")
async def get_call_transcript(call_sid: str):
    """Get full transcript of a call"""
    if call_sid in call_manager["active_calls"]:
        return {"transcript": call_manager["active_calls"][call_sid].get("transcript", [])}
    
    for call in call_manager["call_history"]:
        if call.get("call_sid") == call_sid:
            return {"transcript": call.get("transcript", [])}
    
    raise HTTPException(status_code=404, detail="Call not found")

@app.get("/voice/calls")
async def list_calls(status: Optional[str] = None, limit: int = 50):
    """List all calls with optional filtering"""
    calls = []
    
    # Active calls
    for call_sid, call_data in call_manager["active_calls"].items():
        calls.append({"call_sid": call_sid, **call_data})
    
    # Historical calls
    for call_data in call_manager["call_history"][-limit:]:
        calls.append(call_data)
    
    if status:
        calls = [c for c in calls if c.get("status") == status]
    
    return {"calls": calls[:limit], "total": len(calls)}

@app.get("/receptionist/analytics")
async def get_receptionist_analytics():
    """Get analytics for AI receptionist performance"""
    total_calls = len(call_manager["call_history"])
    active_calls = len(call_manager["active_calls"])
    
    # Calculate metrics
    completed_calls = [c for c in call_manager["call_history"] if c.get("status") == "completed"]
    avg_duration = 0
    
    if completed_calls:
        durations = []
        for call in completed_calls:
            if call.get("started_at") and call.get("ended_at"):
                start = datetime.fromisoformat(call["started_at"])
                end = datetime.fromisoformat(call["ended_at"])
                durations.append((end - start).total_seconds())
        
        if durations:
            avg_duration = sum(durations) / len(durations)
    
    return {
        "total_calls": total_calls,
        "active_calls": active_calls,
        "completed_calls": len(completed_calls),
        "average_duration_seconds": round(avg_duration, 2),
        "success_rate": round(len(completed_calls) / total_calls * 100, 2) if total_calls > 0 else 0
    }


# ==========================================
# WORKFLOW ENGINE API
# ==========================================

from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any

class CreateWorkflowRequest(BaseModel):
    name: str
    trigger: Literal["pre_call", "in_call", "post_call", "on_escalation", "on_booking", "on_order"]
    actions: List[Dict[str, Any]]

class ExecuteWorkflowRequest(BaseModel):
    call_sid: str
    caller_number: str
    caller_name: Optional[str] = None
    persona_id: str = "anya"
    metadata: Optional[Dict[str, Any]] = None

@app.post("/workflows")
async def create_workflow(request: CreateWorkflowRequest):
    """Create a new workflow for automation"""
    workflow_id = f"WF_{uuid.uuid4().hex[:12]}"
    
    actions = []
    for i, action_data in enumerate(request.actions):
        action = WorkflowAction(
            id=f"{workflow_id}_action_{i}",
            type=ActionType(action_data.get("type", "webhook")),
            config=action_data.get("config", {}),
            conditions=action_data.get("conditions", []),
            on_error=action_data.get("on_error", "continue"),
            retry_count=action_data.get("retry_count", 3)
        )
        actions.append(action)
    
    workflow = Workflow(
        id=workflow_id,
        name=request.name,
        trigger=WorkflowTrigger(request.trigger),
        actions=actions
    )
    
    workflow_engine.create_workflow(workflow)
    
    return {
        "workflow_id": workflow_id,
        "name": request.name,
        "trigger": request.trigger,
        "actions_count": len(actions),
        "status": "created"
    }

@app.get("/workflows")
async def list_workflows(trigger: Optional[str] = None):
    """List all workflows or filter by trigger"""
    trigger_enum = WorkflowTrigger(trigger) if trigger else None
    workflows = workflow_engine.list_workflows(trigger=trigger_enum)
    
    return {
        "workflows": [
            {
                "id": w.id,
                "name": w.name,
                "trigger": w.trigger.value,
                "enabled": w.enabled,
                "actions_count": len(w.actions)
            }
            for w in workflows
        ],
        "total": len(workflows)
    }

@app.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get workflow details"""
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return {
        "id": workflow.id,
        "name": workflow.name,
        "trigger": workflow.trigger.value,
        "enabled": workflow.enabled,
        "actions": [
            {
                "id": a.id,
                "type": a.type.value,
                "config": a.config,
                "conditions": a.conditions
            }
            for a in workflow.actions
        ]
    }

@app.post("/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, request: ExecuteWorkflowRequest):
    """Execute a workflow manually"""
    context = CallContext(
        call_sid=request.call_sid,
        caller_number=request.caller_number,
        caller_name=request.caller_name,
        persona_id=request.persona_id,
        metadata=request.metadata or {}
    )
    
    result = await workflow_engine.execute_workflow(workflow_id, context)
    return result

@app.post("/workflows/trigger/{trigger}")
async def trigger_workflows(trigger: str, request: ExecuteWorkflowRequest):
    """Trigger all workflows for a specific trigger type"""
    try:
        trigger_enum = WorkflowTrigger(trigger)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid trigger: {trigger}")
    
    context = CallContext(
        call_sid=request.call_sid,
        caller_number=request.caller_number,
        caller_name=request.caller_name,
        persona_id=request.persona_id,
        metadata=request.metadata or {}
    )
    
    results = await workflow_engine.trigger_workflows(trigger_enum, context)
    return {
        "trigger": trigger,
        "executed": len(results),
        "results": results
    }

@app.get("/workflows/executions/history")
async def get_workflow_history(call_sid: Optional[str] = None, limit: int = 100):
    """Get workflow execution history"""
    history = workflow_engine.get_execution_history(call_sid=call_sid, limit=limit)
    return {
        "executions": history,
        "total": len(history)
    }


# ==========================================
# BOOKING SYSTEM API
# ==========================================

class CreateBookingRequest(BaseModel):
    customer_name: str
    customer_phone: str
    service_id: str
    start_time: datetime
    customer_email: Optional[str] = None
    notes: str = ""

class RescheduleBookingRequest(BaseModel):
    new_start_time: datetime

@app.get("/booking/services")
async def list_services(service_type: Optional[str] = None):
    """List all available booking services"""
    bs = get_booking_system()
    
    service_type_enum = None
    if service_type:
        try:
            service_type_enum = ServiceType(service_type)
        except ValueError:
            pass
    
    services = bs.list_services(service_type=service_type_enum)
    
    return {
        "services": [
            {
                "id": s.id,
                "name": s.name,
                "type": s.type.value,
                "duration_minutes": s.duration_minutes,
                "price": s.price,
                "description": s.description
            }
            for s in services
        ]
    }

@app.get("/booking/slots")
async def get_available_slots(
    date: str,  # ISO format date string
    service_id: str
):
    """Get available time slots for a date and service"""
    bs = get_booking_system()
    
    try:
        date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
    except:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")
    
    slots = bs.get_available_slots(date_obj, service_id)
    
    return {
        "date": date,
        "service_id": service_id,
        "slots": [
            {
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat(),
                "available": s.available
            }
            for s in slots
        ]
    }

@app.post("/bookings")
async def create_booking(request: CreateBookingRequest):
    """Create a new booking/appointment"""
    bs = get_booking_system()
    
    result = bs.create_booking(
        customer_name=request.customer_name,
        customer_phone=request.customer_phone,
        service_id=request.service_id,
        start_time=request.start_time,
        customer_email=request.customer_email,
        notes=request.notes
    )
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.post("/bookings/{booking_id}/confirm")
async def confirm_booking(booking_id: str):
    """Confirm a pending booking"""
    bs = get_booking_system()
    result = bs.confirm_booking(booking_id)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.post("/bookings/{booking_id}/reschedule")
async def reschedule_booking(booking_id: str, request: RescheduleBookingRequest):
    """Reschedule an existing booking"""
    bs = get_booking_system()
    result = bs.reschedule_booking(booking_id, request.new_start_time)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.post("/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: str, reason: str = ""):
    """Cancel a booking"""
    bs = get_booking_system()
    result = bs.cancel_booking(booking_id, reason)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.get("/bookings/{booking_id}")
async def get_booking(booking_id: str):
    """Get booking details"""
    bs = get_booking_system()
    booking = bs.get_booking(booking_id)
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return {
        "id": booking.id,
        "customer_name": booking.customer_name,
        "customer_phone": booking.customer_phone,
        "customer_email": booking.customer_email,
        "service_id": booking.service_id,
        "service_name": booking.service_name,
        "start_time": booking.start_time.isoformat(),
        "end_time": booking.end_time.isoformat(),
        "status": booking.status.value,
        "notes": booking.notes,
        "created_at": booking.created_at,
        "confirmation_sent": booking.confirmation_sent,
        "reminder_sent": booking.reminder_sent
    }

@app.get("/bookings")
async def list_bookings(
    customer_phone: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 50
):
    """List bookings with filters"""
    bs = get_booking_system()
    
    status_enum = None
    if status:
        try:
            status_enum = BookingStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    bookings = bs.list_bookings(
        customer_phone=customer_phone,
        status=status_enum,
        date_from=date_from,
        date_to=date_to,
        limit=limit
    )
    
    return {
        "bookings": [
            {
                "id": b.id,
                "customer_name": b.customer_name,
                "service_name": b.service_name,
                "start_time": b.start_time.isoformat(),
                "status": b.status.value
            }
            for b in bookings
        ],
        "total": len(bookings)
    }

@app.get("/booking/schedule/{date}")
async def get_day_schedule(date: str):
    """Get full schedule for a specific day"""
    bs = get_booking_system()
    
    try:
        date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
    except:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    schedule = bs.get_day_schedule(date_obj)
    return schedule

@app.get("/booking/stats")
async def get_booking_stats(days: int = 30):
    """Get booking statistics"""
    bs = get_booking_system()
    stats = bs.get_booking_stats(days=days)
    return stats


# ==========================================
# CRM INTEGRATION API
# ==========================================

class CRMCustomer(BaseModel):
    customer_id: str
    name: str
    email: Optional[str]
    phone: str
    tags: List[str] = []
    last_contact: Optional[str] = None
    total_calls: int = 0
    notes: str = ""

# In-memory CRM storage (replace with real DB in production)
crm_storage: Dict[str, CRMCustomer] = {}

@app.get("/crm/customers/{customer_id}")
async def get_crm_customer(customer_id: str):
    """Get customer details from CRM"""
    customer = crm_storage.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer.dict()

@app.get("/crm/customers")
async def list_crm_customers(
    phone: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 50
):
    """List CRM customers with filters"""
    customers = list(crm_storage.values())
    
    if phone:
        customers = [c for c in customers if c.phone == phone]
    
    if tag:
        customers = [c for c in customers if tag in c.tags]
    
    return {
        "customers": [c.dict() for c in customers[:limit]],
        "total": len(customers)
    }

@app.post("/crm/customers")
async def create_crm_customer(customer: CRMCustomer):
    """Create or update a CRM customer"""
    crm_storage[customer.customer_id] = customer
    return {"status": "created", "customer_id": customer.customer_id}

@app.post("/crm/customers/{customer_id}/interactions")
async def add_crm_interaction(
    customer_id: str,
    interaction_type: str,
    call_sid: Optional[str] = None,
    notes: str = ""
):
    """Add an interaction to customer history"""
    customer = crm_storage.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Update last contact
    customer.last_contact = datetime.utcnow().isoformat()
    if interaction_type == "call":
        customer.total_calls += 1
    
    return {
        "status": "logged",
        "customer_id": customer_id,
        "interaction_type": interaction_type,
        "timestamp": customer.last_contact
    }

@app.get("/crm/customers/{customer_id}/history")
async def get_customer_history(customer_id: str):
    """Get customer interaction history"""
    customer = crm_storage.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get call history for this customer
    calls = [
        c for c in call_manager.get("call_history", [])
        if c.get("from") == customer.phone or c.get("caller_number") == customer.phone
    ]
    
    return {
        "customer": customer.dict(),
        "calls": calls,
        "total_interactions": customer.total_calls
    }


# ==========================================
# SPRINT 3: MULTI-CHANNEL INTEGRATION
# ==========================================

# Initialize multi-channel components
twilio = get_twilio_integration()
widget_generator = get_widget_generator()
channel_router = get_channel_router()
booking_system = get_booking_system()
analytics = get_analytics_engine()

# --- Twilio Voice Integration ---

class TwilioMakeCallRequest(BaseModel):
    to_number: str
    from_number: Optional[str] = None
    persona_id: str = "anya"
    context: Optional[Dict[str, Any]] = None

class TwilioTransferRequest(BaseModel):
    transfer_to: str
    whisper_message: Optional[str] = None

@app.post("/voice/twilio/calls")
async def twilio_make_call(request: TwilioMakeCallRequest):
    """Make an outbound phone call via Twilio"""
    if not twilio.is_configured():
        raise HTTPException(status_code=503, detail="Twilio not configured")
    
    result = await twilio.make_outbound_call(
        to_number=request.to_number,
        from_number=request.from_number,
        persona_id=request.persona_id,
        context=request.context
    )
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.post("/webhooks/twilio/inbound")
async def twilio_inbound_webhook(request: Request):
    """Handle inbound call webhook from Twilio"""
    form_data = await request.form()
    data = dict(form_data)
    
    twiml = await twilio.handle_inbound_webhook(data)
    
    from fastapi.responses import Response
    return Response(content=twiml, media_type="application/xml")

@app.post("/webhooks/twilio/status")
async def twilio_status_webhook(request: Request):
    """Handle Twilio status callbacks"""
    form_data = await request.form()
    data = dict(form_data)
    
    result = await twilio.handle_status_callback(data)
    return result

@app.post("/webhooks/twilio/recording")
async def twilio_recording_webhook(request: Request):
    """Handle recording completion webhook"""
    form_data = await request.form()
    data = dict(form_data)
    
    return {
        "status": "received",
        "recording_url": data.get("RecordingUrl"),
        "call_sid": data.get("CallSid")
    }

@app.websocket("/voice/stream/twilio/{call_sid}")
async def twilio_websocket_stream(websocket: WebSocket, call_sid: str):
    """WebSocket endpoint for Twilio Media Streams"""
    await websocket.accept()
    
    async def audio_callback(call_sid: str, audio_chunk: bytes):
        """Process audio from caller"""
        # TODO: Integrate with STT and AI response
        # This is where you'd:
        # 1. Transcribe audio to text
        # 2. Get AI response
        # 3. Generate TTS audio
        # 4. Send back to caller
        pass
    
    await twilio.handle_twilio_stream(websocket, call_sid, audio_callback)

@app.post("/voice/twilio/calls/{call_sid}/hangup")
async def twilio_hangup_call(call_sid: str):
    """End an active Twilio call"""
    if not twilio.is_configured():
        raise HTTPException(status_code=503, detail="Twilio not configured")
    
    result = await twilio.hangup_call(call_sid)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.post("/voice/twilio/calls/{call_sid}/transfer")
async def twilio_transfer_call(call_sid: str, request: TwilioTransferRequest):
    """Transfer an active call to another number"""
    if not twilio.is_configured():
        raise HTTPException(status_code=503, detail="Twilio not configured")
    
    result = await twilio.transfer_call(
        call_sid=call_sid,
        transfer_to=request.transfer_to,
        whisper_message=request.whisper_message
    )
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.get("/voice/twilio/calls")
async def list_twilio_calls(
    status: Optional[str] = None,
    direction: Optional[str] = None,
    limit: int = 50
):
    """List Twilio calls with filtering"""
    status_enum = CallStatus(status) if status else None
    direction_enum = CallDirection(direction) if direction else None
    
    calls = twilio.list_calls(
        status=status_enum,
        direction=direction_enum,
        limit=limit
    )
    
    return {
        "calls": [
            {
                "call_sid": c.call_sid,
                "direction": c.direction.value,
                "from": c.from_number,
                "to": c.to_number,
                "status": c.status.value,
                "duration": c.duration,
                "started_at": c.started_at,
                "ended_at": c.ended_at
            }
            for c in calls
        ],
        "total": len(calls)
    }

@app.get("/voice/twilio/analytics")
async def get_twilio_analytics():
    """Get Twilio call analytics"""
    return twilio.get_analytics()


# --- Web Widget Integration ---

class CreateWidgetRequest(BaseModel):
    business_id: str
    business_name: str
    persona_id: str = "anya"
    primary_color: str = "#3B82F6"
    position: str = "bottom-right"
    greeting_message: str = "Hi there! How can I help you today?"
    auto_open: bool = False
    auto_open_delay: int = 5
    show_avatar: bool = True
    allow_voice: bool = True
    allowed_domains: List[str] = []

class WidgetMessageRequest(BaseModel):
    widget_id: str
    business_id: str
    message: str
    persona_id: str = "anya"
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None

@app.post("/widgets")
async def create_widget(request: CreateWidgetRequest):
    """Create a new web widget"""
    widget_id = f"WG_{uuid.uuid4().hex[:12]}"
    
    config = WidgetConfig(
        widget_id=widget_id,
        business_id=request.business_id,
        business_name=request.business_name,
        persona_id=request.persona_id,
        primary_color=request.primary_color,
        position=request.position,
        greeting_message=request.greeting_message,
        auto_open=request.auto_open,
        auto_open_delay=request.auto_open_delay,
        show_avatar=request.show_avatar,
        allow_voice=request.allow_voice,
        allowed_domains=request.allowed_domains
    )
    
    widget_generator.create_widget(config)
    
    # Generate embed code
    embed_code = widget_generator.generate_embed_code(
        widget_id,
        os.getenv("PUBLIC_BASE_URL", "https://api.avatario.com")
    )
    
    return {
        "widget_id": widget_id,
        "status": "created",
        "embed_code": embed_code,
        "config": {
            "business_name": request.business_name,
            "position": request.position,
            "primary_color": request.primary_color
        }
    }

@app.get("/widgets/{widget_id}")
async def get_widget(widget_id: str):
    """Get widget configuration"""
    widget = widget_generator.get_widget(widget_id)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    return {
        "widget_id": widget.widget_id,
        "business_id": widget.business_id,
        "business_name": widget.business_name,
        "persona_id": widget.persona_id,
        "primary_color": widget.primary_color,
        "position": widget.position,
        "greeting_message": widget.greeting_message,
        "auto_open": widget.auto_open,
        "show_avatar": widget.show_avatar,
        "allow_voice": widget.allow_voice
    }

@app.get("/widgets/{widget_id}/embed")
async def get_widget_embed(widget_id: str):
    """Get widget embed code"""
    widget = widget_generator.get_widget(widget_id)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    embed_code = widget_generator.generate_embed_code(
        widget_id,
        os.getenv("PUBLIC_BASE_URL", "https://api.avatario.com")
    )
    
    iframe_code = widget_generator.generate_iframe_embed(
        widget_id,
        os.getenv("PUBLIC_BASE_URL", "https://api.avatario.com")
    )
    
    return {
        "widget_id": widget_id,
        "javascript_embed": embed_code,
        "iframe_embed": iframe_code
    }

@app.post("/widget/message")
async def handle_widget_message(request: WidgetMessageRequest):
    """Handle message from web widget"""
    # Route through channel router
    message = channel_router.route_inbound_message(
        channel=Channel.WEB_WIDGET,
        sender_id=request.widget_id,
        content=request.message,
        metadata={
            "persona_id": request.persona_id,
            "customer_name": request.customer_name,
            "customer_email": request.customer_email,
            "business_id": request.business_id
        },
        recipient_id=request.business_id
    )
    
    # TODO: Get AI response
    response_text = f"Thanks for your message! You said: {request.message}"
    
    # Send response back through channel router
    channel_router.route_outbound_message(
        conversation_id=message.conversation_id,
        content=response_text
    )
    
    return {
        "response": response_text,
        "conversation_id": message.conversation_id,
        "message_id": message.id
    }

@app.get("/widget/v1/avatar-widget.js")
async def serve_widget_script():
    """Serve the widget JavaScript file"""
    from fastapi.responses import Response
    
    script = widget_generator.generate_widget_script()
    
    return Response(
        content=script,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*"
        }
    )


# --- Unified Inbox ---

@app.get("/inbox/unified")
async def get_unified_inbox(
    business_id: Optional[str] = None,
    show_closed: bool = False,
    limit: int = 50
):
    """Get unified inbox across all channels"""
    inbox = channel_router.get_unified_inbox(
        business_id=business_id,
        show_closed=show_closed,
        limit=limit
    )
    
    return {
        "total": inbox["total"],
        "active": inbox["active"],
        "waiting": inbox["waiting"],
        "escalated": inbox["escalated"],
        "channels": {
            channel: {
                "total": data["total"],
                "unread": data["unread"],
                "conversations": [
                    {
                        "id": c.id,
                        "channel": c.channel.value,
                        "customer_id": c.customer_id,
                        "customer_name": c.customer_name,
                        "status": c.status,
                        "priority": c.priority,
                        "assigned_to": c.assigned_to,
                        "last_message_at": c.last_message_at,
                        "message_count": len(c.messages),
                        "tags": c.tags
                    }
                    for c in data["conversations"][:10]  # Limit per channel
                ]
            }
            for channel, data in inbox["channels"].items()
        },
        "all_conversations": [
            {
                "id": c.id,
                "channel": c.channel.value,
                "customer_id": c.customer_id,
                "customer_name": c.customer_name,
                "status": c.status,
                "priority": c.priority,
                "last_message_at": c.last_message_at
            }
            for c in inbox["all"]
        ]
    }

@app.get("/inbox/conversations")
async def list_conversations(
    channel: Optional[str] = None,
    status: Optional[str] = None,
    business_id: Optional[str] = None,
    limit: int = 50
):
    """List conversations with filtering"""
    channel_enum = Channel(channel) if channel else None
    
    conversations = channel_router.list_conversations(
        channel=channel_enum,
        status=status,
        business_id=business_id,
        limit=limit
    )
    
    return {
        "conversations": [
            {
                "id": c.id,
                "channel": c.channel.value,
                "customer_id": c.customer_id,
                "customer_name": c.customer_name,
                "status": c.status,
                "priority": c.priority,
                "assigned_to": c.assigned_to,
                "message_count": len(c.messages),
                "created_at": c.created_at,
                "last_message_at": c.last_message_at,
                "tags": c.tags
            }
            for c in conversations
        ],
        "total": len(conversations)
    }

@app.get("/inbox/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, message_limit: int = 100):
    """Get conversation details with messages"""
    history = channel_router.get_conversation_history(conversation_id, message_limit)
    
    if not history:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation = history["conversation"]
    messages = history["messages"]
    
    return {
        "conversation": {
            "id": conversation.id,
            "channel": conversation.channel.value,
            "customer_id": conversation.customer_id,
            "customer_name": conversation.customer_name,
            "customer_email": conversation.customer_email,
            "status": conversation.status,
            "priority": conversation.priority,
            "assigned_to": conversation.assigned_to,
            "tags": conversation.tags,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at
        },
        "messages": [
            {
                "id": m.id,
                "direction": m.direction,
                "type": m.message_type.value,
                "content": m.content,
                "media_url": m.media_url,
                "timestamp": m.timestamp,
                "read": m.read,
                "delivered": m.delivered
            }
            for m in messages
        ],
        "total_messages": history["total_messages"]
    }

@app.post("/inbox/conversations/{conversation_id}/reply")
async def reply_to_conversation(conversation_id: str, message: str):
    """Send a reply to a conversation"""
    result = channel_router.route_outbound_message(
        conversation_id=conversation_id,
        content=message
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "success": True,
        "message_id": result.id,
        "conversation_id": conversation_id,
        "timestamp": result.timestamp
    }

@app.post("/inbox/conversations/{conversation_id}/close")
async def close_conversation(conversation_id: str, reason: str = ""):
    """Close a conversation"""
    success = channel_router.close_conversation(conversation_id, reason)
    
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"success": True, "conversation_id": conversation_id, "status": "closed"}

@app.post("/inbox/conversations/{conversation_id}/assign")
async def assign_conversation(
    conversation_id: str,
    agent_id: str,
    priority: Optional[str] = None
):
    """Assign conversation to an agent"""
    success = channel_router.assign_conversation(conversation_id, agent_id, priority)
    
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "success": True,
        "conversation_id": conversation_id,
        "assigned_to": agent_id,
        "priority": priority
    }

@app.get("/inbox/stats")
async def get_inbox_stats():
    """Get inbox statistics by channel"""
    return channel_router.get_channel_stats()

@app.get("/inbox/search")
async def search_conversations(query: str, limit: int = 20):
    """Search conversations by content"""
    results = channel_router.search_conversations(query, limit=limit)
    
    return {
        "query": query,
        "results": [
            {
                "id": c.id,
                "channel": c.channel.value,
                "customer_id": c.customer_id,
                "customer_name": c.customer_name,
                "status": c.status,
                "last_message_at": c.last_message_at
            }
            for c in results
        ],
        "total": len(results)
    }


# ==========================================
# SPRINT 4: INTELLIGENCE & ANALYTICS
# ==========================================

# --- Analytics Dashboard ---

@app.get("/analytics/dashboard")
async def get_analytics_dashboard():
    """Get comprehensive analytics dashboard data"""
    return analytics.generate_dashboard_data()

@app.get("/analytics/metrics/{metric_type}")
async def get_metric_summary(
    metric_type: str,
    hours: int = 24
):
    """Get summary for a specific metric"""
    try:
        metric_enum = MetricType(metric_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid metric type: {metric_type}")
    
    return analytics.get_metrics_summary(metric_enum, hours)

@app.get("/analytics/metrics/{metric_type}/timeseries")
async def get_metric_timeseries(
    metric_type: str,
    granularity: str = "hourly",
    hours: int = 24
):
    """Get time series data for a metric"""
    try:
        metric_enum = MetricType(metric_type)
        granularity_enum = TimeGranularity(granularity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "metric": metric_type,
        "granularity": granularity,
        "data": analytics.get_time_series(metric_enum, granularity_enum, hours)
    }

# --- Call Quality Scoring ---

class CallQualityRequest(BaseModel):
    call_sid: str
    transcript: List[Dict]
    resolution_achieved: bool
    escalation_required: bool
    duration_seconds: int

@app.post("/analytics/calls/{call_sid}/quality")
async def score_call_quality(call_sid: str, request: CallQualityRequest):
    """Score the quality of a completed call"""
    score = analytics.score_call_quality(
        call_sid=call_sid,
        transcript=request.transcript,
        resolution_achieved=request.resolution_achieved,
        escalation_required=request.escalation_required,
        duration_seconds=request.duration_seconds
    )
    
    return {
        "call_sid": call_sid,
        "overall_score": score.overall_score,
        "factors": score.factors,
        "resolution_achieved": score.resolution_achieved,
        "escalation_required": score.escalation_required,
        "timestamp": score.timestamp
    }

@app.get("/analytics/calls/quality-summary")
async def get_quality_summary(hours: int = 24):
    """Get summary of call quality scores"""
    return analytics.get_quality_summary(hours)

# --- Sentiment Analysis ---

class SentimentRequest(BaseModel):
    transcript: List[Dict[str, str]]

@app.post("/analytics/calls/{call_sid}/sentiment")
async def analyze_call_sentiment(call_sid: str, request: SentimentRequest):
    """Analyze sentiment for a call transcript"""
    analysis = analytics.analyze_sentiment(call_sid, request.transcript)
    
    return {
        "call_sid": call_sid,
        "overall_sentiment": analysis.overall_sentiment,
        "sentiment_score": analysis.sentiment_score,
        "emotions": analysis.emotions,
        "key_phrases": analysis.key_phrases,
        "timestamp": analysis.timestamp
    }

@app.get("/analytics/calls/{call_sid}/sentiment")
async def get_call_sentiment(call_sid: str):
    """Get stored sentiment analysis for a call"""
    analysis = analytics.sentiment_analyses.get(call_sid)
    if not analysis:
        raise HTTPException(status_code=404, detail="Sentiment analysis not found")
    
    return {
        "call_sid": call_sid,
        "overall_sentiment": analysis.overall_sentiment,
        "sentiment_score": analysis.sentiment_score,
        "emotions": analysis.emotions,
        "timestamp": analysis.timestamp
    }

# --- A/B Testing ---

class CreateABTestRequest(BaseModel):
    name: str
    hypothesis: str
    variants: List[Dict]
    metrics: List[str]
    duration_days: int = 14

class RecordABMetricRequest(BaseModel):
    variant_id: str
    metric_name: str
    value: float

@app.post("/analytics/ab-tests")
async def create_ab_test(request: CreateABTestRequest):
    """Create a new A/B test"""
    test_id = analytics.create_ab_test(
        name=request.name,
        hypothesis=request.hypothesis,
        variants=request.variants,
        metrics=request.metrics,
        duration_days=request.duration_days
    )
    
    return {
        "test_id": test_id,
        "name": request.name,
        "status": "running",
        "message": "A/B test created successfully"
    }

@app.get("/analytics/ab-tests")
async def list_ab_tests():
    """List all A/B tests"""
    return {
        "tests": [
            {
                "test_id": t.test_id,
                "name": t.name,
                "hypothesis": t.hypothesis,
                "status": t.status,
                "start_date": t.start_date,
                "end_date": t.end_date,
                "variant_count": len(t.variants)
            }
            for t in analytics.ab_tests.values()
        ]
    }

@app.get("/analytics/ab-tests/{test_id}")
async def get_ab_test(test_id: str):
    """Get A/B test details and results"""
    results = analytics.get_ab_test_results(test_id)
    if not results:
        raise HTTPException(status_code=404, detail="A/B test not found")
    return results

@app.get("/analytics/ab-tests/{test_id}/variant")
async def get_ab_test_variant(test_id: str, user_id: str):
    """Get variant assignment for a user"""
    variant = analytics.get_ab_test_variant(test_id, user_id)
    if not variant:
        raise HTTPException(status_code=404, detail="No active variant found")
    
    return {
        "test_id": test_id,
        "variant_id": variant.variant_id,
        "name": variant.name,
        "config": variant.config
    }

@app.post("/analytics/ab-tests/{test_id}/metrics")
async def record_ab_metric(test_id: str, request: RecordABMetricRequest):
    """Record a metric for an A/B test variant"""
    analytics.record_ab_test_metric(
        test_id=test_id,
        variant_id=request.variant_id,
        metric_name=request.metric_name,
        value=request.value
    )
    
    return {"status": "recorded"}

# --- Real-time Monitoring ---

@app.get("/analytics/realtime")
async def get_realtime_metrics():
    """Get real-time metrics snapshot"""
    now = datetime.utcnow()
    
    return {
        "timestamp": now.isoformat(),
        "active_calls": len(call_manager["active_calls"]),
        "calls_today": len([
            c for c in call_manager["call_history"]
            if datetime.fromisoformat(c.get("started_at", "1970-01-01")).date() == now.date()
        ]),
        "conversations_active": len([
            c for c in channel_router.conversations.values()
            if c.status == "active"
        ]),
        "bookings_today": len([
            b for b in booking_system.bookings.values()
            if b.start_time.date() == now.date()
        ]),
        "metrics": {
            "call_volume": analytics.get_metrics_summary(MetricType.CALL_VOLUME, 1),
            "response_time": analytics.get_metrics_summary(MetricType.RESPONSE_TIME, 1),
            "sentiment": analytics.get_metrics_summary(MetricType.SENTIMENT_SCORE, 1)
        },
        "alerts": analytics._generate_alerts()
    }

# --- Reports ---

@app.get("/analytics/reports/daily")
async def get_daily_report(date: Optional[str] = None):
    """Generate daily analytics report"""
    if date:
        report_date = datetime.fromisoformat(date)
    else:
        report_date = datetime.utcnow()
    
    next_day = report_date + timedelta(days=1)
    
    # Get calls for the day
    day_calls = [
        c for c in call_manager["call_history"]
        if report_date <= datetime.fromisoformat(c.get("started_at", "1970-01-01")) < next_day
    ]
    
    return {
        "date": report_date.date().isoformat(),
        "summary": {
            "total_calls": len(day_calls),
            "completed": len([c for c in day_calls if c.get("status") == "completed"]),
            "avg_duration": sum(c.get("duration", 0) for c in day_calls) / len(day_calls) if day_calls else 0,
            "escalations": len([c for c in day_calls if c.get("escalated")])
        },
        "hourly_breakdown": analytics.get_time_series(
            MetricType.CALL_VOLUME,
            TimeGranularity.HOURLY,
            24
        ),
        "top_issues": [],  # TODO: Extract from transcripts
        "satisfaction": analytics.get_metrics_summary(MetricType.CUSTOMER_SATISFACTION, 24)
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "voice": "active",
            "booking": "active",
            "workflow": "active",
            "crm": "active",
            "twilio": "configured" if twilio.is_configured() else "not_configured",
            "widget": "active",
            "channels": "active",
            "analytics": "active",
            "voice_cloning": "active"
        }
    }


# ==================== VOICE CLONING API ====================

class VoiceCloneRequest(BaseModel):
    name: str
    description: str = ""
    user_id: str = "default_user"
    labels: Optional[Dict[str, str]] = None


class VoiceSynthesisRequest(BaseModel):
    voice_id: str
    text: str
    model_id: str = "eleven_multilingual_v2"
    stability: float = 0.5
    similarity_boost: float = 0.75


class MobileSettingsRequest(BaseModel):
    user_id: str
    settings: Dict
    push_token: Optional[str] = None


TRANSLATION_LANGUAGE_OPTIONS = [
    {"code": "en-IN", "label": "English"},
    {"code": "hi-IN", "label": "Hindi"},
    {"code": "ta-IN", "label": "Tamil"},
    {"code": "te-IN", "label": "Telugu"},
    {"code": "kn-IN", "label": "Kannada"},
    {"code": "ml-IN", "label": "Malayalam"},
    {"code": "bn-IN", "label": "Bengali"},
    {"code": "mr-IN", "label": "Marathi"},
    {"code": "gu-IN", "label": "Gujarati"},
    {"code": "pa-IN", "label": "Punjabi"},
]
TRANSLATION_LANGUAGE_LABELS = {
    option["code"]: option["label"] for option in TRANSLATION_LANGUAGE_OPTIONS
}


class TranslationSessionRequest(BaseModel):
    user_id: str = "mobile_user"
    translation_enabled: bool = True
    caller_language: str = "auto"
    user_language: str = "en-IN"
    preserve_voice: bool = True


class TranslationUtteranceRequest(BaseModel):
    user_id: str = "mobile_user"
    speaker: Literal["caller", "assistant", "user"]
    text: str
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    synthesize_audio: bool = True


def normalize_language_code(language: Optional[str], fallback: str = "en-IN") -> str:
    if not language:
        return fallback
    if language == "auto":
        return "auto"
    normalized = language.strip()
    return normalized if normalized in TRANSLATION_LANGUAGE_LABELS else fallback


def build_translation_settings(user_id: str, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    settings = mobile_user_settings.get(user_id, {})
    overrides = overrides or {}
    caller_language = overrides.get(
        "caller_language",
        "auto" if settings.get("autoDetectCallerLanguage", True) else settings.get("callerLanguage", "hi-IN"),
    )
    user_language = overrides.get("user_language", settings.get("userLanguage", "en-IN"))
    preserve_voice = overrides.get(
        "preserve_voice",
        settings.get("voicePreservationEnabled", settings.get("useClonedVoice", False)),
    )

    return {
        "enabled": bool(overrides.get("translation_enabled", settings.get("translationEnabled", True))),
        "caller_language": normalize_language_code(caller_language, "hi-IN"),
        "user_language": normalize_language_code(user_language, "en-IN"),
        "auto_detect": caller_language == "auto",
        "preserve_voice": bool(preserve_voice),
        "voice_id": settings.get("selectedVoiceId"),
    }


async def translate_text_with_llm(text: str, source_language: str, target_language: str) -> str:
    if not text.strip() or source_language == target_language:
        return text

    base_url = os.getenv("VLLM_API_BASE", "").rstrip("/")
    if not base_url:
        return text

    if base_url.endswith("/chat/completions"):
        endpoint = base_url
    elif base_url.endswith("/v1"):
        endpoint = f"{base_url}/chat/completions"
    else:
        endpoint = f"{base_url}/v1/chat/completions"

    payload = {
        "model": os.getenv("VLLM_MODEL", "default-model"),
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a realtime phone-call interpreter. Translate faithfully, preserve tone, "
                    "keep names and numbers intact, and return only the translated text."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Translate from {TRANSLATION_LANGUAGE_LABELS.get(source_language, source_language)} "
                    f"to {TRANSLATION_LANGUAGE_LABELS.get(target_language, target_language)}:\n{text}"
                ),
            },
        ],
        "temperature": 0.2,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('VLLM_API_KEY', 'EMPTY')}",
    }

    try:
        import httpx

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip() or text
    except Exception as exc:
        print(f"⚠️  Translation fallback used: {exc}")
        return text


async def synthesize_translation_audio(
    user_id: str,
    text: str,
    target_language: str,
    preserve_voice: bool,
) -> Dict[str, Any]:
    settings = mobile_user_settings.get(user_id, {})
    voice_id = settings.get("selectedVoiceId")

    if preserve_voice and settings.get("useClonedVoice") and voice_id:
        try:
            audio_bytes = await voice_cloning_engine.synthesize_speech(
                voice_id=voice_id,
                text=text,
                model_id="eleven_multilingual_v2",
            )
            return {
                "audio_base64": base64.b64encode(audio_bytes).decode(),
                "mime_type": "audio/mpeg",
                "voice_mode": "cloned_voice",
            }
        except Exception as exc:
            print(f"⚠️  Cloned-voice synthesis failed, falling back to Sarvam: {exc}")

    audio_bytes = await sarvam_tts(text, role="client", target_language_code=target_language)
    if not audio_bytes:
        return {"audio_base64": None, "mime_type": None, "voice_mode": "none"}

    return {
        "audio_base64": base64.b64encode(audio_bytes).decode(),
        "mime_type": "audio/wav",
        "voice_mode": "sarvam_tts",
    }


@app.post("/voice/clone")
async def clone_voice(
    name: str = Form(...),
    description: str = Form(""),
    user_id: str = Form("default_user"),
    files: List[UploadFile] = File(...)
):
    """Clone a voice from uploaded audio samples"""
    try:
        # Convert uploaded files to file-like objects
        audio_files = []
        for file in files:
            content = await file.read()
            from io import BytesIO
            audio_files.append(BytesIO(content))
        
        voice = await voice_cloning_engine.clone_voice(
            user_id=user_id,
            name=name,
            description=description,
            audio_files=audio_files
        )
        
        return {
            "voice_id": voice.id,
            "elevenlabs_voice_id": voice.elevenlabs_voice_id,
            "name": voice.name,
            "status": voice.status.value,
            "created_at": voice.created_at.isoformat(),
            "message": "Voice cloning started" if voice.status == VoiceStatus.PROCESSING else "Voice ready"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice cloning failed: {str(e)}")


@app.get("/voice/clones/{user_id}")
async def get_user_cloned_voices(user_id: str):
    """Get all cloned voices for a user"""
    voices = voice_cloning_engine.get_user_voices(user_id)
    return {
        "voices": [
            {
                "id": v.id,
                "name": v.name,
                "elevenlabs_voice_id": v.elevenlabs_voice_id,
                "status": v.status.value,
                "created_at": v.created_at.isoformat(),
                "preview_url": v.preview_url,
                "description": v.description,
            }
            for v in voices
        ]
    }


@app.get("/voice/clones/{voice_id}/details")
async def get_voice_details(voice_id: str):
    """Get details of a specific cloned voice"""
    voice = voice_cloning_engine.get_voice(voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    
    return {
        "id": voice.id,
        "name": voice.name,
        "elevenlabs_voice_id": voice.elevenlabs_voice_id,
        "status": voice.status.value,
        "created_at": voice.created_at.isoformat(),
        "updated_at": voice.updated_at.isoformat(),
        "preview_url": voice.preview_url,
        "description": voice.description,
        "sample_count": voice.sample_count,
    }


@app.delete("/voice/clones/{voice_id}")
async def delete_cloned_voice(voice_id: str):
    """Delete a cloned voice"""
    success = await voice_cloning_engine.delete_voice(voice_id)
    if not success:
        raise HTTPException(status_code=404, detail="Voice not found")
    return {"message": "Voice deleted successfully"}


@app.post("/voice/synthesize")
async def synthesize_speech(request: VoiceSynthesisRequest):
    """Synthesize speech using a cloned voice"""
    try:
        audio_data = await voice_cloning_engine.synthesize_speech(
            voice_id=request.voice_id,
            text=request.text,
            model_id=request.model_id,
            stability=request.stability,
            similarity_boost=request.similarity_boost
        )
        
        # Save to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(audio_data)
            audio_path = f.name
        
        return {
            "voice_id": request.voice_id,
            "audio_url": f"/voice/audio/{Path(audio_path).name}",
            "text": request.text,
            "duration": len(audio_data) / 24000  # Approximate duration
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


# ==================== MOBILE APP API ====================

# Store mobile user settings
mobile_user_settings: Dict[str, Dict] = load_json_state("mobile_settings.json", {})
mobile_push_tokens: Dict[str, str] = load_json_state("mobile_push_tokens.json", {})


@app.post("/mobile/settings")
async def update_mobile_settings(request: MobileSettingsRequest):
    """Update mobile app settings for call handling"""
    mobile_user_settings[request.user_id] = request.settings
    
    if request.push_token:
        mobile_push_tokens[request.user_id] = request.push_token
        save_json_state("mobile_push_tokens.json", mobile_push_tokens)
        await persist_push_token_supabase(request.user_id, request.push_token, "ios")
    save_json_state("mobile_settings.json", mobile_user_settings)
    await persist_mobile_settings_supabase(request.user_id, request.settings)
    
    # Log the settings change
    print(f"Updated settings for user {request.user_id}: {request.settings}")
    
    return {
        "user_id": request.user_id,
        "settings": request.settings,
        "push_registered": request.push_token is not None,
        "message": "Settings updated successfully"
    }


@app.get("/mobile/settings/{user_id}")
async def get_mobile_settings(user_id: str):
    """Get mobile app settings for a user"""
    settings = mobile_user_settings.get(user_id, {})
    return {
        "user_id": user_id,
        "settings": settings,
        "call_handling_enabled": settings.get("enabled", False),
    }


@app.get("/mobile/translation/languages")
async def get_mobile_translation_languages():
    """List supported languages for the mobile live-translation flow."""
    return {"languages": TRANSLATION_LANGUAGE_OPTIONS}


@app.post("/voice/calls/{call_sid}/translation/start")
async def start_translation_session(call_sid: str, request: TranslationSessionRequest):
    """Initialize translation preferences for a live or demo call."""
    call_data = call_manager["active_calls"].setdefault(call_sid, {
        "call_sid": call_sid,
        "user_id": request.user_id,
        "status": "ringing",
        "started_at": datetime.utcnow().isoformat(),
        "transcript": [],
    })
    call_data["user_id"] = request.user_id
    call_data["translation"] = build_translation_settings(request.user_id, request.model_dump())
    save_json_state("calls.json", call_manager)
    await persist_call_supabase(call_data)
    return {"call_sid": call_sid, "translation": call_data["translation"]}


@app.get("/voice/calls/{call_sid}/translation")
async def get_translation_session(call_sid: str):
    """Read the live translation state for a call."""
    call_data = call_manager["active_calls"].get(call_sid)
    if not call_data:
        call_data = next((call for call in call_manager["call_history"] if call.get("call_sid") == call_sid), None)
    if not call_data:
        raise HTTPException(status_code=404, detail="Call not found")
    return {
        "call_sid": call_sid,
        "translation": call_data.get("translation", build_translation_settings(call_data.get("user_id", "mobile_user"))),
    }


@app.post("/voice/calls/{call_sid}/translation/utterance")
async def process_translation_utterance(call_sid: str, request: TranslationUtteranceRequest):
    """Translate one side of a call and optionally synthesize audio for playback."""
    call_data = call_manager["active_calls"].get(call_sid)
    if not call_data:
        raise HTTPException(status_code=404, detail="Call not found")

    translation = call_data.get("translation") or build_translation_settings(request.user_id)
    caller_language = translation.get("caller_language", "hi-IN")
    user_language = translation.get("user_language", "en-IN")

    default_source = caller_language if request.speaker == "caller" else user_language
    default_target = user_language if request.speaker == "caller" else caller_language
    source_language = normalize_language_code(request.source_language or default_source, "en-IN")
    target_language = normalize_language_code(request.target_language or default_target, "en-IN")

    translated_text = await translate_text_with_llm(request.text, source_language, target_language)
    entry = {
        "role": request.speaker,
        "text": request.text,
        "translated_text": translated_text,
        "source_language": source_language,
        "target_language": target_language,
        "timestamp": datetime.utcnow().isoformat(),
    }
    call_data.setdefault("transcript", []).append(entry)
    save_json_state("calls.json", call_manager)
    await persist_call_supabase(call_data)

    audio_payload = {"audio_base64": None, "mime_type": None, "voice_mode": "none"}
    should_preserve_voice = request.speaker in {"assistant", "user"} and translation.get("preserve_voice", False)
    if request.synthesize_audio:
        audio_payload = await synthesize_translation_audio(
            request.user_id,
            translated_text,
            target_language,
            should_preserve_voice,
        )

    return {
        "call_sid": call_sid,
        "speaker": request.speaker,
        "original_text": request.text,
        "translated_text": translated_text,
        "source_language": source_language,
        "target_language": target_language,
        **audio_payload,
    }


@app.post("/mobile/register-push")
async def register_push_token(request: PushTokenRequest):
    """Register push notification token for incoming calls"""
    mobile_push_tokens[request.user_id] = request.push_token
    save_json_state("mobile_push_tokens.json", mobile_push_tokens)
    await persist_push_token_supabase(request.user_id, request.push_token, request.platform)
    
    return {
        "user_id": request.user_id,
        "platform": request.platform,
        "registered": True,
        "message": "Push token registered successfully"
    }


@app.get("/mobile/calls/{user_id}")
async def get_user_calls(user_id: str, limit: int = 20):
    """Get call history for mobile user"""
    calls = [
        call
        for call in call_manager.get("call_history", [])
        if call.get("user_id", "mobile_user") == user_id or user_id in {"demo-001", "mobile_user"}
    ][-limit:]
    return {
        "user_id": user_id,
        "calls": calls,
        "total": len(calls)
    }


# ==================== DEPLOYMENT CONFIG ====================

@app.get("/app/config")
async def get_app_config():
    """Get mobile app configuration"""
    return {
        "app_name": "Avatario AI",
        "version": "1.0.0",
        "features": {
            "voice_cloning": True,
            "call_handling": True,
            "push_notifications": True,
            "offline_mode": False,
        },
        "api_endpoints": {
            "voice_clone": "/voice/clone",
            "voice_synthesize": "/voice/synthesize",
            "mobile_settings": "/mobile/settings",
            "push_register": "/mobile/register-push",
        },
        "limits": {
            "max_voices_per_user": 5,
            "max_recording_duration": 300,  # 5 minutes
            "min_recording_duration": 30,  # 30 seconds
        }
    }


# ==================== CLONED VOICE CALL INTEGRATION ====================

class SetCallVoiceRequest(BaseModel):
    user_id: str
    voice_id: str
    use_cloned_voice: bool = True
    greeting_script: str = "Hello! You've reached me. I'm using my AI assistant to take this call. How can I help you today?"


@app.post("/voice/calls/set-voice")
async def set_call_voice(request: SetCallVoiceRequest):
    """Set the cloned voice to use for a user's phone calls"""
    try:
        # Verify voice exists and is ready
        voice = voice_cloning_engine.get_voice(request.voice_id)
        if not voice:
            raise HTTPException(status_code=404, detail="Voice not found")
        
        if voice.status != VoiceStatus.READY:
            raise HTTPException(status_code=400, detail=f"Voice not ready. Status: {voice.status.value}")
        
        # Set the voice for the user
        success = await voice_call_integration.set_user_voice(request.user_id, request.voice_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to set voice")
        
        # Update mobile settings
        if request.user_id in mobile_user_settings:
            mobile_user_settings[request.user_id].update({
                'selectedVoiceId': request.voice_id,
                'useClonedVoice': request.use_cloned_voice,
                'greetingScript': request.greeting_script
            })
        
        return {
            "success": True,
            "user_id": request.user_id,
            "voice_id": request.voice_id,
            "voice_name": voice.name,
            "use_cloned_voice": request.use_cloned_voice,
            "message": "Voice set successfully for phone calls"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting voice: {str(e)}")


@app.get("/voice/calls/get-voice/{user_id}")
async def get_call_voice(user_id: str):
    """Get the current voice settings for a user's calls"""
    voice_id = voice_call_integration.get_user_voice(user_id)
    settings = mobile_user_settings.get(user_id, {})
    
    if voice_id:
        voice = voice_cloning_engine.get_voice(voice_id)
        return {
            "user_id": user_id,
            "voice_id": voice_id,
            "voice_name": voice.name if voice else None,
            "voice_status": voice.status.value if voice else None,
            "use_cloned_voice": settings.get('useClonedVoice', False),
            "greeting_script": settings.get('greetingScript'),
            "preview_url": voice.preview_url if voice else None
        }
    else:
        return {
            "user_id": user_id,
            "voice_id": None,
            "use_cloned_voice": settings.get('useClonedVoice', False),
            "greeting_script": settings.get('greetingScript'),
            "message": "No cloned voice set. Using default TTS."
        }


@app.post("/voice/calls/test-greeting")
async def test_call_greeting(user_id: str, custom_text: Optional[str] = None):
    """Test the greeting that will be used for calls"""
    try:
        # Get user's voice settings
        settings = mobile_user_settings.get(user_id, {})
        voice_id = settings.get('selectedVoiceId')
        use_cloned = settings.get('useClonedVoice', False)
        greeting = custom_text or settings.get('greetingScript')
        
        if use_cloned and voice_id:
            # Generate with cloned voice
            audio_data = await voice_cloning_engine.synthesize_speech(
                voice_id=voice_id,
                text=greeting or "Hello! This is a test of my cloned voice.",
                stability=0.5,
                similarity_boost=0.75
            )
            
            # Save to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                f.write(audio_data)
                audio_path = f.name
            
            return {
                "success": True,
                "user_id": user_id,
                "voice_id": voice_id,
                "greeting": greeting,
                "audio_url": f"/voice/audio/{Path(audio_path).name}",
                "using_cloned_voice": True
            }
        else:
            return {
                "success": True,
                "user_id": user_id,
                "greeting": greeting,
                "using_cloned_voice": False,
                "message": "Using default TTS (no cloned voice configured)"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating greeting: {str(e)}")


# Updated Twilio webhook to use cloned voice
@app.post("/webhooks/twilio/inbound-cloned")
async def twilio_inbound_webhook_cloned(request: Request):
    """Handle inbound Twilio calls with cloned voice support"""
    form_data = await request.form()
    request_data = dict(form_data)
    
    call_sid = request_data.get("CallSid")
    from_number = request_data.get("From")
    to_number = request_data.get("To")
    
    # Get user_id from phone number mapping (in production, lookup from database)
    # For now, use default_user
    user_id = "default_user"
    
    # Generate TwiML with cloned voice
    twiml = await handle_inbound_call_with_cloned_voice(
        call_sid=call_sid,
        from_number=from_number,
        to_number=to_number,
        user_id=user_id
    )
    
    from fastapi.responses import Response
    return Response(content=twiml, media_type="application/xml")


# WebSocket endpoint for streaming with cloned voice
@app.websocket("/voice/stream/twilio/{call_sid}")
async def twilio_websocket_stream_cloned(websocket: WebSocket, call_sid: str, user_id: str = "default_user", voice_id: Optional[str] = None):
    """WebSocket endpoint for bidirectional audio streaming with cloned voice"""
    await websocket.accept()
    
    print(f"[WebSocket] Call {call_sid} connected with user {user_id}")
    
    try:
        # Initialize call with voice settings
        if voice_id:
            await voice_call_integration.set_user_voice(user_id, voice_id)
        
        # Send greeting with cloned voice
        settings = mobile_user_settings.get(user_id, {})
        greeting = settings.get('greetingScript')
        
        # Generate and stream greeting
        greeting_audio = await voice_call_integration.generate_call_greeting(
            call_sid=call_sid,
            user_id=user_id,
            custom_greeting=greeting
        )
        
        if greeting_audio:
            # Stream audio in chunks
            chunk_size = 160  # 20ms at 8kHz
            for i in range(0, len(greeting_audio), chunk_size):
                chunk = greeting_audio[i:i + chunk_size]
                await websocket.send_bytes(chunk)
                await asyncio.sleep(0.02)
        else:
            # Fallback: send text message for TTS on Twilio side
            await websocket.send_text(json.dumps({
                "type": "ai_greeting",
                "text": greeting or "Hello! How can I help you today?"
            }))
        
        # Continue with normal audio streaming loop
        # ... (existing audio processing logic)
        
    except WebSocketDisconnect:
        print(f"[WebSocket] Call {call_sid} disconnected")
    except Exception as e:
        print(f"[WebSocket] Error for call {call_sid}: {e}")
    finally:
        # Cleanup
        voice_call_integration.cleanup_call(call_sid)
        
        # Update call status in Twilio integration
        if call_sid in twilio_integration.active_calls:
            twilio_integration.active_calls[call_sid].status = CallStatus.COMPLETED
            twilio_integration.active_calls[call_sid].ended_at = datetime.utcnow().isoformat()


# ==================== CLONE LLM API (Digital Twin Intelligence) ====================

class CreateCloneRequest(BaseModel):
    user_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    bio: Optional[str] = None
    expertise: List[str] = []
    model_name: str = "gpt-4o"


class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class DocumentUploadRequest(BaseModel):
    clone_id: str
    source_type: str = "text"  # text, email, chat, pdf, etc.


@app.post("/clone/create")
async def create_clone(request: CreateCloneRequest):
    """Create a new AI clone of a person"""
    try:
        # Create user profile
        profile = UserProfile(
            name=request.name,
            email=request.email,
            phone=request.phone,
            job_title=request.job_title,
            company=request.company,
            bio=request.bio,
            expertise=request.expertise
        )
        
        # Create the clone
        clone_id = await clone_llm_engine.create_clone(
            user_id=request.user_id,
            model_name=request.model_name,
            user_profile=profile
        )
        
        return {
            "success": True,
            "clone_id": clone_id,
            "user_id": request.user_id,
            "name": request.name,
            "status": "created",
            "message": "Clone created successfully. Now upload documents to train it."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create clone: {str(e)}")


@app.post("/clone/{clone_id}/upload-text")
async def upload_text_documents(
    clone_id: str,
    text_content: str = Form(...),
    source_name: str = Form("manual_upload")
):
    """Upload text documents to train the clone"""
    try:
        # Create document from text
        from langchain_core.documents import Document
        documents = [Document(
            page_content=text_content,
            metadata={"source": source_name, "type": "text"}
        )]
        
        result = await clone_llm_engine.ingest_documents(clone_id, documents, "text")
        
        return {
            "success": True,
            "clone_id": clone_id,
            "documents_ingested": result["documents_ingested"],
            "chunks_created": result["chunks_created"],
            "status": result["status"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload documents: {str(e)}")


@app.post("/clone/{clone_id}/upload-files")
async def upload_file_documents(
    clone_id: str,
    files: List[UploadFile] = File(...),
    source_type: str = Form("file")
):
    """Upload file documents (txt, pdf, etc.) to train the clone"""
    try:
        from langchain_core.documents import Document
        
        documents = []
        for file in files:
            content = await file.read()
            
            # Try to decode as text
            try:
                text = content.decode('utf-8')
            except:
                text = content.decode('latin-1')
            
            doc = Document(
                page_content=text,
                metadata={
                    "source": file.filename,
                    "type": source_type,
                    "filename": file.filename
                }
            )
            documents.append(doc)
        
        result = await clone_llm_engine.ingest_documents(clone_id, documents, source_type)
        
        return {
            "success": True,
            "clone_id": clone_id,
            "files_processed": len(files),
            "documents_ingested": result["documents_ingested"],
            "chunks_created": result["chunks_created"],
            "status": result["status"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload files: {str(e)}")


@app.post("/clone/{clone_id}/upload-chat")
async def upload_chat_history(
    clone_id: str,
    chat_history: List[Dict[str, str]],
    platform: str = "whatsapp"
):
    """Upload chat history to learn communication style"""
    try:
        result = await clone_llm_engine.ingest_chat_history(
            clone_id=clone_id,
            chat_history=chat_history,
            platform=platform
        )
        
        return {
            "success": True,
            "clone_id": clone_id,
            "messages_ingested": result["documents_ingested"],
            "status": result["status"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload chat history: {str(e)}")


@app.post("/clone/{clone_id}/chat")
async def chat_with_clone(clone_id: str, message: ChatMessage):
    """Chat with the AI clone"""
    try:
        response = await clone_llm_engine.generate_response(
            clone_id=clone_id,
            message=message.message,
            conversation_id=message.conversation_id
        )
        
        return {
            "success": True,
            "clone_id": clone_id,
            "message": message.message,
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.get("/clone/{clone_id}/info")
async def get_clone_info(clone_id: str):
    """Get information about a clone"""
    info = clone_llm_engine.get_clone_info(clone_id)
    
    if "error" in info:
        raise HTTPException(status_code=404, detail=info["error"])
    
    return info


@app.get("/clone/user/{user_id}")
async def get_user_clones(user_id: str):
    """Get all clones for a user"""
    clones = []
    for clone_id, config in clone_llm_engine.clones.items():
        if config.user_id == user_id:
            info = clone_llm_engine.get_clone_info(clone_id)
            clones.append(info)
    
    return {
        "user_id": user_id,
        "clones": clones,
        "count": len(clones)
    }


@app.delete("/clone/{clone_id}")
async def delete_clone(clone_id: str):
    """Delete a clone"""
    success = clone_llm_engine.delete_clone(clone_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Clone not found")
    
    return {
        "success": True,
        "clone_id": clone_id,
        "message": "Clone deleted successfully"
    }


@app.get("/clone/{clone_id}/personality")
async def get_clone_personality(clone_id: str):
    """Get personality analysis of a clone"""
    if clone_id not in clone_llm_engine.clones:
        raise HTTPException(status_code=404, detail="Clone not found")
    
    traits = clone_llm_engine.personality_profiles.get(clone_id, PersonalityTraits())
    profile = clone_llm_engine.user_profiles.get(clone_id, UserProfile(name="Unknown"))
    
    return {
        "clone_id": clone_id,
        "name": profile.name,
        "communication_style": traits.greeting_style,
        "formality_level": traits.formality_level,
        "enthusiasm_level": traits.enthusiasm_level,
        "emoji_usage": traits.emoji_usage,
        "response_length_preference": traits.response_length_preference,
        "common_phrases": traits.common_phrases,
        "analysis_summary": f"{profile.name} tends to write in a {traits.response_length_preference} manner with {traits.greeting_style} style."
    }


# Integration endpoint: Use Clone LLM for phone calls
@app.post("/clone/{clone_id}/enable-for-calls")
async def enable_clone_for_calls(clone_id: str, user_id: str):
    """Enable the clone to handle phone calls with its personality"""
    try:
        # Get clone info
        info = clone_llm_engine.get_clone_info(clone_id)
        
        if "error" in info:
            raise HTTPException(status_code=404, detail=info["error"])
        
        # Update mobile settings to use this clone
        if user_id in mobile_user_settings:
            mobile_user_settings[user_id]["clone_llm_id"] = clone_id
            mobile_user_settings[user_id]["use_clone_llm"] = True
        
        return {
            "success": True,
            "clone_id": clone_id,
            "user_id": user_id,
            "message": "Clone is now active for phone calls. It will respond using your personality and knowledge.",
            "personality": info.get("personality"),
            "voice_integration": "When combined with cloned voice, calls will sound AND respond like you."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enable clone for calls: {str(e)}")


# =============================================================================
# VOICE PROVIDER API - SignalWire + Asterisk Integration
# Multi-provider support with automatic failover
# =============================================================================

@app.get("/voice/providers/health")
async def get_voice_providers_health():
    """Get health status of all configured voice providers"""
    health = await voice_provider_manager.get_all_health()
    return {
        "providers": health,
        "primary": voice_provider_manager.primary_provider,
        "fallback_chain": voice_provider_manager.fallback_chain,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/voice/providers/pricing")
async def get_voice_providers_pricing():
    """Get pricing comparison for all providers"""
    pricing = []
    for name, provider in voice_provider_manager.providers.items():
        if hasattr(provider, 'get_pricing_info'):
            info = provider.get_pricing_info()
            pricing.append(info)
    return {
        "providers": pricing,
        "recommendation": "SignalWire for cost savings, Asterisk for high volume"
    }


@app.post("/voice/calls/outbound")
async def make_outbound_call(
    to: str,
    from_number: Optional[str] = None,
    provider: Optional[str] = None,
    custom_data: Optional[dict] = None
):
    """Make outbound call using configured provider"""
    try:
        # Get provider
        if provider:
            voice_provider = voice_provider_manager.get_provider(provider)
        else:
            voice_provider = voice_provider_manager.get_provider()
        
        # Make call
        call_sid = await voice_provider.make_outbound_call(
            to_number=to,
            from_number=from_number,
            custom_data=custom_data
        )
        
        return {
            "success": True,
            "call_sid": call_sid,
            "provider": voice_provider.name,
            "to": to,
            "status": "initiated"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/voice/calls/{call_sid}/status")
async def get_call_status(call_sid: str, provider: Optional[str] = None):
    """Get status of a specific call"""
    try:
        if provider:
            voice_provider = voice_provider_manager.get_provider(provider)
        else:
            voice_provider = voice_provider_manager.get_provider()
        
        info = await voice_provider.get_call_status(call_sid)
        return {
            "call_sid": info.call_sid,
            "from": info.from_number,
            "to": info.to_number,
            "status": info.status,
            "direction": info.direction,
            "start_time": info.start_time.isoformat() if info.start_time else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/voice/calls/{call_sid}/end")
async def end_call(call_sid: str, provider: Optional[str] = None):
    """End an active call"""
    try:
        if provider:
            voice_provider = voice_provider_manager.get_provider(provider)
        else:
            voice_provider = voice_provider_manager.get_provider()
        
        success = await voice_provider.end_call(call_sid)
        return {
            "success": success,
            "call_sid": call_sid,
            "provider": voice_provider.name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SIGNALWIRE WEBHOOKS
# =============================================================================

@app.post("/webhooks/signalwire/inbound")
async def signalwire_inbound_webhook(request: Request):
    """Handle inbound calls from SignalWire"""
    try:
        data = await request.json()
        
        # Use SignalWire provider specifically
        provider = voice_provider_manager.get_provider("signalwire")
        result = await provider.handle_inbound_call(data)
        
        # Return LaML response (SignalWire's TwiML)
        from fastapi.responses import JSONResponse
        return JSONResponse(content=result.get("body", {}))
        
    except Exception as e:
        logger.error(f"SignalWire webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhooks/signalwire/status")
async def signalwire_status_webhook(request: Request):
    """Handle call status callbacks from SignalWire"""
    data = await request.form()
    logger.info(f"SignalWire status: {dict(data)}")
    return {"status": "received"}


# SignalWire WebSocket streaming endpoint
@app.websocket("/voice/stream/signalwire/{call_sid}")
async def signalwire_websocket(websocket: WebSocket, call_sid: str):
    """WebSocket for SignalWire audio streaming"""
    try:
        provider = voice_provider_manager.get_provider("signalwire")
        # Hand off to SignalWire's WebSocket handler
        await provider.handle_websocket(websocket.scope, websocket.receive, websocket.send)
    except Exception as e:
        logger.error(f"SignalWire WebSocket error: {e}")


# =============================================================================
# EXOTEL WEBHOOKS & WEBSOCKETS (India-Optimized)
# =============================================================================

@app.post("/webhooks/exotel/inbound")
async def exotel_inbound_webhook(request: Request):
    """Handle inbound calls from Exotel (India)"""
    try:
        # Exotel sends form-encoded data
        data = await request.form()
        call_data = dict(data)
        
        # Use Exotel provider
        provider = voice_provider_manager.get_provider("exotel")
        result = await provider.handle_inbound_call(call_data)
        
        # Return XML applet (Exotel expects XML)
        from fastapi.responses import Response
        return Response(
            content=result.get("body", ""),
            media_type="application/xml"
        )
        
    except Exception as e:
        logger.error(f"Exotel webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhooks/exotel/status")
async def exotel_status_webhook(request: Request):
    """Handle call status callbacks from Exotel"""
    data = await request.form()
    logger.info(f"Exotel status: {dict(data)}")
    return {"status": "received"}


@app.post("/webhooks/exotel/sms-status")
async def exotel_sms_status_webhook(request: Request):
    """Handle SMS delivery status from Exotel"""
    data = await request.form()
    logger.info(f"Exotel SMS status: {dict(data)}")
    return {"status": "received"}


@app.websocket("/voice/stream/exotel/{call_sid}")
async def exotel_websocket(websocket: WebSocket, call_sid: str):
    """WebSocket for Exotel audio streaming"""
    try:
        provider = voice_provider_manager.get_provider("exotel")
        await provider.handle_websocket(websocket.scope, websocket.receive, websocket.send)
    except Exception as e:
        logger.error(f"Exotel WebSocket error: {e}")


@app.post("/voice/sms/send")
async def send_sms(
    to: str,
    message: str,
    provider: Optional[str] = "exotel"
):
    """Send SMS via configured provider (Exotel recommended for India)"""
    try:
        voice_provider = voice_provider_manager.get_provider(provider)
        
        # Check if provider supports SMS
        if not hasattr(voice_provider, 'send_sms'):
            raise HTTPException(status_code=400, detail=f"Provider {provider} does not support SMS")
        
        sms_sid = await voice_provider.send_sms(to, message)
        
        return {
            "success": True,
            "sms_sid": sms_sid,
            "provider": provider,
            "to": to,
            "message_preview": message[:50] + "..." if len(message) > 50 else message
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ASTERISK WEBHOOKS & WEBSOCKETS
# =============================================================================

@app.websocket("/voice/stream/asterisk/{channel_id}")
async def asterisk_websocket(websocket: WebSocket, channel_id: str):
    """WebSocket for Asterisk externalMedia audio streaming"""
    try:
        provider = voice_provider_manager.get_provider("asterisk")
        await provider.handle_websocket(websocket.scope, websocket.receive, websocket.send)
    except Exception as e:
        logger.error(f"Asterisk WebSocket error: {e}")


@app.post("/webhooks/asterisk/events")
async def asterisk_event_webhook(request: Request):
    """Optional: HTTP fallback for Asterisk events"""
    data = await request.json()
    logger.info(f"Asterisk event: {data}")
    return {"status": "received"}


# =============================================================================
# UNIVERSAL WEBHOOK (Provider-agnostic with failover)
# =============================================================================

@app.post("/webhooks/voice/inbound")
async def universal_inbound_webhook(
    request: Request,
    provider_hint: Optional[str] = None
):
    """
    Universal inbound webhook that works with any provider.
    Automatically fails over if primary provider is unavailable.
    """
    try:
        data = await request.json()
        
        # Try with automatic failover
        result = await voice_provider_manager.handle_inbound_with_failover(
            data, provider_hint=provider_hint
        )
        
        # Return appropriate format based on provider
        provider_used = result.get('_provider', 'unknown')
        
        if provider_used == 'signalwire':
            from fastapi.responses import JSONResponse
            return JSONResponse(content=result.get("body", {}))
        elif provider_used == 'twilio':
            from fastapi.responses import XMLResponse
            # Twilio expects XML (TwiML)
            return XMLResponse(content=result.get("body", ""))
        else:
            return result
            
    except Exception as e:
        logger.error(f"Universal webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# PROVIDER SWITCHING ENDPOINTS
# =============================================================================

@app.post("/voice/providers/switch")
async def switch_primary_provider(provider: str):
    """Switch the primary voice provider at runtime"""
    if provider not in voice_provider_manager.providers:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown provider: {provider}. Available: {list(voice_provider_manager.providers.keys())}"
        )
    
    voice_provider_manager.primary_provider = provider
    return {
        "success": True,
        "new_primary": provider,
        "all_providers": list(voice_provider_manager.providers.keys()),
        "message": f"Switched to {provider} as primary provider"
    }


@app.get("/voice/providers/list")
async def list_providers():
    """List all configured providers"""
    return {
        "providers": [
            {
                "name": name,
                "enabled": provider.enabled,
                "is_primary": voice_provider_manager.primary_provider == name,
                "fallback_order": voice_provider_manager.fallback_chain.index(name) if name in voice_provider_manager.fallback_chain else None
            }
            for name, provider in voice_provider_manager.providers.items()
        ],
        "primary": voice_provider_manager.primary_provider,
        "fallback_chain": voice_provider_manager.fallback_chain
    }
