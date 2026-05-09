import json
import logging
from typing import Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage
from engine.personas import UserRole, get_persona, get_welcome_message, get_voice_speaker
from engine.graph import ai_conversation_graph
from engine.audio import sarvam_stt, sarvam_tts

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, role: UserRole) -> None:
        await websocket.accept()
        self.active_connections[websocket] = {"role": role, "messages": []}

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.pop(websocket, None)

    async def process_message(
        self, websocket: WebSocket, message: str, persona_id: Optional[str] = None
    ) -> None:
        state = self.active_connections[websocket]
        role = state["role"]

        state["messages"].append(HumanMessage(content=message))

        input_state = {
            "messages": state["messages"],
            "role": role,
            "persona_id": persona_id,
            "extracted_entities": {},
            "conversation_context": {},
        }

        result = await ai_conversation_graph.ainvoke(input_state)
        ai_response = result["messages"][-1].content
        state["messages"] = result["messages"]

        await websocket.send_text(
            json.dumps({
                "status": "success",
                "type": "text",
                "content": ai_response,
                "persona_id": persona_id,
                "role": role.value,
            })
        )

        voice_speaker = get_voice_speaker(persona_id) if persona_id else role.value
        audio_bytes = await sarvam_tts(ai_response, role=voice_speaker)
        if audio_bytes:
            await websocket.send_bytes(audio_bytes)


manager = ConnectionManager()


@router.websocket("/chat/{persona_id}")
async def websocket_chat(websocket: WebSocket, persona_id: str):
    persona = get_persona(persona_id)
    if not persona:
        await websocket.close(
            code=1008,
            reason=f"Invalid persona_id: {persona_id}. Use /personas to see available options.",
        )
        return

    try:
        user_role = UserRole(persona_id)
    except ValueError:
        user_role = UserRole.CLIENT

    await manager.connect(websocket, user_role)

    try:
        welcome = get_welcome_message(persona_id)
        await websocket.send_text(
            json.dumps({
                "status": "connected",
                "type": "info",
                "content": welcome,
                "persona_id": persona_id,
                "persona_name": persona.name,
            })
        )

        welcome_audio = await sarvam_tts(welcome, role=persona.voice_speaker)
        if welcome_audio:
            await websocket.send_bytes(welcome_audio)

        while True:
            message = await websocket.receive()

            if "bytes" in message:
                audio_chunk = message["bytes"]
                logger.debug("[%s] Received audio payload: %d bytes", persona.name, len(audio_chunk))
                transcribed_text = await sarvam_stt(audio_chunk)
                logger.debug("[%s] STT output: %r", persona.name, transcribed_text)
                if transcribed_text:
                    await manager.process_message(websocket, transcribed_text, persona_id)
                else:
                    logger.warning("[%s] STT failed to transcribe audio", persona.name)

            elif "text" in message:
                await manager.process_message(websocket, message["text"], persona_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from %s", persona.name)
