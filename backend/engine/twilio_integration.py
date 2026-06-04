"""
Twilio Voice Integration for Phone Calls
Handles inbound/outbound calls, WebSocket streaming, and call control
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json
import os
import aiohttp
import base64

class CallDirection(Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class CallStatus(Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no_answer"

@dataclass
class PhoneCall:
    call_sid: str
    direction: CallDirection
    from_number: str
    to_number: str
    status: CallStatus
    account_sid: Optional[str] = None
    persona_id: str = "anya"
    business_id: str = "default"
    transcript: List[Dict] = field(default_factory=list)
    recording_url: Optional[str] = None
    duration: int = 0
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class TwilioIntegration:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.phone_number = os.getenv("TWILIO_PHONE_NUMBER", "")
        self.base_url = "https://api.twilio.com/2010-04-01"
        
        # Active calls storage
        self.active_calls: Dict[str, PhoneCall] = {}
        self.call_history: List[PhoneCall] = []
        
        # WebSocket handlers
        self.websocket_handlers: Dict[str, Callable] = {}
        
        # Audio processing
        self.audio_queues: Dict[str, asyncio.Queue] = {}
    
    def is_configured(self) -> bool:
        """Check if Twilio credentials are configured"""
        return bool(self.account_sid and self.auth_token)
    
    async def make_outbound_call(
        self,
        to_number: str,
        from_number: Optional[str] = None,
        twiml_url: Optional[str] = None,
        webhook_url: Optional[str] = None,
        persona_id: str = "anya",
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make an outbound phone call"""
        if not self.is_configured():
            return {"error": "Twilio not configured", "status": "failed"}
        
        from_num = from_number or self.phone_number
        
        # Use default webhook URL if not provided
        status_callback = webhook_url or f"{self._get_base_url()}/webhooks/twilio/status"
        
        # Build TwiML URL for call handling
        if not twiml_url:
            twiml_url = f"{self._get_base_url()}/voice/twiml?persona_id={persona_id}"
        
        # Make API request to Twilio
        url = f"{self.base_url}/Accounts/{self.account_sid}/Calls.json"
        
        payload = {
            "To": to_number,
            "From": from_num,
            "Url": twiml_url,
            "StatusCallback": status_callback,
            "StatusCallbackEvent": ["initiated", "ringing", "answered", "completed"],
            "StatusCallbackMethod": "POST",
            "MachineDetection": "Enable",
            "MachineDetectionTimeout": 30
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)
                
                async with session.post(url, data=payload, auth=auth) as response:
                    data = await response.json()
                    
                    if response.status == 201:
                        call_sid = data.get("sid")
                        
                        # Create call record
                        call = PhoneCall(
                            call_sid=call_sid,
                            direction=CallDirection.OUTBOUND,
                            from_number=from_num,
                            to_number=to_number,
                            status=CallStatus.INITIATED,
                            account_sid=self.account_sid,
                            persona_id=persona_id,
                            metadata=context or {}
                        )
                        self.active_calls[call_sid] = call
                        
                        return {
                            "success": True,
                            "call_sid": call_sid,
                            "status": "initiated",
                            "to": to_number,
                            "from": from_num,
                            "direction": "outbound"
                        }
                    else:
                        return {
                            "error": data.get("message", "Unknown error"),
                            "status": "failed",
                            "code": data.get("code")
                        }
                        
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    async def handle_inbound_webhook(self, request_data: Dict) -> str:
        """Generate TwiML for inbound call handling"""
        call_sid = request_data.get("CallSid")
        from_number = request_data.get("From")
        to_number = request_data.get("To")
        
        # Create call record
        call = PhoneCall(
            call_sid=call_sid,
            direction=CallDirection.INBOUND,
            from_number=from_number,
            to_number=to_number,
            status=CallStatus.ANSWERED,
            account_sid=request_data.get("AccountSid"),
            started_at=datetime.utcnow().isoformat()
        )
        self.active_calls[call_sid] = call
        
        # Generate TwiML with streaming
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="wss://{self._get_host()}/voice/stream/twilio/{call_sid}" />
    </Connect>
