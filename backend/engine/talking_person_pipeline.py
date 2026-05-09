# backend/engine/talking_person_pipeline.py
"""
Talking Person Pipeline - Complete AI-generated human with lip-sync
Pipeline: Text -> AI Image (FLUX) -> TTS Audio -> Lip Sync Video
"""

import logging
import os
import httpx
import asyncio
import hashlib
import json
from typing import Optional, Dict, Any, Literal
from dataclasses import dataclass
from pathlib import Path
import tempfile
from datetime import datetime

logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURATION
# ==========================================

# Image generation API (FLUX via Replicate, Fal.ai, or local)
IMAGE_API_URL = os.getenv("IMAGE_API_URL", "https://api.replicate.com/v1/predictions")
IMAGE_API_KEY = os.getenv("REPLICATE_API_TOKEN", "")

# TTS API (Sarvam or Chatterbox)
TTS_API_URL = os.getenv("TTS_API_URL", "")

# ==========================================
# DATA MODELS
# ==========================================

@dataclass
class PersonConfig:
    """Configuration for AI person generation"""
    gender: Literal["male", "female"]
    age: Literal["young", "middle", "mature"]
    ethnicity: str
    profession: str
    style: Literal["professional", "casual", "formal"] = "professional"
    expression: str = "friendly, approachable"

@dataclass
class TalkingPerson:
    """Complete AI-generated talking person"""
    id: str
    name: str
    config: PersonConfig
    image_path: str  # Local path to generated image
    audio_path: Optional[str] = None  # Generated TTS audio
    video_path: Optional[str] = None  # Lip-synced video
    status: Literal["image", "audio", "video", "complete", "error"] = "image"
    error_message: Optional[str] = None


# ==========================================
# TALKING PERSON PIPELINE
# ==========================================

