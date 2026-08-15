"""Endpoint de catégorisation. N'accepte QUE du texte déjà anonymisé."""

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.extraction import CategorizeRequest, CategorizeResponse, ExtractedFields
from app.services.categorizer import categorize
from app.services.medaicr_rules import safety_sweep

logger = logging.getLogger(__name__)
router = APIRouter(tags=["catégorisation"])


@router.post("/categorize", response_model=CategorizeResponse)
def categorize_endpoint(payload: CategorizeRequest) -> CategorizeResponse:
    residues = safety_sweep(payload.textAnonymized)
    if residues:
        kinds = sorted({r.type for r in residues})
        raise HTTPException(
            status_code=422,
            detail=(
                "Le texte fourni contient des données identifiantes résiduelles "
                f"({', '.join(kinds)}). Anonymisez-le via /api/v1/anonymize avant catégorisation."
            ),
        )

    fields, confidence, warnings = categorize(payload.textAnonymized)
    return CategorizeResponse(
        fields=ExtractedFields(**fields),
        confidence=confidence,
        warnings=warnings,
        requiresHumanValidation=True,
    )