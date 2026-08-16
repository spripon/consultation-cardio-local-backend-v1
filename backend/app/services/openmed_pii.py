"""Adaptateur local autour d'OpenMed 2.0 (détection PII par modèle, français).

Le modèle OpenMed est utilisé comme seconde couche après les règles déterministes.
Cette couche est volontairement CONSERVATRICE vis-à-vis des valeurs cliniques :
un label modèle seul ne suffit pas à transformer n'importe quel nombre en ID.

Principes de filtrage :
  * labels OpenMed inconnus -> ignorés (plus de fallback automatique vers [ID]);
  * DOB/IPP/ID/téléphone/NIR numériques -> validation de forme et/ou contexte;
  * valeurs cliniques (dose, TA, FC, poids, FE, dimensions, biologie...) -> conservées;
  * LOCATION/HOSPITAL/ORGANIZATION/CITY/COUNTRY -> non assimilés automatiquement
    à l'adresse personnelle du patient;
  * aucune donnée n'est journalisée, aucun téléchargement au runtime.
"""

from __future__ import annotations

import logging
import os
import re
import threading
from dataclasses import dataclass
from pathlib import Path

from app.config import settings
from app.services.medaicr_rules import Finding

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_STATE: dict[str, object] = {"loaded": False, "engine": None, "error": None}

# Correspondance EXPLICITE uniquement. Un label inconnu n'est plus transformé
# automatiquement en ID : c'était la cause principale du sur-masquage de nombres
# cliniques (FE, TA, poids, doses, DFG, fréquence, dimensions, etc.).
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
    "STREET": "ADDRESS",
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

# Ces catégories peuvent être pertinentes pour d'autres politiques de
# dé-identification, mais ne correspondent pas à une donnée identifiante directe
# du patient dans notre politique cardio. Les transformer en ADDRESS/ID détruit
# inutilement le contenu clinique (établissement, marque, année, lieu de soin...).
IGNORED_LABELS = {
    "LOCATION",
    "LOC",
    "CITY",
    "COUNTRY",
    "ZIP",
    "ZIPCODE",
    "POSTCODE",
    "POSTAL_CODE",
    "HOSPITAL",
    "ORGANIZATION",
    "ORGANISATION",
    "FACILITY",
    "HEALTHCARE_FACILITY",
    "DATE",
    "AGE",
    "SEX",
    "GENDER",
}

_DOB_RE = re.compile(r"\b\d{1,2}[/\-.]\d{1,2}[/\-.](?:19|20)\d{2}\b")
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
_PHONE_RE = re.compile(r"^(?:(?:\+|00)33[ .\-]?[1-9]|0[1-9])(?:[ .\-]?\d{2}){4}$")
_NIR_RE = re.compile(r"^[12][ .]?\d{2}[ .]?\d{2}[ .]?\d{2,3}[ .]?\d{2,3}[ .]?\d{3}(?:[ .]?\d{2})?$")

_BIRTH_CONTEXT_RE = re.compile(
    r"(?:date\s+de\s+naissance|n[ée]e?\s+le|dob|birth\s*date)", re.IGNORECASE
)
_ID_CONTEXT_RE = re.compile(
    r"(?:\bipp\b|\bmrn\b|\bnda\b|identifiant\s+(?:patient|dossier)|"
    r"n[°ºo]?\s*(?:de\s*)?(?:dossier|patient|s[ée]jour)|num[ée]ro\s+(?:de\s+)?dossier|"
    r"patient\s*id|id\s*patient|n[°ºo]?\s*s[ée]jour)",
    re.IGNORECASE,
)
_ADDRESS_CONTEXT_RE = re.compile(
    r"(?:\badresse\b|\bdomicile\b|\bdemeurant\b|\brue\b|\bavenue\b|\bav\.\b|"
    r"\bboulevard\b|\bbd\b|\bimpasse\b|\ball[ée]e\b|\bchemin\b|\bplace\b|\broute\b)",
    re.IGNORECASE,
)

