# backend/engine/personas.py

import logging
import os
import yaml
from enum import Enum
from pydantic import BaseModel
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURATION LOADING
# ==========================================

CONFIG_PATH = os.getenv("PERSONA_CONFIG_PATH", "config/personas.yaml")

class PersonaConfig(BaseModel):
    id: str
    name: str
    title: str
    description: str
    color: str
    shadow: str
    avatar: str
    voice_speaker: str
    system_prompt: str
    welcome_message: str

class AppConfig(BaseModel):
    vertical: str
    personas: List[PersonaConfig]
    settings: Dict

# Global config cache
_config_cache: Optional[AppConfig] = None

def load_config() -> AppConfig:
    """Load persona configuration from YAML file."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    
    config_file = CONFIG_PATH
    if not os.path.isabs(config_file):
        config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), config_file)
    
    try:
        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)
        
        # Process environment variables in strings
        def process_env_vars(obj):
            if isinstance(obj, dict):
                return {k: process_env_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [process_env_vars(item) for item in obj]
            elif isinstance(obj, str):
                import re
                # Replace ${VAR} with environment variable values
                pattern = r'\$\{([^}]+)\}'
                def replace_var(match):
                    var_name = match.group(1)
                    return os.getenv(var_name, match.group(0))
                return re.sub(pattern, replace_var, obj)
            return obj
        
        data = process_env_vars(data)
        _config_cache = AppConfig(**data)
        return _config_cache
    except Exception as e:
        logger.error("Error loading config from %s: %s", config_file, e)
        return AppConfig(
            vertical="generic",
            personas=[],
            settings={"app_name": "AI Assistant"},
        )

def reload_config() -> AppConfig:
    """Force reload configuration from file."""
    global _config_cache
    _config_cache = None
    return load_config()

# ==========================================
# LEGACY ROLE SUPPORT (for backward compatibility)
# ==========================================

class UserRole(str, Enum):
    """Legacy role enum - maps to persona IDs."""
    LAWYER = "lawyer"
    CLIENT = "client"
    EXPERT = "expert"
    CUSTOMER = "customer"
    USER = "user"
    DOCTOR = "doctor"
    PATIENT = "patient"
    ADVISOR = "advisor"
    ANALYST = "analyst"

class SessionContext(BaseModel):
    user_id: str
    role: UserRole
    persona_id: Optional[str] = None
    # Other potential context fields: case_id, jurisdiction, etc.

# ==========================================
# PERSONA MANAGEMENT
# ==========================================

def get_all_personas() -> List[PersonaConfig]:
    """Get all configured personas."""
    config = load_config()
    return config.personas

def get_persona(persona_id: str) -> Optional[PersonaConfig]:
    """Get a specific persona by ID."""
    config = load_config()
    for persona in config.personas:
        if persona.id == persona_id:
            return persona
    return None

def get_system_prompt_for_role(role: UserRole, persona_id: Optional[str] = None) -> str:
    """Get system prompt for a role or persona ID."""
    # First try to find by persona_id
    if persona_id:
        persona = get_persona(persona_id)
        if persona:
            return persona.system_prompt
    
    # Fall back to legacy role mapping
    config = load_config()
    for persona in config.personas:
        if persona.id == role.value:
            return persona.system_prompt
    
    # Default prompt if no match
    return """You are an AI assistant. Be helpful, clear, and concise.
Always respond in the same language as the user.
"""

def get_welcome_message(persona_id: str) -> str:
    """Get welcome message for a persona."""
    persona = get_persona(persona_id)
    if persona:
        return persona.welcome_message
    return "Hello! How can I assist you today?"

def get_voice_speaker(persona_id: str) -> str:
    """Get voice speaker for a persona."""
    persona = get_persona(persona_id)
    if persona:
        return persona.voice_speaker
    return "priya"  # Default

def get_vertical() -> str:
    """Get the current vertical/industry."""
    config = load_config()
    return config.vertical

def get_app_name() -> str:
    """Get the application name."""
    config = load_config()
    return config.settings.get("app_name", "AI Assistant")

def get_setting(key: str, default=None):
    """Get a setting from the configuration."""
    config = load_config()
    return config.settings.get(key, default)

# ==========================================
# BACKWARD COMPATIBILITY
# ==========================================

# Legacy prompts (for systems that need them)
# These are now loaded from config

def get_legacy_prompts():
    """Get legacy prompts for backward compatibility."""
    config = load_config()
    
    base_prompt = """Always respond in the SAME LANGUAGE as the user. 
If the user speaks Hindi, respond in Hindi.
If the user speaks Tamil, respond in Tamil.
If they speak Hinglish, respond in Hinglish.
"""
    
    prompts = {}
    for persona in config.personas:
        prompts[persona.id] = persona.system_prompt
    
    return prompts

# For backward compatibility with existing code
BASE_ANYA_PROMPT = """You are an AI assistant. Be helpful, clear, and concise."""
CLIENT_PERSONA_PROMPT = BASE_ANYA_PROMPT
LAWYER_PERSONA_PROMPT = BASE_ANYA_PROMPT

def _init_legacy_prompts():
    """Initialize legacy prompt variables from config."""
    global BASE_ANYA_PROMPT, CLIENT_PERSONA_PROMPT, LAWYER_PERSONA_PROMPT
    
    client_persona = get_persona("client")
    if client_persona:
        CLIENT_PERSONA_PROMPT = client_persona.system_prompt
        BASE_ANYA_PROMPT = client_persona.system_prompt
    
    lawyer_persona = get_persona("lawyer")
    if lawyer_persona:
        LAWYER_PERSONA_PROMPT = lawyer_persona.system_prompt

# Initialize on module load
_init_legacy_prompts()
