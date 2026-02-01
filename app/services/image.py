"""Image Generation Service using OpenAI DALL-E 3"""
import os
import uuid
import base64
import asyncio
from typing import Optional, TypedDict
from pathlib import Path

from app.core.config import settings


class GeneratedImages(TypedDict):
    """Generated images result"""
    face_image_url: Optional[str]
    full_body_image_url: Optional[str]
    appearance_description: Optional[str]


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

    async def generate_character_images(
        self,
        name: str,
        description: Optional[str] = None,
        style: str = "anime",
    ) -> GeneratedImages:
        """
        Generate both face close-up and full body images using DALL-E 3.

        Args:
            name: Character name
            description: Character description/personality
            style: Art style ("anime", "realistic", "illustration")

        Returns:
            Dictionary with face_image_url, full_body_image_url, and appearance_description
        """
        if not settings.LLM_API_KEY:
            return {
                "face_image_url": None,
                "full_body_image_url": None,
                "appearance_description": None,
            }

        try:
            # First, generate detailed appearance description using GPT
            appearance_desc = await self._generate_appearance_description(
                name, description, style
            )
            
            # Generate both images concurrently using the appearance description
            face_task = self._generate_single_image(
                self._build_face_prompt(name, appearance_desc, style)
            )
            full_body_task = self._generate_single_image(
                self._build_full_body_prompt(name, appearance_desc, style)
            )
            
            face_url, full_body_url = await asyncio.gather(face_task, full_body_task)
            
            return {
                "face_image_url": face_url,
                "full_body_image_url": full_body_url,
                "appearance_description": appearance_desc,
            }

        except Exception as e:
            print(f"Image generation error: {e}")
            return {
                "face_image_url": None,
                "full_body_image_url": None,
                "appearance_description": None,
            }

    async def _generate_appearance_description(
        self,
        name: str,
        description: Optional[str],
        style: str,
    ) -> str:
        """
        Generate detailed visual appearance description using GPT.
        This ensures character consistency across multiple image generations.
        """
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=settings.LLM_API_KEY)
            
            system_prompt = (
                "You are a character designer. Generate a detailed visual appearance "
                "description for an anime/illustration style character. "
                "Focus ONLY on visual elements that can be depicted in an image.\n\n"
                "Include:\n"
                "- Hair: color, length, style (e.g., 'long black hair with purple highlights')\n"
                "- Eyes: color, shape, notable features (e.g., 'large purple eyes')\n"
                "- Face: distinctive features, expression type\n"
                "- Clothing: detailed outfit description with colors\n"
                "- Accessories: hats, jewelry, items they carry\n"
                "- Body type: height impression, build\n"
                "- Overall aesthetic: cute, cool, elegant, etc.\n\n"
                "Output ONLY the appearance description in English, no explanations. "
                "Be specific with colors and details. Maximum 150 words."
            )
            
            user_prompt = f"Character Name: {name}\n"
            if description:
                user_prompt += f"Character Concept: {description}\n"
            user_prompt += f"Art Style: {style}\n"
            user_prompt += "\nGenerate a detailed visual appearance description:"
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=250,
                temperature=0.7,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Appearance description generation error: {e}")
            # Fallback to original description if GPT fails
            return description or f"A {style} style character named {name}"

    async def generate_character_image(
        self,
        name: str,
        description: Optional[str] = None,
        style: str = "anime",
    ) -> Optional[str]:
        """
        Generate a character image using DALL-E 3 (legacy single image).

        Args:
            name: Character name
            description: Character description/personality
            style: Art style ("anime", "realistic", "illustration")

        Returns:
            URL path to the generated image or None if failed
        """
        if not settings.LLM_API_KEY:
            return None

        prompt = self._build_face_prompt(name, description, style)
        return await self._generate_single_image(prompt)

    async def _generate_single_image(self, prompt: str) -> Optional[str]:
        """Generate a single image from prompt"""
        try:
            import openai
            
            client = openai.OpenAI(api_key=settings.LLM_API_KEY)
            
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
            print(f"Single image generation error: {e}")
            return None

    def _build_face_prompt(
        self,
        name: str,
        description: Optional[str],
        style: str,
    ) -> str:
        """Build DALL-E prompt for face close-up image"""
        
        style_prompts = {
            "anime": "beautiful anime style, high quality anime art, detailed expressive eyes, soft lighting, studio ghibli inspired",
            "realistic": "photorealistic, beautiful person, professional photography, soft studio lighting, high detail",
            "illustration": "digital illustration style, vibrant colors, detailed artwork, professional concept art",
        }
        
        style_desc = style_prompts.get(style, style_prompts["anime"])
        
        prompt_parts = [
            f"Close-up portrait of {name}, face and shoulders only.",
            "Single character only, exactly one person in the image.",
            style_desc,
            "Focus on the face with detailed expression.",
            "Centered composition, clean simple background.",
            "No other characters, no duplicates, no mirror reflections, no split screen.",
        ]
        
        if description:
            prompt_parts.append(f"Character appearance: {description}")
        
        prompt_parts.extend([
            "Appropriate for all ages.",
            "Friendly and approachable expression.",
            "Solo portrait, single subject only.",
        ])
        
        return " ".join(prompt_parts)

    def _build_full_body_prompt(
        self,
        name: str,
        description: Optional[str],
        style: str,
    ) -> str:
        """Build DALL-E prompt for character design sheet"""
        
        style_prompts = {
            "anime": "beautiful anime style, high quality anime art, detailed character design, soft lighting",
            "realistic": "semi-realistic style, detailed character artwork, professional concept art",
            "illustration": "digital illustration style, vibrant colors, detailed character artwork, professional concept art",
        }
        
        style_desc = style_prompts.get(style, style_prompts["anime"])
        
        prompt_parts = [
            f"Character design reference sheet of {name}.",
            "Character turnaround sheet showing multiple views.",
            style_desc,
            "Front view, side view, and back view of the same character.",
            "Full body visible from head to feet in each view.",
            "Clean white background, professional character sheet layout.",
            "Consistent character design across all views.",
        ]
        
        if description:
            prompt_parts.append(f"Character appearance: {description}")
        
        prompt_parts.extend([
            "Appropriate for all ages.",
            "Detailed outfit and character design.",
            "Professional game or anime character reference sheet style.",
        ])
        
        return " ".join(prompt_parts)

    def get_available_styles(self) -> list[dict]:
        """Get list of available art styles"""
        return [
            {"id": "anime", "name": "アニメ風", "description": "日本のアニメスタイル"},
            {"id": "realistic", "name": "リアル", "description": "写実的なスタイル"},
            {"id": "illustration", "name": "イラスト", "description": "デジタルイラスト風"},
        ]

    async def generate_scene_image(self, scene_prompt: str) -> Optional[str]:
        """
        Generate a scene image from a description prompt.

        Args:
            scene_prompt: Scene description for DALL-E

        Returns:
            URL path to the generated image or None if failed
        """
        if not settings.LLM_API_KEY:
            return None

        try:
            import openai
            
            client = openai.OpenAI(api_key=settings.LLM_API_KEY)
            
            # Add safety and quality modifiers
            full_prompt = f"{scene_prompt} Single scene illustration, no text, no watermarks, appropriate for all ages."
            
            response = client.images.generate(
                model=self.DEFAULT_MODEL,
                prompt=full_prompt,
                size=self.DEFAULT_SIZE,
                quality=self.DEFAULT_QUALITY,
                n=1,
                response_format="b64_json",
            )
            
            # Get base64 image data
            image_data = response.data[0].b64_json
            
            # Save image to file
            filename = f"scene_{uuid.uuid4()}.png"
            filepath = self.IMAGES_DIR / filename
            
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(image_data))
            
            # Return URL path
            return f"/static/images/characters/{filename}"

        except Exception as e:
            print(f"Scene image generation error: {e}")
            return None
