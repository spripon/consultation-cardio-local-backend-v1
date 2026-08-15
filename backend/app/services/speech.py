"""Transcription locale via faster-whisper. Aucun service cloud, jamais."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_MODEL = None


class SpeechUnavailable(RuntimeError):
    pass


def _load_model():
    global _MODEL
    with _LOCK:
        if _MODEL is not None:
            return _MODEL
        try:
            from faster_whisper import WhisperModel  # type: ignore
        except Exception as exc:
            raise SpeechUnavailable("faster-whisper n'est pas installé sur ce serveur.") from exc

        model_ref = settings.whisper_model_path
        if model_ref.startswith("/") and not Path(model_ref).exists():
            raise SpeechUnavailable(
                "Modèle de transcription local absent : téléchargez-le hors ligne avant utilisation."
            )
        _MODEL = WhisperModel(
            model_ref,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
            local_files_only=True,
        )
        return _MODEL


def speech_available() -> bool:
    if not settings.enable_speech:
        return False
    try:
        _load_model()
        return True
    except SpeechUnavailable:
        return False


def transcribe_file(audio_path: Path) -> str:
    if not settings.enable_speech:
        raise SpeechUnavailable("La dictée locale est désactivée sur ce serveur (ENABLE_SPEECH=false).")
    model = _load_model()
    segments, _info = model.transcribe(
        str(audio_path), language=settings.whisper_language, beam_size=5, vad_filter=True
    )
    return " ".join(segment.text.strip() for segment in segments).strip()