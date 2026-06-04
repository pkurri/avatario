"""
Voice Provider Abstraction Layer
Switch between Twilio, SignalWire, Asterisk, Vonage seamlessly
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import os
import logging
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class CallInfo:
    """Standardized call information across all providers"""
    call_sid: str
    from_number: str
    to_number: str
    status: str
    direction: str  # 'inbound' or 'outbound'
    start_time: Optional[datetime] = None
    custom_data: Dict[str, Any] = None


@dataclass
class AudioStreamConfig:
    """WebSocket audio streaming configuration"""
    websocket_url: str
    content_type: str = "audio/l16;rate=16000"
    enabled: bool = True


class VoiceProvider(ABC):
    """
    Abstract base class for voice providers.
    Implement this for Twilio, SignalWire, Asterisk, Vonage, etc.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.name = config.get('name', 'unknown')
        
    @abstractmethod
    async def handle_inbound_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming call webhook.
        Returns TwiML-like response (provider-specific XML/JSON).
        """
        pass
    
    @abstractmethod
    async def make_outbound_call(self, to_number: str, from_number: str, 
                                  callback_url: str, custom_data: Dict = None) -> str:
        """
        Initiate outbound call.
        Returns call SID/ID.
        """
        pass
    
    @abstractmethod
    async def get_call_status(self, call_sid: str) -> CallInfo:
        """
        Get current call status.
        """
        pass
    
    @abstractmethod
    async def end_call(self, call_sid: str) -> bool:
        """
        Terminate active call.
        Returns success status.
        """
        pass
    
    @abstractmethod
    async def stream_audio_to_call(self, call_sid: str, audio_data: bytes) -> bool:
        """
        Stream audio data to active call via WebSocket.
        """
        pass
    
    @abstractmethod
    def get_websocket_config(self, call_sid: str) -> AudioStreamConfig:
        """
        Get WebSocket configuration for audio streaming.
        """
        pass
    
    @abstractmethod
    async def transfer_call(self, call_sid: str, to_number: str) -> bool:
        """
        Transfer call to another number.
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check provider health/status.
        Override for provider-specific checks.
        """
        return {
            "provider": self.name,
            "enabled": self.enabled,
            "status": "unknown"
        }


class VoiceProviderManager:
    """
    Manages multiple voice providers with automatic failover.
    Primary: SignalWire (cheap)
    Fallback: Asterisk (self-hosted)
    Backup: Twilio (reliable)
    """
    
    def __init__(self):
        self.providers: Dict[str, VoiceProvider] = {}
        self.primary_provider: Optional[str] = None
        self.fallback_chain: List[str] = []
        
    def register_provider(self, name: str, provider: VoiceProvider, 
                          is_primary: bool = False, fallback_order: int = None):
        """Register a voice provider"""
        self.providers[name] = provider
        
        if is_primary:
            self.primary_provider = name
            
        if fallback_order is not None:
            # Insert at specific position in fallback chain
            while len(self.fallback_chain) <= fallback_order:
                self.fallback_chain.append(None)
            self.fallback_chain[fallback_order] = name
            # Remove None entries
            self.fallback_chain = [p for p in self.fallback_chain if p is not None]
            
        logger.info(f"Registered provider: {name} (primary={is_primary})")
        
    def get_provider(self, name: Optional[str] = None) -> VoiceProvider:
        """Get provider by name or primary"""
        if name:
            if name not in self.providers:
                raise ValueError(f"Unknown provider: {name}")
            return self.providers[name]
        
        if not self.primary_provider:
            raise ValueError("No primary provider configured")
            
        return self.providers[self.primary_provider]
    
    async def handle_inbound_with_failover(self, call_data: Dict[str, Any],
                                           provider_hint: str = None) -> Dict[str, Any]:
        """
        Handle inbound call with automatic failover.
        Try primary first, then fallbacks.
        """
        providers_to_try = []
        
        # Specific provider requested
        if provider_hint and provider_hint in self.providers:
            providers_to_try.append(provider_hint)
        
        # Add primary
        if self.primary_provider and self.primary_provider not in providers_to_try:
            providers_to_try.append(self.primary_provider)
        
        # Add fallbacks
        for fallback in self.fallback_chain:
            if fallback not in providers_to_try:
                providers_to_try.append(fallback)
        
        # Try each provider
        last_error = None
        for provider_name in providers_to_try:
            try:
                provider = self.providers[provider_name]
                if not provider.enabled:
                    continue
                    
                logger.info(f"Trying provider: {provider_name}")
                result = await provider.handle_inbound_call(call_data)
                
                # Add provider info to result
                result['_provider'] = provider_name
                return result
                
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed: {e}")
                last_error = e
                continue
        
        # All providers failed
        raise RuntimeError(f"All providers failed. Last error: {last_error}")
    
    async def get_all_health(self) -> Dict[str, Any]:
        """Get health status of all providers"""
        health_checks = {}
        for name, provider in self.providers.items():
            if asyncio.iscoroutinefunction(provider.health_check):
                health_checks[name] = await provider.health_check()
            else:
                health_checks[name] = provider.health_check()
        return health_checks


# Global provider manager instance
_provider_manager: Optional[VoiceProviderManager] = None


def get_provider_manager() -> VoiceProviderManager:
    """Get or create global provider manager"""
    global _provider_manager
    if _provider_manager is None:
        _provider_manager = VoiceProviderManager()
    return _provider_manager


class TwilioProvider(VoiceProvider):
    """Wrapper for existing TwilioIntegration to make it compatible with VoiceProvider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        from engine.twilio_integration import TwilioIntegration
        self.twilio = TwilioIntegration()
        # Update with config if provided
        if config.get('account_sid'):
            self.twilio.account_sid = config['account_sid']
        if config.get('auth_token'):
            self.twilio.auth_token = config['auth_token']
        if config.get('phone_number'):
            self.twilio.phone_number = config['phone_number']
        if config.get('base_url'):
            self.twilio.base_url = config['base_url']
    
    async def handle_inbound_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle inbound call - returns TwiML"""
        return {
            "contentType": "application/xml",
            "body": "<?xml version='1.0'?><Response><Say>Hello from AI</Say></Response>",
            "call_sid": call_data.get('CallSid', 'unknown')
        }
    
    async def make_outbound_call(self, to_number: str, from_number: str = None,
                                  callback_url: str = None, custom_data: Dict = None) -> str:
        """Make outbound call"""
        result = await self.twilio.make_outbound_call(
            to_number=to_number,
            from_number=from_number,
            webhook_url=callback_url
        )
        return result.get('call_sid', 'unknown')
    
    async def get_call_status(self, call_sid: str) -> CallInfo:
        """Get call status"""
        call = self.twilio.active_calls.get(call_sid)
        if call:
            return CallInfo(
                call_sid=call_sid,
                from_number=call.from_number,
                to_number=call.to_number,
                status=call.status.value,
                direction=call.direction.value,
                start_time=datetime.fromisoformat(call.started_at) if call.started_at else None
            )
        return CallInfo(call_sid=call_sid, from_number='', to_number='', status='unknown', direction='unknown')
    
    async def end_call(self, call_sid: str) -> bool:
        """End call"""
        return await self.twilio.end_call(call_sid)
    
    async def stream_audio_to_call(self, call_sid: str, audio_data: bytes) -> bool:
        """Stream audio"""
        # Twilio implementation would go here
        return False
    
    def get_websocket_config(self, call_sid: str) -> AudioStreamConfig:
        """Get WebSocket config"""
        return AudioStreamConfig(
            websocket_url=f"{self.config.get('base_url', '')}/voice/stream/twilio/{call_sid}",
            content_type="audio/x-mulaw;rate=8000",
            enabled=True
        )
    
    async def transfer_call(self, call_sid: str, to_number: str) -> bool:
        """Transfer call"""
        return await self.twilio.transfer_call(call_sid, to_number)
    
    def health_check(self) -> Dict[str, Any]:
        """Check Twilio health"""
        return {
            "provider": "twilio",
            "enabled": self.enabled and self.twilio.is_configured(),
            "status": "healthy" if self.twilio.is_configured() else "not_configured",
            "account_sid": self.twilio.account_sid[:10] + "..." if self.twilio.account_sid else None
        }
    
    def get_pricing_info(self) -> Dict[str, Any]:
        """Twilio pricing"""
        return {
            "provider": "twilio",
            "inbound_per_minute": 0.013,
            "outbound_per_minute": 0.013,
            "phone_number_monthly": 1.15,
            "region": "Global"
        }


def init_providers_from_env():
    """
    Initialize providers from environment variables.
    Call this on startup.
    """
    from engine.signalwire_integration import SignalWireProvider
    from engine.asterisk_integration import AsteriskProvider
    from engine.exotel_integration import ExotelProvider
    
    manager = get_provider_manager()
    
    # Exotel (Primary for India - Best Value + TRAI Compliant)
    if os.getenv('EXOTEL_API_KEY') and os.getenv('EXOTEL_API_TOKEN'):
        exotel_config = {
            'name': 'exotel',
            'enabled': os.getenv('USE_EXOTEL', 'true').lower() == 'true',
            'api_key': os.getenv('EXOTEL_API_KEY'),
            'api_token': os.getenv('EXOTEL_API_TOKEN'),
            'subdomain': os.getenv('EXOTEL_SUBDOMAIN', 'api.exotel.com'),
            'caller_id': os.getenv('EXOTEL_CALLER_ID'),
            'base_url': os.getenv('BASE_URL', 'http://localhost:8000')
        }
        manager.register_provider(
            'exotel',
            ExotelProvider(exotel_config),
            is_primary=os.getenv('PRIMARY_PROVIDER', 'exotel') == 'exotel',
            fallback_order=0
        )
    
    # SignalWire (Primary - Best Value for International)
    if os.getenv('SIGNALWIRE_PROJECT_ID') and os.getenv('SIGNALWIRE_TOKEN'):
        sw_config = {
            'name': 'signalwire',
            'enabled': os.getenv('USE_SIGNALWIRE', 'false').lower() == 'true',
            'project_id': os.getenv('SIGNALWIRE_PROJECT_ID'),
            'token': os.getenv('SIGNALWIRE_TOKEN'),
            'space_url': os.getenv('SIGNALWIRE_SPACE_URL'),
            'phone_number': os.getenv('SIGNALWIRE_PHONE_NUMBER'),
            'base_url': os.getenv('BASE_URL', 'http://localhost:8000')
        }
        manager.register_provider(
            'signalwire',
            SignalWireProvider(sw_config),
            is_primary=os.getenv('PRIMARY_PROVIDER') == 'signalwire',
            fallback_order=1
        )
    
    # Asterisk (Self-hosted Fallback)
    if os.getenv('ASTERISK_HOST'):
        asterisk_config = {
            'name': 'asterisk',
            'enabled': os.getenv('USE_ASTERISK', 'false').lower() == 'true',
            'host': os.getenv('ASTERISK_HOST', 'localhost'),
            'port': int(os.getenv('ASTERISK_PORT', '8088')),
            'username': os.getenv('ASTERISK_USER', 'ai_user'),
            'password': os.getenv('ASTERISK_PASSWORD', ''),
            'app_name': 'ai_receptionist',
            'base_url': os.getenv('BASE_URL', 'http://localhost:8000')
        }
        manager.register_provider(
            'asterisk',
            AsteriskProvider(asterisk_config),
            is_primary=os.getenv('PRIMARY_PROVIDER') == 'asterisk',
            fallback_order=2
        )
    
    # Twilio (Reliable Backup)
    if os.getenv('TWILIO_ACCOUNT_SID'):
        twilio_config = {
            'name': 'twilio',
            'enabled': os.getenv('USE_TWILIO', 'false').lower() == 'true',
            'account_sid': os.getenv('TWILIO_ACCOUNT_SID'),
            'auth_token': os.getenv('TWILIO_AUTH_TOKEN'),
            'phone_number': os.getenv('TWILIO_PHONE_NUMBER'),
            'base_url': os.getenv('BASE_URL', 'http://localhost:8000')
        }
        manager.register_provider(
            'twilio',
            TwilioProvider(twilio_config),
            is_primary=os.getenv('PRIMARY_PROVIDER') == 'twilio',
            fallback_order=3
        )
    
    logger.info(f"Initialized {len(manager.providers)} voice providers")
    return manager
