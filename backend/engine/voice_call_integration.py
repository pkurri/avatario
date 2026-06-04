"""
Voice Call Integration - Connect Cloned Voice to Phone Calls
Handles TTS generation using cloned voices for call responses
"""
import asyncio
import base64
import io
import json
try:
    import audioop
except ImportError:
    import audioop_lts as audioop
from typing import Optional, Dict, Any
from datetime import datetime

from engine.voice_cloning import voice_cloning_engine, VoiceStatus
from engine.twilio_integration import twilio_integration, PhoneCall


class VoiceCallIntegration:
    """Integrates cloned voices with phone calls"""
    
    def __init__(self):
        self.active_voices: Dict[str, str] = {}  # user_id -> voice_id
        self.call_voice_settings: Dict[str, Dict] = {}  # call_sid -> settings
    
    async def set_user_voice(self, user_id: str, voice_id: str) -> bool:
        """Set the cloned voice to use for a user's calls"""
        # Verify voice exists and is ready
        voice = voice_cloning_engine.get_voice(voice_id)
        if not voice or voice.status != VoiceStatus.READY:
            return False
        
        self.active_voices[user_id] = voice_id
        return True
    
    def get_user_voice(self, user_id: str) -> Optional[str]:
        """Get the active voice ID for a user"""
        return self.active_voices.get(user_id)
    
    async def generate_call_greeting(
        self,
        call_sid: str,
        user_id: str,
        custom_greeting: Optional[str] = None
    ) -> Optional[bytes]:
        """Generate greeting audio using cloned voice"""
        voice_id = self.get_user_voice(user_id)
        if not voice_id:
            # No cloned voice set, use default TTS
            return await self._generate_default_greeting(custom_greeting)
        
        # Use cloned voice
        greeting_text = custom_greeting or "Hello! You've reached me. I'm using my AI assistant to take this call. How can I help you today?"
        
        try:
            # Generate speech with cloned voice
            audio_data = await voice_cloning_engine.synthesize_speech(
                voice_id=voice_id,
                text=greeting_text,
                stability=0.5,
                similarity_boost=0.75
            )
            
            # Convert to μ-law format for Twilio
            pcm_audio = await self._convert_mp3_to_pcm(audio_data)
            mulaw_audio = audioop.lin2ulaw(pcm_audio, 2)  # 16-bit PCM to μ-law
            
            # Store call settings
            self.call_voice_settings[call_sid] = {
                'user_id': user_id,
                'voice_id': voice_id,
                'greeting': greeting_text
            }
            
            return mulaw_audio
            
        except Exception as e:
            print(f"[VoiceCall] Failed to generate greeting: {e}")
            return await self._generate_default_greeting(greeting_text)
    
    async def generate_call_response(
        self,
        call_sid: str,
        response_text: str
    ) -> Optional[bytes]:
        """Generate AI response audio using cloned voice"""
        call_settings = self.call_voice_settings.get(call_sid)
        if not call_settings:
            # No voice set for this call
            return await self._generate_default_response(response_text)
        
        voice_id = call_settings.get('voice_id')
        if not voice_id:
            return await self._generate_default_response(response_text)
        
        try:
            # Generate speech with cloned voice
            audio_data = await voice_cloning_engine.synthesize_speech(
                voice_id=voice_id,
                text=response_text,
                stability=0.5,
                similarity_boost=0.75
            )
            
            # Convert to μ-law format
            pcm_audio = await self._convert_mp3_to_pcm(audio_data)
            mulaw_audio = audioop.lin2ulaw(pcm_audio, 2)
            
            return mulaw_audio
            
        except Exception as e:
            print(f"[VoiceCall] Failed to generate response: {e}")
            return await self._generate_default_response(response_text)
    
    async def _convert_mp3_to_pcm(self, mp3_data: bytes) -> bytes:
        """Convert MP3 audio to 16-bit PCM at 8kHz"""
        try:
            # Use pydub for audio conversion
            from pydub import AudioSegment
            
            # Load MP3
            audio = AudioSegment.from_mp3(io.BytesIO(mp3_data))
            
            # Convert to 8kHz, mono, 16-bit
            audio = audio.set_frame_rate(8000).set_channels(1).set_sample_width(2)
            
            # Export as raw PCM
            pcm_io = io.BytesIO()
            audio.export(pcm_io, format='raw')
            return pcm_io.getvalue()
            
        except ImportError:
            # Fallback: return MP3 data as-is (Twilio will handle it)
            return mp3_data
        except Exception as e:
            print(f"[VoiceCall] Audio conversion failed: {e}")
            return mp3_data
    
    async def _generate_default_greeting(self, text: Optional[str] = None) -> bytes:
        """Generate default greeting using standard TTS"""
        greeting = text or "Hello! This is an automated assistant. How can I help you?"
        
        # TODO: Use default TTS (Sarvam or other)
        # For now, return empty (Twilio will use <Say> verb as fallback)
        return b""
    
    async def _generate_default_response(self, text: str) -> bytes:
        """Generate default response using standard TTS"""
        # TODO: Use default TTS
        return b""
    
    def cleanup_call(self, call_sid: str):
        """Clean up call voice settings when call ends"""
        if call_sid in self.call_voice_settings:
            del self.call_voice_settings[call_sid]
    
    async def stream_cloned_voice_to_call(
        self,
        call_sid: str,
        websocket: Any,
        text: str
    ):
        """Stream cloned voice audio to an active call"""
        audio_data = await self.generate_call_response(call_sid, text)
        if audio_data and websocket:
            # Stream audio in chunks
            chunk_size = 160  # 20ms at 8kHz μ-law
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                await websocket.send_bytes(chunk)
                await asyncio.sleep(0.02)  # 20ms delay between chunks


# Global instance
voice_call_integration = VoiceCallIntegration()


# Helper functions for API endpoints
async def handle_inbound_call_with_cloned_voice(
    call_sid: str,
    from_number: str,
    to_number: str,
    user_id: str = "default_user"
) -> str:
    """Handle inbound call with cloned voice greeting"""
    # Get user's voice settings from mobile settings
    from backend.main import mobile_user_settings
    
    user_settings = mobile_user_settings.get(user_id, {})
    voice_id = user_settings.get('selectedVoiceId')
    use_cloned = user_settings.get('useClonedVoice', False)
    greeting = user_settings.get('greetingScript')
    
    if use_cloned and voice_id:
        # Set the voice for this call
        await voice_call_integration.set_user_voice(user_id, voice_id)
        
        # Generate TwiML with streaming
        from backend.engine.twilio_integration import twilio_integration
        host = twilio_integration._get_host()
        
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="wss://{host}/voice/stream/twilio/{call_sid}?user_id={user_id}&voice_id={voice_id}" />
    </Connect>
</Response>"""
        return twiml
    else:
        # Use standard TTS greeting
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>{greeting or "Hello! You've reached me. I'm using my AI assistant. How can I help you?"}</Say>
    <Connect>
        <Stream url="wss://{host}/voice/stream/twilio/{call_sid}" />
    </Connect>
</Response>"""
        return twiml
