"""Transcription locale (faster-whisper). 503 explicite si indisponible, jamais de cloud."""

from __future__ import annotations

import logging
import os
import tempfile
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import settings
from app.services.ocr import ensure_temp_root
from app.services.speech import SpeechUnavailable, transcribe_file

logger = logging.getLogger(__name__)
router = APIRouter(tags=["transcription"])

ALLOWED_AUDIO_PREFIX = ("audio/", "video/webm")


@router.post("/transcribe")
async def transcribe_endpoint(audio: UploadFile = File(...)) -> dict:
    request_id = uuid.uuid4().hex[:12]
    started = time.perf_counter()

    if not settings.enable_speech:
        raise HTTPException(
            status_code=503,
            detail="Dictée locale désactivée sur ce serveur (ENABLE_SPEECH=false).",
        )

    content_type = (audio.content_type or "").lower()
    if not content_type.startswith(ALLOWED_AUDIO_PREFIX):
        raise HTTPException(status_code=415, detail="Fichier audio requis.")

    data = await audio.read()
    if not data:
        raise HTTPException(status_code=400, detail="Enregistrement audio vide.")
    if len(data) > settings.max_upload_size:
        raise HTTPException(status_code=413, detail="Enregistrement audio trop volumineux.")

    suffix = Path(audio.filename or "audio.webm").suffix or ".webm"
    tmp_path: Path | None = None
    try:
        fd, name = tempfile.mkstemp(suffix=suffix, dir=ensure_temp_root())
        tmp_path = Path(name)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        text = transcribe_file(tmp_path)
    except SpeechUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"Transcription locale indisponible : {exc}") from exc
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
        logger.info(
            "transcribe request_id=%s size=%s duration_ms=%s",
            request_id,
            len(data),
            int((time.perf_counter() - started) * 1000),
        )

    return {"text": text}