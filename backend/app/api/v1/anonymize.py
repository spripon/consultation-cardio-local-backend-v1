"""Endpoint d'anonymisation de texte brut (texte -> texte anonymisé)."""

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.extraction import AnonymizeRequest, AnonymizeResponse, Entity
from app.services.anonymizer import anonymize
from app.services.openmed_pii import OpenMedUnavailable

logger = logging.getLogger(__name__)
router = APIRouter(tags=["anonymisation"])


@router.post("/anonymize", response_model=AnonymizeResponse)
def anonymize_endpoint(payload: AnonymizeRequest) -> AnonymizeResponse:
    try:
        result = anonymize(payload.text)
    except OpenMedUnavailable as exc:
        # Fail-closed : aucun repli externe.
        raise HTTPException(status_code=503, detail=f"Anonymisation locale indisponible : {exc}") from exc

    return AnonymizeResponse(
        textAnonymized=result.text,
        entities=[
            Entity(type=e.type, placeholder=e.placeholder, source=e.source, confidence=e.confidence)
            for e in result.entities
        ],
        warnings=result.warnings,
        confidence=result.confidence,
        requiresHumanValidation=True,
        safeToInject=result.safe_to_inject,
    )