class TalkingPersonPipeline:
    """
    End-to-end pipeline for generating realistic talking AI persons
    """
    
    def __init__(self, cache_dir: str = "/tmp/talking_persons"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir = self.cache_dir / "images"
        self.audio_dir = self.cache_dir / "audio"
        self.video_dir = self.cache_dir / "videos"
        
        for d in [self.images_dir, self.audio_dir, self.video_dir]:
            d.mkdir(exist_ok=True)
    
    def _generate_person_id(self, config: PersonConfig) -> str:
        """Generate unique ID from config"""
        config_str = f"{config.gender}_{config.age}_{config.ethnicity}_{config.profession}_{config.style}_{config.expression}"
        return hashlib.md5(config_str.encode()).hexdigest()[:16]
    
    def _generate_prompt(self, config: PersonConfig) -> str:
        """Generate detailed prompt for FLUX image generation"""
        
        # Ethnicity descriptors
        ethnicity_desc = {
            "indian": "South Asian",
            "asian": "East Asian",
            "caucasian": "Caucasian",
            "african": "African",
            "hispanic": "Hispanic/Latino",
            "middle_eastern": "Middle Eastern"
        }.get(config.ethnicity, config.ethnicity)
        
        # Age descriptors
        age_desc = {
            "young": "in their late 20s",
            "middle": "in their 40s",
            "mature": "in their 60s"
        }.get(config.age, "middle-aged")
        
        # Style/clothing based on profession and style
        clothing = {
            "professional": {
                "legal": "wearing a formal navy business suit with white shirt",
                "medical": "wearing a white medical coat over scrubs",
                "finance": "wearing a tailored charcoal business suit",
                "education": "wearing smart casual academic attire",
                "generic": "wearing professional business casual"
            },
            "formal": {
                "legal": "wearing an elegant formal black suit",
                "medical": "wearing pristine white medical coat with stethoscope",
                "finance": "wearing high-end tailored dark suit with tie",
                "education": "wearing formal academic robes",
                "generic": "wearing formal professional attire"
            }
        }.get(config.style, {}).get(config.profession, "wearing professional attire")
        
        prompt = f"""
Ultra-realistic portrait photograph of a {ethnicity_desc} {config.gender} {age_desc},
{clothing},
{config.expression} expression, looking directly at camera,
professional headshot lighting, soft studio lights, 
neutral blurred office background, shallow depth of field,
sharp focus on face, detailed skin texture with natural pores,
photorealistic 8K quality, professional DSLR photography,
corporate headshot style, authentic human features,
no jewelry, natural makeup, clean professional appearance
"""
        
        return prompt.strip().replace("\n", " ")
    
    async def generate_image(
        self, 
        config: PersonConfig,
        person_id: str
    ) -> str:
        """
        Generate AI person image using FLUX or similar model
        Returns local path to saved image
        """
        image_path = self.images_dir / f"{person_id}.png"
        
        # Check cache
        if image_path.exists():
            return str(image_path)
        
        prompt = self._generate_prompt(config)
        negative_prompt = "cartoon, illustration, painting, drawing, 3d render, anime, blurry, low quality, distorted, deformed"
        
        try:
            # Try Replicate FLUX API
            if IMAGE_API_KEY:
                headers = {
                    "Authorization": f"Token {IMAGE_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "version": "black-forest-labs/flux-dev",  # or schnell
                    "input": {
                        "prompt": prompt,
                        "negative_prompt": negative_prompt,
                        "width": 1024,
                        "height": 1024,
                        "num_inference_steps": 50,
                        "guidance_scale": 7.5
                    }
                }
                
                async with httpx.AsyncClient(timeout=300) as client:
                    # Start prediction
                    response = await client.post(
                        IMAGE_API_URL,
                        headers=headers,
                        json=payload
                    )
                    response.raise_for_status()
                    prediction = response.json()
                    
                    # Poll for completion
                    prediction_id = prediction["id"]
                    status_url = f"{IMAGE_API_URL}/{prediction_id}"
                    
                    for _ in range(60):  # Poll for 5 minutes max
                        await asyncio.sleep(5)
                        
                        status_response = await client.get(status_url, headers=headers)
                        status_data = status_response.json()
                        
                        if status_data["status"] == "succeeded":
                            raw_output = status_data["output"]
                            image_url = raw_output[0] if isinstance(raw_output, list) else raw_output
                            
                            # Download image
                            img_response = await client.get(image_url)
                            img_response.raise_for_status()
                            
                            with open(image_path, 'wb') as f:
                                f.write(img_response.content)
                            
                            return str(image_path)
                            
                        elif status_data["status"] == "failed":
                            raise Exception(f"Image generation failed: {status_data.get('error')}")
            
            # Fallback: Try other APIs (Fal.ai, RunPod, etc.)
            # For now, return placeholder path
            return str(image_path)
            
        except Exception as e:
            logger.error("Image generation error: %s", e)
            return str(image_path)
    
    async def generate_audio(
        self,
        text: str,
        person_id: str,
        voice_id: Optional[str] = None
    ) -> str:
        """
        Generate TTS audio for the person
        Uses Sarvam AI or Chatterbox TTS
        """
        audio_path = self.audio_dir / f"{person_id}_{hashlib.md5(text.encode()).hexdigest()[:8]}.wav"
        
        if audio_path.exists():
            return str(audio_path)
        
        try:
            # Use existing Sarvam TTS
            from engine.audio import sarvam_tts
            
            audio_bytes = await sarvam_tts(text)
            
            if audio_bytes:
                with open(audio_path, 'wb') as f:
                    f.write(audio_bytes)
                return str(audio_path)
            
        except Exception as e:
            logger.error("TTS error: %s", e)

        return str(audio_path)
    
    async def generate_lip_sync_video(
        self,
        image_path: str,
        audio_path: str,
        person_id: str,
        text: str = ""
    ) -> Optional[str]:
        """
        Generate lip-synced video from image + audio.
        Uses failover chain: Wav2Lip → Duix-Avatar → D-ID.
        Returns the video path on success, None if unavailable.
        """
        from engine.lipsync_failover import get_lipsync_failover

        failover = get_lipsync_failover()
        result = await failover.generate(
            image_path=image_path,
            audio_path=audio_path,
            text=text,
            person_id=person_id,
        )

        if result.success and result.video_path:
            logger.info(f"[TalkingPerson] Lip-sync video generated via {result.provider.value}")
            return result.video_path

        if result.error:
            logger.error(f"[TalkingPerson] Lip sync unavailable: {result.error}")

        return None
    
    async def create_complete_person(
        self,
        config: PersonConfig,
        name: str,
        welcome_text: str
    ) -> TalkingPerson:
        """
        Create a complete talking AI person end-to-end
        """
        person_id = self._generate_person_id(config)
        
        person = TalkingPerson(
            id=person_id,
            name=name,
            config=config,
            image_path=""
        )
        
        try:
            # Step 1: Generate image
            logger.info(f"[TalkingPerson] Generating image for {name}...")
            person.status = "image"
            image_path = await self.generate_image(config, person_id)
            person.image_path = image_path
            image_ok = Path(image_path).exists() and Path(image_path).stat().st_size > 100
            
            # Step 2: Generate TTS audio
            logger.info(f"[TalkingPerson] Generating TTS audio...")
            person.status = "audio"
            audio_path = await self.generate_audio(welcome_text, person_id)
            person.audio_path = audio_path
            audio_ok = Path(audio_path).exists() and Path(audio_path).stat().st_size > 100
            
            # Step 3: Try lip-sync video (non-blocking — audio still works without it)
            video_path = None
            if image_ok and audio_ok:
                logger.info(f"[TalkingPerson] Generating lip-sync video...")
                person.status = "video"
                video_path = await self.generate_lip_sync_video(image_path, audio_path, person_id, welcome_text)
            
            person.video_path = video_path
            person.status = "complete"
            if video_path:
                logger.info(f"[TalkingPerson] Complete! Video saved to {video_path}")
            else:
                logger.error(f"[TalkingPerson] Complete (audio-only — lip-sync unavailable)")
            
        except Exception as e:
            person.status = "error"
            person.error_message = str(e)
            logger.error(f"[TalkingPerson] Error: {e}")
        
        return person
    
    def get_person_status(self, person_id: str) -> Dict[str, Any]:
        """Check status of a person generation"""
        image_path = self.images_dir / f"{person_id}.png"
        
        has_image = image_path.exists() and image_path.stat().st_size > 100
        
        audios = list(self.audio_dir.glob(f"{person_id}*.wav"))
        has_audio = len(audios) > 0
        
        videos = list(self.video_dir.glob(f"{person_id}*.mp4"))
        has_video = len(videos) > 0
        
        return {
            "person_id": person_id,
            "has_image": has_image,
            "has_audio": has_audio,
            "has_video": has_video,
            "audio_count": len(audios),
            "video_count": len(videos),
            "audios": [str(a) for a in audios],
            "videos": [str(v) for v in videos]
        }


# ==========================================
# CONVENIENCE FUNCTIONS
# ==========================================

_pipeline = None

def get_pipeline() -> TalkingPersonPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = TalkingPersonPipeline()
    return _pipeline


async def generate_real_talking_person(
    vertical: str,
    gender: Literal["male", "female"] = "female",
    name: Optional[str] = None,
    ethnicity: str = "indian"
) -> Dict[str, Any]:
    """
    Generate a complete real talking AI person
    
    Returns dict with person info and paths
    """
    pipeline = get_pipeline()
    
    # Create config
    config = PersonConfig(
        gender=gender,
        age="middle",
        ethnicity=ethnicity,
        profession=vertical,
        style="professional"
    )
    
    # Generate name if not provided
    if not name:
        from engine.ai_person_generator import ai_person_generator
        name = ai_person_generator._generate_name(
            type('obj', (object,), {'value': gender})(),
            type('obj', (object,), {'value': ethnicity})()
        )
    
    welcome_text = f"Hello, I'm {name}. I'm here to help you with {vertical} matters. How can I assist you today?"
    
    # Generate complete person
    person = await pipeline.create_complete_person(config, name, welcome_text)
    
    image_ok = bool(person.image_path) and Path(person.image_path).exists() and Path(person.image_path).stat().st_size > 100
    audio_ok = bool(person.audio_path) and Path(person.audio_path).exists() and Path(person.audio_path).stat().st_size > 100
    
    return {
        "id": person.id,
        "name": person.name,
        "status": person.status,
        "has_image": image_ok,
        "has_audio": audio_ok,
        "has_video": bool(person.video_path),
        "image_url": f"/talking-person/{person.id}/image" if image_ok else None,
        "audio_url": f"/talking-person/{person.id}/audio/welcome" if audio_ok else None,
        "video_url": f"/talking-person/{person.id}/video/latest" if person.video_path else None,
        "error": person.error_message,
        "config": {
            "gender": config.gender,
            "age": config.age,
            "ethnicity": config.ethnicity,
            "profession": config.profession
        }
    }


async def get_person_video(
    person_id: str,
    text: str,
    emotion: str = "neutral"
) -> Dict[str, Any]:
    """
    Generate a new video for an existing person with new text
    """
    pipeline = get_pipeline()
    
    # Get person image
    image_path = pipeline.images_dir / f"{person_id}.png"
    
    if not image_path.exists():
        return {"error": "Person not found", "status": "error"}
    
    # Generate new audio
    audio_path = await pipeline.generate_audio(text, person_id + f"_{hashlib.md5(text.encode()).hexdigest()[:8]}")
    
    # Generate new video
    video_path = await pipeline.generate_lip_sync_video(
        str(image_path), 
        audio_path, 
        person_id + f"_{hashlib.md5(text.encode()).hexdigest()[:8]}"
    )
    
    text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
    video_ok = bool(video_path) and Path(video_path).exists() and Path(video_path).stat().st_size > 1000
    audio_ok = Path(audio_path).exists() and Path(audio_path).stat().st_size > 100
    
    return {
        "person_id": person_id,
        "text": text,
        "has_video": video_ok,
        "has_audio": audio_ok,
        "video_url": f"/talking-person/{person_id}/video/{text_hash}" if video_ok else None,
        "audio_url": f"/talking-person/{person_id}/audio/{text_hash}" if audio_ok else None,
        "status": "complete"
    }
