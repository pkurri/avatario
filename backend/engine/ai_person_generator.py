import logging
# backend/engine/ai_person_generator.py
"""
AI Person Generator - Creates realistic AI human avatars
Integrates with image generation models to create unique, realistic personas
"""

import os
import httpx
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import hashlib
import json

logger = logging.getLogger(__name__)

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"

class Ethnicity(str, Enum):
    ASIAN = "asian"
    CAUCASIAN = "caucasian"
    AFRICAN = "african"
    HISPANIC = "hispanic"
    INDIAN = "indian"
    MIDDLE_EASTERN = "middle_eastern"
    MIXED = "mixed"

class AgeGroup(str, Enum):
    YOUNG = "young"  # 20s-30s
    MIDDLE = "middle"  # 40s-50s
    MATURE = "mature"  # 60s+

@dataclass
class PersonTraits:
    """Traits for AI person generation"""
    gender: Gender
    ethnicity: Ethnicity
    age_group: AgeGroup
    profession: str
    expression: str = "warm, approachable, professional"
    setting: str = "professional office"
    
@dataclass
class AIPerson:
    """Generated AI person"""
    id: str
    name: str
    image_url: str
    traits: PersonTraits
    vertical: str
    voice_id: Optional[str] = None
    video_url: Optional[str] = None


class AIPersonGenerator:
    """
    Generates realistic AI human avatars using image generation APIs
    Compatible with FLUX, Midjourney, Stable Diffusion, etc.
    """
    
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.api_url = api_url or os.getenv("AI_IMAGE_API_URL", "http://localhost:7860")
        self.api_key = api_key or os.getenv("AI_IMAGE_API_KEY", "")
        self.cache_dir = "/tmp/ai_persons"
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _generate_prompt(self, traits: PersonTraits, vertical: str) -> str:
        """Generate detailed prompt for realistic person"""
        
        base_prompts = {
            "legal": f"professional lawyer, {traits.age_group} age, confident, trustworthy, wearing formal business attire, law office background",
            "medical": f"caring doctor/physician, {traits.age_group} age, compassionate, wearing white medical coat or scrubs, hospital/clinic background",
            "finance": f"financial advisor, {traits.age_group} age, intelligent, trustworthy, wearing business suit, corporate office background",
            "education": f"knowledgeable professor/teacher, {traits.age_group} age, wise, approachable, academic setting",
            "generic": f"professional assistant, {traits.age_group} age, friendly, helpful, modern office background"
        }
        
        base = base_prompts.get(vertical, base_prompts["generic"])
        
        prompt = f"""
        Ultra-realistic portrait photograph of a {traits.ethnicity} {traits.gender} person, 
        {traits.age_group} adult, {traits.expression} expression, 
        {base},
        professional headshot style, studio lighting, 
        sharp focus on face, detailed skin texture, natural features,
        photorealistic, 8k resolution, DSLR quality, 
        neutral background that doesn't distract,
        looking directly at camera with {traits.expression} expression
        """
        
        return prompt.strip().replace("\n", " ")
    
    async def generate_person(
        self,
        traits: PersonTraits,
        vertical: str,
        name: Optional[str] = None,
        use_cache: bool = True
    ) -> AIPerson:
        """
        Generate a realistic AI person
        
        Returns AIPerson with image URL
        """
        # Create unique ID from traits
        traits_str = f"{traits.gender}_{traits.ethnicity}_{traits.age_group}_{vertical}_{traits.profession}"
        person_id = hashlib.md5(traits_str.encode()).hexdigest()[:12]
        
        # Check cache
        cache_file = f"{self.cache_dir}/{person_id}.json"
        if use_cache and os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached = json.load(f)
                return AIPerson(
                    id=person_id,
                    name=cached['name'],
                    image_url=cached['image_url'],
                    traits=traits,
                    vertical=vertical,
                    voice_id=cached.get('voice_id')
                )
        
        # Generate prompt
        prompt = self._generate_prompt(traits, vertical)
        
        # Try to generate image via API
        image_url = await self._generate_image(prompt, person_id)
        
        # Generate name if not provided
        if not name:
            name = self._generate_name(traits.gender, traits.ethnicity)
        
        person = AIPerson(
            id=person_id,
            name=name,
            image_url=image_url,
            traits=traits,
            vertical=vertical
        )
        
        # Cache result
        if use_cache:
            with open(cache_file, 'w') as f:
                json.dump({
                    'id': person_id,
                    'name': name,
                    'image_url': image_url,
                    'traits': {
                        'gender': traits.gender.value,
                        'ethnicity': traits.ethnicity.value,
                        'age_group': traits.age_group.value,
                        'profession': traits.profession
                    },
                    'vertical': vertical
                }, f)
        
        return person
    
    async def _generate_image(self, prompt: str, person_id: str) -> str:
        """
        Generate image using AI image generation API
        Falls back to placeholder if API unavailable
        """
        try:
            # Try FLUX/Stable Diffusion API
            endpoint = f"{self.api_url}/api/image/generate"
            
            payload = {
                "prompt": prompt,
                "model": "flux-dev",  # or "sdxl", "midjourney", etc.
                "width": 1024,
                "height": 1024,
                "steps": 30,
                "guidance_scale": 7.5
            }
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("image_url"):
                        return data["image_url"]
                    if data.get("images"):
                        return data["images"][0]
        except Exception as e:
            logger.error(f"Image generation API failed: {e}")
        
        # Fallback: Return placeholder that indicates AI generation needed
        # In production, this would be a generated image URL
        return f"ai://person/{person_id}"
    
    def _generate_name(self, gender: Gender, ethnicity: Ethnicity) -> str:
        """Generate appropriate name based on traits"""
        names = {
            Gender.MALE: {
                Ethnicity.ASIAN: ["James Chen", "Michael Park", "David Kim", "Andrew Wong"],
                Ethnicity.CAUCASIAN: ["John Smith", "Michael Johnson", "David Williams", "James Brown"],
                Ethnicity.AFRICAN: ["Michael Johnson", "David Williams", "James Brown", "Robert Davis"],
                Ethnicity.HISPANIC: ["Carlos Rodriguez", "Jose Martinez", "Luis Garcia", "Miguel Lopez"],
                Ethnicity.INDIAN: ["Raj Patel", "Amit Kumar", "Vikram Singh", "Arjun Sharma"],
                Ethnicity.MIDDLE_EASTERN: ["Omar Hassan", "Amir Khan", "Karim Al-Fayed", "Samir"],
                Ethnicity.MIXED: ["Jordan Williams", "Alex Chen", "Taylor Johnson", "Morgan Lee"]
            },
            Gender.FEMALE: {
                Ethnicity.ASIAN: ["Sarah Chen", "Emily Park", "Jessica Kim", "Amy Wong"],
                Ethnicity.CAUCASIAN: ["Emily Johnson", "Sarah Williams", "Jessica Brown", "Amanda Davis"],
                Ethnicity.AFRICAN: ["Tasha Williams", "Keisha Johnson", "Monica Davis", "Angela Brown"],
                Ethnicity.HISPANIC: ["Maria Garcia", "Sofia Martinez", "Isabella Rodriguez", "Carmen Lopez"],
                Ethnicity.INDIAN: ["Priya Sharma", "Ananya Patel", "Divya Kumar", "Neha Singh"],
                Ethnicity.MIDDLE_EASTERN: ["Fatima Hassan", "Amira Khan", "Leila Al-Fayed", "Noor"],
                Ethnicity.MIXED: ["Jordan Williams", "Alex Chen", "Taylor Johnson", "Morgan Lee"]
            }
        }
        
        import random
        name_list = names.get(gender, {}).get(ethnicity, ["Alex Johnson"])
        return random.choice(name_list)
    
    async def generate_talking_video(
        self,
        person: AIPerson,
        text: str,
        audio_url: Optional[str] = None
    ) -> str:
        """
        Generate talking video using lip sync
        """
        from engine.lipsync import lipsync_service, LipSyncModel
        
        # Generate audio if not provided (using TTS)
        if not audio_url:
            from engine.audio import sarvam_tts
            # This would need to be async
            # audio_bytes = await sarvam_tts(text, role="priya")
            # For now, assume audio is generated separately
            pass
        
        # Generate lip-synced video
        result = await lipsync_service.generate_talking_video(
            image_url=person.image_url,
            audio_url=audio_url or "",
            model=LipSyncModel.INFINITETALK_IMAGE,
            prompt=f"Natural talking head, {person.traits.expression}, professional"
        )
        
        return result.get("video_url", "")
    
    async def create_vertical_personas(
        self,
        vertical: str,
        count: int = 2
    ) -> List[AIPerson]:
        """
        Create multiple AI personas for a vertical
        
        Example: create 2 legal personas (male/female)
        """
        personas = []
        
        configs = [
            (Gender.FEMALE, Ethnicity.INDIAN, AgeGroup.MIDDLE),
            (Gender.MALE, Ethnicity.INDIAN, AgeGroup.MIDDLE),
        ]
        
        for gender, ethnicity, age in configs[:count]:
            traits = PersonTraits(
                gender=gender,
                ethnicity=ethnicity,
                age_group=age,
                profession=vertical
            )
            
            person = await self.generate_person(traits, vertical)
            personas.append(person)
        
        return personas


