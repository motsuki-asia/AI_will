"""Image Generation Service using OpenAI DALL-E 3"""
import os
import uuid
import base64
from typing import Optional
from pathlib import Path

from app.core.config import settings


class ImageService:
    """Service for AI image generation"""

    # DALL-E 3 settings
    DEFAULT_MODEL = "dall-e-3"
    DEFAULT_SIZE = "1024x1024"
    DEFAULT_QUALITY = "standard"  # "standard" or "hd"
    
    # Storage settings
    IMAGES_DIR = Path("static/images/characters")

    def __init__(self):
        # Ensure images directory exists
        self.IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    async def generate_character_image(
        self,
        name: str,
        description: Optional[str] = None,
        style: str = "anime",
    ) -> Optional[str]:
        """
        Generate a character image using DALL-E 3.

        Args:
            name: Character name
            description: Character description/personality
            style: Art style ("anime", "realistic", "illustration")

        Returns:
            URL path to the generated image or None if failed
        """
        if not settings.LLM_API_KEY:
            return None

        try:
            import openai
            
            client = openai.OpenAI(api_key=settings.LLM_API_KEY)
            
            # Build prompt based on style
            prompt = self._build_prompt(name, description, style)
            
            response = client.images.generate(
                model=self.DEFAULT_MODEL,
                prompt=prompt,
                size=self.DEFAULT_SIZE,
                quality=self.DEFAULT_QUALITY,
                n=1,
                response_format="b64_json",
            )
            
            # Get base64 image data
            image_data = response.data[0].b64_json
            
            # Save image to file
            filename = f"{uuid.uuid4()}.png"
            filepath = self.IMAGES_DIR / filename
            
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(image_data))
            
            # Return URL path
            return f"/static/images/characters/{filename}"

        except Exception as e:
            print(f"Image generation error: {e}")
            return None

    def _build_prompt(
        self,
        name: str,
        description: Optional[str],
        style: str,
    ) -> str:
        """Build DALL-E prompt for character image"""
        
        style_prompts = {
            "anime": "beautiful anime style character portrait, high quality anime art, detailed eyes, soft lighting, studio ghibli inspired",
            "realistic": "photorealistic portrait, beautiful person, professional photography, soft studio lighting, high detail",
            "illustration": "digital illustration character portrait, vibrant colors, detailed artwork, professional concept art",
        }
        
        style_desc = style_prompts.get(style, style_prompts["anime"])
        
        # Base prompt
        prompt_parts = [
            f"Create a character portrait of {name}.",
            style_desc,
        ]
        
        # Add description if provided
        if description:
            prompt_parts.append(f"Character personality/appearance: {description}")
        
        # Safety and quality guidelines
        prompt_parts.extend([
            "Appropriate for all ages.",
            "Friendly and approachable expression.",
            "Clean background, focus on the character.",
        ])
        
        return " ".join(prompt_parts)

    def get_available_styles(self) -> list[dict]:
        """Get list of available art styles"""
        return [
            {"id": "anime", "name": "アニメ風", "description": "日本のアニメスタイル"},
            {"id": "realistic", "name": "リアル", "description": "写実的なスタイル"},
            {"id": "illustration", "name": "イラスト", "description": "デジタルイラスト風"},
        ]
