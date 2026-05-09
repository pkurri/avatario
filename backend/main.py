import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.personas import router as personas_router
from routes.livekit import router as livekit_router
from routes.llm import router as llm_router
from routes.lipsync import router as lipsync_router
from routes.ai_person import router as ai_person_router
from routes.talking_person import router as talking_person_router
from routes.face_clone import router as face_clone_router
from routes.websocket import router as websocket_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Assistant API",
    description="Voice-Native AI Backend - Multi-Vertical AI Assistant Platform",
    version="1.0.0",
)

# CORS — set CORS_ORIGINS as comma-separated list in production
_cors_origins_raw = os.getenv("CORS_ORIGINS", "")
_cors_origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(personas_router)
app.include_router(livekit_router)
app.include_router(llm_router)
app.include_router(lipsync_router)
app.include_router(ai_person_router)
app.include_router(talking_person_router)
app.include_router(face_clone_router)
app.include_router(websocket_router)


@app.get("/")
async def root():
    return {
        "message": "AI Assistant API is running",
        "endpoints": {
            "websocket_chat": "/chat/{persona_id}",
            "personas": "/personas",
            "livekit_token": "/get_livekit_token",
            "health": "/health",
        },
    }


@app.get("/health")
async def health():
    from engine.lipsync_failover import get_lipsync_failover
    failover = get_lipsync_failover()
    lipsync_status = await failover.health()
    return {"status": "healthy", "version": "1.0.0", "lipsync": lipsync_status}
