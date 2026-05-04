# backend/engine/lipsync_failover.py
"""
Lip Sync Failover Chain: Mac Local → NVIDIA Audio2Face → D-ID

Tier 1: Mac Local Lip-Sync (free, CPU/MPS at localhost:7860)
Tier 2: NVIDIA Audio2Face (free credits, needs NVIDIA_API_KEY)
Tier 3: D-ID API (managed, ~$0.05/video, needs DID_API_KEY)

Each tier is health-checked. First available wins.
Falls back to audio-only if all tiers unavailable.
"""

import os
import httpx
import base64
import hashlib
import time
import asyncio
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


# ==========================================
# CONFIGURATION
# ==========================================

WAV2LIP_URL = os.getenv("WAV2LIP_URL", "http://localhost:7860")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_A2F_URL = "https://api.nvidia.com/v1/ace/audio2face-3d"
DID_API_KEY = os.getenv("DID_API_KEY", "")
DID_API_URL = "https://api.d-id.com/talks"

CACHE_DIR = os.getenv("LIPSYNC_CACHE_DIR", "/tmp/lipsync_cache")
HEALTH_CHECK_TIMEOUT = 3.0
GENERATION_TIMEOUT = 300


class Provider(str, Enum):
    WAV2LIP = "wav2lip"
    NVIDIA = "nvidia"
    DID = "did"
    NONE = "none"


@dataclass
class GenerationResult:
    success: bool
    provider: Provider
    video_path: Optional[str] = None
    video_url: Optional[str] = None
    audio_path: Optional[str] = None
    error: Optional[str] = None
    cached: bool = False


# ==========================================
# FAILOVER LIP SYNC SERVICE
# ==========================================

