from fastapi import APIRouter
from engine.aws_controller import get_llm_instance_status, start_llm_instance

router = APIRouter(tags=["llm"])


@router.get("/llm_status")
async def llm_status():
    return await get_llm_instance_status()


@router.post("/wake_llm")
async def wake_llm():
    return await start_llm_instance()
