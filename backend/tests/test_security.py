"""Tests de sécurité synthétiques (aucune donnée patient réelle)."""

import io

import pytest

from app.config import settings
from app.services import medaicr_rules as rules
from app.services.anonymizer import anonymize
from tests.fixtures import CLINICAL_STRINGS, SYNTHETIC_REPORT


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Nom : Kervella-Estève", "NAME"),
        ("Prénom : Aurélie-Anne", "FIRSTNAME"),
        ("Adresse : 12 rue des Lilas, 65000 TARBES", "ADDRESS"),
        ("Médecin traitant : Dr Nguyên-Lefèvre", "DOCTOR"),
        ("Correspondant : Pr Étienne Vasseur", "DOCTOR"),
        ("NIR : 1 85 05 78 006 084 36", "NIR"),
        ("IPP : 1234567", "IPP"),
        ("Email : a.b@example.invalid", "EMAIL"),
        ("Téléphone : 06 12 34 56 78", "PHONE"),
        ("Date de naissance : 03/03/1972", "DOB"),
    ],
)
def test_safety_sweep_flags_residual_pii(text, expected):
    residues = rules.safety_sweep(text)
    assert expected in {r.type for r in residues}, text


def test_footer_repetition_is_swept():
    residues = rules.safety_sweep("Compte rendu\n...\nNom : Kervella-Estève - IPP 1234567 - page 1/1")
    kinds = {r.type for r in residues}
    assert "NAME" in kinds and "IPP" in kinds


def test_accented_and_compound_names_are_redacted():
    result = anonymize(
        "Nom : Nguyên-Lefèvre\nPrénom : Aurélie-Anne\nECG :\nRythme sinusal.",
        require_openmed=False,
    )
    lowered = result.text.lower()
    assert "nguyên-lefèvre" not in lowered
    assert "aurélie-anne" not in lowered
    assert "Rythme sinusal" in result.text


def test_clinical_pipeline_preserves_sections():
    result = anonymize(SYNTHETIC_REPORT, require_openmed=False)
    for clinical in CLINICAL_STRINGS:
        assert clinical.lower() in result.text.lower()
    for section in ("Antécédents", "Traitement actuel", "ECG", "Biologie", "Conclusion"):
        assert section in result.text


def test_categorize_refuses_residual_pii(client):
    response = client.post(
        "/api/v1/categorize",
        json={"textAnonymized": "ECG :\nRythme sinusal.\nEmail : a.b@example.invalid"},
    )
    assert response.status_code == 422


def test_debug_raw_text_never_returned_in_production(client, monkeypatch):
    """Même avec ALLOW_RAW_OCR_DEBUG=true, la production ne renvoie jamais l'OCR brut."""
    from app.api.v1 import extract as extract_module
    from app.services.ocr import OcrResult

    monkeypatch.setattr(settings, "app_env", "production", raising=False)
    monkeypatch.setattr(settings, "allow_raw_ocr_debug", True, raising=False)
    monkeypatch.setattr(settings, "require_openmed", False, raising=False)
    monkeypatch.setattr(
        extract_module,
        "run_ocr",
        lambda *_a, **_k: OcrResult(
            text="Nom : Kervella-Estève\nECG :\nRythme sinusal.", confidence=0.9, source="tesseract"
        ),
    )

    payload = b"\x89PNG\r\n\x1a\n" + b"0" * 64
    response = client.post(
        "/api/v1/extract", files={"file": ("scan.png", io.BytesIO(payload), "image/png")}
    )
    assert response.status_code == 200
    body = response.json()
    assert body.get("debugRawText") is None
    assert "Kervella" not in body["rawTextAnonymized"]


def test_readyz_reports_missing_speech_when_enabled(client, monkeypatch):
    monkeypatch.setattr(settings, "enable_speech", True, raising=False)
    monkeypatch.setattr(settings, "whisper_model_path", "/models/absent-local-whisper", raising=False)
    response = client.get("/api/v1/readyz")
    assert response.status_code == 503
    assert "speech" in response.json()["missing"]
