"""Endpoint de catégorisation. N'accepte QUE du texte déjà anonymisé.

Sécurité : un appelant direct (hors UI) ne doit pas pouvoir contourner la
couche modèle. Le texte reçu est donc SYSTÉMATIQUEMENT repassé par le pipeline
`anonymize()` complet, avec la politique OpenMed du runtime (obligatoire en
production). Cela peut dupliquer une inférence déjà faite par le workflow UI :
choix assumé, la sécurité primant sur le coût CPU.
"""

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.extraction import CategorizeRequest, CategorizeResponse, ExtractedFields
from app.services.anonymizer import anonymize
from app.services.categorizer import categorize
from app.services.openmed_pii import OpenMedUnavailable

logger = logging.getLogger(__name__)
router = APIRouter(tags=["catégorisation"])


@router.post("/categorize", response_model=CategorizeResponse)
def categorize_endpoint(payload: CategorizeRequest) -> CategorizeResponse:
    try:
        revalidated = anonymize(payload.textAnonymized)
    except OpenMedUnavailable:
        # Fail-closed : jamais de catégorisation sans le modèle PII local requis.
        raise HTTPException(
            status_code=503,
            detail=(
                "Modèle PII local indisponible : la catégorisation est refusée. "
                "Aucun service externe n'est utilisé."
            ),
        ) from None

    modified = revalidated.text != payload.textAnonymized
    if modified or not revalidated.safe_to_inject:
        kinds = sorted({e.type for e in revalidated.entities} | {r.type for r in revalidated.residues})
        raise HTTPException(
            status_code=422,
            detail=(
                "Le texte fourni contient des données identifiantes résiduelles "
                f"({', '.join(kinds) or 'non typées'}). Anonymisez-le via "
                "/api/v1/anonymize avant catégorisation."
            ),
        )

    fields, confidence, warnings = categorize(payload.textAnonymized)
    return CategorizeResponse(
        fields=ExtractedFields(**fields),
        confidence=confidence,
        warnings=warnings,
        requiresHumanValidation=True,
    )
