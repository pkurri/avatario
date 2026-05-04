# backend/engine/face_clone.py
"""
Face Clone Engine - Clone any real human face for Conversational AI

Modes:
  1. Clone Mode: Upload/URL a real human photo → process face → talking avatar
  2. Generate Mode: Create brand new AI face from scratch → talking avatar

Both modes feed into: Face Image → TTS Audio → Lip Sync Video → Conversational AI
"""

import os
import httpx
import hashlib
import shutil
import uuid
from typing import Optional, Dict, Any, List, Literal
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import json


# ==========================================
# CONFIGURATION
# ==========================================

IMAGE_API_URL = os.getenv("IMAGE_API_URL", "https://api.replicate.com/v1/predictions")
IMAGE_API_KEY = os.getenv("REPLICATE_API_TOKEN", "")
CLONE_CACHE_DIR = os.getenv("CLONE_CACHE_DIR", "/tmp/face_clones")


# ==========================================
# DATA MODELS
# ==========================================

@dataclass
class ClonedFace:
    """A cloned or generated face identity"""
    id: str
    name: str
    mode: Literal["clone", "generate"]
    source: Literal["upload", "url", "ai_generated"]
    image_path: str
    thumbnail_path: Optional[str] = None
    original_url: Optional[str] = None
    created_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Generation config (for generate mode)
    gender: Optional[str] = None
    ethnicity: Optional[str] = None
    age: Optional[str] = None
    profession: Optional[str] = None
    # Status tracking
    status: Literal["processing", "ready", "talking", "error"] = "processing"
    error: Optional[str] = None
    # Generated assets
    videos: Dict[str, str] = field(default_factory=dict)  # text_hash -> video_path
    audio_files: Dict[str, str] = field(default_factory=dict)  # text_hash -> audio_path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "mode": self.mode,
            "source": self.source,
            "status": self.status,
            "image_url": f"/face-clone/{self.id}/image",
            "thumbnail_url": f"/face-clone/{self.id}/thumbnail",
            "created_at": self.created_at,
            "gender": self.gender,
            "ethnicity": self.ethnicity,
            "age": self.age,
            "profession": self.profession,
            "video_count": len(self.videos),
            "error": self.error,
            "metadata": self.metadata,
        }


# ==========================================
# FACE CLONE ENGINE
# ==========================================

