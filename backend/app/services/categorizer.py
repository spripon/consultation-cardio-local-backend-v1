"""Catégorisation déterministe d'un compte-rendu ANONYMISÉ en 8 rubriques.

Aucun LLM n'est appelé : titres explicites FR/EN, puis repli par mots-clés
cardiologiques. Le texte est repris tel quel (aucune reformulation, aucun
diagnostic ajouté).
"""

from __future__ import annotations

import re
import unicodedata

FIELDS = (
    "previousHistory",
    "currentTreatment",
    "interrogation",
    "clinicalExamination",
    "ecg",
    "lastBiologyResults",
    "conclusion",
    "treatmentPlan",
)

#: Titres de section reconnus (texte sans accents, en minuscules).
HEADERS: list[tuple[str, tuple[str, ...]]] = [
    ("previousHistory", ("antecedents", "antecedent", "atcd", "history", "past medical history", "comorbidites")),
    (
        "currentTreatment",
        (
            "traitement actuel",
            "traitement habituel",
            "traitement en cours",
            "traitements",
            "traitement",
            "medicaments",
            "ordonnance actuelle",
            "medications",
            "current medications",
        ),
    ),
    (
        "interrogation",
        ("interrogatoire", "motif de consultation", "symptomes", "plaintes", "anamnese", "symptoms", "history of present illness"),
    ),
    (
        "clinicalExamination",
        ("examen clinique", "examen physique", "examen cardiovasculaire", "physical exam", "physical examination", "examen"),
    ),
    ("ecg", ("ecg", "e.c.g", "electrocardiogramme", "electrocardiogram", "ekg")),
    (
        "lastBiologyResults",
        ("biologie", "bilan biologique", "derniere biologie", "bilan sanguin", "laboratoire", "labs", "laboratory", "biology"),
    ),
    ("conclusion", ("conclusion", "au total", "synthese", "impression", "assessment")),
    (
        "treatmentPlan",
        (
            "conduite a tenir",
            "cat",
            "plan de traitement",
            "plan therapeutique",
            "propositions",
            "proposition therapeutique",
            "suivi",
            "plan",
            "recommandations",
            "treatment plan",
        ),
    ),
]

#: Repli par mots-clés pour les segments non rattachés à un titre.
KEYWORDS: dict[str, tuple[str, ...]] = {
    "previousHistory": (
        "fibrillation auriculaire", "fa ", "hta", "hypertension", "diabete", "dyslipidemie",
        "tabagisme", "stent", "pontage", "angioplastie", "infarctus", "avc", "bpco",
        "insuffisance cardiaque", "valvulopathie", "antecedent",
    ),
    "currentTreatment": (
        "mg/j", "mg x", "mg matin", "comprime", "gelule", "apixaban", "rivaroxaban",
        "bisoprolol", "ramipril", "atorvastatine", "furosemide", "amiodarone", "aspirine",
        "clopidogrel", "posologie", "traitement en cours",
    ),
    "interrogation": (
        "dyspnee", "palpitation", "douleur thoracique", "syncope", "lipothymie", "asthenie",
        "oedeme des membres", "nyha", "se plaint", "signale", "angor",
    ),
    "clinicalExamination": (
        "ta ", "tension arterielle", "fc ", "frequence cardiaque", "spo2", "auscultation",
        "souffle", "oedemes", "poids", "imc", "bruits du coeur", "pouls",
    ),
    "ecg": (
        "rythme sinusal", "qrs", "intervalle pr", "qtc", "sus-decalage", "sous-decalage",
        "onde t", "bloc de branche", "extrasystole", "derivation",
    ),
    "lastBiologyResults": (
        "hb ", "hemoglobine", "creatinine", "egfr", "dfg", "kaliemie", "natremie",
        "ldl", "hdl", "bnp", "nt-probnp", "troponine", "tsh", "hba1c", "inr", "g/l", "mmol/l",
    ),
    "conclusion": ("au total", "conclusion", "patient stable", "bilan satisfaisant", "fevg"),
    "treatmentPlan": (
        "poursuite du traitement", "revoir", "controle dans", "prochain rendez-vous",
        "majoration", "introduction de", "arret de", "adresser", "holter", "echocardiographie de controle",
    ),
}

_HEADER_LINE = re.compile(r"^\s*([A-Za-zÀ-ÖØ-öø-ÿ .'’/()\-]{2,60}?)\s*[:\-–]\s*(.*)$")


def _normalise(value: str) -> str:
    stripped = "".join(
        c for c in unicodedata.normalize("NFD", value) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", stripped).strip().lower()


def _match_header(candidate: str) -> str | None:
    normalised = _normalise(candidate).rstrip(" :.-")
    if not normalised or len(normalised) > 60:
        return None
    best: tuple[int, str] | None = None
    for field_name, titles in HEADERS:
        for title in titles:
            if normalised == title or normalised.startswith(title + " ") or normalised.startswith(title + "s"):
                score = len(title)
                if best is None or score > best[0]:
                    best = (score, field_name)
    return best[1] if best else None


def _split_sections(text: str) -> tuple[dict[str, list[str]], list[str]]:
    sections: dict[str, list[str]] = {}
    orphans: list[str] = []
    current: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        field_name: str | None = None
        remainder = ""

        match = _HEADER_LINE.match(line)
        if match:
            field_name = _match_header(match.group(1))
            remainder = match.group(2).strip()
        if field_name is None:
            candidate = _match_header(line)
            # Un titre seul sur sa ligne (souvent en majuscules) sans deux-points.
            if candidate and len(line) <= 60:
                field_name = candidate
                remainder = ""

        if field_name:
            current = field_name
            sections.setdefault(current, [])
            if remainder:
                sections[current].append(remainder)
            continue

        if current:
            sections[current].append(line)
        else:
            orphans.append(line)

    return sections, orphans


def _classify_by_keywords(segment: str) -> str | None:
    normalised = _normalise(segment)
    scores: dict[str, int] = {}
    for field_name, keywords in KEYWORDS.items():
        for keyword in keywords:
            if keyword.strip() and keyword in normalised:
                scores[field_name] = scores.get(field_name, 0) + 1
    if not scores:
        return None
    return max(scores.items(), key=lambda item: item[1])[0]


def categorize(text: str) -> tuple[dict[str, str], float, list[str]]:
    """Retourne (champs, confiance, avertissements)."""
    warnings: list[str] = []
    fields: dict[str, str] = {name: "" for name in FIELDS}

    if not text or not text.strip():
        return fields, 0.0, ["Aucun texte à catégoriser."]

    sections, orphans = _split_sections(text)
    for field_name, lines in sections.items():
        content = "\n".join(lines).strip()
        if content:
            fields[field_name] = content

    unassigned: list[str] = []
    for segment in orphans:
        field_name = _classify_by_keywords(segment)
        if field_name is None:
            unassigned.append(segment)
            continue
        fields[field_name] = (fields[field_name] + "\n" + segment).strip() if fields[field_name] else segment

    filled = sum(1 for value in fields.values() if value.strip())
    confidence = round(min(1.0, filled / len(FIELDS) * 1.1), 2)

    if filled == 0:
        warnings.append("Aucune rubrique n'a pu être identifiée : saisie manuelle nécessaire.")
    else:
        missing = [name for name, value in fields.items() if not value.strip()]
        if missing:
            warnings.append("Rubriques non détectées : " + ", ".join(missing) + ".")
    if unassigned:
        warnings.append(f"{len(unassigned)} segment(s) non attribué(s) — à vérifier manuellement.")

    return fields, confidence, warnings