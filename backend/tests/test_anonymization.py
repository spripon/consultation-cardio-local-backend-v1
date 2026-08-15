from app.services import medaicr_rules as rules
from app.services.anonymizer import anonymize
from tests.fixtures import CLINICAL_STRINGS, PII_STRINGS, SYNTHETIC_REPORT


def test_deterministic_removes_all_synthetic_pii():
    result = anonymize(SYNTHETIC_REPORT, require_openmed=False)
    lowered = result.text.lower()
    for pii in PII_STRINGS:
        assert pii.lower() not in lowered, f"résidu PII synthétique détecté : {pii}"


def test_clinical_content_is_preserved_with_cardio_policy():
    result = anonymize(SYNTHETIC_REPORT, require_openmed=False)
    for clinical in CLINICAL_STRINGS:
        assert clinical.lower() in result.text.lower(), f"contenu clinique perdu : {clinical}"


def test_tokens_are_used():
    result = anonymize(SYNTHETIC_REPORT, require_openmed=False)
    assert "[NOM]" in result.text or "[PRENOM]" in result.text
    assert "[DATE_NAISSANCE]" in result.text
    assert "[NIR]" in result.text
    assert "[TELEPHONE]" in result.text
    assert "[EMAIL]" in result.text


def test_global_replacement_catches_footer_repetition():
    result = anonymize(SYNTHETIC_REPORT, require_openmed=False)
    # Le nom répété en pied de page doit aussi disparaître.
    assert result.text.lower().count("dupont") == 0


def test_strict_policy_removes_age_and_sex():
    stripped = rules.strip_age_and_sex("Patiente de 74 ans, femme, née 03/03/1972")
    assert "74 ans" not in stripped
    assert "[AGE]" in stripped
    assert "[SEXE]" in stripped


def test_safety_sweep_flags_residual_email():
    residues = rules.safety_sweep("contact : test.residu@example.invalid")
    assert any(r.type == "EMAIL" for r in residues)


def test_anonymize_flags_unsafe_when_residue_present():
    # Un texte contenant un NIR non étiqueté doit rester détecté (donc anonymisé).
    result = anonymize("Numéro : 1 85 05 78 006 084 36", require_openmed=False)
    assert "[NIR]" in result.text
    assert not rules.safety_sweep(result.text)