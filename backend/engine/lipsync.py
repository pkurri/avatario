# backend/engine/lipsync.py
"""
Lip Sync Video Generation Service
Integrates with external lip sync APIs (Open-Generative-AI compatible)
Generates talking avatar videos from portrait images + audio
"""

import os
import httpx
import base64
import asyncio
from typing import Optional, Dict, Any
from enum import Enum

# Configuration
LIPSYNC_API_URL = os.getenv("LIPSYNC_API_URL", "http://localhost:7860")  # Default for Open-Generative-AI
LIPSYNC_TIMEOUT = int(os.getenv("LIPSYNC_TIMEOUT", "300"))  # 5 minutes for video generation

class LipSyncModel(str, Enum):
    """Available lip sync models"""
    INFINITETALK_IMAGE = "infinitetalk-image-to-video"
    WAN2_SPEECH = "wan2.2-speech-to-video"
    LTX_2_3 = "ltx-2.3-lipsync"
    LTX_2_19B = "ltx-2-19b-lipsync"
    SYNC_LIPSYNC = "sync-lipsync"
    LATENTSYNC = "latentsync-video"
    CREATIFY = "creatify-lipsync"
    VEED = "veed-lipsync"
    INFINITETALK_VIDEO = "infinitetalk-video-to-video"

class LipSyncService:
    """Service for generating lip-synced talking avatar videos"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or LIPSYNC_API_URL
        
    async def generate_talking_video(
        self,
        image_url: str,
        audio_url: str,
        model: LipSyncModel = LipSyncModel.INFINITETALK_IMAGE,
        prompt: Optional[str] = None,
        resolution: str = "512x512",
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a talking avatar video from image + audio
        
        Args:
            image_url: URL of the portrait image
            audio_url: URL of the audio file (TTS output)
            model: Lip sync model to use
            prompt: Optional motion style guidance
            resolution: Output resolution
            webhook_url: Callback URL when generation completes
            
        Returns:
            Dict with job_id, status, and video_url (when complete)
        """
        endpoint = f"{self.base_url}/api/lipsync/generate"
        
        payload = {
            "model": model.value,
            "image_url": image_url,
            "audio_url": audio_url,
            "resolution": resolution,
        }
        
        if prompt:
            payload["prompt"] = prompt
        if webhook_url:
            payload["webhook_url"] = webhook_url
            
        try:
            async with httpx.AsyncClient(timeout=LIPSYNC_TIMEOUT) as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": f"Lip sync API error: {e.response.status_code}",
                "details": str(e)
            }
        except Exception as e:
            return {
                "error": "Failed to generate talking video",
                "details": str(e)
            }
    
    async def generate_talking_video_bytes(
        self,
        image_bytes: bytes,
        audio_bytes: bytes,
        model: LipSyncModel = LipSyncModel.INFINITETALK_IMAGE,
        prompt: Optional[str] = None,
        resolution: str = "512x512"
    ) -> Dict[str, Any]:
        """
        Generate talking video from raw bytes (for direct file uploads)
        """
        endpoint = f"{self.base_url}/api/lipsync/generate"
        
        # Encode bytes as base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        payload = {
            "model": model.value,
            "image_base64": image_b64,
            "audio_base64": audio_b64,
            "resolution": resolution,
        }
        
        if prompt:
            payload["prompt"] = prompt
            
        try:
            async with httpx.AsyncClient(timeout=LIPSYNC_TIMEOUT) as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {
                "error": "Failed to generate talking video",
                "details": str(e)
            }
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Check the status of a lip sync job"""
        endpoint = f"{self.base_url}/api/lipsync/status/{job_id}"
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(endpoint)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {
                "error": "Failed to check job status",
                "details": str(e)
            }
    
    async def list_models(self) -> Dict[str, Any]:
        """List available lip sync models"""
        endpoint = f"{self.base_url}/api/lipsync/models"
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(endpoint)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            # Return default models if API not available
            return {
                "models": [
                    {"id": m.value, "name": m.value.replace("-", " ").title()}
                    for m in LipSyncModel
                ],
                "note": "Using default models - API unavailable"
            }


# ==========================================
# PERSONA VIDEO CACHE
# ==========================================

class PersonaVideoCache:
    """Cache for pre-generated persona talking videos"""
    
    def __init__(self):
        # In production, use Redis or similar
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, persona_id: str, text_hash: str) -> Optional[str]:
        """Get cached video URL for persona + text combination"""
        key = f"{persona_id}:{text_hash}"
        entry = self._cache.get(key)
        if entry and entry.get("video_url"):
            return entry["video_url"]
        return None
    
    def set(self, persona_id: str, text_hash: str, video_url: str, metadata: Optional[Dict] = None):
        """Cache a generated video URL"""
        key = f"{persona_id}:{text_hash}"
        self._cache[key] = {
            "video_url": video_url,
            "metadata": metadata or {},
            "created_at": asyncio.get_event_loop().time()
        }
    
    def clear(self, persona_id: Optional[str] = None):
        """Clear cache entries"""
        if persona_id:
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{persona_id}:")]
            for k in keys_to_remove:
                del self._cache[k]
        else:
            self._cache.clear()


# Global instances
lipsync_service = LipSyncService()
persona_video_cache = PersonaVideoCache()


# ==========================================
# CONVENIENCE FUNCTIONS
# ==========================================

async def generate_persona_video(
    persona_id: str,
    image_url: str,
    audio_url: str,
    text_content: str,  # For caching purposes
    model: LipSyncModel = LipSyncModel.INFINITETALK_IMAGE
) -> Dict[str, Any]:
    """
    Generate or retrieve cached talking video for a persona
    """
    import hashlib
    
    # Check cache first
    text_hash = hashlib.md5(text_content.encode()).hexdigest()[:16]
    cached_url = persona_video_cache.get(persona_id, text_hash)
    
    if cached_url:
        return {
            "status": "completed",
            "video_url": cached_url,
            "cached": True,
            "persona_id": persona_id
        }
    
    # Generate new video
    result = await lipsync_service.generate_talking_video(
        image_url=image_url,
        audio_url=audio_url,
        model=model,
        prompt=f"Natural talking head, professional {persona_id} persona, smooth lip sync"
    )
    
    # Cache if successful
    if result.get("video_url") and not result.get("error"):
        persona_video_cache.set(persona_id, text_hash, result["video_url"], {
            "model": model.value,
            "prompt": result.get("prompt")
        })
    
    return result


async def get_available_models() -> list:
    """Get list of available lip sync models"""
    result = await lipsync_service.list_models()
    return result.get("models", [])
