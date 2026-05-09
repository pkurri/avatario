import json
import os
import logging
from fastapi import APIRouter, HTTPException
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(tags=["livekit"])


@router.get("/get_livekit_token")
async def get_livekit_token(
    participant_name: str = "User",
    room_name: str = "ai-room",
    role: str = "client",
    persona_id: Optional[str] = None,
):
    from livekit.api import AccessToken, VideoGrants

    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    if not api_key or not api_secret:
        raise HTTPException(status_code=500, detail="LiveKit credentials missing")

    grant = VideoGrants(room_join=True, room=room_name)
    token = AccessToken(api_key, api_secret)
    token.with_identity(participant_name)
    token.with_name(participant_name)
    token.with_grants(grant)

    metadata: dict = {"role": role}
    if persona_id:
        metadata["persona_id"] = persona_id
    token.with_metadata(json.dumps(metadata))

    try:
        from livekit.api import LiveKitAPI
        from livekit.protocol.agent_dispatch import CreateAgentDispatchRequest

        lk_api = LiveKitAPI(
            url=os.getenv("LIVEKIT_URL"),
            api_key=api_key,
            api_secret=api_secret,
        )
        dispatch_req = CreateAgentDispatchRequest(room=room_name, agent_name="")
        await lk_api.agent_dispatch.create_dispatch(dispatch_req)
        await lk_api.aclose()
    except Exception as e:
        logger.warning("LiveKit agent dispatch (non-fatal): %s", e)

    return {"token": token.to_jwt(), "url": os.getenv("LIVEKIT_URL")}
