"""Scene Generation Service - Generate scene descriptions from conversation"""
from typing import Optional, List
from app.core.config import settings


class SceneService:
    """Service for generating scene descriptions from conversation"""

    async def generate_scene_prompt(
        self,
        character_name: str,
        character_description: Optional[str],
        messages: List,
        appearance_description: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a scene description prompt for image generation.

        Args:
            character_name: Name of the character
            character_description: Character's description/personality
            messages: Recent conversation messages
            appearance_description: Detailed visual appearance of the character

        Returns:
            Scene description prompt for DALL-E or None if failed
        """
        if not settings.LLM_API_KEY:
            return None

        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=settings.LLM_API_KEY)
            
            # Format conversation history
            conversation_text = self._format_messages(messages, character_name)
            
            # Build prompt for GPT-4
            system_prompt = (
                "You are a scene description generator for anime/illustration "
                "style images. Based on the conversation between a user and a "
                "character, generate a detailed scene description in English "
                "for image generation.\n\n"
                "IMPORTANT: You MUST use the exact character appearance provided. "
                "Do not change any visual details (hair color, eye color, clothing, etc.).\n\n"
                "Rules:\n"
                "- ALWAYS include the character's exact appearance as described\n"
                "- Describe the scene, setting, and atmosphere\n"
                "- Include the character's expression matching the conversation mood\n"
                "- Use anime/illustration style descriptors\n"
                "- Keep it appropriate for all ages\n"
                "- Focus on visual elements that can be depicted in a single image\n"
                "- Output ONLY the scene description, nothing else\n"
                "- Maximum 200 words"
            )

            # Use appearance_description if available, otherwise fall back to description
            visual_desc = appearance_description or character_description or "A friendly anime character"
            
            user_prompt = (
                f"Character Name: {character_name}\n\n"
                f"CHARACTER APPEARANCE (use this exactly):\n{visual_desc}\n\n"
            )
            
            if character_description and appearance_description:
                user_prompt += f"Character Personality: {character_description}\n\n"
            
            user_prompt += (
                f"Recent Conversation:\n{conversation_text}\n\n"
                "Generate a scene description for this moment. "
                "The character's appearance MUST match the description exactly. "
                "Describe what the scene would look like as an anime illustration."
            )

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=300,
                temperature=0.7,
            )

            scene_description = response.choices[0].message.content.strip()

            # Add style modifiers and reinforce character appearance
            final_prompt = f"{scene_description} Beautiful anime style illustration, "
            final_prompt += "high quality, detailed artwork, soft lighting. "
            final_prompt += "Single character in the scene, consistent character design."

            return final_prompt

        except Exception as e:
            print(f"Scene generation error: {e}")
            return None

    def _format_messages(self, messages: List, character_name: str) -> str:
        """Format messages for the prompt"""
        formatted = []
        # Messages are in desc order, reverse for chronological
        for msg in reversed(messages[-10:]):
            role = character_name if msg.role == "character" else "User"
            formatted.append(f"{role}: {msg.content}")
        return "\n".join(formatted)
