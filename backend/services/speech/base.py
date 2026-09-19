from abc import ABC, abstractmethod
from typing import Optional


class SpeechProvider(ABC):
    """
    Provider-independent interface for speech services.

    Implementations can provide:
    - speech-to-text
    - text-to-speech

    The rest of the application should depend on this
    interface instead of a specific vendor.
    """

    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        *,
        filename: str = "audio.webm",
        content_type: Optional[str] = None,
        language: str = "en",
    ) -> str:
        """
        Convert audio into text.
        """
        raise NotImplementedError

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        *,
        language: str = "en",
        voice: Optional[str] = None,
        format: str = "mp3",
    ) -> bytes:
        """
        Convert text into audio bytes.
        """
        raise NotImplementedError