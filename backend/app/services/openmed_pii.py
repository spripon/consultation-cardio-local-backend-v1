"""Adaptateur local autour d'OpenMed 2.0 (détection PII par modèle, français).

API officielle utilisée :
    openmed.extract_pii(text, model_name=..., lang="fr",
                        confidence_threshold=..., use_smart_merging=True)
et lecture de `result.entities`.

Le module est tolérant à l'absence du paquet `openmed` au démarrage, mais
`/extract` et `/anonymize` échouent en 503 dès que OpenMed est requis
(obligatoire par défaut en production) : aucun repli cloud n'existe et aucun
repli silencieux sur la seule couche déterministe. Aucun téléchargement de
modèle n'est déclenché pendant une requête contenant des données patient : le
modèle doit être présent localement (`OPENMED_PII_MODEL`, par défaut
`/models/openmed-pii-fr`) et le hub est forcé hors-ligne.
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
    "PATIENT_NAME": "NAME",
    "NAME": "NAME",
    "FULL_NAME": "NAME",
    "LAST_NAME": "NAME",
    "LASTNAME": "NAME",
    "FAMILY_NAME": "NAME",
    "NOM": "NAME",
    "PERSON": "NAME",
    "PERSON_NAME": "NAME",
    "PER": "NAME",
    "FIRSTNAME": "FIRSTNAME",
    "FIRST_NAME": "FIRSTNAME",
    "GIVENNAME": "FIRSTNAME",
    "GIVEN_NAME": "FIRSTNAME",
    "PRENOM": "FIRSTNAME",
    "SURNAME": "NAME",
    "DOCTOR": "DOCTOR",
    "PHYSICIAN": "DOCTOR",
    "PROVIDER": "DOCTOR",
    "HEALTHCARE_PROVIDER": "DOCTOR",
    "STAFF": "DOCTOR",
    "HCW": "DOCTOR",
    "DATE_OF_BIRTH": "DOB",
    "DATEOFBIRTH": "DOB",
    "DOB": "DOB",
    "BIRTHDATE": "DOB",
    "BIRTH_DATE": "DOB",
    "PHONE": "PHONE",
    "PHONE_NUMBER": "PHONE",
    "TELEPHONE": "PHONE",
    "FAX": "PHONE",
    "CONTACT": "PHONE",
    "EMAIL": "EMAIL",
    "EMAIL_ADDRESS": "EMAIL",
    "ADDRESS": "ADDRESS",
    "STREET_ADDRESS": "ADDRESS",
    "ADRESSE": "ADDRESS",
    "LOCATION": "ADDRESS",
    "STREET": "ADDRESS",
    "ZIP": "ADDRESS",
    "ZIPCODE": "ADDRESS",
    "POSTCODE": "ADDRESS",
    "POSTAL_CODE": "ADDRESS",
    "CITY": "ADDRESS",
    "COUNTRY": "ADDRESS",
    "HOSPITAL": "ADDRESS",
    "ORGANIZATION": "ADDRESS",
    "ID": "ID",
    "IDNUM": "ID",
    "ID_NUMBER": "ID",
    "NATIONAL_ID": "NIR",
    "NIR": "NIR",
    "MEDICALRECORD": "IPP",
    "MEDICAL_RECORD_NUMBER": "IPP",
    "MEDICAL_RECORD": "IPP",
    "MRN": "IPP",
    "IPP": "IPP",
    "SSN": "NIR",
    "SOCIAL_SECURITY_NUMBER": "NIR",
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
    if settings.openmed_offline:
        os.environ.setdefault("OPENMED_OFFLINE", "1")


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
            score = float(entity.get("confidence") or entity.get("score") or 0.8)
        else:  # objets typés côté openmed
            label = str(
                getattr(entity, "label", None)
                or getattr(entity, "entity_group", None)
                or getattr(entity, "type", None)
                or "ID"
            )
            value = str(
                getattr(entity, "text", None)
                or getattr(entity, "word", None)
                or getattr(entity, "value", None)
                or ""
            )
            score = float(
                getattr(entity, "confidence", None) or getattr(entity, "score", None) or 0.8
            )
        key = label.upper().replace("B-", "").replace("I-", "").replace(" ", "_")
        # Un label inconnu n'est JAMAIS ignoré : il est rédigé de façon conservatrice.
        pii_type = LABEL_MAP.get(key, "ID")
        value = value.strip()
        if value:
            findings.append(Finding(type=pii_type, value=value, confidence=round(score, 3), source="openmed"))
    return findings


def detect_pii(text: str) -> list[Finding]:
    """Détection PII par modèle local. Lève OpenMedUnavailable si absent."""
    openmed = get_engine()

    # API officielle OpenMed 2.0.
    if hasattr(openmed, "extract_pii"):
        result = openmed.extract_pii(  # type: ignore[attr-defined]
            text,
            model_name=settings.openmed_pii_model,
            lang=settings.openmed_language,
            confidence_threshold=settings.openmed_confidence_threshold,
            use_smart_merging=True,
        )
        if isinstance(result, dict):
            entities = result.get("entities")
        else:
            entities = getattr(result, "entities", None)
        if entities is None:
            raise OpenMedUnavailable("réponse OpenMed inattendue : `entities` absent")
        return _normalise_entities(entities)

    raise OpenMedUnavailable("API openmed inattendue : `extract_pii` introuvable")