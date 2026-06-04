"""
SignalWire Integration - 70% cheaper than Twilio
Drop-in replacement with compatible API
"""

import asyncio
import base64
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import aiohttp
from aiohttp import web, WSMsgType

from engine.voice_provider import VoiceProvider, CallInfo, AudioStreamConfig

logger = logging.getLogger(__name__)


class SignalWireProvider(VoiceProvider):
    """
    SignalWire voice provider implementation.
    Costs: $0.004/min vs Twilio $0.013/min = 70% savings
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.project_id = config.get('project_id')
        self.token = config.get('token')
        self.space_url = config.get('space_url')
        self.phone_number = config.get('phone_number')
        self.base_url = config.get('base_url', 'http://localhost:8000')
        
        # Active call management
        self.active_calls: Dict[str, Dict] = {}
        self.websocket_connections: Dict[str, web.WebSocketResponse] = {}
        
        # Build REST API URL
        self.api_base = f"https://{self.space_url}/api/laml/2010-04-01/Accounts/{self.project_id}"
        
    async def _make_request(self, method: str, endpoint: str, 
                           data: Dict = None, params: Dict = None) -> Dict:
        """Make authenticated request to SignalWire API"""
        url = f"{self.api_base}{endpoint}"
        auth = aiohttp.BasicAuth(self.project_id, self.token)
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method, url, auth=auth, json=data, params=params
            ) as response:
                if response.status >= 400:
                    text = await response.text()
                    raise RuntimeError(f"SignalWire API error: {response.status} - {text}")
                
                # Some endpoints return empty body
                if response.status == 204:
                    return {}
                    
                return await response.json()
    
    async def handle_inbound_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming call from SignalWire webhook.
        Returns LaML (SignalWire's TwiML equivalent).
        """
        call_sid = call_data.get('CallSid') or call_data.get('call_sid')
        from_number = call_data.get('From') or call_data.get('from')
        to_number = call_data.get('To') or call_data.get('to')
        
        logger.info(f"SignalWire inbound call: {call_sid} from {from_number}")
        
        # Store call info
        self.active_calls[call_sid] = {
            'sid': call_sid,
            'from': from_number,
            'to': to_number,
            'direction': 'inbound',
            'started_at': datetime.now(),
            'status': 'ringing'
        }
        
        # Build LaML response (TwiML compatible)
        # Connect to WebSocket for AI streaming
        websocket_url = f"{self.base_url}/voice/stream/signalwire/{call_sid}"
        
        laml_response = {
            "Response": {
                "Connect": {
                    "Stream": {
                        "url": websocket_url,
                        "name": f"ai_stream_{call_sid}"
                    }
                },
                # Fallback if streaming fails
                "Say": {
                    "voice": "alice",
                    "language": "en-US",
                    "text": "Please wait while I connect you to the AI assistant."
                }
            }
        }
        
        return {
            "contentType": "application/json",
            "body": laml_response,
            "call_sid": call_sid
        }
    
    async def make_outbound_call(self, to_number: str, from_number: str = None,
                                  callback_url: str = None, 
                                  custom_data: Dict = None) -> str:
        """
        Make outbound call via SignalWire.
        """
        if not from_number:
            from_number = self.phone_number
            
        if not callback_url:
            callback_url = f"{self.base_url}/webhooks/signalwire/outbound"
        
        endpoint = f"/Calls.json"
        data = {
            'To': to_number,
            'From': from_number,
            'Url': callback_url,
            'StatusCallback': f"{self.base_url}/webhooks/signalwire/status",
            'StatusCallbackEvent': ['initiated', 'ringing', 'answered', 'completed'],
            'MachineDetection': 'Enable',
            'AsyncAmd': 'true'
        }
        
        # Add custom data if provided
        if custom_data:
            data.update(custom_data)
        
        try:
            result = await self._make_request('POST', endpoint, data=data)
            call_sid = result.get('sid')
            
            self.active_calls[call_sid] = {
                'sid': call_sid,
                'to': to_number,
                'from': from_number,
                'direction': 'outbound',
                'started_at': datetime.now(),
                'status': 'initiated',
                'custom_data': custom_data
            }
            
            logger.info(f"SignalWire outbound call initiated: {call_sid}")
            return call_sid
            
        except Exception as e:
            logger.error(f"Failed to make SignalWire call: {e}")
            raise
    
    async def get_call_status(self, call_sid: str) -> CallInfo:
        """Get call status from SignalWire"""
        if call_sid in self.active_calls:
            cached = self.active_calls[call_sid]
            return CallInfo(
                call_sid=call_sid,
                from_number=cached.get('from', ''),
                to_number=cached.get('to', ''),
                status=cached.get('status', 'unknown'),
                direction=cached.get('direction', 'unknown'),
                start_time=cached.get('started_at')
            )
        
        # Fetch from API
        try:
            result = await self._make_request('GET', f"/Calls/{call_sid}.json")
            return CallInfo(
                call_sid=call_sid,
                from_number=result.get('from', ''),
                to_number=result.get('to', ''),
                status=result.get('status', 'unknown'),
                direction='inbound' if result.get('direction') == 'inbound' else 'outbound',
                start_time=datetime.fromisoformat(result.get('date_created', '').replace('Z', '+00:00'))
            )
        except Exception as e:
            logger.error(f"Failed to get call status: {e}")
            return CallInfo(
                call_sid=call_sid,
                from_number='',
                to_number='',
                status='error',
                direction='unknown'
            )
    
    async def end_call(self, call_sid: str) -> bool:
        """Hang up active call"""
        try:
            await self._make_request(
                'POST', 
                f"/Calls/{call_sid}.json",
                data={'Status': 'completed'}
            )
            
            # Cleanup
            if call_sid in self.active_calls:
                self.active_calls[call_sid]['status'] = 'completed'
                
            # Close WebSocket if open
            if call_sid in self.websocket_connections:
                ws = self.websocket_connections[call_sid]
                await ws.close()
                del self.websocket_connections[call_sid]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to end SignalWire call: {e}")
            return False
    
    async def stream_audio_to_call(self, call_sid: str, audio_data: bytes) -> bool:
        """
        Stream audio via WebSocket.
        SignalWire sends audio in mu-law format (8000Hz).
        """
        if call_sid not in self.websocket_connections:
            logger.warning(f"No WebSocket connection for call: {call_sid}")
            return False
        
        try:
            ws = self.websocket_connections[call_sid]
            
            # SignalWire expects base64-encoded mu-law audio
            # Format: {"event": "media", "media": {"payload": "base64audio"}}
            message = {
                "event": "media",
                "stream_sid": call_sid,
                "media": {
                    "payload": base64.b64encode(audio_data).decode('utf-8')
                }
            }
            
            await ws.send_str(json.dumps(message))
            return True
            
        except Exception as e:
            logger.error(f"Failed to stream audio: {e}")
            return False
    
    def get_websocket_config(self, call_sid: str) -> AudioStreamConfig:
        """Get WebSocket config for streaming"""
        return AudioStreamConfig(
            websocket_url=f"{self.base_url}/voice/stream/signalwire/{call_sid}",
            content_type="audio/x-mulaw;rate=8000",  # SignalWire uses mu-law
            enabled=True
        )
    
    async def transfer_call(self, call_sid: str, to_number: str) -> bool:
        """Transfer call to another number"""
        try:
            # Use LaML Dial verb
            dial_laml = {
                "Response": {
                    "Dial": {
                        "Number": to_number
                    }
                }
            }
            
            # Update the call with new LaML
            await self._make_request(
                'POST',
                f"/Calls/{call_sid}.json",
                data={'Url': f"{self.base_url}/voice/transfer"}  # Endpoint that returns dial_laml
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to transfer call: {e}")
            return False
    
    async def handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """
        Handle WebSocket connection from SignalWire.
        This is the main audio streaming interface.
        """
        call_sid = request.match_info.get('call_sid', 'unknown')
        
        ws = web.WebSocketResponse(
            autoping=True,
            heartbeat=30.0
        )
        await ws.prepare(request)
        
        self.websocket_connections[call_sid] = ws
        logger.info(f"SignalWire WebSocket connected: {call_sid}")
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    event_type = data.get('event')
                    
                    if event_type == 'start':
                        # Stream started
                        stream_sid = data.get('start', {}).get('stream_sid')
                        call_sid = data.get('start', {}).get('call_sid')
                        logger.info(f"Stream started: {stream_sid} for call {call_sid}")
                        
                        # Send welcome message
                        await self._send_ai_greeting(ws, call_sid)
                        
                    elif event_type == 'media':
                        # Received audio from caller
                        payload = data.get('media', {}).get('payload')
                        if payload:
                            audio_data = base64.b64decode(payload)
                            # TODO: Send to AI for processing
                            # This is where you'd integrate with your AI backend
                            await self._process_incoming_audio(call_sid, audio_data)
                            
                    elif event_type == 'stop':
                        # Stream ended
                        logger.info(f"Stream stopped: {call_sid}")
                        break
                        
                    elif event_type == 'mark':
                        # Media playback mark
                        pass
                        
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
                    break
                    
                elif msg.type == WSMsgType.CLOSE:
                    logger.info(f"WebSocket closed: {call_sid}")
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
            
        finally:
            # Cleanup
            if call_sid in self.websocket_connections:
                del self.websocket_connections[call_sid]
            if call_sid in self.active_calls:
                self.active_calls[call_sid]['status'] = 'completed'
                
        return ws
    
    async def _send_ai_greeting(self, ws: web.WebSocketResponse, call_sid: str):
        """Send AI greeting message via TTS"""
        # This would integrate with your TTS service
        # For now, placeholder
        greeting = "Hello! I'm your AI assistant. How can I help you today?"
        logger.info(f"AI greeting for {call_sid}: {greeting}")
    
    async def _process_incoming_audio(self, call_sid: str, audio_data: bytes):
        """Process audio from caller - integrate with AI"""
        # TODO: Integrate with your AI backend
        # 1. Speech-to-text
        # 2. AI processing
        # 3. Text-to-speech with cloned voice
        # 4. Stream back audio
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Check SignalWire API connectivity"""
        try:
            # Try to fetch account info
            result = await self._make_request('GET', ".json")
            return {
                "provider": "signalwire",
                "enabled": self.enabled,
                "status": "healthy",
                "account_type": result.get('type', 'unknown'),
                "space": self.space_url
            }
        except Exception as e:
            return {
                "provider": "signalwire",
                "enabled": self.enabled,
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_pricing_info(self) -> Dict[str, Any]:
        """Return pricing comparison"""
        return {
            "provider": "signalwire",
            "inbound_per_minute": 0.004,
            "outbound_per_minute": 0.004,
            "phone_number_monthly": 1.00,
            "savings_vs_twilio": "70%",
            "currency": "USD"
        }


# Legacy compatibility - keep old import working
class SignalWireIntegration(SignalWireProvider):
    """Alias for backward compatibility"""
    pass