class FaceCloneEngine:
    """
    Engine for cloning real human faces and generating new ones
    for use in conversational AI with lip-sync video
    """

    def __init__(self, cache_dir: str = CLONE_CACHE_DIR):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.images_dir = self.cache_dir / "images"
        self.thumbnails_dir = self.cache_dir / "thumbnails"
        self.audio_dir = self.cache_dir / "audio"
        self.video_dir = self.cache_dir / "videos"
        
        for d in [self.images_dir, self.thumbnails_dir, self.audio_dir, self.video_dir]:
            d.mkdir(exist_ok=True)
        
        # In-memory registry of cloned faces
        self._faces: Dict[str, ClonedFace] = {}
        
        # Load existing faces from disk
        self._load_existing()

    def _load_existing(self):
        """Load existing cloned faces from disk"""
        meta_dir = self.cache_dir / "meta"
        meta_dir.mkdir(exist_ok=True)
        
        for meta_file in meta_dir.glob("*.json"):
            try:
                with open(meta_file, 'r') as f:
                    data = json.load(f)
                face = ClonedFace(**data)
                # Restore dict fields
                if isinstance(face.videos, list):
                    face.videos = {}
                if isinstance(face.audio_files, list):
                    face.audio_files = {}
                self._faces[face.id] = face
            except Exception as e:
                print(f"[FaceClone] Error loading {meta_file}: {e}")

    def _save_meta(self, face: ClonedFace):
        """Save face metadata to disk"""
        meta_dir = self.cache_dir / "meta"
        meta_dir.mkdir(exist_ok=True)
        
        meta_path = meta_dir / f"{face.id}.json"
        data = {
            "id": face.id,
            "name": face.name,
            "mode": face.mode,
            "source": face.source,
            "image_path": face.image_path,
            "thumbnail_path": face.thumbnail_path,
            "original_url": face.original_url,
            "created_at": face.created_at,
            "metadata": face.metadata,
            "gender": face.gender,
            "ethnicity": face.ethnicity,
            "age": face.age,
            "profession": face.profession,
            "status": face.status,
            "error": face.error,
            "videos": face.videos,
            "audio_files": face.audio_files,
        }
        with open(meta_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _generate_id(self, source: str) -> str:
        """Generate unique face ID"""
        unique = f"{source}_{datetime.now().isoformat()}_{uuid.uuid4().hex[:8]}"
        return hashlib.md5(unique.encode()).hexdigest()[:16]

    # ------------------------------------------
    # CLONE MODE: Clone from uploaded image
    # ------------------------------------------

    async def clone_from_upload(
        self,
        image_bytes: bytes,
        name: str,
        content_type: str = "image/png",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ClonedFace:
        """
        Clone a face from an uploaded image file.
        The image should contain a clear frontal face.
        """
        face_id = self._generate_id(f"upload_{name}")
        
        # Determine extension
        ext = "png"
        if "jpeg" in content_type or "jpg" in content_type:
            ext = "jpg"
        elif "webp" in content_type:
            ext = "webp"
        
        image_path = self.images_dir / f"{face_id}.{ext}"
        
        # Save uploaded image
        with open(image_path, 'wb') as f:
            f.write(image_bytes)
        
        # Process face (crop, align, enhance)
        processed_path = await self._process_face(str(image_path), face_id)
        
        face = ClonedFace(
            id=face_id,
            name=name,
            mode="clone",
            source="upload",
            image_path=processed_path or str(image_path),
            created_at=datetime.now().isoformat(),
            metadata=metadata or {},
            status="ready",
        )
        
        self._faces[face_id] = face
        self._save_meta(face)
        
        print(f"[FaceClone] Cloned face from upload: {name} -> {face_id}")
        return face

    # ------------------------------------------
    # CLONE MODE: Clone from URL
    # ------------------------------------------

    async def clone_from_url(
        self,
        image_url: str,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ClonedFace:
        """
        Clone a face from a URL pointing to an image.
        Downloads the image and processes the face.
        """
        face_id = self._generate_id(f"url_{image_url}")
        
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                image_bytes = response.content
                content_type = response.headers.get("content-type", "image/png")
        except Exception as e:
            face = ClonedFace(
                id=face_id,
                name=name,
                mode="clone",
                source="url",
                image_path="",
                original_url=image_url,
                created_at=datetime.now().isoformat(),
                status="error",
                error=f"Failed to download image: {str(e)}",
            )
            self._faces[face_id] = face
            self._save_meta(face)
            return face
        
        # Determine extension
        ext = "png"
        if "jpeg" in content_type or "jpg" in content_type:
            ext = "jpg"
        elif "webp" in content_type:
            ext = "webp"
        
        image_path = self.images_dir / f"{face_id}.{ext}"
        
        with open(image_path, 'wb') as f:
            f.write(image_bytes)
        
        # Process face
        processed_path = await self._process_face(str(image_path), face_id)
        
        face = ClonedFace(
            id=face_id,
            name=name,
            mode="clone",
            source="url",
            image_path=processed_path or str(image_path),
            original_url=image_url,
            created_at=datetime.now().isoformat(),
            metadata=metadata or {},
            status="ready",
        )
        
        self._faces[face_id] = face
        self._save_meta(face)
        
        print(f"[FaceClone] Cloned face from URL: {name} -> {face_id}")
        return face

    # ------------------------------------------
    # GENERATE MODE: Brand new AI face
    # ------------------------------------------

    async def generate_new_face(
        self,
        name: str,
        gender: str = "female",
        ethnicity: str = "indian",
        age: str = "middle",
        profession: str = "generic",
        style: str = "professional",
    ) -> ClonedFace:
        """
        Generate a completely new realistic AI face using FLUX.
        """
        face_id = self._generate_id(f"gen_{gender}_{ethnicity}_{profession}")
        
        image_path = self.images_dir / f"{face_id}.png"
        
        # Build FLUX prompt
        prompt = self._build_face_prompt(gender, ethnicity, age, profession, style)
        
        try:
            generated_path = await self._generate_with_flux(prompt, str(image_path))
            status = "ready" if generated_path and Path(generated_path).exists() else "error"
        except Exception as e:
            print(f"[FaceClone] FLUX generation error: {e}")
            generated_path = str(image_path)
            status = "error"
        
        face = ClonedFace(
            id=face_id,
            name=name,
            mode="generate",
            source="ai_generated",
            image_path=generated_path or str(image_path),
            created_at=datetime.now().isoformat(),
            gender=gender,
            ethnicity=ethnicity,
            age=age,
            profession=profession,
            status=status,
            metadata={"prompt": prompt, "style": style},
        )
        
        self._faces[face_id] = face
        self._save_meta(face)
        
        print(f"[FaceClone] Generated new AI face: {name} -> {face_id}")
        return face

    # ------------------------------------------
    # TALK: Make any cloned/generated face talk
    # ------------------------------------------

    async def make_face_talk(
        self,
        face_id: str,
        text: str,
        voice_id: Optional[str] = None,
        emotion: str = "neutral",
    ) -> Dict[str, Any]:
        """
        Make a cloned or generated face talk with lip-sync.
        Pipeline: Face Image + Text → TTS Audio → Lip Sync Video
        """
        face = self._faces.get(face_id)
        if not face:
            return {"error": "Face not found", "status": "error"}
        
        if face.status == "error":
            return {"error": f"Face has errors: {face.error}", "status": "error"}
        
        text_hash = hashlib.md5(text.encode()).hexdigest()[:10]
        
        # Check cache (video or audio)
        has_cached_video = text_hash in face.videos
        has_cached_audio = text_hash in face.audio_files
        if has_cached_video or has_cached_audio:
            return {
                "face_id": face_id,
                "name": face.name,
                "text": text,
                "video_url": f"/face-clone/{face_id}/video/{text_hash}" if has_cached_video else None,
                "audio_url": f"/face-clone/{face_id}/audio/{text_hash}" if has_cached_audio else None,
                "image_url": f"/face-clone/{face_id}/image",
                "status": "complete",
                "has_video": has_cached_video,
                "has_audio": has_cached_audio,
                "cached": True,
            }
        
        face.status = "talking"
        
        try:
            # Step 1: Generate TTS audio
            print(f"[FaceClone] Generating TTS for: {text[:50]}...")
            audio_path = await self._generate_tts(text, face_id, text_hash, voice_id)
            face.audio_files[text_hash] = audio_path
            
            # Check if TTS actually produced audio
            audio_ok = Path(audio_path).exists() and Path(audio_path).stat().st_size > 100
            
            # Step 2: Try lip-sync video (non-blocking — audio still works without it)
            video_url = None
            try:
                print(f"[FaceClone] Generating lip-sync video...")
                video_path = await self._generate_lipsync(
                    face.image_path, audio_path, face_id, text_hash
                )
                # Only store if the video file has real content (not empty placeholder)
                if Path(video_path).exists() and Path(video_path).stat().st_size > 1000:
                    face.videos[text_hash] = video_path
                    video_url = f"/face-clone/{face_id}/video/{text_hash}"
                else:
                    print(f"[FaceClone] Lip-sync produced empty file, using audio-only mode")
                    Path(video_path).unlink(missing_ok=True)
            except Exception as lipsync_err:
                print(f"[FaceClone] Lip-sync unavailable, using audio-only: {lipsync_err}")
            
            face.status = "ready"
            self._save_meta(face)
            
            return {
                "face_id": face_id,
                "name": face.name,
                "text": text,
                "video_url": video_url,
                "audio_url": f"/face-clone/{face_id}/audio/{text_hash}" if audio_ok else None,
                "image_url": f"/face-clone/{face_id}/image",
                "status": "complete",
                "has_video": video_url is not None,
                "has_audio": audio_ok,
                "cached": False,
            }
        
        except Exception as e:
            face.status = "ready"
            self._save_meta(face)
            print(f"[FaceClone] Talk generation error: {e}")
            return {"error": str(e), "status": "error"}

    # ------------------------------------------
    # REGISTRY / LISTING
    # ------------------------------------------

    def list_faces(self, mode: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all cloned/generated faces"""
        faces = self._faces.values()
        if mode:
            faces = [f for f in faces if f.mode == mode]
        return [f.to_dict() for f in faces]

    def get_face(self, face_id: str) -> Optional[ClonedFace]:
        """Get a specific face by ID"""
        return self._faces.get(face_id)

    def delete_face(self, face_id: str) -> bool:
        """Delete a cloned face and all its assets"""
        face = self._faces.get(face_id)
        if not face:
            return False
        
        # Delete files
        for pattern in [f"{face_id}.*"]:
            for f in self.images_dir.glob(pattern):
                f.unlink(missing_ok=True)
            for f in self.thumbnails_dir.glob(pattern):
                f.unlink(missing_ok=True)
        
        for path in face.videos.values():
            Path(path).unlink(missing_ok=True)
        for path in face.audio_files.values():
            Path(path).unlink(missing_ok=True)
        
        # Delete meta
        meta_path = self.cache_dir / "meta" / f"{face_id}.json"
        meta_path.unlink(missing_ok=True)
        
        del self._faces[face_id]
        return True

    # ------------------------------------------
    # INTERNAL: Face processing
    # ------------------------------------------

    async def _process_face(self, image_path: str, face_id: str) -> Optional[str]:
        """
        Process uploaded face image:
        - Detect face region
        - Crop and align for optimal lip-sync
        - Create thumbnail
        
        For now, we keep the original image as-is since Wav2Lip/SadTalker
        handle face detection internally. In production, add face alignment.
        """
        try:
            # Create a copy as the processed version
            processed_path = str(self.images_dir / f"{face_id}_processed.png")
            
            # For now, just copy the original
            # In production: use dlib/mediapipe for face alignment
            shutil.copy2(image_path, processed_path)
            
            # Create thumbnail (same for now, would resize in production)
            thumb_path = str(self.thumbnails_dir / f"{face_id}_thumb.png")
            shutil.copy2(image_path, thumb_path)
            
            return processed_path
            
        except Exception as e:
            print(f"[FaceClone] Face processing error: {e}")
            return None

    # ------------------------------------------
    # INTERNAL: FLUX image generation
    # ------------------------------------------

    def _build_face_prompt(
        self,
        gender: str,
        ethnicity: str,
        age: str,
        profession: str,
        style: str,
    ) -> str:
        """Build a detailed prompt for FLUX face generation"""
        
        ethnicity_map = {
            "indian": "South Asian Indian",
            "asian": "East Asian",
            "caucasian": "Caucasian European",
            "african": "African",
            "hispanic": "Hispanic Latino",
            "middle_eastern": "Middle Eastern Arab",
            "mixed": "mixed ethnicity",
        }
        
        age_map = {
            "young": "in their late 20s to early 30s",
            "middle": "in their mid 40s",
            "mature": "in their late 50s to 60s",
        }
        
        clothing_map = {
            "legal": "wearing a formal dark business suit with white shirt",
            "medical": "wearing a pristine white medical coat with stethoscope",
            "finance": "wearing a tailored navy business suit",
            "education": "wearing smart casual academic attire",
            "tech": "wearing a clean tech-casual outfit",
            "generic": "wearing neat professional business casual clothing",
        }
        
        eth = ethnicity_map.get(ethnicity, ethnicity)
        age_desc = age_map.get(age, "middle-aged")
        clothes = clothing_map.get(profession, clothing_map["generic"])
        
        prompt = (
            f"Ultra-realistic high-resolution portrait photograph of a real {eth} {gender} person "
            f"{age_desc}, {clothes}, looking directly at the camera with a natural warm friendly expression, "
            f"professional corporate headshot, soft studio lighting, "
            f"neutral blurred background, shallow depth of field, "
            f"sharp focus on face, natural skin texture with pores and subtle imperfections, "
            f"photorealistic 8K quality, Canon EOS R5, 85mm lens, f/1.8 aperture, "
            f"authentic human being, no AI artifacts, no uncanny valley, "
            f"natural eye reflections, real hair texture"
        )
        
        return prompt

    async def _generate_with_flux(self, prompt: str, output_path: str) -> str:
        """Generate face image using FLUX API"""
        
        negative_prompt = (
            "cartoon, illustration, painting, drawing, 3d render, anime, "
            "blurry, low quality, distorted, deformed, ugly, "
            "artificial, plastic, mannequin, wax figure, "
            "multiple people, text, watermark, logo"
        )
        
        if not IMAGE_API_KEY:
            print("[FaceClone] No REPLICATE_API_TOKEN set, using placeholder")
            # Create a placeholder file so the path exists
            Path(output_path).touch()
            return output_path
        
        try:
            import asyncio
            
            headers = {
                "Authorization": f"Token {IMAGE_API_KEY}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "version": "black-forest-labs/flux-dev",
                "input": {
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "width": 1024,
                    "height": 1024,
                    "num_inference_steps": 50,
                    "guidance_scale": 7.5,
                },
            }
            
            async with httpx.AsyncClient(timeout=300) as client:
                response = await client.post(IMAGE_API_URL, headers=headers, json=payload)
                response.raise_for_status()
                prediction = response.json()
                
                prediction_id = prediction["id"]
                status_url = f"{IMAGE_API_URL}/{prediction_id}"
                
                for _ in range(60):
                    await asyncio.sleep(5)
                    status_response = await client.get(status_url, headers=headers)
                    status_data = status_response.json()
                    
                    if status_data["status"] == "succeeded":
                        image_url = status_data["output"]
                        if isinstance(image_url, list):
                            image_url = image_url[0]
                        
                        img_response = await client.get(image_url)
                        img_response.raise_for_status()
                        
                        with open(output_path, 'wb') as f:
                            f.write(img_response.content)
                        
                        return output_path
                    
                    elif status_data["status"] == "failed":
                        raise Exception(f"FLUX failed: {status_data.get('error')}")
            
            return output_path
            
        except Exception as e:
            print(f"[FaceClone] FLUX error: {e}")
            Path(output_path).touch()
            return output_path

    # ------------------------------------------
    # INTERNAL: TTS Audio generation
    # ------------------------------------------

    async def _generate_tts(
        self,
        text: str,
        face_id: str,
        text_hash: str,
        voice_id: Optional[str] = None,
    ) -> str:
        """Generate TTS audio using Sarvam or Chatterbox"""
        audio_path = str(self.audio_dir / f"{face_id}_{text_hash}.wav")
        
        if Path(audio_path).exists():
            return audio_path
        
        try:
            from engine.audio import sarvam_tts
            audio_bytes = await sarvam_tts(text)
            
            if audio_bytes:
                with open(audio_path, 'wb') as f:
                    f.write(audio_bytes)
                return audio_path
        except Exception as e:
            print(f"[FaceClone] TTS error: {e}")
        
        # Create empty file as fallback
        Path(audio_path).touch()
        return audio_path

    # ------------------------------------------
    # INTERNAL: Lip-sync video generation
    # ------------------------------------------

    async def _generate_lipsync(
        self,
        image_path: str,
        audio_path: str,
        face_id: str,
        text_hash: str,
    ) -> str:
        """Generate lip-synced talking video from face image + audio using failover chain"""
        from engine.lipsync_failover import get_lipsync_failover

        failover = get_lipsync_failover()
        result = await failover.generate(
            image_path=image_path,
            audio_path=audio_path,
            text="",
            person_id=f"{face_id}_{text_hash}",
        )

        if result.success and result.video_path:
            print(f"[FaceClone] Lip-sync video generated via {result.provider.value}")
            return result.video_path

        if result.error:
            print(f"[FaceClone] Lip-sync unavailable: {result.error}")

        # Return empty placeholder
        video_path = str(self.video_dir / f"{face_id}_{text_hash}.mp4")
        Path(video_path).touch()
        return video_path


# ==========================================
# SINGLETON & CONVENIENCE FUNCTIONS
# ==========================================

_engine: Optional[FaceCloneEngine] = None

def get_face_clone_engine() -> FaceCloneEngine:
    global _engine
    if _engine is None:
        _engine = FaceCloneEngine()
    return _engine


async def clone_face_from_upload(
    image_bytes: bytes,
    name: str,
    content_type: str = "image/png",
) -> Dict[str, Any]:
    """Clone a face from uploaded image bytes"""
    engine = get_face_clone_engine()
    face = await engine.clone_from_upload(image_bytes, name, content_type)
    return face.to_dict()


async def clone_face_from_url(
    image_url: str,
    name: str,
) -> Dict[str, Any]:
    """Clone a face from a URL"""
    engine = get_face_clone_engine()
    face = await engine.clone_from_url(image_url, name)
    return face.to_dict()


async def generate_new_ai_face(
    name: str,
    gender: str = "female",
    ethnicity: str = "indian",
    age: str = "middle",
    profession: str = "generic",
) -> Dict[str, Any]:
    """Generate a completely new AI face"""
    engine = get_face_clone_engine()
    face = await engine.generate_new_face(name, gender, ethnicity, age, profession)
    return face.to_dict()


async def make_clone_talk(
    face_id: str,
    text: str,
    voice_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Make a cloned/generated face talk"""
    engine = get_face_clone_engine()
    return await engine.make_face_talk(face_id, text, voice_id)
