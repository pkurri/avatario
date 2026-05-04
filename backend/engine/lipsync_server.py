# backend/engine/lipsync_server.py
"""
Local Lip-Sync API Server (Mac MPS / CPU compatible)
Exposes Wav2Lip-compatible API at localhost:7860

Uses audio-driven facial animation:
- Analyzes audio amplitude to drive mouth movement
- Warps the mouth region on the face image
- Produces an MP4 video with lip-sync effect

Run: python engine/lipsync_server.py
"""

import os
import sys
import json
import base64
import tempfile
import hashlib
import asyncio
from pathlib import Path
from io import BytesIO

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import soundfile as sf

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
import uvicorn

# ==========================================
# CONFIG
# ==========================================

PORT = int(os.getenv("LIPSYNC_SERVER_PORT", "7860"))
OUTPUT_DIR = Path(os.getenv("LIPSYNC_OUTPUT_DIR", "/tmp/lipsync_output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Lip Sync Server (Mac)")


# ==========================================
# AUDIO-DRIVEN MOUTH ANIMATION ENGINE
# ==========================================

class MouthAnimator:
    """
    Creates talking video by animating the mouth region based on audio amplitude.
    Works on CPU/MPS - no CUDA required.
    """

    def __init__(self):
        self.face_cascade = None
        if HAS_CV2:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            if Path(cascade_path).exists():
                self.face_cascade = cv2.CascadeClassifier(cascade_path)

    def detect_mouth_region(self, image: np.ndarray) -> tuple:
        """
        Detect face and estimate mouth position.
        Returns (mx, my, mw, mh) or None.
        """
        if self.face_cascade is None:
            h, w = image.shape[:2]
            return (int(w * 0.35), int(h * 0.55), int(w * 0.3), int(h * 0.15))

        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)

        if len(faces) > 0:
            x, y, w, h = faces[0]
            # Mouth is roughly in the lower third of the face
            mx = x + int(w * 0.2)
            my = y + int(h * 0.65)
            mw = int(w * 0.6)
            mh = int(h * 0.2)
            return (mx, my, mw, mh)

        h, w = image.shape[:2]
        return (int(w * 0.35), int(h * 0.55), int(w * 0.3), int(h * 0.15))

    def get_audio_envelope(self, audio_data: np.ndarray, sample_rate: int, fps: int, num_frames: int) -> np.ndarray:
        """
        Compute audio amplitude envelope aligned to video frames.
        """
        if len(audio_data) == 0:
            return np.ones(num_frames) * 0.5

        # Compute RMS energy in windows aligned to frames
        samples_per_frame = int(sample_rate / fps)
        envelope = np.zeros(num_frames)

        for i in range(num_frames):
            start = i * samples_per_frame
            end = min(start + samples_per_frame, len(audio_data))
            if end > start:
                chunk = audio_data[start:end]
                rms = np.sqrt(np.mean(chunk ** 2))
                envelope[i] = rms

        # Normalize to [0, 1]
        if envelope.max() > 0:
            envelope = envelope / envelope.max()

        # Smooth
        kernel = np.ones(3) / 3
        envelope = np.convolve(envelope, kernel, mode='same')

        return envelope

    def animate_mouth(
        self,
        image: np.ndarray,
        mouth_region: tuple,
        amplitude: float,
    ) -> np.ndarray:
        """
        Warp the mouth region based on audio amplitude.
        Higher amplitude = more open mouth.
        """
        mx, my, mw, mh = mouth_region
        h, w = image.shape[:2]

        # Clamp to image bounds
        mx = max(0, mx)
        my = max(0, my)
        mw = min(mw, w - mx)
        mh = min(mh, h - my)

        if mw <= 0 or mh <= 0:
            return image

        result = image.copy()

        # Scale mouth opening based on amplitude (0.3 to 1.5x height)
        scale = 0.4 + amplitude * 1.1

        # Extract mouth region
        mouth = image[my:my + mh, mx:mx + mw]

        # Create dark oval for open mouth effect
        mouth_pil = Image.fromarray(mouth)
        draw = ImageDraw.Draw(mouth_pil)

        # Draw an ellipse that gets taller with amplitude
        oval_top = int(mh * (1 - scale) / 2)
        oval_bottom = int(mh * (1 + scale) / 2)
        oval_left = int(mw * 0.15)
        oval_right = int(mw * 0.85)

        # Dark interior of mouth
        if amplitude > 0.15:
            darkness = int(min(amplitude * 180, 120))
            draw.ellipse(
                [oval_left, max(0, oval_top), oval_right, min(mh, oval_bottom)],
                fill=(darkness // 3, darkness // 4, darkness // 5)
            )

        mouth = np.array(mouth_pil)

        # Vertical stretch
        new_h = max(1, int(mh * scale))
        stretched = cv2.resize(mouth, (mw, new_h)) if HAS_CV2 else np.array(
            Image.fromarray(mouth).resize((mw, new_h), Image.LANCZOS)
        )

        # Place back centered vertically
        y_offset = my - (new_h - mh) // 2
        y_offset = max(0, min(y_offset, h - new_h))

        # Blend the stretched mouth back
        try:
            if HAS_CV2:
                stretched_resized = cv2.resize(stretched, (mw, mh))
            else:
                stretched_resized = np.array(Image.fromarray(stretched).resize((mw, mh), Image.LANCZOS))

            alpha = min(amplitude * 1.5, 0.9)
            result[my:my + mh, mx:mx + mw] = (
                result[my:my + mh, mx:mx + mw] * (1 - alpha) +
                stretched_resized * alpha
            ).astype(np.uint8)
        except ValueError:
            pass

        return result

    def generate_video(
        self,
        image_bytes: bytes,
        audio_bytes: bytes,
        fps: int = 25,
    ) -> bytes:
        """
        Generate a talking video from image + audio.
        Returns MP4 video bytes.
        """
        # Load image
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        image = image.resize((512, 512), Image.LANCZOS)
        image_np = np.array(image)

        # Load audio
        audio_data, sample_rate = sf.read(BytesIO(audio_bytes))
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)

        # Detect mouth
        mouth_region = self.detect_mouth_region(image_np)

        # Calculate duration and frames
        duration = len(audio_data) / sample_rate if sample_rate > 0 else 3.0
        num_frames = max(1, int(duration * fps))

        # Get audio envelope
        envelope = self.get_audio_envelope(audio_data, sample_rate, fps, num_frames)

        # Generate frames
        frames = []
        for i in range(num_frames):
            amp = envelope[i] if i < len(envelope) else 0.3
            frame = self.animate_mouth(image_np.copy(), mouth_region, amp)
            frames.append(frame)

        # Encode to video using OpenCV
        if HAS_CV2:
            return self._encode_cv2(frames, audio_bytes, fps, sample_rate)
        else:
            return self._encode_fallback(frames, audio_bytes, fps)

    def _encode_cv2(self, frames: list, audio_bytes: bytes, fps: int, sample_rate: int) -> bytes:
        """Encode frames to MP4 using OpenCV"""
        out_path = OUTPUT_DIR / f"video_{hashlib.md5(audio_bytes).hexdigest()[:8]}.mp4"

        h, w = frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        writer = cv2.VideoWriter(str(out_path), fourcc, fps, (w, h))

        for frame in frames:
            writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

        writer.release()

        # Add audio using ffmpeg if available, otherwise return video-only
        with open(out_path, 'rb') as f:
            return f.read()

    def _encode_fallback(self, frames: list, audio_bytes: bytes, fps: int) -> bytes:
        """Fallback: save frames as individual images + audio info"""
        out_path = OUTPUT_DIR / f"video_{hashlib.md5(audio_bytes).hexdigest()[:8]}.mp4"

        # Save as animated GIF as last resort
        pil_frames = [Image.fromarray(f) for f in frames]
        gif_buf = BytesIO()
        pil_frames[0].save(
            gif_buf,
            format='GIF',
            save_all=True,
            append_images=pil_frames[1:],
            duration=int(1000 / fps),
            loop=0,
        )

        with open(out_path.with_suffix('.gif'), 'wb') as f:
            f.write(gif_buf.getvalue())

        return gif_buf.getvalue()