# Hints volontairement larges : si un nombre est voisin d'un contexte clinique,
# on préfère le conserver. Les identifiants directs restent couverts par les
# règles déterministes et par les validateurs spécifiques ci-dessus.
_CLINICAL_CONTEXT_RE = re.compile(
    r"(?:\bmg\b|\bµg\b|\bug\b|\bg\b|\bkg\b|\bml\b|\bmmhg\b|\bbpm\b|/\s*min(?:ute)?|"
    r"\bmm\b|\bcm2?\b|\bm2\b|\b%\b|\bmmol\b|\bmmol/l\b|\bµmol\b|\bumol\b|"
    r"\bmg/l\b|\bg/l\b|\bml/min\b|\bdfg\b|cr[ée]atinin|kali[ée]m|glyc[ée]m|"
    r"\bldl\b|\bhdl\b|albumin|\brac\b|\bta\b|tension|\bpoids\b|\bfc\b|fr[ée]quence|"
    r"\bfevg\b|\bfe\b|\bpaps\b|\bdtd\b|septal|paroi|oreillette|ventricul|"
    r"seuil|imp[ée]dance|d[ée]tection|stimulation|dose|comprim[ée]|\bcp\b|g[ée]lule|\bgel\b|"
    r"matin|soir|rythme|flutter|sinusal|bloc|repolarisation)",
    re.IGNORECASE,
)


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
    except Exception as exc:  # pragma: no cover
        raise OpenMedUnavailable(f"paquet openmed indisponible ({exc.__class__.__name__})") from exc

    if model_path.startswith("/") and not Path(model_path).exists():
        raise OpenMedUnavailable(
            "modèle PII local absent : exécutez scripts/download_openmed_model.py avant utilisation"
        )

    _warmup(openmed)
    return openmed


WARMUP_TEXT = "Le patient X a consulté le service de cardiologie."


def _warmup(openmed) -> None:
    if not hasattr(openmed, "extract_pii"):
        raise OpenMedUnavailable("API openmed inattendue : `extract_pii` introuvable")
    try:
        result = openmed.extract_pii(  # type: ignore[attr-defined]
            WARMUP_TEXT,
            model_name=settings.openmed_pii_model,
            lang=settings.openmed_language,
            confidence_threshold=settings.openmed_confidence_threshold,
            use_smart_merging=True,
        )
    except Exception as exc:  # pragma: no cover
        raise OpenMedUnavailable(
            f"chargement du modèle PII local impossible ({exc.__class__.__name__})"
        ) from exc

    entities = result.get("entities") if isinstance(result, dict) else getattr(result, "entities", None)
    if entities is None:
        raise OpenMedUnavailable("réponse OpenMed inattendue au warm-up : `entities` absent")


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


def _normalise_label(label: str) -> str:
    return (
        label.upper()
        .replace("B-", "")
        .replace("I-", "")
        .replace(" ", "_")
        .replace("-", "_")
    )


def _entity_fields(entity) -> tuple[str, str, float, int | None, int | None]:
    if isinstance(entity, dict):
        label = str(entity.get("entity_group") or entity.get("label") or entity.get("type") or "")
        value = str(entity.get("word") or entity.get("text") or entity.get("value") or "")
        score = float(entity.get("confidence") or entity.get("score") or 0.8)
        start = entity.get("start")
        end = entity.get("end")
    else:
        label = str(
            getattr(entity, "label", None)
            or getattr(entity, "entity_group", None)
            or getattr(entity, "type", None)
            or ""
        )
        value = str(
            getattr(entity, "text", None)
            or getattr(entity, "word", None)
            or getattr(entity, "value", None)
            or ""
        )
        score = float(getattr(entity, "confidence", None) or getattr(entity, "score", None) or 0.8)
        start = getattr(entity, "start", None)
        end = getattr(entity, "end", None)
    return label, value.strip(), score, start if isinstance(start, int) else None, end if isinstance(end, int) else None


