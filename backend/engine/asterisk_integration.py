"""
Asterisk Integration - Self-Hosted VoIP Gateway
Zero per-minute costs, unlimited scale
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import aiohttp
from aiohttp import web, WSMsgType
import aiofiles

from engine.voice_provider import VoiceProvider, CallInfo, AudioStreamConfig

logger = logging.getLogger(__name__)


class AsteriskProvider(VoiceProvider):
    """
    Asterisk ARI (Asterisk REST Interface) integration.
    Self-hosted = Zero per-minute costs
    Requires: Asterisk 16+ with ARI enabled
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 8088)
        self.username = config.get('username', 'ai_user')
        self.password = config.get('password', '')
        self.app_name = config.get('app_name', 'ai_receptionist')
        self.base_url = config.get('base_url', 'http://localhost:8000')
        
        # ARI base URL
        self.ari_base = f"http://{self.host}:{self.port}/ari"
        
        # Active channel tracking
        self.active_channels: Dict[str, Dict] = {}
        self.websocket_connections: Dict[str, web.WebSocketResponse] = {}
        self.event_session: Optional[aiohttp.ClientSession] = None
        self._event_listener_started = False
        
    def _start_event_listener_if_needed(self):
        """Start event listener only if event loop is running"""
        if not self._event_listener_started:
            try:
                asyncio.get_running_loop()
                asyncio.create_task(self._start_event_listener())
                self._event_listener_started = True
            except RuntimeError:
                # No event loop running, will start later
                pass
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create authenticated session"""
        if not self.event_session:
            self.event_session = aiohttp.ClientSession(
                auth=aiohttp.BasicAuth(self.username, self.password)
            )
        return self.event_session
    
    async def _make_ari_request(self, method: str, endpoint: str,
                                 data: Dict = None, params: Dict = None) -> Dict:
        """Make ARI request to Asterisk"""
        url = f"{self.ari_base}{endpoint}"
        session = await self._get_session()
        
        async with session.request(
            method, url, json=data, params=params
        ) as response:
            if response.status >= 400:
                text = await response.text()
                raise RuntimeError(f"Asterisk ARI error: {response.status} - {text}")
            
            if response.status == 204:
                return {}
                
            return await response.json()
    
    async def _start_event_listener(self):
        """Listen for Asterisk events via WebSocket"""
        ws_url = f"ws://{self.host}:{self.port}/ari/events?api_key={self.username}:{self.password}&app={self.app_name}"
        
        while True:
            try:
                session = await self._get_session()
                async with session.ws_connect(ws_url) as ws:
                    logger.info(f"Connected to Asterisk ARI events: {self.host}")
                    
                    async for msg in ws:
                        if msg.type == WSMsgType.TEXT:
                            event = json.loads(msg.data)
                            await self._handle_ari_event(event)
                            
                        elif msg.type == WSMsgType.ERROR:
                            logger.error(f"ARI WebSocket error: {ws.exception()}")
                            break
                            
            except Exception as e:
                logger.error(f"ARI event listener error: {e}")
                await asyncio.sleep(5)  # Retry delay
    
    async def _handle_ari_event(self, event: Dict):
        """Handle Asterisk ARI events"""
        event_type = event.get('type')
        
        if event_type == 'StasisStart':
            # New call entered Stasis (our app)
            channel_id = event.get('channel', {}).get('id')
            caller_number = event.get('channel', {}).get('caller', {}).get('number')
            caller_name = event.get('channel', {}).get('caller', {}).get('name')
            
            logger.info(f"Asterisk call started: {channel_id} from {caller_number}")
            
            self.active_channels[channel_id] = {
                'channel_id': channel_id,
                'caller': caller_number,
                'caller_name': caller_name,
                'started_at': datetime.now(),
                'status': 'in_stasis'
            }
            
            # Auto-answer with AI
            await self._answer_with_ai(channel_id)
            
        elif event_type == 'ChannelDestroyed':
            # Call ended
            channel_id = event.get('channel', {}).get('id')
            if channel_id in self.active_channels:
                self.active_channels[channel_id]['status'] = 'completed'
                logger.info(f"Asterisk call ended: {channel_id}")
                
        elif event_type == 'ChannelStateChange':
            channel_id = event.get('channel', {}).get('id')
            state = event.get('channel', {}).get('state')
            
            if channel_id in self.active_channels:
                self.active_channels[channel_id]['status'] = state
    
    async def _answer_with_ai(self, channel_id: str):
        """Answer call and connect to AI streaming"""
        try:
            # Answer the channel
            await self._make_ari_request(
                'POST',
                f"/channels/{channel_id}/answer"
            )
            
            # Create external media for WebSocket streaming
            external_id = f"external_{channel_id}"
            
            # Create bridge to mix audio
            bridge_id = f"ai_bridge_{channel_id}"
            await self._make_ari_request(
                'POST',
                f"/bridges",
                data={
                    'bridgeId': bridge_id,
                    'type': 'mixing',
                    'name': f'AI Call {channel_id}'
                }
            )
            
            # Add channel to bridge
            await self._make_ari_request(
                'POST',
                f"/bridges/{bridge_id}/addChannel",
                data={'channel': channel_id}
            )
            
            # Create external media channel (WebSocket)
            # This connects to our AI WebSocket endpoint
            ws_url = f"{self.base_url}/voice/stream/asterisk/{channel_id}"
            
            await self._make_ari_request(
                'POST',
                f"/channels/externalMedia",
                data={
                    'app': self.app_name,
                    'external_host': ws_url.replace('ws://', '').replace('wss://', ''),
                    'format': 'slin16',  # Signed linear 16-bit
                    'encapsulation': 'rtp',
                    'transport': 'tcp',
                    'connection_type': 'client'
                }
            )
            
            self.active_channels[channel_id]['status'] = 'answered'
            self.active_channels[channel_id]['bridge_id'] = bridge_id
            
            logger.info(f"AI streaming setup for call: {channel_id}")
            
        except Exception as e:
            logger.error(f"Failed to setup AI streaming: {e}")
    
    async def handle_inbound_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle inbound call notification.
        For Asterisk, this is triggered via ARI events, not webhooks.
        """
        # Asterisk handles this via StasisStart event
        # This method is for compatibility with other providers
        channel_id = call_data.get('channel_id')
        
        return {
            "provider": "asterisk",
            "channel_id": channel_id,
            "status": "handled_via_ari",
            "message": "Asterisk uses ARI events, not webhooks"
        }
    
    async def make_outbound_call(self, to_number: str, from_number: str = None,
                                  callback_url: str = None,
                                  custom_data: Dict = None) -> str:
        """Make outbound call via Asterisk"""
        try:
            # Originate call via ARI
            originate_data = {
                'endpoint': f"PJSIP/{to_number}@trunk",  # Adjust endpoint format
                'app': self.app_name,
                'callerId': from_number or 'AI Assistant',
                'timeout': 30,
                'variables': {
                    'CUSTOM_DATA': json.dumps(custom_data or {})
                }
            }
            
            result = await self._make_ari_request(
                'POST',
                "/channels",
                data=originate_data
            )
            
            channel_id = result.get('id')
            
            self.active_channels[channel_id] = {
                'channel_id': channel_id,
                'to': to_number,
                'from': from_number,
                'direction': 'outbound',
                'started_at': datetime.now(),
                'status': 'originating',
                'custom_data': custom_data
            }
            
            logger.info(f"Asterisk outbound call: {channel_id} to {to_number}")
            return channel_id
            
        except Exception as e:
            logger.error(f"Failed to make Asterisk call: {e}")
            raise
    
    async def get_call_status(self, channel_id: str) -> CallInfo:
        """Get channel/call status"""
        if channel_id in self.active_channels:
            cached = self.active_channels[channel_id]
            return CallInfo(
                call_sid=channel_id,
                from_number=cached.get('caller', ''),
                to_number=cached.get('to', ''),
                status=cached.get('status', 'unknown'),
                direction=cached.get('direction', 'unknown'),
                start_time=cached.get('started_at')
            )
        
        # Fetch from ARI
        try:
            result = await self._make_ari_request('GET', f"/channels/{channel_id}")
            return CallInfo(
                call_sid=channel_id,
                from_number=result.get('caller', {}).get('number', ''),
                to_number=result.get('dialplan', {}).get('exten', ''),
                status=result.get('state', 'unknown'),
                direction='outbound' if result.get('dialplan') else 'inbound'
            )
        except Exception as e:
            logger.error(f"Failed to get channel status: {e}")
            return CallInfo(
                call_sid=channel_id,
                from_number='',
                to_number='',
                status='error',
                direction='unknown'
            )
    
    async def end_call(self, channel_id: str) -> bool:
        """Hang up channel"""
        try:
            await self._make_ari_request(
                'DELETE',
                f"/channels/{channel_id}"
            )
            
            # Cleanup
            if channel_id in self.active_channels:
                self.active_channels[channel_id]['status'] = 'completed'
            
            if channel_id in self.websocket_connections:
                ws = self.websocket_connections[channel_id]
                await ws.close()
                del self.websocket_connections[channel_id]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to end Asterisk call: {e}")
            return False
    
    async def stream_audio_to_call(self, channel_id: str, audio_data: bytes) -> bool:
        """
        Stream audio via WebSocket to externalMedia.
        Asterisk expects 16-bit signed linear PCM (slin16) at 16kHz.
        """
        if channel_id not in self.websocket_connections:
            logger.warning(f"No WebSocket for channel: {channel_id}")
            return False
        
        try:
            ws = self.websocket_connections[channel_id]
            
            # Asterisk externalMedia receives raw RTP/PCM audio
            # Just send raw bytes
            await ws.send_bytes(audio_data)
            return True
            
        except Exception as e:
            logger.error(f"Failed to stream audio: {e}")
            return False
    
    def get_websocket_config(self, channel_id: str) -> AudioStreamConfig:
        """Get WebSocket config"""
        return AudioStreamConfig(
            websocket_url=f"{self.base_url}/voice/stream/asterisk/{channel_id}",
            content_type="audio/L16;rate=16000",  # 16-bit signed linear, 16kHz
            enabled=True
        )
    
    async def transfer_call(self, channel_id: str, to_number: str) -> bool:
        """Transfer call via dialplan or redirect"""
        try:
            # Continue to dialplan context that handles transfer
            await self._make_ari_request(
                'POST',
                f"/channels/{channel_id}/continue",
                data={
                    'context': 'transfer',
                    'extension': to_number,
                    'priority': 1
                }
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to transfer call: {e}")
            return False
    
    async def handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """
        Handle WebSocket for audio streaming.
        This connects to Asterisk's externalMedia.
        """
        channel_id = request.match_info.get('channel_id', 'unknown')
        
        ws = web.WebSocketResponse(
            autoping=True,
            heartbeat=30.0
        )
        await ws.prepare(request)
        
        self.websocket_connections[channel_id] = ws
        logger.info(f"Asterisk audio WebSocket connected: {channel_id}")
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.BINARY:
                    # Received audio from Asterisk (caller)
                    # Send to AI for processing
                    await self._process_incoming_audio(channel_id, msg.data)
                    
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"Asterisk WS error: {ws.exception()}")
                    break
                    
                elif msg.type == WSMsgType.CLOSE:
                    logger.info(f"Asterisk WS closed: {channel_id}")
                    break
                    
        except Exception as e:
            logger.error(f"Asterisk WS handler error: {e}")
            
        finally:
            if channel_id in self.websocket_connections:
                del self.websocket_connections[channel_id]
                
        return ws
    
    async def _process_incoming_audio(self, channel_id: str, audio_data: bytes):
        """Process audio from caller - integrate with AI"""
        # TODO: Integrate with your AI backend
        # 1. Speech-to-text
        # 2. AI processing
        # 3. Text-to-speech
        # 4. Stream back via stream_audio_to_call()
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Asterisk ARI connectivity"""
        try:
            result = await self._make_ari_request('GET', "/asterisk/info")
            return {
                "provider": "asterisk",
                "enabled": self.enabled,
                "status": "healthy",
                "asterisk_version": result.get('version', 'unknown'),
                "system_name": result.get('system', {}).get('name', 'unknown'),
                "host": self.host
            }
        except Exception as e:
            return {
                "provider": "asterisk",
                "enabled": self.enabled,
                "status": "unhealthy",
                "error": str(e),
                "host": self.host
            }
    
    def get_pricing_info(self) -> Dict[str, Any]:
        """Return pricing info"""
        return {
            "provider": "asterisk",
            "inbound_per_minute": 0.0,  # Self-hosted = free
            "outbound_per_minute": 0.0,  # Just carrier costs (~$0.005/min)
            "infrastructure_monthly": "~$20-50 (VPS)",
            "requires_setup": True,
            "best_for": "High volume, unlimited scale"
        }


class AsteriskIntegration(AsteriskProvider):
    """Alias for backward compatibility"""
    pass
