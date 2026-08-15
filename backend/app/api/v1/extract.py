"""Pipeline /extract : OCR local -> PII déterministe -> OpenMed -> anonymisation -> catégorisation.

Aucun contenu patient n'est journalisé, aucun fichier n'est conservé.
"""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import settings
from app.schemas.extraction import (
    ConfidenceBlock,
    Entity,
    ExtractedFields,
    ExtractionResponse,
)
from app.services.anonymizer import anonymize
from app.services.categorizer import categorize
from app.services.ocr import OcrUnavailable, PdfTooLong, run_ocr
from app.services.openmed_pii import OpenMedUnavailable
from app.services.preprocess import UnsupportedFormat

logger = logging.getLogger(__name__)
router = APIRouter(tags=["extraction"])

ALLOWED_MIME = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/tiff",
    "image/heic",
    "image/heif",
    "application/pdf",
}

MAGIC_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"%PDF", "application/pdf"),
    (b"II*\x00", "image/tiff"),
    (b"MM\x00*", "image/tiff"),
)


def _sniff_mime(data: bytes, declared: str) -> str:
    """Contrôle du type réel du fichier à partir de sa signature binaire."""
    for signature, mime in MAGIC_SIGNATURES:
        if data.startswith(signature):
            return mime
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[4:8] == b"ftyp" and (
        b"heic" in data[8:24].lower() or b"heif" in data[8:24].lower() or b"mif1" in data[8:24].lower()
    ):
        return "image/heic"
    if declared in ALLOWED_MIME:
        return declared
    raise HTTPException(status_code=415, detail="Type de fichier réel non reconnu ou non autorisé.")


@router.post("/extract", response_model=ExtractionResponse)
async def extract_endpoint(file: UploadFile = File(...)) -> ExtractionResponse:
    request_id = uuid.uuid4().hex[:12]
    started = time.perf_counter()

    declared = (file.content_type or "").lower()
    if declared and declared not in ALLOWED_MIME:
        raise HTTPException(
            status_code=415,
            detail="Formats acceptés : JPEG, PNG, WEBP, TIFF, HEIC ou PDF.",
        )

    data = await file.read()
    size = len(data)
    if size == 0:
        raise HTTPException(status_code=400, detail="Fichier vide.")
    if size > settings.max_upload_size:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux (max {settings.max_upload_size // (1024 * 1024)} Mo).",
        )

    content_type = _sniff_mime(data, declared)
    warnings: list[str] = []

    try:
        # 1) OCR strictement local
        try:
            ocr = run_ocr(data, content_type)
        except UnsupportedFormat as exc:
            raise HTTPException(status_code=415, detail=str(exc)) from exc
        except PdfTooLong as exc:
            raise HTTPException(status_code=413, detail=str(exc)) from exc
        except OcrUnavailable as exc:
            raise HTTPException(status_code=503, detail=f"OCR local indisponible : {exc}") from exc

        warnings.extend(ocr.warnings)
        if not ocr.text.strip():
            warnings.append("Aucun texte détecté sur le document.")

        # 2) PII déterministe + OpenMed + union + anonymisation + safety sweep
        try:
            anon = anonymize(ocr.text)
        except OpenMedUnavailable as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Anonymisation locale indisponible (fail-closed) : {exc}",
            ) from exc

        warnings.extend(anon.warnings)

        # 3) Catégorisation uniquement sur le texte anonymisé, jamais si résidu critique
        if anon.safe_to_inject:
            fields_dict, cat_confidence, cat_warnings = categorize(anon.text)
            warnings.extend(cat_warnings)
        else:
            fields_dict = {}
            cat_confidence = 0.0
            warnings.append(
                "Catégorisation automatique bloquée : corrigez et validez le texte anonymisé manuellement."
            )

        response = ExtractionResponse(
            fields=ExtractedFields(**fields_dict) if fields_dict else ExtractedFields(),
            rawTextAnonymized=anon.text,
            entities=[
                Entity(type=e.type, placeholder=e.placeholder, source=e.source, confidence=e.confidence)
                for e in anon.entities
            ],
            confidence=ConfidenceBlock(
                ocr=ocr.confidence,
                anonymization=anon.confidence,
                categorization=cat_confidence,
            ),
            warnings=warnings,
            requiresHumanValidation=True,
            safeToInject=anon.safe_to_inject,
            debugRawText=ocr.text if settings.debug_raw_ocr_allowed else None,
        )
        return response
    finally:
        # Aucune persistance : on libère les octets et on journalise sans contenu.
        del data
        logger.info(
            "extract request_id=%s type=%s size=%s duration_ms=%s",
            request_id,
            content_type,
            size,
            int((time.perf_counter() - started) * 1000),
        )