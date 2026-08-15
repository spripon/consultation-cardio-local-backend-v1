"""Règles déterministes inspirées de MedAiCR (« MedAiCR-derived deterministic rules »).

Ce module N'EST PAS le paquet MedAiCR complet (qui comporte notamment la
rédaction PDF par zones, un watcher de dossiers et un LLM optionnel) : il en
reprend uniquement la couche déterministe de détection d'identifiants, adaptée
à la cardiologie. Aucun LLM MedAiCR externe n'est activé dans cette variante.

Principes reproduits :
  * extraction par étiquettes (« Nom : », « IPP : », « Né le ») ;
  * regex de sécurité (email, téléphone FR, NIR, IPP/MRN, adresse, Dr/Pr) ;
  * remplacement GLOBAL insensible à la casse de chaque valeur trouvée, afin
    d'attraper les répétitions en en-tête / pied de page ;
  * politique cardio par défaut : l'âge, le sexe et les dates cliniques
    ordinaires sont conservés (contrairement à une politique « tout supprimer »).

Aucune donnée n'est journalisée par ce module.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

TOKENS: dict[str, str] = {
    "NAME": "[NOM]",
    "FIRSTNAME": "[PRENOM]",
    "DOB": "[DATE_NAISSANCE]",
    "IPP": "[IPP]",
    "NIR": "[NIR]",
    "PHONE": "[TELEPHONE]",
    "EMAIL": "[EMAIL]",
    "ADDRESS": "[ADRESSE]",
    "DOCTOR": "[MEDECIN]",
    "ID": "[ID]",
}

#: Types dont un résidu constitue une fuite à haut risque (identifiants directs).
HIGH_RISK_TYPES = {
    "NIR",
    "EMAIL",
    "PHONE",
    "DOB",
    "IPP",
    "ID",
    "NAME",
    "FIRSTNAME",
    "ADDRESS",
    "DOCTOR",
}

#: Types soumis au filtre de plausibilité onomastique lors du balayage final.
_NAME_LIKE_TYPES = {"NAME", "FIRSTNAME", "DOCTOR"}

_NAME_CHARS = r"A-Za-zÀ-ÖØ-öø-ÿ'’\-"
#: Séparateur intra-valeur : espaces horizontaux uniquement. Un motif ne doit
#: JAMAIS traverser un retour à la ligne, sinon la valeur capturée engloutit
#: l'étiquette suivante et masque des champs entiers du compte rendu.
_INLINE_SPACE = r"[ \t]+"

# --- Regex directes (valeur capturée dans le groupe 1 quand nécessaire) ---
DIRECT_PATTERNS: list[tuple[str, re.Pattern[str], float]] = [
    (
        "EMAIL",
        re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"),
        0.99,
    ),
    (
        "NIR",
        re.compile(r"\b[12][\s.]?\d{2}[\s.]?\d{2}[\s.]?\d{2,3}[\s.]?\d{2,3}[\s.]?\d{3}(?:[\s.]?\d{2})?\b"),
        0.97,
    ),
    (
        "PHONE",
        re.compile(r"(?:(?:\+|00)33[\s.\-]?[1-9]|0[1-9])(?:[\s.\-]?\d{2}){4}\b"),
        0.95,
    ),
    (
        "ADDRESS",
        re.compile(
            r"\b\d{1,4}\s?(?:bis|ter)?\s*(?:rue|avenue|av\.|boulevard|bd|impasse|allée|allee|chemin|place|route|quai|lotissement|résidence|residence)"
            rf"[ \t{_NAME_CHARS}0-9,.']{{2,60}}",
            re.IGNORECASE,
        ),
        0.85,
    ),
    (
        "ADDRESS",
        re.compile(
            r"\b\d{5}[ \t]+[A-ZÀ-Ö][A-Za-zÀ-ÖØ-öø-ÿ'’\-]{1,30}"
            r"(?:[ \t\-][A-ZÀ-Öa-z][A-Za-zÀ-ÖØ-öø-ÿ'’\-]{1,30})?"
        ),
        0.7,
    ),
]

# --- Extraction par étiquettes : (type, regex avec groupe 1 = valeur, confiance) ---
LABEL_PATTERNS: list[tuple[str, re.Pattern[str], float]] = [
    (
        "DOB",
        re.compile(
            r"(?:date\s+de\s+naissance|né[e]?\s+le|nee\s+le|dob|d\.o\.b\.?|birth\s*date)"
            r"\s*[:\-]?\s*(\d{1,2}[/\-. ]\d{1,2}[/\-. ](?:19|20)?\d{2})",
            re.IGNORECASE,
        ),
        0.97,
    ),
    (
        "IPP",
        re.compile(
            r"(?:ipp|mrn|n[°ºo]?\s*(?:de\s*)?(?:dossier|patient)|num[ée]ro\s+(?:de\s+)?dossier|identifiant\s+patient)"
            r"\s*[:\-]?\s*([A-Z]{0,3}[\-]?\d{3,12})",
            re.IGNORECASE,
        ),
        0.95,
    ),
    (
        "ID",
        re.compile(r"(?:id\s*patient|patient\s*id|nda|n[°ºo]\s*s[ée]jour)\s*[:\-]?\s*([A-Z0-9\-]{3,15})", re.IGNORECASE),
        0.9,
    ),
    (
        "NAME",
        re.compile(
            rf"(?:nom{_INLINE_SPACE}de{_INLINE_SPACE}famille|nom{_INLINE_SPACE}patient|nom|patient|patiente)"
            rf"[ \t]*[:\-][ \t]*([{_NAME_CHARS}]{{2,30}}(?:{_INLINE_SPACE}[{_NAME_CHARS}]{{2,30}})?)",
            re.IGNORECASE,
        ),
        0.9,
    ),
    (
        "FIRSTNAME",
        re.compile(rf"(?:pr[ée]nom)[ \t]*[:\-][ \t]*([{_NAME_CHARS}]{{2,30}})", re.IGNORECASE),
        0.9,
    ),
    (
        "ADDRESS",
        re.compile(r"(?:adresse|domicile|demeurant)\s*[:\-]\s*([^\n]{5,80})", re.IGNORECASE),
        0.9,
    ),
    (
        "PHONE",
        re.compile(r"(?:t[ée]l(?:[ée]phone)?|portable|mobile)\s*[:\-]?\s*([+0-9][0-9\s.\-]{7,20})", re.IGNORECASE),
        0.93,
    ),
    (
        "DOCTOR",
        re.compile(
            rf"\b(?:Dr|Dr\.|Docteur|Pr|Pr\.|Professeur)[ \t]+"
            rf"((?:[{_NAME_CHARS}]{{2,30}})(?:{_INLINE_SPACE}[{_NAME_CHARS}]{{2,30}})?)"
        ),
        0.85,
    ),
]

#: Mots qui ne doivent jamais être considérés comme un nom de patient.
STOPWORDS = {
    "monsieur",
    "madame",
    "mr",
    "mme",
    "m",
    "le",
    "la",
    "les",
    "de",
    "du",
    "des",
    "ans",
    "an",
    "homme",
    "femme",
    "masculin",
    "feminin",
    "féminin",
    "consultation",
    "cardiologie",
    "compte",
    "rendu",
    "docteur",
    "hopital",
    "hôpital",
    "clinique",
    "service",
    "inconnu",
}


@dataclass
class Finding:
    """Une occurrence de donnée identifiante trouvée dans le texte."""

    type: str
    value: str
    confidence: float
    source: str = "deterministic"

    @property
    def placeholder(self) -> str:
        return TOKENS.get(self.type, "[ID]")


@dataclass
class RulesResult:
    text: str
    findings: list[Finding] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _strip_accents(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", value) if unicodedata.category(c) != "Mn")


def _clean_value(raw: str) -> str:
    value = raw.strip().strip(".,;:()[]\u2013-").strip()
    return re.sub(r"\s{2,}", " ", value)


def _is_plausible_name(value: str) -> bool:
    if len(value) < 3:
        return False
    words = [w for w in re.split(r"\s+", value) if w]
    if not words:
        return False
    for word in words:
        if _strip_accents(word).lower() in STOPWORDS:
            return False
    return not any(char.isdigit() for char in value)


def find_pii(text: str, *, redact_doctors: bool = True) -> list[Finding]:
    """Retourne les données identifiantes détectées par la couche déterministe."""
    findings: list[Finding] = []
    seen: set[tuple[str, str]] = set()

    def add(pii_type: str, value: str, confidence: float) -> None:
        # Un fragment contenant déjà un jeton d'anonymisation (« [ADRESSE] ») est
        # du texte DÉJÀ masqué : le re-détecter casserait l'idempotence de la
        # revalidation (le texte serait « modifié » sans nouvelle fuite).
        if "[" in value or "]" in value:
            return
        value = _clean_value(value)
        if not value:
            return
        if pii_type in {"NAME", "FIRSTNAME", "DOCTOR"} and not _is_plausible_name(value):
            return
        key = (pii_type, value.lower())
        if key in seen:
            return
        seen.add(key)
        findings.append(Finding(type=pii_type, value=value, confidence=confidence))

    for pii_type, pattern, confidence in LABEL_PATTERNS:
        if pii_type == "DOCTOR" and not redact_doctors:
            continue
        for match in pattern.finditer(text):
            add(pii_type, match.group(1), confidence)

    for pii_type, pattern, confidence in DIRECT_PATTERNS:
        for match in pattern.finditer(text):
            add(pii_type, match.group(0), confidence)

    # Les valeurs les plus longues d'abord : évite les remplacements partiels.
    findings.sort(key=lambda f: len(f.value), reverse=True)
    return findings


def apply_findings(text: str, findings: list[Finding]) -> str:
    """Remplace globalement (insensible à la casse) chaque valeur par son jeton."""
    redacted = text
    for finding in findings:
        value = finding.value
        if not value or value.startswith("["):
            continue
        # Tolère des espaces multiples/retours ligne entre les mots de la valeur.
        flexible = r"\s+".join(re.escape(part) for part in value.split())
        redacted = re.sub(flexible, finding.placeholder, redacted, flags=re.IGNORECASE)
    return redacted


def strip_age_and_sex(text: str) -> str:
    """Politique stricte uniquement : retire âge, sexe et dates résiduelles."""
    text = re.sub(r"\b\d{1,3}\s*ans\b", "[AGE]", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:homme|femme|masculin|f[ée]minin)\b", "[SEXE]", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\d{1,2}[/\-.]\d{1,2}[/\-.](?:19|20)?\d{2}\b", "[DATE]", text)
    return text


def deterministic_anonymize(text: str, *, redact_doctors: bool = True, strict: bool = False) -> RulesResult:
    findings = find_pii(text, redact_doctors=redact_doctors)
    redacted = apply_findings(text, findings)
    if strict:
        redacted = strip_age_and_sex(redacted)
    return RulesResult(text=redacted, findings=findings)


def safety_sweep(text: str) -> list[Finding]:
    """Recherche des résidus évidents après anonymisation (fail-closed)."""
    residues: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    for pii_type, pattern, confidence in DIRECT_PATTERNS:
        if pii_type not in HIGH_RISK_TYPES:
            continue
        for match in pattern.finditer(text):
            raw = match.group(0)
            # Un fragment contenant déjà un jeton d'anonymisation n'est pas un
            # résidu : c'est du texte déjà masqué (ex. « [ADRESSE] »). Le test
            # porte sur la chaîne BRUTE, avant nettoyage des crochets.
            if "[" in raw or "]" in raw:
                continue
            value = _clean_value(raw)
            if not value:
                continue
            if pii_type in _NAME_LIKE_TYPES and not _is_plausible_name(value):
                continue
            key = (pii_type, value.lower())
            if key in seen:
                continue
            seen.add(key)
            residues.append(Finding(type=pii_type, value=value, confidence=confidence, source="safety_sweep"))
    for pii_type, pattern, confidence in LABEL_PATTERNS:
        if pii_type not in HIGH_RISK_TYPES:
            continue
        for match in pattern.finditer(text):
            raw = match.group(1)
            # Valeur déjà masquée (« Adresse : [ADRESSE] ») : ce n'est pas un résidu.
            if "[" in raw or "]" in raw:
                continue
            value = _clean_value(raw)
            if not value:
                continue
            if pii_type in _NAME_LIKE_TYPES and not _is_plausible_name(value):
                continue
            key = (pii_type, value.lower())
            if key in seen:
                continue
            seen.add(key)
            residues.append(Finding(type=pii_type, value=value, confidence=confidence, source="safety_sweep"))
    return residues