class LipSyncFailover:
    """
    Failover chain for lip-sync video generation.
    Probes each provider in order, uses first available.
    """

    def __init__(self):
        self.cache_dir = Path(CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        (self.cache_dir / "video").mkdir(exist_ok=True)
        (self.cache_dir / "audio").mkdir(exist_ok=True)

        self._last_provider: Optional[Provider] = None
        self._provider_available: Dict[Provider, bool] = {}
        self._last_health_check: float = 0

    # ------------------------------------------
    # PUBLIC API
    # ------------------------------------------

    async def generate(
        self,
        image_path: str,
        audio_path: str,
        text: str = "",
        person_id: str = "",
    ) -> GenerationResult:
        """
        Generate lip-sync video with automatic failover.
        Returns GenerationResult with video_path on success,
        or audio-only fallback if all providers fail.
        """
        text_hash = hashlib.md5(text.encode()).hexdigest()[:10] if text else "notalk"

        # Check cache
        cached = self._check_cache(person_id, text_hash)
        if cached:
            return cached

        # Probe providers in order
        provider = await self._find_provider()

        if provider == Provider.WAV2LIP:
            result = await self._generate_wav2lip(image_path, audio_path, person_id, text_hash)
        elif provider == Provider.NVIDIA:
            result = await self._generate_nvidia(image_path, audio_path, text, person_id, text_hash)
        elif provider == Provider.DID:
            result = await self._generate_did(image_path, audio_path, text, person_id, text_hash)
        else:
            result = GenerationResult(
                success=False,
                provider=Provider.NONE,
                audio_path=audio_path,
                error="No lip-sync provider available",
            )

        # Cache result
        if result.success and result.video_path:
            self._cache_result(person_id, text_hash, result)

        return result

    async def health(self) -> Dict[str, Any]:
        """Check health of all providers"""
        results = {}
        for provider in [Provider.WAV2LIP, Provider.NVIDIA, Provider.DID]:
            available = await self._check_provider(provider)
            results[provider.value] = "available" if available else "unavailable"
        results["active"] = (await self._find_provider()).value
        return results

    # ------------------------------------------
    # PROVIDER DISCOVERY
    # ------------------------------------------

    async def _find_provider(self) -> Provider:
        """Find first available provider, caching results for 30s"""
        now = time.time()
        if now - self._last_health_check < 30 and self._last_provider:
            if self._provider_available.get(self._last_provider, False):
                return self._last_provider

        for provider in [Provider.WAV2LIP, Provider.NVIDIA, Provider.DID]:
            if await self._check_provider(provider):
                self._last_provider = provider
                self._last_health_check = now
                return provider

        self._last_provider = Provider.NONE
        self._last_health_check = now
        return Provider.NONE

    async def _check_provider(self, provider: Provider) -> bool:
        """Check if a specific provider is reachable"""
        try:
            if provider == Provider.WAV2LIP:
                async with httpx.AsyncClient(timeout=HEALTH_CHECK_TIMEOUT) as c:
                    r = await c.get(f"{WAV2LIP_URL}/api/health")
                    available = r.status_code == 200
            elif provider == Provider.NVIDIA:
                available = bool(NVIDIA_API_KEY)
            elif provider == Provider.DID:
                available = bool(DID_API_KEY)
            else:
                available = False

            self._provider_available[provider] = available
            return available
        except Exception:
            self._provider_available[provider] = False
            return False

    # ------------------------------------------
    # TIER 1: LOCAL WAV2LIP
    # ------------------------------------------

    async def _generate_wav2lip(
        self, image_path: str, audio_path: str, person_id: str, text_hash: str
    ) -> GenerationResult:
        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()

            if not image_bytes or not audio_bytes:
                return GenerationResult(False, Provider.WAV2LIP, error="Empty input files")

            image_b64 = base64.b64encode(image_bytes).decode()
            audio_b64 = base64.b64encode(audio_bytes).decode()

            payload = {
                "image": f"data:image/png;base64,{image_b64}",
                "audio": f"data:audio/wav;base64,{audio_b64}",
                "model": "wav2lip",
                "face_resolution": 512,
                "pads": [0, 10, 0, 0],
                "fps": 25,
            }

            async with httpx.AsyncClient(timeout=GENERATION_TIMEOUT) as client:
                r = await client.post(f"{WAV2LIP_URL}/api/lip-sync", json=payload)
                if r.status_code != 200:
                    return GenerationResult(False, Provider.WAV2LIP, error=f"HTTP {r.status_code}")

                data = r.json()
                video_b64 = data.get("video", "")
                if not video_b64:
                    return GenerationResult(False, Provider.WAV2LIP, error="No video in response")

                if "," in video_b64:
                    video_b64 = video_b64.split(",")[1]

                video_bytes = base64.b64decode(video_b64)
                out_path = str(self.cache_dir / "video" / f"{person_id}_{text_hash}.mp4")
                with open(out_path, "wb") as f:
                    f.write(video_bytes)

                return GenerationResult(True, Provider.WAV2LIP, video_path=out_path)

        except Exception as e:
            return GenerationResult(False, Provider.WAV2LIP, error=str(e))

    # ------------------------------------------
    # TIER 2: NVIDIA AUDIO2FACE
    # ------------------------------------------

    async def _generate_nvidia(
        self, image_path: str, audio_path: str, text: str, person_id: str, text_hash: str
    ) -> GenerationResult:
        """
        NVIDIA Audio2Face API: audio → facial blendshapes → animated 3D face.
        Uses free credits from build.nvidia.com.
        """
        if not NVIDIA_API_KEY:
            return GenerationResult(False, Provider.NVIDIA, error="No NVIDIA API key")

        try:
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()

            headers = {
                "Authorization": f"Bearer {NVIDIA_API_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "audio": base64.b64encode(audio_bytes).decode(),
                "emotion": "neutral",
                "format": "mp4",
            }

            async with httpx.AsyncClient(timeout=GENERATION_TIMEOUT) as client:
                r = await client.post(NVIDIA_A2F_URL, headers=headers, json=payload)

                if r.status_code == 200:
                    data = r.json()
                    video_b64 = data.get("video", data.get("output", ""))
                    if video_b64:
                        if "," in video_b64:
                            video_b64 = video_b64.split(",")[1]
                        video_bytes = base64.b64decode(video_b64)
                        out_path = str(self.cache_dir / "video" / f"{person_id}_{text_hash}.mp4")
                        with open(out_path, "wb") as f:
                            f.write(video_bytes)
                        return GenerationResult(True, Provider.NVIDIA, video_path=out_path)

                return GenerationResult(False, Provider.NVIDIA, error=f"NVIDIA HTTP {r.status_code}: {r.text[:200]}")

        except Exception as e:
            return GenerationResult(False, Provider.NVIDIA, error=str(e))

    # ------------------------------------------
    # TIER 3: D-ID MANAGED API
    # ------------------------------------------

    async def _generate_did(
        self, image_path: str, audio_path: str, text: str, person_id: str, text_hash: str
    ) -> GenerationResult:
        """
        D-ID talk API: upload image + text/audio → get talking video.
        Falls back to text-driven if audio upload fails.
        """
        if not DID_API_KEY:
            return GenerationResult(False, Provider.DID, error="No D-ID API key")

        try:
            headers = {
                "Authorization": f"Basic {DID_API_KEY}",
                "Content-Type": "application/json",
            }

            # Read image as base64 data URI
            with open(image_path, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode()

            # Try audio-driven first
            payload = {
                "source_url": f"data:image/png;base64,{image_b64}",
                "script": {
                    "type": "audio",
                    "audio_url": f"data:audio/wav;base64,{self._read_b64(audio_path)}",
                },
                "config": {"fluent": True, "pad_audio": 0.1},
            }

            async with httpx.AsyncClient(timeout=GENERATION_TIMEOUT) as client:
                r = await client.post(DID_API_URL, headers=headers, json=payload)

                if r.status_code != 201:
                    # Fall back to text-driven
                    if text:
                        payload["script"] = {
                            "type": "text",
                            "input": text,
                            "provider": {"type": "microsoft", "voice_id": "en-US-JennyNeural"},
                        }
                        r = await client.post(DID_API_URL, headers=headers, json=payload)

                if r.status_code != 201:
                    return GenerationResult(False, Provider.DID, error=f"D-ID HTTP {r.status_code}")

                data = r.json()
                talk_id = data.get("id", "")

                # Poll for completion
                for _ in range(60):
                    await asyncio.sleep(2)
                    status_r = await client.get(f"{DID_API_URL}/{talk_id}", headers=headers)
                    if status_r.status_code == 200:
                        status_data = status_r.json()
                        if status_data.get("status") == "done":
                            result_url = status_data.get("result_url", "")
                            if result_url:
                                dl = await client.get(result_url)
                                out_path = str(self.cache_dir / "video" / f"{person_id}_{text_hash}.mp4")
                                with open(out_path, "wb") as f:
                                    f.write(dl.content)
                                return GenerationResult(True, Provider.DID, video_path=out_path)
                        elif status_data.get("status") == "error":
                            return GenerationResult(False, Provider.DID, error="D-ID processing failed")

                return GenerationResult(False, Provider.DID, error="D-ID timed out")

        except Exception as e:
            return GenerationResult(False, Provider.DID, error=str(e))

    # ------------------------------------------
    # CACHE
    # ------------------------------------------

    def _check_cache(self, person_id: str, text_hash: str) -> Optional[GenerationResult]:
        cached = self.cache_dir / "video" / f"{person_id}_{text_hash}.mp4"
        if cached.exists() and cached.stat().st_size > 1000:
            return GenerationResult(
                success=True,
                provider=Provider.WAV2LIP,
                video_path=str(cached),
                cached=True,
            )
        return None

    def _cache_result(self, person_id: str, text_hash: str, result: GenerationResult):
        """Cache metadata about the generation"""
        pass

    def _read_b64(self, path: str) -> str:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()


# ==========================================
# SINGLETON
# ==========================================

_failover: Optional[LipSyncFailover] = None


def get_lipsync_failover() -> LipSyncFailover:
    global _failover
    if _failover is None:
        _failover = LipSyncFailover()
    return _failover