# Global instance
ai_person_generator = AIPersonGenerator()


# ==========================================
# CONVENIENCE FUNCTIONS
# ==========================================

async def generate_real_ai_person(
    vertical: str = "generic",
    gender: str = "female",
    name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a complete AI person with image and metadata
    """
    traits = PersonTraits(
        gender=Gender(gender),
        ethnicity=Ethnicity.INDIAN,  # Default - can be randomized
        age_group=AgeGroup.MIDDLE,
        profession=vertical
    )
    
    person = await ai_person_generator.generate_person(traits, vertical, name)
    
    return {
        "id": person.id,
        "name": person.name,
        "image_url": person.image_url,
        "vertical": vertical,
        "gender": gender,
        "ready": person.image_url.startswith("http")  # True if real image generated
    }


async def generate_talking_head(
    person_id: str,
    text: str,
    persona_image_url: str
) -> Dict[str, Any]:
    """
    Generate a talking head video for an AI person
    """
    from engine.lipsync import lipsync_service, LipSyncModel
    
    # This would integrate with TTS to get audio first
    # Then generate lip-synced video
    
    result = await lipsync_service.generate_talking_video(
        image_url=persona_image_url,
        audio_url="",  # Would be TTS output
        model=LipSyncModel.INFINITETALK_IMAGE,
        prompt="Professional talking head, natural lip sync"
    )
    
    return {
        "person_id": person_id,
        "text": text,
        "video_url": result.get("video_url"),
        "status": result.get("status", "processing"),
        "job_id": result.get("job_id")
    }
