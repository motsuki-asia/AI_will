"""Text-to-Speech Service using OpenAI TTS API"""
from typing import Optional
import io

from app.core.config import settings


class TTSService:
    """Service for text-to-speech conversion"""

    # Available voices: alloy, echo, fable, onyx, nova, shimmer
    # 日本語に適した声: nova (女性的), onyx (男性的), shimmer (女性的・柔らかい)
    DEFAULT_VOICE = "nova"
    
    # Models: tts-1 (faster, lower quality), tts-1-hd (slower, higher quality)
    DEFAULT_MODEL = "tts-1"

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        Convert text to speech using OpenAI TTS API.

        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            model: Model to use (tts-1 or tts-1-hd)

        Returns:
            Audio data as bytes (MP3 format) or None if API not configured
        """
        if not settings.LLM_API_KEY:
            return None

        try:
            import openai
            
            client = openai.OpenAI(api_key=settings.LLM_API_KEY)
            
            response = client.audio.speech.create(
                model=model or self.DEFAULT_MODEL,
                voice=voice or self.DEFAULT_VOICE,
                input=text,
                response_format="mp3",
            )
            
            # Get audio bytes
            audio_bytes = response.content
            return audio_bytes

        except Exception as e:
            print(f"TTS API error: {e}")
            return None

    def get_available_voices(self) -> list[dict]:
        """Get list of available voices with descriptions"""
        return [
            {"id": "alloy", "name": "Alloy", "description": "中性的な声"},
            {"id": "echo", "name": "Echo", "description": "男性的な声"},
            {"id": "fable", "name": "Fable", "description": "イギリス風の声"},
            {"id": "onyx", "name": "Onyx", "description": "深みのある男性の声"},
            {"id": "nova", "name": "Nova", "description": "明るい女性の声（推奨）"},
            {"id": "shimmer", "name": "Shimmer", "description": "柔らかい女性の声"},
        ]
