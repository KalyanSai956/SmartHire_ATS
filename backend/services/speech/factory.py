import io
import os
import wave
from typing import List, Optional

import httpx

from .base import SpeechProvider


class GroqSpeechProvider(SpeechProvider):
    BASE_URL = "https://api.groq.com/openai/v1"

    STT_MODEL = "whisper-large-v3-turbo"

    TTS_MODEL = "canopylabs/orpheus-v1-english"

    DEFAULT_TTS_VOICE = "troy"

    MAX_TTS_CHARS = 200

    def __init__(self):
        self.api_key = os.getenv(
            "GROQ_API_KEY",
            "",
        ).strip()

        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured."
            )

    def _headers(self):
        return {
            "Authorization": (
                f"Bearer {self.api_key}"
            ),
        }

    # ========================================================
    # SPEECH TO TEXT
    # ========================================================

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        content_type: Optional[str] = None,
        language: str = "en",
    ) -> str:

        if not audio_bytes:
            raise ValueError(
                "Audio data is empty."
            )

        content_type = (
            content_type
            or "audio/webm"
        )

        files = {
            "file": (
                filename,
                audio_bytes,
                content_type,
            )
        }

        data = {
            "model": self.STT_MODEL,
            "language": language,
            "response_format": "json",
            "temperature": "0",
        }

        async with httpx.AsyncClient(
            timeout=60.0
        ) as client:

            response = await client.post(
                f"{self.BASE_URL}/audio/transcriptions",
                headers=self._headers(),
                files=files,
                data=data,
            )

            response.raise_for_status()

            payload = response.json()

        transcript = (
            payload.get("text") or ""
        ).strip()

        if not transcript:
            raise ValueError(
                "Groq returned an empty transcript."
            )

        return transcript

    # ========================================================
    # TEXT TO SPEECH
    # ========================================================

    async def synthesize(
        self,
        text: str,
        language: str = "en",
        voice: Optional[str] = None,
        format: str = "wav",
    ) -> bytes:

        text = (text or "").strip()

        if not text:
            raise ValueError(
                "Text for synthesis is empty."
            )

        if language != "en":
            raise ValueError(
                "The current Groq Orpheus voice provider "
                "is configured for English."
            )

        if format != "wav":
            raise ValueError(
                "Groq Orpheus currently supports WAV output."
            )

        selected_voice = (
            voice
            or self.DEFAULT_TTS_VOICE
        )

        chunks = self._split_text(
            text,
            self.MAX_TTS_CHARS,
        )

        audio_chunks: List[bytes] = []

        for index, chunk in enumerate(chunks):

            print(
                f"[Groq TTS] Generating chunk "
                f"{index + 1}/{len(chunks)} "
                f"({len(chunk)} chars)"
            )

            audio = await self._synthesize_chunk(
                text=chunk,
                voice=selected_voice,
            )

            audio_chunks.append(audio)

        if len(audio_chunks) == 1:
            return audio_chunks[0]

        return self._combine_wav_files(
            audio_chunks
        )

    # ========================================================
    # SINGLE GROQ TTS REQUEST
    # ========================================================

    async def _synthesize_chunk(
        self,
        text: str,
        voice: str,
    ) -> bytes:

        text = text.strip()

        if not text:
            raise ValueError(
                "TTS chunk is empty."
            )

        if len(text) > self.MAX_TTS_CHARS:
            raise ValueError(
                "TTS chunk exceeds Groq's "
                "200-character limit."
            )

        payload = {
            "model": self.TTS_MODEL,
            "input": text,
            "voice": voice,
            "response_format": "wav",
        }

        async with httpx.AsyncClient(
            timeout=60.0
        ) as client:

            response = await client.post(
                f"{self.BASE_URL}/audio/speech",
                headers={
                    **self._headers(),
                    "Content-Type": (
                        "application/json"
                    ),
                },
                json=payload,
            )

        if response.is_error:

            print(
                "[Groq TTS] status:",
                response.status_code,
            )

            print(
                "[Groq TTS] response:",
                response.text,
            )

            if (
                response.status_code == 400
                and "model_terms_required"
                in response.text
            ):
                raise RuntimeError(
                    "Groq Orpheus TTS requires model "
                    "terms acceptance. Accept the "
                    "Orpheus model terms in the Groq "
                    "Console."
                )

        response.raise_for_status()

        if not response.content:
            raise RuntimeError(
                "Groq returned empty TTS audio."
            )

        return response.content

    # ========================================================
    # TEXT CHUNKING
    # ========================================================

    @classmethod
    def _split_text(
        cls,
        text: str,
        max_chars: int,
    ) -> List[str]:

        if len(text) <= max_chars:
            return [text]

        words = text.split()

        chunks: List[str] = []

        current = ""

        for word in words:

            candidate = (
                f"{current} {word}".strip()
            )

            if len(candidate) <= max_chars:
                current = candidate
                continue

            if current:
                chunks.append(current)

            # Handle a single unusually long word.
            if len(word) > max_chars:

                start = 0

                while start < len(word):
                    end = min(
                        start + max_chars,
                        len(word),
                    )

                    chunks.append(
                        word[start:end]
                    )

                    start = end

                current = ""

            else:
                current = word

        if current:
            chunks.append(current)

        return chunks

    # ========================================================
    # WAV COMBINATION
    # ========================================================

    @staticmethod
    def _combine_wav_files(
        wav_files: List[bytes],
    ) -> bytes:

        if not wav_files:
            raise ValueError(
                "No WAV files to combine."
            )

        output = io.BytesIO()

        output_wave = None

        try:

            for index, wav_bytes in enumerate(
                wav_files
            ):

                input_wave = wave.open(
                    io.BytesIO(wav_bytes),
                    "rb",
                )

                try:

                    if index == 0:

                        output_wave = wave.open(
                            output,
                            "wb",
                        )

                        output_wave.setnchannels(
                            input_wave.getnchannels()
                        )

                        output_wave.setsampwidth(
                            input_wave.getsampwidth()
                        )

                        output_wave.setframerate(
                            input_wave.getframerate()
                        )

                    else:

                        if (
                            input_wave.getnchannels()
                            != output_wave.getnchannels()
                            or
                            input_wave.getsampwidth()
                            != output_wave.getsampwidth()
                            or
                            input_wave.getframerate()
                            != output_wave.getframerate()
                        ):
                            raise RuntimeError(
                                "Groq returned WAV chunks "
                                "with incompatible audio "
                                "parameters."
                            )

                    output_wave.writeframes(
                        input_wave.readframes(
                            input_wave.getnframes()
                        )
                    )

                finally:
                    input_wave.close()

        finally:

            if output_wave is not None:
                output_wave.close()

        return output.getvalue()


# ============================================================
# BROWSER SPEECH PROVIDER
# ============================================================

class BrowserSpeechProvider(
    SpeechProvider
):

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        content_type: Optional[str] = None,
        language: str = "en",
    ) -> str:

        raise NotImplementedError(
            "Browser STT runs on the client."
        )

    async def synthesize(
        self,
        text: str,
        language: str = "en",
        voice: Optional[str] = None,
        format: str = "wav",
    ) -> bytes:

        raise NotImplementedError(
            "Browser TTS runs on the client."
        )


# ============================================================
# PROVIDER FACTORY
# ============================================================

def get_speech_provider(
    provider: Optional[str] = None,
) -> SpeechProvider:

    selected = (
        provider
        or os.getenv(
            "SPEECH_PROVIDER",
            "groq",
        )
    ).strip().lower()

    if selected == "groq":
        return GroqSpeechProvider()

    if selected == "browser":
        return BrowserSpeechProvider()

    raise ValueError(
        f"Unsupported speech provider: {selected}"
    )