"""Rule-based categorization of an anonymized medical report into form fields."""

import re

from app.schemas.extraction import ExtractedFields
from app.config import settings


# Section header keywords (French) mapped to form keys.
_SECTION_KEYWORDS = {
    "previousHistory": [
        "antécédent", "antécédents", "comorbidité", "comorbidités", "historique",
        "pathologie", "pathologies", "maladie", "maladies",
    ],
    "currentTreatment": [
        "traitement habituel", "traitement de fond", "traitement au long cours",
        "médicament", "médicaments", "pris en charge",
    ],
    "interrogation": [
        "interrogatoire", "interrogé", "dice", "plainte", "symptôme", "symptômes",
    ],
    "clinicalExamination": [
        "examen clinique", "examen physique", "auscultation", "examen cardiovasculaire",
    ],
    "ecg": [
        "ecg", "électrocardiogramme", "électrocardiographie",
    ],
    "lastBiologyResults": [
        "biologie", "bilan biologique", "bilan sanguin", "laboratoire", "créatinine",
        "cholestérol", "tsh", "nfs", "crp", "glycémie", "ionogramme",
    ],
    "conclusion": [
        "conclusion", "au total", "diagnostic", "synthèse", "résumé",
    ],
    "treatmentPlan": [
        "conduite à tenir", "plan de traitement", "proposition", "ordonnance",
        "programme", "suivi", "recommandation",
    ],
}


def _split_into_sections(text: str) -> dict[str, str]:
    """Split text into sections based on headers."""
    # Normalize whitespace and newlines
    normalized = re.sub(r"\n+", "\n", text.strip())
    lines = normalized.split("\n")

    sections: dict[str, list[str]] = {}
    current_key: str | None = None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        lower = stripped.lower().rstrip(" :")
        matched_key: str | None = None
        best_match_len = 0
        for key, keywords in _SECTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in lower:
                    # Prefer more specific / longer matches
                    if len(keyword) > best_match_len:
                        matched_key = key
                        best_match_len = len(keyword)

        # Only treat as header if it looks like a short line, ends with colon,
        # or starts with a known section word at the beginning of the line.
        is_header = matched_key and (
            len(stripped) < 50
            or stripped.endswith(":")
            or re.match(rf"^({'|'.join(_SECTION_KEYWORDS.get(matched_key, []))})\s*[:\-]", lower)
        )

        if is_header:
            current_key = matched_key
            # Extract any text after the colon and keep it in the section
            # e.g. "Conclusion: stable" -> "stable" goes into conclusion
            header_text = stripped
            for keyword in _SECTION_KEYWORDS.get(matched_key, []):
                pattern = rf"(?i)^\s*{re.escape(keyword)}\s*[:\-]\s*(.*)"
                match = re.match(pattern, stripped)
                if match:
                    header_text = match.group(1).strip()
                    break
            if header_text:
                sections.setdefault(current_key, []).append(header_text)
            continue

        if current_key:
            sections[current_key].append(stripped)

    return {key: "\n".join(value) for key, value in sections.items()}


def categorize_text(text: str) -> ExtractedFields:
    """Map anonymized text to form fields."""
    if settings.categorizer_engine == "mock":
        return ExtractedFields()

    sections = _split_into_sections(text)

    # Extract next appointment from conclusion or treatment plan as a heuristic
    next_appointment = None
    combined = text.lower()
    match = re.search(r"prochain rendez-vous[^\n]*(?:dans|à|sous)?\s*([^\n]{0,40})", combined)
    if match:
        next_appointment = match.group(1).strip()

    return ExtractedFields(
        previousHistory=sections.get("previousHistory"),
        currentTreatment=sections.get("currentTreatment"),
        interrogation=sections.get("interrogation"),
        clinicalExamination=sections.get("clinicalExamination"),
        ecg=sections.get("ecg"),
        lastBiologyResults=sections.get("lastBiologyResults"),
        conclusion=sections.get("conclusion"),
        treatmentPlan=sections.get("treatmentPlan"),
    )
