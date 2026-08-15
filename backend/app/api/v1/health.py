"""Endpoint de santé. Ne révèle ni chemin, ni secret."""

from fastapi import APIRouter

from app.config import settings
from app.schemas.extraction import HealthResponse
from app.services.ocr import tesseract_available
from app.services.openmed_pii import status as openmed_status
from app.services.speech import speech_available

router = APIRouter(tags=["health"])

VERSION = "1.0.0-local"


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=VERSION,
        ocr=tesseract_available(),
        openmed=openmed_status().available,
        speech=speech_available(),
        policy=settings.openmed_policy,
        environment="production" if settings.is_production else "development",
    )