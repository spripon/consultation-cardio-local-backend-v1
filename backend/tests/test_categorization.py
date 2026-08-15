from app.services.anonymizer import anonymize
from app.services.categorizer import FIELDS, categorize
from tests.fixtures import SYNTHETIC_REPORT


def test_categorizes_synthetic_report_into_eight_sections():
    anonymized = anonymize(SYNTHETIC_REPORT, require_openmed=False).text
    fields, confidence, _warnings = categorize(anonymized)

    assert set(fields) == set(FIELDS)
    for name in FIELDS:
        assert fields[name].strip(), f"rubrique vide : {name}"
    assert confidence > 0.8


def test_section_content_routing():
    anonymized = anonymize(SYNTHETIC_REPORT, require_openmed=False).text
    fields, _confidence, _warnings = categorize(anonymized)

    assert "fibrillation auriculaire" in fields["previousHistory"].lower()
    assert "apixaban" in fields["currentTreatment"].lower()
    assert "dyspnée" in fields["interrogation"].lower()
    assert "auscultation" in fields["clinicalExamination"].lower()
    assert "qrs" in fields["ecg"].lower()
    assert "créatinine" in fields["lastBiologyResults"].lower()
    assert "au total" in fields["conclusion"].lower()
    assert "contrôle dans 6 mois" in fields["treatmentPlan"].lower()


def test_keyword_fallback_for_untitled_text():
    fields, _confidence, _warnings = categorize(
        "Rythme sinusal régulier, QRS fins.\nHb 13 g/L et créatinine 80."
    )
    assert fields["ecg"]
    assert fields["lastBiologyResults"]


def test_empty_text_is_handled():
    fields, confidence, warnings = categorize("   ")
    assert confidence == 0.0
    assert warnings
    assert all(value == "" for value in fields.values())