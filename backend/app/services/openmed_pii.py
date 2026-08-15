"""Adaptateur local autour d'OpenMed 2.0 (détection PII par modèle).

Le module est tolérant à l'absence du paquet `openmed` au démarrage, mais
`/extract` échoue en production si `REQUIRE_OPENMED=true` : aucun repli cloud
n'existe. Aucun téléchargement de modèle n'est déclenché pendant une requête
contenant des données patient ; le modèle doit être présent localement
(`OPENMED_PII_MODEL`, par défaut `/models/openmed-pii`) et le hub est forcé en
mode hors-ligne.
"""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass
from pathlib import Path

from app.config import settings
from app.services.medaicr_rules import Finding

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_STATE: dict[str, object] = {"loaded": False, "engine": None, "error": None}

#: Correspondance des étiquettes OpenMed / HF vers nos types internes.
LABEL_MAP = {
    "PATIENT": "NAME",
    "NAME": "NAME",
    "PERSON": "NAME",
    "PER": "NAME",
    "FIRSTNAME": "FIRSTNAME",
    "GIVENNAME": "FIRSTNAME",
    "SURNAME": "NAME",
    "DOCTOR": "DOCTOR",
    "HCW": "DOCTOR",
    "DATE_OF_BIRTH": "DOB",
    "DOB": "DOB",
    "BIRTHDATE": "DOB",
    "PHONE": "PHONE",
    "PHONE_NUMBER": "PHONE",
    "CONTACT": "PHONE",
    "EMAIL": "EMAIL",
    "ADDRESS": "ADDRESS",
    "LOCATION": "ADDRESS",
    "STREET": "ADDRESS",
    "ZIP": "ADDRESS",
    "CITY": "ADDRESS",
    "ID": "ID",
    "IDNUM": "ID",
    "MEDICALRECORD": "IPP",
    "MRN": "IPP",
    "SSN": "NIR",
    "SOCIALSECURITY": "NIR",
}


class OpenMedUnavailable(RuntimeError):
    """Le moteur OpenMed local n'est pas disponible."""


@dataclass
class OpenMedStatus:
    available: bool
    reason: str | None = None


def _force_offline() -> None:
    if settings.hf_hub_offline:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


def _load_engine():
    """Charge (une seule fois) le moteur OpenMed local. Jamais de téléchargement."""
    _force_offline()
    model_path = settings.openmed_pii_model

    try:
        import openmed  # type: ignore
    except Exception as exc:  # pragma: no cover - dépend de l'environnement
        raise OpenMedUnavailable(f"paquet openmed indisponible ({exc.__class__.__name__})") from exc

    # Un chemin local est exigé lorsqu'il ressemble à un répertoire de modèle.
    if model_path.startswith("/") and not Path(model_path).exists():
        raise OpenMedUnavailable(
            "modèle PII local absent : exécutez scripts/download_openmed_model.py avant utilisation"
        )

    return openmed


def get_engine():
    with _LOCK:
        if not _STATE["loaded"]:
            try:
                _STATE["engine"] = _load_engine()
                _STATE["error"] = None
            except OpenMedUnavailable as exc:
                _STATE["engine"] = None
                _STATE["error"] = str(exc)
            _STATE["loaded"] = True
    if _STATE["engine"] is None:
        raise OpenMedUnavailable(str(_STATE["error"] or "moteur OpenMed indisponible"))
    return _STATE["engine"]


def status() -> OpenMedStatus:
    try:
        get_engine()
    except OpenMedUnavailable as exc:
        return OpenMedStatus(available=False, reason=str(exc))
    return OpenMedStatus(available=True)


def _normalise_entities(raw_entities) -> list[Finding]:
    findings: list[Finding] = []
    for entity in raw_entities or []:
        if isinstance(entity, dict):
            label = str(entity.get("entity_group") or entity.get("label") or entity.get("type") or "ID")
            value = str(entity.get("word") or entity.get("text") or entity.get("value") or "")
            score = float(entity.get("score") or entity.get("confidence") or 0.8)
        else:  # objets typés côté openmed
            label = str(getattr(entity, "label", getattr(entity, "type", "ID")))
            value = str(getattr(entity, "text", getattr(entity, "value", "")))
            score = float(getattr(entity, "score", 0.8) or 0.8)
        key = label.upper().replace("B-", "").replace("I-", "").replace(" ", "_")
        pii_type = LABEL_MAP.get(key, "ID")
        value = value.strip()
        if value:
            findings.append(Finding(type=pii_type, value=value, confidence=round(score, 3), source="openmed"))
    return findings


def detect_pii(text: str) -> list[Finding]:
    """Détection PII par modèle local. Lève OpenMedUnavailable si absent."""
    openmed = get_engine()
    policy = settings.openmed_policy
    model = settings.openmed_pii_model

    # L'API OpenMed 2.0 expose `deidentify` et/ou `extract_pii` selon la version.
    if hasattr(openmed, "extract_pii"):
        raw = openmed.extract_pii(text, model=model, policy=policy)  # type: ignore[attr-defined]
        entities = raw.get("entities") if isinstance(raw, dict) else raw
        return _normalise_entities(entities)

    if hasattr(openmed, "deidentify"):
        raw = openmed.deidentify(text, model=model, policy=policy)  # type: ignore[attr-defined]
        if isinstance(raw, dict):
            return _normalise_entities(raw.get("entities"))
        return _normalise_entities(getattr(raw, "entities", []))

    raise OpenMedUnavailable("API openmed inattendue : ni extract_pii ni deidentify")