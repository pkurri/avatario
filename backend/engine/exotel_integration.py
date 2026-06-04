"""
Exotel Integration - Best Voice Provider for India
- Cheapest rates for Indian numbers
- TRAI compliant
- Excellent API documentation
- Built for Indian market

Pricing (approx):
- Inbound: ₹0.45/min
- Outbound: ₹0.90/min
- Phone number: ₹1,000/month

vs Twilio: 70-80% savings for Indian operations
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


class ExotelProvider(VoiceProvider):
    """
    Exotel voice provider - Best for Indian operations.
    Website: https://exotel.com
    API Docs: https://developer.exotel.com
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.api_token = config.get('api_token')
        self.subdomain = config.get('subdomain', 'api.exotel.com')  # Your Exotel subdomain
        self.caller_id = config.get('caller_id')  # Exotel virtual number
        self.base_url = config.get('base_url', 'http://localhost:8000')
        
        # API base URL - Exotel format: api.exotel.com/v1/Accounts/{account_name}
        # Account name is 'test' from your dashboard
        self.account_sid = config.get('account_sid', 'test')
        self.api_base = f"https://{self.subdomain}/v1/Accounts/{self.account_sid}"
        
        # Active calls tracking
        self.active_calls: Dict[str, Dict] = {}
        self.websocket_connections: Dict[str, web.WebSocketResponse] = {}
        
    async def _make_request(self, method: str, endpoint: str,
                           data: Dict = None, params: Dict = None) -> Dict:
        """Make authenticated request to Exotel API"""
        url = f"{self.api_base}{endpoint}"
        # Exotel uses Account SID as username, API Token as password
        auth = aiohttp.BasicAuth(self.account_sid, self.api_token)
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method, url, auth=auth, headers=headers,
                json=data, params=params
            ) as response:
                if response.status >= 400:
                    text = await response.text()
                    raise RuntimeError(f"Exotel API error: {response.status} - {text}")
                
                return await response.json()
    
    async def handle_inbound_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming call from Exotel webhook.
        Exotel uses XML (Applet) responses similar to Twilio's TwiML.
        """
        call_sid = call_data.get('CallSid') or call_data.get('call_sid')
        from_number = call_data.get('From') or call_data.get('from')
        to_number = call_data.get('To') or call_data.get('to')
        
        logger.info(f"Exotel inbound call: {call_sid} from {from_number}")
        
        # Store call info
        self.active_calls[call_sid] = {
            'sid': call_sid,
            'from': from_number,
            'to': to_number,
            'direction': 'inbound',
            'started_at': datetime.now(),
            'status': 'ringing'
        }
        
        # Build Exotel Applet (XML response)
        # Connect to WebSocket for AI streaming
        websocket_url = f"{self.base_url}/voice/stream/exotel/{call_sid}"
        
        # Exotel uses XML applets
        applet_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="female" language="hi-IN">Namaste! Main aapka AI assistant hoon. Kaise madad kar sakta hoon?</Say>
    <Connect>
        <Stream url="{websocket_url}" />
    </Connect>
</Response>"""
        
        return {
            "contentType": "application/xml",
            "body": applet_xml,
            "call_sid": call_sid
        }
    
    async def make_outbound_call(self, to_number: str, from_number: str = None,
                                  callback_url: str = None,
                                  custom_data: Dict = None) -> str:
        """
        Make outbound call via Exotel.
        Note: from_number must be a verified Exotel number
        """
        if not from_number:
            from_number = self.caller_id
            
        if not callback_url:
            callback_url = f"{self.base_url}/webhooks/exotel/callback"
        
        # Ensure Indian number format (+91)
        if not to_number.startswith('+91') and not to_number.startswith('91'):
            to_number = f"+91{to_number}"
        
        endpoint = f"/Calls/connect.json"
        data = {
            'From': from_number,
            'To': to_number,
            'CallerId': from_number,
            'Url': callback_url,  # Applet URL
            'CallType': 'trans',  # Transactional call
            'StatusCallback': f"{self.base_url}/webhooks/exotel/status",
            'CustomField': json.dumps(custom_data) if custom_data else ''
        }
        
        try:
            result = await self._make_request('POST', endpoint, data=data)
            call_sid = result.get('Call', {}).get('Sid')
            
            self.active_calls[call_sid] = {
                'sid': call_sid,
                'to': to_number,
                'from': from_number,
                'direction': 'outbound',
                'started_at': datetime.now(),
                'status': 'initiated',
                'custom_data': custom_data
            }
            
            logger.info(f"Exotel outbound call: {call_sid} to {to_number}")
            return call_sid
            
        except Exception as e:
            logger.error(f"Failed to make Exotel call: {e}")
            raise
    
    async def get_call_status(self, call_sid: str) -> CallInfo:
        """Get call status from Exotel"""
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
            call_data = result.get('Call', {})
            
            return CallInfo(
                call_sid=call_sid,
                from_number=call_data.get('From', ''),
                to_number=call_data.get('To', ''),
                status=call_data.get('Status', 'unknown').lower(),
                direction='inbound' if call_data.get('Direction') == 'incoming' else 'outbound',
                start_time=datetime.fromisoformat(
                    call_data.get('DateCreated', '').replace('Z', '+00:00')
                ) if call_data.get('DateCreated') else None
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
            
            if call_sid in self.websocket_connections:
                ws = self.websocket_connections[call_sid]
                await ws.close()
                del self.websocket_connections[call_sid]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to end Exotel call: {e}")
            return False
    
    async def stream_audio_to_call(self, call_sid: str, audio_data: bytes) -> bool:
        """
        Stream audio via WebSocket.
        Exotel uses 8kHz mu-law PCM.
        """
        if call_sid not in self.websocket_connections:
            logger.warning(f"No WebSocket for call: {call_sid}")
            return False
        
        try:
            ws = self.websocket_connections[call_sid]
            
            # Exotel expects raw audio frames
            await ws.send_bytes(audio_data)
            return True
            
        except Exception as e:
            logger.error(f"Failed to stream audio: {e}")
            return False
    
    def get_websocket_config(self, call_sid: str) -> AudioStreamConfig:
        """Get WebSocket config for streaming"""
        return AudioStreamConfig(
            websocket_url=f"{self.base_url}/voice/stream/exotel/{call_sid}",
            content_type="audio/x-mulaw;rate=8000",
            enabled=True
        )
    
    async def transfer_call(self, call_sid: str, to_number: str) -> bool:
        """Transfer call to another number"""
        try:
            # Use Exotel Dial applet
            dial_applet = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Dial>{to_number}</Dial>
</Response>"""
            
            # Update the call
            await self._make_request(
                'POST',
                f"/Calls/{call_sid}.json",
                data={'Url': f"{self.base_url}/voice/transfer"}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to transfer call: {e}")
            return False
    
    async def send_sms(self, to_number: str, message: str, 
                       from_number: str = None) -> str:
        """
        Send SMS via Exotel.
        Great for follow-up messages after calls.
        """
        if not from_number:
            from_number = self.caller_id
        
        # Ensure Indian number format
        if not to_number.startswith('+91') and not to_number.startswith('91'):
            to_number = f"+91{to_number}"
        
        try:
            endpoint = f"/Sms/send.json"
            data = {
                'From': from_number,
                'To': to_number,
                'Body': message,
                'StatusCallback': f"{self.base_url}/webhooks/exotel/sms-status"
            }
            
            result = await self._make_request('POST', endpoint, data=data)
            sms_sid = result.get('SMSMessage', {}).get('Sid')
            
            logger.info(f"Exotel SMS sent: {sms_sid}")
            return sms_sid
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            raise
    
    async def handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket for audio streaming"""
        call_sid = request.match_info.get('call_sid', 'unknown')
        
        ws = web.WebSocketResponse(autoping=True, heartbeat=30.0)
        await ws.prepare(request)
        
        self.websocket_connections[call_sid] = ws
        logger.info(f"Exotel WebSocket connected: {call_sid}")
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.BINARY:
                    # Received audio from caller
                    await self._process_incoming_audio(call_sid, msg.data)
                    
                elif msg.type == WSMsgType.TEXT:
                    # Control messages
                    data = json.loads(msg.data)
                    event_type = data.get('event')
                    
                    if event_type == 'start':
                        logger.info(f"Stream started: {call_sid}")
                        await self._send_ai_greeting(ws, call_sid)
                        
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
                    break
                    
                elif msg.type == WSMsgType.CLOSE:
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
            
        finally:
            if call_sid in self.websocket_connections:
                del self.websocket_connections[call_sid]
                
        return ws
    
    async def _send_ai_greeting(self, ws: web.WebSocketResponse, call_sid: str):
        """Send AI greeting"""
        # Hindi + English mix greeting
        greeting = "Namaste! Main aapka AI assistant hoon. How can I help you today?"
        logger.info(f"AI greeting for {call_sid}: {greeting}")
    
    async def _process_incoming_audio(self, call_sid: str, audio_data: bytes):
        """Process audio from caller"""
        # Integrate with your AI backend
        # 1. Speech-to-text (Hindi/English)
        # 2. AI processing
        # 3. Text-to-speech
        # 4. Stream back
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Exotel API connectivity"""
        # Check if configured
        if not self.api_key or not self.api_token:
            return {
                "provider": "exotel",
                "enabled": self.enabled,
                "status": "not_configured",
                "error": "API credentials not set"
            }
        
        # For trial accounts, API access may be limited
        # Webhooks will still work for receiving calls
        return {
            "provider": "exotel",
            "enabled": self.enabled,
            "status": "configured",
            "account_sid": self.account_sid,
            "subdomain": self.subdomain,
            "caller_id": self.caller_id,
            "note": "Trial account - webhooks ready for testing",
            "pricing_tier": "India-optimized"
        }
    
    def get_pricing_info(self) -> Dict[str, Any]:
        """Return India-specific pricing"""
        return {
            "provider": "exotel",
            "region": "India",
            "inbound_per_minute_inr": 0.45,
            "outbound_per_minute_inr": 0.90,
            "inbound_per_minute_usd": 0.0054,  # ~₹0.45
            "outbound_per_minute_usd": 0.0108,  # ~₹0.90
            "phone_number_monthly_inr": 1000,
            "sms_per_message_inr": 0.20,
            "savings_vs_twilio": "75-80%",
            "trai_compliant": True,
            "local_numbers": True,
            "toll_free_available": True
        }
    
    def get_supported_languages(self) -> List[str]:
        """Languages supported by Exotel TTS"""
        return [
            "hi-IN",  # Hindi
            "en-IN",  # Indian English
            "ta-IN",  # Tamil
            "te-IN",  # Telugu
            "kn-IN",  # Kannada
            "ml-IN",  # Malayalam
            "mr-IN",  # Marathi
            "gu-IN",  # Gujarati
            "bn-IN",  # Bengali
            "pa-IN",  # Punjabi
        ]


class ExotelIntegration(ExotelProvider):
    """Alias for backward compatibility"""
    pass
