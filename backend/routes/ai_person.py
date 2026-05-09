from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from engine.ai_person_generator import (
    generate_real_ai_person,
    generate_talking_head,
    ai_person_generator,
    Gender,
    Ethnicity,
    AgeGroup,
)

router = APIRouter(prefix="/ai-person", tags=["ai-person"])


class GenerateAIPersonRequest(BaseModel):
    vertical: str = "generic"
    gender: str = "female"
    name: Optional[str] = None
    ethnicity: Optional[str] = None
    age_group: Optional[str] = "middle"


class TalkingHeadRequest(BaseModel):
    persona_id: str
    text: str
    image_url: str


@router.post("/generate")
async def create_ai_person(request: GenerateAIPersonRequest):
    result = await generate_real_ai_person(
        vertical=request.vertical,
        gender=request.gender,
        name=request.name,
    )
    return {
        "status": "success",
        "person": result,
        "message": (
            "AI person generated successfully"
            if result["ready"]
            else "AI person queued for generation"
        ),
    }


@router.post("/talking-head")
async def create_talking_head(request: TalkingHeadRequest):
    return await generate_talking_head(
        person_id=request.persona_id,
        text=request.text,
        persona_image_url=request.image_url,
    )


@router.get("/vertical/{vertical}")
async def get_vertical_personas(vertical: str, count: int = 2):
    personas = await ai_person_generator.create_vertical_personas(vertical, count)
    return {
        "vertical": vertical,
        "personas": [
            {
                "id": p.id,
                "name": p.name,
                "image_url": p.image_url,
                "traits": {
                    "gender": p.traits.gender.value,
                    "ethnicity": p.traits.ethnicity.value,
                    "age_group": p.traits.age_group.value,
                    "profession": p.traits.profession,
                },
            }
            for p in personas
        ],
    }


@router.get("/ethnicities")
async def list_ethnicities():
    return {
        "ethnicities": [e.value for e in Ethnicity],
        "genders": [g.value for g in Gender],
        "age_groups": [a.value for a in AgeGroup],
    }