def _context_for(text: str, value: str, start: int | None, end: int | None, window: int = 60) -> str:
    if start is None or end is None or start < 0 or end < start or end > len(text):
        idx = text.lower().find(value.lower()) if value else -1
        if idx < 0:
            return ""
        start, end = idx, idx + len(value)
    return text[max(0, start - window): min(len(text), end + window)]


def _contains_digit(value: str) -> bool:
    return any(ch.isdigit() for ch in value)


def _looks_like_person_name(value: str) -> bool:
    if len(value) < 2 or len(value) > 80 or _contains_digit(value):
        return False
    return bool(re.search(r"[A-Za-zÀ-ÖØ-öø-ÿ]", value))


def _looks_clinical_numeric(value: str, context: str) -> bool:
    if not _contains_digit(value):
        return False
    if _CLINICAL_CONTEXT_RE.search(context):
        return True
    # Une valeur courte purement numérique/mesure sans contexte d'identifiant est
    # bien plus probablement clinique qu'un identifiant administratif.
    compact = re.sub(r"\s+", "", value)
    return bool(re.fullmatch(r"\d{1,4}(?:[.,]\d{1,4})?(?:/\d{1,4})?%?", compact))


def _accept_entity(pii_type: str, value: str, context: str) -> bool:
    """Garde seulement les entités suffisamment plausibles pour être du PII direct."""
    if not value or "[" in value or "]" in value:
        return False

    if pii_type in {"NAME", "FIRSTNAME"}:
        return _looks_like_person_name(value)

    if pii_type == "DOCTOR":
        return settings.redact_doctor_names and _looks_like_person_name(value)

    if pii_type == "EMAIL":
        return bool(_EMAIL_RE.fullmatch(value))

    if pii_type == "PHONE":
        return bool(_PHONE_RE.fullmatch(value))

    if pii_type == "NIR":
        return bool(_NIR_RE.fullmatch(value))

    if pii_type == "DOB":
        # Une TA 120/80 ou une année clinique 2018 ne peut plus devenir DOB.
        return bool(_DOB_RE.fullmatch(value)) and bool(_BIRTH_CONTEXT_RE.search(context))

    if pii_type in {"IPP", "ID"}:
        # Ne jamais masquer un nombre clinique simplement parce que le modèle l'a
        # étiqueté ID. Un contexte administratif explicite est obligatoire.
        if _looks_clinical_numeric(value, context):
            return False
        return bool(_ID_CONTEXT_RE.search(context))

    if pii_type == "ADDRESS":
        # Une adresse personnelle doit contenir du texte/adressage plausible.
        # Un simple nombre, une année ou une mesure ne suffit jamais.
        if _looks_clinical_numeric(value, context):
            return False
        if not re.search(r"[A-Za-zÀ-ÖØ-öø-ÿ]", value):
            return False
        return bool(_ADDRESS_CONTEXT_RE.search(value) or _ADDRESS_CONTEXT_RE.search(context))

    return False


def _normalise_entities(raw_entities, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for entity in raw_entities or []:
        label, value, score, start, end = _entity_fields(entity)
        key = _normalise_label(label)

        # Label volontairement non utilisé dans notre politique cardio.
        if key in IGNORED_LABELS:
            continue

        pii_type = LABEL_MAP.get(key)
        if pii_type is None:
            # IMPORTANT : plus de fallback vers ID pour un label inconnu.
            continue

        context = _context_for(text, value, start, end)
        if not _accept_entity(pii_type, value, context):
            continue

        findings.append(
            Finding(
                type=pii_type,
                value=value,
                confidence=round(score, 3),
                source="openmed",
            )
        )
    return findings


def detect_pii(text: str) -> list[Finding]:
    """Détection PII par modèle local, puis filtre anti-sur-masquage clinique."""
    openmed = get_engine()

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
        return _normalise_entities(entities, text)

    raise OpenMedUnavailable("API openmed inattendue : `extract_pii` introuvable")
