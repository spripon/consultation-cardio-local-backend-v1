"""Extraction router: OCR -> anonymisation -> catégorisation."""

import io
import logging
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import settings
from app.schemas.extraction import ExtractionResponse, ExtractedFields
from app.services.ocr import extract_text
from app.services.anonymize import anonymize_text
from app.services.categorize import categorize_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/extract", tags=["extraction"])


@router.post("", response_model=ExtractionResponse)
async def extract_endpoint(
    file: UploadFile = File(...),
    engine: str = Form(settings.ocr_engine),
) -> ExtractionResponse:
    """Upload an image or PDF, get anonymized text and categorized form fields."""
    if not file.content_type:
        raise HTTPException(status_code=400, detail="Type de fichier inconnu")

    allowed = {"image/png", "image/jpeg", "image/jpg", "image/webp", "application/pdf"}
    if file.content_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Type {file.content_type} non autorisé. Formats acceptés: image/*, PDF",
        )

    content = await file.read()
    if len(content) > settings.max_upload_size:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux")

    try:
        raw_text = extract_text(content, file.content_type, engine=engine)
    except Exception as exc:
        logger.error("OCR error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Erreur OCR: {exc}") from exc

    try:
        anonymized_text, entities = anonymize_text(raw_text)
    except Exception as exc:
        logger.error("Anonymization error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Erreur d'anonymisation: {exc}") from exc

    try:
        fields = categorize_text(anonymized_text)
    except Exception as exc:
        logger.error("Categorization error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Erreur de catégorisation: {exc}") from exc

    warnings: list[str] = []
    if not raw_text or not raw_text.strip():
        warnings.append("Aucun texte détecté sur le document.")
    if engine == "mock":
        warnings.append("Moteur OCR mock activé: le vrai OCR local n'est pas configuré.")
    if not fields.conclusion:
        warnings.append("Section 'conclusion' non détectée.")

    return ExtractionResponse(
        fields=fields,
        rawTextAnonymized=anonymized_text,
        entities=entities,
        confidence={"ocr": "mock" if engine == "mock" else "tesseract", "entities": len(entities)},
        warnings=warnings,
    )
