"""Local transcription router using faster-whisper (or a mock fallback)."""

import io
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transcribe", tags=["transcription"])


def _transcribe_with_whisper(audio_path: Path) -> str:
    try:
        import faster_whisper
    except ImportError as exc:
        raise RuntimeError("faster-whisper n'est pas installé") from exc

    model = faster_whisper.WhisperModel(
        settings.whisper_model,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
    )
    segments, _ = model.transcribe(str(audio_path), language="fr", beam_size=5)
    return " ".join(segment.text for segment in segments).strip()


def _transcribe_mock(audio_path: Path) -> str:
    logger.info("Transcription mock: %s", audio_path)
    return "[Dictée locale mock] Le modèle de transcription n'est pas encore activé."


@router.post("")
async def transcribe_endpoint(
    audio: UploadFile = File(...),
    engine: str = Form(settings.transcription_engine),
) -> dict:
    if not audio.content_type or not audio.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Fichier audio requis")

    content = await audio.read()
    if len(content) > settings.max_upload_size:
        raise HTTPException(status_code=413, detail="Fichier audio trop volumineux")

    # Determine extension from MIME type or filename
    ext = Path(audio.filename).suffix.lstrip(".").lower()
    if not ext:
        if "wav" in (audio.content_type or ""):
            ext = "wav"
        elif "webm" in (audio.content_type or ""):
            ext = "webm"
        elif "mp4" in (audio.content_type or ""):
            ext = "mp4"
        else:
            ext = "webm"

    try:
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        if engine == "whisper":
            text = _transcribe_with_whisper(tmp_path)
        else:
            text = _transcribe_mock(tmp_path)
    except Exception as exc:
        logger.error("Transcription error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Erreur de transcription: {exc}") from exc
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except NameError:
            pass

    return {"text": text}
