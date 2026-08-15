"""Anonymization engine using rules-based redaction."""

import re
from typing import Any

from app.config import settings


# Regex patterns commonly found in French medical reports.
# Order matters: longer/more specific patterns should be checked first.
_SENSITIVE_PATTERNS = [
    ("NIR", r"\b[12](?:\s*\d){12}\b"),
    ("DATE_NAISSANCE", r"\b(?:né(?:\s+le)?|née(?:\s+le)?|date\s+de\s+naissance\s*:?\s*)\s*[0-9]{1,2}[/-][0-9]{1,2}[/-](?:19|20)?[0-9]{2}\b"),
    ("EMAIL", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    ("TELEPHONE", r"\b(?:0|\+33)\s*[1-9](?:\s*\d\s*){8}\b"),
    ("IPP", r"\b(?:IPP|N°\s*dossier|N°\s*patient|Dossier)\s*:?\s*\d+\b"),
]


def _replace_with_token(text: str, label: str, pattern: str) -> tuple[str, list[dict[str, Any]]]:
    entities = []

    def repl(match: re.Match) -> str:
        entities.append({"label": label, "start": match.start(), "end": match.end(), "text": "[REDACTED]"})
        return f"[{label}]"

    new_text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return new_text, entities


def _anonymize_rules(text: str) -> tuple[str, list[dict[str, Any]]]:
    all_entities: list[dict[str, Any]] = []
    anonymized = text
    for label, pattern in _SENSITIVE_PATTERNS:
        anonymized, entities = _replace_with_token(anonymized, label, pattern)
        all_entities.extend(entities)
    return anonymized, all_entities


def anonymize_text(text: str) -> tuple[str, list[dict[str, Any]]]:
    """Return anonymized text and a list of redacted entities."""
    if settings.anonymizer_engine == "mock":
        return text, []
    return _anonymize_rules(text)
