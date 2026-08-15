"""Pipeline d'anonymisation : déterministe -> OpenMed -> union -> safety sweep."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.config import settings
from app.services import medaicr_rules as rules
from app.services.medaicr_rules import Finding
from app.services.openmed_pii import OpenMedUnavailable, detect_pii

logger = logging.getLogger(__name__)


@dataclass
class AnonymizationResult:
    text: str
    entities: list[Finding] = field(default_factory=list)
    residues: list[Finding] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    confidence: float = 0.0
    safe_to_inject: bool = True

    @property
    def has_critical_warning(self) -> bool:
        return any(w.startswith("CRITICAL") for w in self.warnings)


def _union(deterministic: list[Finding], model: list[Finding]) -> list[Finding]:
    merged: dict[tuple[str, str], Finding] = {}
    for finding in [*deterministic, *model]:
        key = (finding.type, finding.value.lower())
        existing = merged.get(key)
        if existing is None or finding.confidence > existing.confidence:
            merged[key] = finding
    ordered = sorted(merged.values(), key=lambda f: len(f.value), reverse=True)
    return ordered


def anonymize(text: str, *, require_openmed: bool | None = None) -> AnonymizationResult:
    """Anonymise un texte. Ne journalise jamais le contenu."""
    require = settings.openmed_required if require_openmed is None else require_openmed
    warnings: list[str] = []

    deterministic = rules.find_pii(text, redact_doctors=settings.redact_doctor_names)

    model_findings: list[Finding] = []
    try:
        model_findings = detect_pii(text)
    except OpenMedUnavailable as exc:
        message = f"Modèle PII local OpenMed indisponible : {exc}"
        if require:
            # Fail-closed : aucun repli externe n'est autorisé.
            raise
        warnings.append(f"WARNING {message} — seule la couche déterministe a été appliquée.")

    entities = _union(deterministic, model_findings)
    redacted = rules.apply_findings(text, entities)
    if settings.strict_policy:
        redacted = rules.strip_age_and_sex(redacted)

    residues = rules.safety_sweep(redacted)
    safe_to_inject = True
    if residues:
        kinds = sorted({r.type for r in residues})
        warnings.append(
            "CRITICAL Résidus potentiellement identifiants détectés après anonymisation "
            f"({', '.join(kinds)}). Validation manuelle obligatoire avant injection."
        )
        safe_to_inject = False

    if not model_findings:
        confidence = 0.6 if entities else 0.5
    else:
        confidence = 0.9
    if residues:
        confidence = min(confidence, 0.3)
    if not text.strip():
        confidence = 0.0

    return AnonymizationResult(
        text=redacted,
        entities=entities,
        residues=residues,
        warnings=warnings,
        confidence=round(confidence, 2),
        safe_to_inject=safe_to_inject,
    )