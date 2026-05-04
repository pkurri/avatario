import logging
import os
import json
import httpx
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, llm
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, sarvam

# Import generic persona system
from engine.personas import get_persona, get_all_personas, get_voice_speaker, PersonaConfig

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)

# ==========================================
# GENERIC RAG CONTEXT FETCHER
# ==========================================

async def fetch_rag_context(query: str) -> str:
    """Fetches RAG context from the knowledge base API."""
    brain_url = os.getenv("BRAIN_API_URL", "http://localhost:8000")
    endpoint = f"{brain_url}/api/v1/ai/enhanced/semantic/search/"
    
    # Skip if no brain API configured
    if not brain_url or brain_url == "http://localhost:8000":
        return ""
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(endpoint, json={
                "query": query,
                "top_k": 3,
                "language": "en"
            })
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if not results:
                    return ""
                
                context_str = "<knowledge_context>\n"
                for i, res in enumerate(results, 1):
                    title = res.get("title") or "Document"
                    content = res.get("content", "").strip()
                    context_str += f"Document {i} ({title}):\n{content}\n\n"
                context_str += "</knowledge_context>\n"
                return context_str
    except Exception as e:
        logger.debug(f"RAG context fetch skipped or failed: {e}")
    return ""

# ==========================================
# GENERIC VOICE AGENT
# ==========================================

class VoiceAgent(Agent):
    def __init__(self, persona_id: str = "client") -> None:
        # Load persona from configuration
        persona = get_persona(persona_id)
        
        if persona:
            instructions = persona.system_prompt
            speaker = persona.voice_speaker
            persona_name = persona.name
        else:
            # Fallback to generic assistant
            instructions = """You are an AI assistant. Be helpful, clear, and concise.
Always respond in the same language as the user.
If asked about a complex issue, ask 2-3 clarifying questions before giving a final answer.
Speak clearly, avoid massive walls of text, and optimize your output for a voice assistant."""
            speaker = "priya"
            persona_name = "AI Assistant"
        
        logger.info(f"Initializing VoiceAgent for persona: {persona_name} (ID: {persona_id}) with speaker: {speaker}")

        super().__init__(
            instructions=instructions,
            # Saaras v3 STT - Converts speech to text with auto-detect
            stt=sarvam.STT(
                language="unknown",
                model="saaras:v3",
                mode="transcribe",
                flush_signal=True
            ),
            # OpenAI LLM directed to custom endpoint
            llm=openai.LLM(
                model=os.getenv("VLLM_MODEL", "default-model"),
                base_url=os.getenv("VLLM_API_BASE", "http://localhost:8000/v1"),
                api_key=os.getenv("VLLM_API_KEY", "EMPTY")
            ),
            # Bulbul v3 TTS - Converts text to speech
            tts=sarvam.TTS(
                target_language_code="en-IN",  # Bulbul v3 handles multi-lang natively
                model="bulbul:v3",
                speaker=speaker
            ),
        )
        self.persona_id = persona_id
        self.persona_name = persona_name

    async def on_user_speech_committed(self, msg: llm.ChatMessage):
        """Intercept the user message to inject dynamic RAG context"""
        logger.info(f"[{self.persona_name}] User speech: {msg.content[:50]}...")
        
        # Fetch matching knowledge base records
        rag_context = await fetch_rag_context(msg.content)
        if rag_context:
            logger.info(f"[{self.persona_name}] Injecting RAG context.")
            msg.content += f"\n\n[Knowledge Context: {rag_context}]"

    async def on_enter(self):
        """Called when user joins - agent starts the conversation"""
        logger.info(f"[{self.persona_name}] Starting conversation")
        self.session.generate_reply()

async def entrypoint(ctx: JobContext):
    """Main entry point - LiveKit calls this when a user connects"""
    logger.info(f"JOB STARTED: {ctx.job.id} room: {ctx.room.name}")
    
    # Extract persona_id from room name
    # Room name format: ai-{persona_id} or any-{persona_id}
    persona_id = "client"  # Default persona
    
    # Try to extract persona from room name
    room_parts = ctx.room.name.lower().split('-')
    if len(room_parts) > 1:
        potential_persona = room_parts[-1]
        # Check if this is a valid persona
        all_personas = get_all_personas()
        valid_ids = [p.id for p in all_personas]
        if potential_persona in valid_ids:
            persona_id = potential_persona
            logger.info(f"Detected persona '{persona_id}' from room name: {ctx.room.name}")
    
    # Also check legacy role names for backward compatibility
    if "lawyer" in ctx.room.name:
        persona_id = "lawyer"
        logger.info(f"Legacy: Detected 'lawyer' persona from room name")
    elif "client" in ctx.room.name or "customer" in ctx.room.name:
        persona_id = "client"
        logger.info(f"Legacy: Detected 'client' persona from room name")
    elif "doctor" in ctx.room.name or "expert" in ctx.room.name:
        # Try to find a doctor/expert persona
        all_personas = get_all_personas()
        for p in all_personas:
            if "doctor" in p.id or "expert" in p.id or p.id == "dr-arjun":
                persona_id = p.id
                break

    # Wait for the participant who triggered the job
    logger.info("Waiting for participant...")
    try:
        participant = await ctx.wait_for_participant()
        logger.info(f"Participant connected: {participant.identity}")
        logger.info(f"Raw Participant Metadata: '{participant.metadata}'")

        if participant.metadata:
            try:
                metadata = json.loads(participant.metadata)
                # Check for persona_id first (new format)
                if "persona_id" in metadata:
                    persona_id = metadata["persona_id"]
                    logger.info(f"SUCCESS: Detected persona_id '{persona_id}' from metadata")
                # Fall back to role (legacy format)
                elif "role" in metadata:
                    role = metadata["role"]
                    # Map legacy role to persona_id
                    all_personas = get_all_personas()
                    for p in all_personas:
                        if p.id == role or (role == "lawyer" and p.id == "lawyer") or (role == "client" and p.id == "client"):
                            persona_id = p.id
                            break
                    logger.info(f"SUCCESS: Mapped role '{role}' to persona '{persona_id}'")
            except Exception as e:
                logger.error(f"Metadata Parse Error: {e}")
    except Exception as e:
        logger.error(f"Error waiting for participant: {e}")

    # Create and start the agent session
    session = AgentSession(
        turn_detection="stt",
        min_endpointing_delay=0.07
    )
    
    # Initialize agent with detected persona
    agent = VoiceAgent(persona_id=persona_id)
    logger.info(f"FINAL AGENT INITIALIZATION - Persona: {persona_id}")

    await session.start(
        agent=agent,
        room=ctx.room
    )
    
    logger.info(f"AgentSession active for persona: {persona_id}")

if __name__ == "__main__":
    # Run the agent
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
