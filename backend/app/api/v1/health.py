"""Endpoints de santé / readiness. Ne révèlent ni chemin, ni secret."""

from fastapi import APIRouter, Response

from app.config import settings
from app.schemas.extraction import HealthResponse
from app.services.ocr import tesseract_available
from app.services.openmed_pii import status as openmed_status
from app.services.speech import speech_available

router = APIRouter(tags=["health"])

VERSION = "1.0.0-local"


def _snapshot() -> HealthResponse:
    ocr_ok = tesseract_available()
    openmed_ok = openmed_status().available
    speech_ok = speech_available()

    missing: list[str] = []
    if settings.ocr_required and not ocr_ok:
        missing.append("ocr")
    if settings.openmed_required and not openmed_ok:
        missing.append("openmed")
    if settings.enable_speech and not speech_ok:
        missing.append("speech")

    ready = not missing
    return HealthResponse(
        status="ok" if ready else "degraded",
        version=VERSION,
        ocr=ocr_ok,
        openmed=openmed_ok,
        speech=speech_ok,
        policy=settings.openmed_policy,
        environment="production" if settings.is_production else "development",
        ready=ready,
        missing=missing,
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Diagnostic : répond toujours 200, mais `status` reflète l'état réel."""
    return _snapshot()


@router.get("/readyz", response_model=HealthResponse)
def readyz(response: Response) -> HealthResponse:
    """Readiness : 503 tant qu'un composant local obligatoire est absent."""
    snapshot = _snapshot()
    if not snapshot.ready:
        response.status_code = 503
    return snapshot