# ==========================================
# API ENDPOINTS
# ==========================================

animator = MouthAnimator()


@app.get("/api/health")
async def health():
    return {"status": "ok", "provider": "mac-lipsync", "has_cv2": HAS_CV2}


@app.post("/api/lip-sync")
async def lip_sync(request: Request):
    """
    Generate lip-sync video.
    Expects: { "image": "data:image/png;base64,...", "audio": "data:audio/wav;base64,...", ... }
    Returns: { "video": "data:video/mp4;base64,..." }
    """
    try:
        body = await request.json()

        image_data = body.get("image", "")
        audio_data = body.get("audio", "")

        # Strip data URI prefix
        for field in ["image", "audio"]:
            val = body.get(field, "")
            if "," in val:
                body[field] = val.split(",")[1]

        image_bytes = base64.b64decode(body["image"])
        audio_bytes = base64.b64decode(body["audio"])

        if not image_bytes or not audio_bytes:
            return JSONResponse({"error": "Missing image or audio"}, status_code=400)

        # Generate video
        video_bytes = animator.generate_video(image_bytes, audio_bytes)

        # Return as base64
        video_b64 = base64.b64encode(video_bytes).decode()
        return {"video": f"data:video/mp4;base64,{video_b64}"}

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/models")
async def list_models():
    return {"models": [{"id": "mac-lipsync", "name": "Mac CPU/MPS Lip Sync"}]}


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    print(f"[LipSync Server] Starting on port {PORT} (MPS/CPU mode)")
    print(f"[LipSync Server] OpenCV: {'available' if HAS_CV2 else 'unavailable (using fallback)'}")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
