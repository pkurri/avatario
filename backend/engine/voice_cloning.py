"""
Voice Cloning Engine using ElevenLabs
Handles voice cloning, synthesis, and management
"""
import os
import uuid
import asyncio
import aiohttp
import aiofiles
from typing import List, Dict, Optional, BinaryIO
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class VoiceStatus(str, Enum):
    RECORDING = "recording"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


@dataclass
class ClonedVoice:
    id: str
    name: str
    elevenlabs_voice_id: Optional[str]
    status: VoiceStatus
    created_at: datetime
    updated_at: datetime
    user_id: str
    description: str = ""
    preview_url: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    sample_count: int = 0


class VoiceCloningEngine:
    """Engine for voice cloning using ElevenLabs API"""
    
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY", "")
        self.base_url = "https://api.elevenlabs.io/v1"
        self.voices: Dict[str, ClonedVoice] = {}  # user_id -> voice
        self.temp_dir = "/tmp/voice_samples"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    async def clone_voice(
        self,
        user_id: str,
        name: str,
        description: str,
        audio_files: List[BinaryIO],
        labels: Optional[Dict[str, str]] = None
    ) -> ClonedVoice:
        """Clone a voice from audio samples"""
        voice_id = str(uuid.uuid4())
        
        # Create voice record
        voice = ClonedVoice(
            id=voice_id,
            name=name,
            elevenlabs_voice_id=None,
            status=VoiceStatus.PROCESSING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            user_id=user_id,
            description=description,
            labels=labels or {},
            sample_count=len(audio_files)
        )
        
        self.voices[voice_id] = voice
        
        # Upload to ElevenLabs
        try:
            elevenlabs_id = await self._upload_to_elevenlabs(
                name, description, audio_files, labels
            )
            voice.elevenlabs_voice_id = elevenlabs_id
            voice.status = VoiceStatus.READY
            
            # Generate preview
            preview_url = await self._generate_preview(elevenlabs_id)
            voice.preview_url = preview_url
            
        except Exception as e:
            voice.status = VoiceStatus.ERROR
            print(f"Voice cloning failed: {e}")
        
        voice.updated_at = datetime.now()
        return voice
    
    async def _upload_to_elevenlabs(
        self,
        name: str,
        description: str,
        audio_files: List[BinaryIO],
        labels: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload voice samples to ElevenLabs"""
        url = f"{self.base_url}/voices/add"
        
        data = aiohttp.FormData()
        data.add_field('name', name)
        data.add_field('description', description)
        if labels:
            data.add_field('labels', json.dumps(labels))
        
        # Add audio files
        for i, file in enumerate(audio_files):
            file.seek(0)
            data.add_field(
                'files',
                file.read(),
                filename=f'sample_{i}.mp3',
                content_type='audio/mpeg'
            )
        
        headers = {
            'xi-api-key': self.api_key,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"ElevenLabs API error: {error_text}")
                
                result = await response.json()
                return result.get('voice_id')
    
    async def synthesize_speech(
        self,
        voice_id: str,
        text: str,
        model_id: str = "eleven_multilingual_v2",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True
    ) -> bytes:
        """Synthesize speech using cloned voice"""
        voice = self.voices.get(voice_id)
        if not voice or not voice.elevenlabs_voice_id:
            raise ValueError("Voice not found or not ready")
        
        url = f"{self.base_url}/text-to-speech/{voice.elevenlabs_voice_id}"
        
        headers = {
            'xi-api-key': self.api_key,
            'Content-Type': 'application/json',
        }
        
        payload = {
            'text': text,
            'model_id': model_id,
            'voice_settings': {
                'stability': stability,
                'similarity_boost': similarity_boost,
                'style': style,
                'use_speaker_boost': use_speaker_boost,
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Synthesis error: {error_text}")
                
                return await response.read()
    
    async def _generate_preview(self, elevenlabs_voice_id: str) -> str:
        """Generate a preview URL for the voice"""
        preview_text = "Hello! This is my cloned voice speaking."
        audio_data = await self.synthesize_speech(
            voice_id=elevenlabs_voice_id,
            text=preview_text
        )
        
        # Save to temp file and return URL
        preview_path = f"{self.temp_dir}/preview_{elevenlabs_voice_id}.mp3"
        async with aiofiles.open(preview_path, 'wb') as f:
            await f.write(audio_data)
        
        return f"/voice/previews/preview_{elevenlabs_voice_id}.mp3"
    
    def get_user_voices(self, user_id: str) -> List[ClonedVoice]:
        """Get all cloned voices for a user"""
        return [
            voice for voice in self.voices.values()
            if voice.user_id == user_id
        ]
    
    def get_voice(self, voice_id: str) -> Optional[ClonedVoice]:
        """Get a specific voice by ID"""
        return self.voices.get(voice_id)
    
    async def delete_voice(self, voice_id: str) -> bool:
        """Delete a cloned voice"""
        voice = self.voices.get(voice_id)
        if not voice:
            return False
        
        # Delete from ElevenLabs
        if voice.elevenlabs_voice_id:
            try:
                url = f"{self.base_url}/voices/{voice.elevenlabs_voice_id}"
                headers = {'xi-api-key': self.api_key}
                
                async with aiohttp.ClientSession() as session:
                    async with session.delete(url, headers=headers) as response:
                        if response.status not in [200, 204]:
                            print(f"Warning: Failed to delete voice from ElevenLabs: {response.status}")
            except Exception as e:
                print(f"Error deleting voice from ElevenLabs: {e}")
        
        # Remove from local storage
        del self.voices[voice_id]
        return True
    
    async def update_voice(
        self,
        voice_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[ClonedVoice]:
        """Update voice metadata"""
        voice = self.voices.get(voice_id)
        if not voice:
            return None
        
        if name:
            voice.name = name
        if description:
            voice.description = description
        if labels:
            voice.labels = labels
        
        voice.updated_at = datetime.now()
        return voice
    
    async def get_elevenlabs_voices(self) -> List[Dict]:
        """Get available voices from ElevenLabs"""
        url = f"{self.base_url}/voices"
        headers = {'xi-api-key': self.api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return []
                
                result = await response.json()
                return result.get('voices', [])


# Global instance
voice_cloning_engine = VoiceCloningEngine()
