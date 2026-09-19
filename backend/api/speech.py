from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.responses import Response
from pydantic import BaseModel, Field

from backend.api.auth import get_current_user
from backend.services.speech.factory import (
    get_speech_provider,
)
from backend.services.speech.service import (
    SpeechService,
)


router = APIRouter(
    prefix="/speech",
    tags=["Speech"],
)


MAX_AUDIO_SIZE = 25 * 1024 * 1024

ALLOWED_AUDIO_TYPES = {
    "audio/webm",
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/m4a",
    "audio/ogg",
    "audio/flac",
}


class SpeechSynthesizeRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
    )

    language: str = Field(
        default="en",
        max_length=20,
    )

    voice: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    format: str = Field(
        default="wav",
        max_length=20,
    )


@router.get("/health")
async def speech_health():
    """
    Public speech configuration health check.
    """

    try:
        provider = get_speech_provider()

        return {
            "status": "ok",
            "provider": provider.__class__.__name__,
            "stt": "groq",
            "tts": "groq",
            "fallback": "browser",
        }

    except Exception as exc:
        return {
            "status": "degraded",
            "provider": "unavailable",
            "error": str(exc),
            "fallback": "browser",
        }


@router.post("/transcribe")
async def transcribe_speech(
    audio: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    """
    Convert interview audio into text.
    """

    if not audio.filename:
        raise HTTPException(
            status_code=400,
            detail="Audio filename is required.",
        )

    content_type = (audio.content_type or "").lower().split(";")[0].strip()

    if content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
        status_code=400,
        detail="Unsupported audio format. Use WebM, WAV, MP3, MP4, M4A, OGG, or FLAC.",
    )

    audio_bytes = await audio.read()

    if not audio_bytes:
        raise HTTPException(
            status_code=400,
            detail="Audio file is empty.",
        )

    if len(audio_bytes) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Audio file is too large. Maximum size is 25 MB.",
        )

    try:
        service = SpeechService()

        transcript = await service.transcribe(
            audio_bytes,
            filename=audio.filename,
            content_type=audio.content_type,
            language="en",
        )

        return {
            "success": True,
            "transcript": transcript,
            "provider": "groq",
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Speech transcription service failed. "
                "Use browser voice fallback."
            ),
        ) from exc


@router.post("/synthesize")
async def synthesize_speech(
    request: SpeechSynthesizeRequest,
    current_user=Depends(get_current_user),
):
    """
    Convert interview question text into audio.
    """

    try:
        service = SpeechService()

        audio_bytes = await service.synthesize(
            request.text,
            language=request.language,
            voice=request.voice,
            format=request.format,
        )

        media_types = {
            "wav": "audio/wav",
            "mp3": "audio/mpeg",
            "ogg": "audio/ogg",
            "flac": "audio/flac",
            "mulaw": "audio/basic",
        }

        response_format = request.format.lower()

        media_type = media_types.get(
            response_format,
            "audio/wav",
        )

        return Response(
            content=audio_bytes,
            media_type=media_type,
            headers={
                "Cache-Control": "no-store",
                "Content-Disposition": (
                    f'inline; filename="smart-hire-speech.'
                    f'{response_format}"'
                ),
            },
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Speech synthesis service failed. "
                "Use browser TTS fallback."
            ),
        ) from exc