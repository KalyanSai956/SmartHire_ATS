from typing import Optional

from .base import SpeechProvider
from .factory import get_speech_provider


class SpeechService:
    """
    Application-level speech service.

    The API layer depends on this service rather than
    directly depending on Groq or browser speech.
    """

    def __init__(
        self,
        provider: Optional[SpeechProvider] = None,
    ):
        self.provider = (
            provider
            or get_speech_provider()
        )

    async def transcribe(
        self,
        audio_bytes: bytes,
        *,
        filename: str = "audio.webm",
        content_type: Optional[str] = None,
        language: str = "en",
    ) -> str:

        if not audio_bytes:
            raise ValueError(
                "Audio payload is empty."
            )

        return await self.provider.transcribe(
            audio_bytes,
            filename=filename,
            content_type=content_type,
            language=language,
        )

    async def synthesize(
        self,
        text: str,
        *,
        language: str = "en",
        voice: Optional[str] = None,
        format: str = "wav",
    ) -> bytes:

        if not text or not text.strip():
            raise ValueError(
                "Text cannot be empty."
            )

        return await self.provider.synthesize(
            text.strip(),
            language=language,
            voice=voice,
            format=format,
        )