</Response>"""
        
        return twiml
    
    async def handle_status_callback(self, request_data: Dict) -> Dict:
        """Handle Twilio status callback"""
        call_sid = request_data.get("CallSid")
        status = request_data.get("CallStatus")
        
        call = self.active_calls.get(call_sid)
        if call:
            # Update call status
            status_map = {
                "initiated": CallStatus.INITIATED,
                "ringing": CallStatus.RINGING,
                "in-progress": CallStatus.IN_PROGRESS,
                "completed": CallStatus.COMPLETED,
                "busy": CallStatus.BUSY,
                "failed": CallStatus.FAILED,
                "no-answer": CallStatus.NO_ANSWER
            }
            
            call.status = status_map.get(status, CallStatus.IN_PROGRESS)
            
            if status == "completed":
                call.ended_at = datetime.utcnow().isoformat()
                call.duration = int(request_data.get("CallDuration", 0))
                call.recording_url = request_data.get("RecordingUrl")
                
                # Move to history
                self.call_history.append(call)
                del self.active_calls[call_sid]
        
        return {"status": "processed"}
    
    async def stream_audio_to_call(
        self,
        call_sid: str,
        audio_data: bytes,
        websocket: Any
    ):
        """Stream audio to an active call via WebSocket"""
        # Twilio uses μ-law (PCMU) encoding at 8kHz
        # Audio data should already be in the correct format
        
        if websocket and not websocket.closed:
            # Send audio chunk as binary
            await websocket.send_bytes(audio_data)
    
    async def handle_twilio_stream(
        self,
        websocket: Any,
        call_sid: str,
        audio_callback: Callable[[str, bytes], asyncio.Future]
    ):
        """Handle bidirectional audio streaming with Twilio"""
        self.websocket_handlers[call_sid] = websocket
        self.audio_queues[call_sid] = asyncio.Queue()
        
        try:
            # Send initial greeting via AI
            await self._send_ai_greeting(call_sid, websocket)
            
            # Start audio processing loop
            while True:
                # Receive audio from caller
                message = await websocket.receive()
                
                if "bytes" in message:
                    audio_chunk = message["bytes"]
                    
                    # Process audio (STT)
                    if audio_callback:
                        await audio_callback(call_sid, audio_chunk)
                        
                elif "text" in message:
                    # Handle control messages
                    text_data = json.loads(message["text"])
                    
                    if text_data.get("event") == "start":
                        # Stream started
                        print(f"[Twilio] Stream started for call {call_sid}")
                        
                    elif text_data.get("event") == "stop":
                        # Stream stopped
                        print(f"[Twilio] Stream stopped for call {call_sid}")
                        break
                        
        except Exception as e:
            print(f"[Twilio] Stream error for {call_sid}: {e}")
        finally:
            # Cleanup
            if call_sid in self.websocket_handlers:
                del self.websocket_handlers[call_sid]
            if call_sid in self.audio_queues:
                del self.audio_queues[call_sid]
    
    async def _send_ai_greeting(self, call_sid: str, websocket: Any):
        """Send AI greeting at the start of the call"""
        # TODO: Integrate with TTS to generate greeting audio
        # For now, just send a text message
        greeting = {
            "type": "ai_greeting",
            "text": "Hello! I'm your AI assistant. How can I help you today?"
        }
        await websocket.send_text(json.dumps(greeting))
    
    async def hangup_call(self, call_sid: str) -> Dict:
        """End an active call"""
        if not self.is_configured():
            return {"error": "Twilio not configured"}
        
        url = f"{self.base_url}/Accounts/{self.account_sid}/Calls/{call_sid}.json"
        
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)
                
                async with session.post(
                    url,
                    data={"Status": "completed"},
                    auth=auth
                ) as response:
                    if response.status == 200:
                        return {"success": True, "call_sid": call_sid, "status": "completed"}
                    else:
                        data = await response.json()
                        return {"error": data.get("message"), "status": "failed"}
                        
        except Exception as e:
            return {"error": str(e)}
    
    async def transfer_call(
        self,
        call_sid: str,
        transfer_to: str,
        whisper_message: Optional[str] = None
    ) -> Dict:
        """Transfer call to another number"""
        if not self.is_configured():
            return {"error": "Twilio not configured"}
        
        # Generate TwiML for transfer
        if whisper_message:
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>{whisper_message}</Say>
    <Dial>{transfer_to}</Dial>
</Response>"""
        else:
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Dial>{transfer_to}</Dial>
</Response>"""
        
        # Update the call with new TwiML
        url = f"{self.base_url}/Accounts/{self.account_sid}/Calls/{call_sid}.json"
        
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)
                
                async with session.post(
                    url,
                    data={"Twiml": twiml},
                    auth=auth
                ) as response:
                    if response.status == 200:
                        return {
                            "success": True,
                            "call_sid": call_sid,
                            "transferred_to": transfer_to
                        }
                    else:
                        data = await response.json()
                        return {"error": data.get("message")}
                        
        except Exception as e:
            return {"error": str(e)}
    
    async def start_recording(
        self,
        call_sid: str,
        recording_callback: Optional[str] = None
    ) -> Dict:
        """Start recording a call"""
        if not self.is_configured():
            return {"error": "Twilio not configured"}
        
        url = f"{self.base_url}/Accounts/{self.account_sid}/Calls/{call_sid}/Recordings.json"
        
        payload = {
            "RecordingStatusCallback": recording_callback or f"{self._get_base_url()}/webhooks/twilio/recording",
            "RecordingChannels": "dual",
            "RecordingStatusCallbackMethod": "POST"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)
                
                async with session.post(url, data=payload, auth=auth) as response:
                    data = await response.json()
                    
                    if response.status == 201:
                        return {
                            "success": True,
                            "recording_sid": data.get("sid"),
                            "call_sid": call_sid
                        }
                    else:
                        return {"error": data.get("message")}
                        
        except Exception as e:
            return {"error": str(e)}
    
    async def send_dtmf(self, call_sid: str, digits: str) -> Dict:
        """Send DTMF tones to the call"""
        if not self.is_configured():
            return {"error": "Twilio not configured"}
        
        url = f"{self.base_url}/Accounts/{self.account_sid}/Calls/{call_sid}.json"
        
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)
                
                async with session.post(
                    url,
                    data={"Twiml": f'<Response><Play digits="{digits}"/></Response>'},
                    auth=auth
                ) as response:
                    if response.status == 200:
                        return {"success": True, "digits_sent": digits}
                    else:
                        data = await response.json()
                        return {"error": data.get("message")}
                        
        except Exception as e:
            return {"error": str(e)}
    
    def get_call(self, call_sid: str) -> Optional[PhoneCall]:
        """Get call details"""
        return self.active_calls.get(call_sid) or next(
            (c for c in self.call_history if c.call_sid == call_sid),
            None
        )
    
    def list_calls(
        self,
        status: Optional[CallStatus] = None,
        direction: Optional[CallDirection] = None,
        limit: int = 50
    ) -> List[PhoneCall]:
        """List calls with optional filtering"""
        calls = list(self.active_calls.values()) + self.call_history
        
        if status:
            calls = [c for c in calls if c.status == status]
        
        if direction:
            calls = [c for c in calls if c.direction == direction]
        
        # Sort by start time, newest first
        calls.sort(
            key=lambda c: c.started_at or "",
            reverse=True
        )
        
        return calls[:limit]
    
    def get_analytics(self) -> Dict:
        """Get call analytics"""
        all_calls = self.call_history + list(self.active_calls.values())
        
        total_calls = len(all_calls)
        inbound = len([c for c in all_calls if c.direction == CallDirection.INBOUND])
        outbound = len([c for c in all_calls if c.direction == CallDirection.OUTBOUND])
        completed = len([c for c in all_calls if c.status == CallStatus.COMPLETED])
        failed = len([c for c in all_calls if c.status == CallStatus.FAILED])
        
        total_duration = sum(c.duration for c in all_calls)
        avg_duration = total_duration / completed if completed > 0 else 0
        
        return {
            "total_calls": total_calls,
            "inbound": inbound,
            "outbound": outbound,
            "completed": completed,
            "failed": failed,
            "success_rate": round(completed / total_calls * 100, 2) if total_calls > 0 else 0,
            "average_duration_seconds": round(avg_duration, 2),
            "total_talk_time_minutes": round(total_duration / 60, 2)
        }
    
    def _get_base_url(self) -> str:
        """Get the base URL for webhooks"""
        return os.getenv("PUBLIC_BASE_URL", "https://api.avatario.com")
    
    def _get_host(self) -> str:
        """Get the host for WebSocket URLs"""
        return os.getenv("WEBSOCKET_HOST", "api.avatario.com")


# Global Twilio integration instance
twilio_integration = TwilioIntegration()


def get_twilio_integration() -> TwilioIntegration:
    """Get the global Twilio integration instance"""
    return twilio_integration


# Example usage and testing
async def test_twilio():
    """Test Twilio integration"""
    twilio = get_twilio_integration()
    
    print("Twilio Configuration:")
    print(f"  Account SID: {twilio.account_sid[:10]}..." if twilio.account_sid else "  Not configured")
    print(f"  Phone Number: {twilio.phone_number}")
    
    # Test analytics
    print("\nCall Analytics:")
    analytics = twilio.get_analytics()
    for key, value in analytics.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(test_twilio())
