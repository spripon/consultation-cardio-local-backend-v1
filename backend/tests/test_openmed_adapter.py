"""Tests de l'adaptateur OpenMed 2.0 — SANS réseau, SANS poids, SANS PHI.

Un faux module `openmed` est injecté dans sys.modules : il vérifie la signature
d'appel officielle et le parsing des entités. Aucune donnée patient réelle.
"""

import sys
import types

import pytest

from app.config import settings
from app.services import openmed_pii


class _Entity:
    def __init__(self, label, text, confidence):
        self.label = label
        self.text = text
        self.confidence = confidence


class _Result:
    def __init__(self, entities):
        self.entities = entities


def _install_fake(monkeypatch, entities, *, dict_result=False, broken=False):
    calls: list[dict] = []
    module = types.ModuleType("openmed")

    def extract_pii(text, **kwargs):
        calls.append({"text": text, **kwargs})
        if broken:
            raise RuntimeError("poids illisibles")
        return {"entities": list(entities)} if dict_result else _Result(list(entities))

    module.extract_pii = extract_pii  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "openmed", module)
    monkeypatch.setattr(settings, "openmed_pii_model", "openmed-pii-fr-test", raising=False)
    return calls


@pytest.fixture(autouse=True)
def _reset_state():
    """Aucune fuite d'état entre les tests."""
    openmed_pii._STATE.update({"loaded": False, "engine": None, "error": None})
    yield
    openmed_pii._STATE.update({"loaded": False, "engine": None, "error": None})


def test_extract_pii_called_with_official_signature(monkeypatch):
    calls = _install_fake(monkeypatch, [])
    openmed_pii.detect_pii("Texte fictif de contrôle.")
    # 1er appel = warm-up synthétique, 2e = runtime : mêmes paramètres exacts.
    assert len(calls) == 2
    for call in calls:
        assert call["model_name"] == settings.openmed_pii_model
        assert call["lang"] == "fr"
        assert call["confidence_threshold"] == settings.openmed_confidence_threshold
        assert call["use_smart_merging"] is True
    assert calls[0]["text"] == openmed_pii.WARMUP_TEXT


def test_warmup_runs_only_once(monkeypatch):
    calls = _install_fake(monkeypatch, [])
    openmed_pii.detect_pii("un")
    openmed_pii.detect_pii("deux")
    warmups = [c for c in calls if c["text"] == openmed_pii.WARMUP_TEXT]
    assert len(warmups) == 1


def test_parses_typed_entities(monkeypatch):
    _install_fake(monkeypatch, [_Entity("PATIENT", "Aurélie-Anne", 0.91)])
    findings = openmed_pii.detect_pii("texte fictif")
    assert [(f.type, f.value, f.source) for f in findings] == [
        ("NAME", "Aurélie-Anne", "openmed")
    ]
    assert findings[0].confidence == 0.91


def test_parses_dict_entities(monkeypatch):
    _install_fake(
        monkeypatch,
        [{"entity_group": "B-EMAIL", "word": "contact@example.invalid", "score": 0.77}],
        dict_result=True,
    )
    findings = openmed_pii.detect_pii("texte fictif")
    assert findings[0].type == "EMAIL"
    assert findings[0].confidence == 0.77


def test_unknown_label_falls_back_to_id(monkeypatch):
    _install_fake(monkeypatch, [_Entity("LABEL_INCONNU", "XYZ-42", 0.5)])
    assert openmed_pii.detect_pii("texte fictif")[0].type == "ID"


def test_broken_model_makes_openmed_unavailable(monkeypatch):
    _install_fake(monkeypatch, [], broken=True)
    assert openmed_pii.status().available is False
    with pytest.raises(openmed_pii.OpenMedUnavailable):
        openmed_pii.detect_pii("texte fictif")


def test_incompatible_api_makes_openmed_unavailable(monkeypatch):
    module = types.ModuleType("openmed")
    monkeypatch.setitem(sys.modules, "openmed", module)
    assert openmed_pii.status().available is False


def test_anonymize_returns_503_when_openmed_required_but_missing(client, monkeypatch):
    _install_fake(monkeypatch, [], broken=True)
    monkeypatch.setattr(settings, "require_openmed", True, raising=False)
    response = client.post("/api/v1/anonymize", json={"text": "texte fictif"})
    assert response.status_code == 503


def test_readyz_not_ready_when_openmed_required_but_missing(client, monkeypatch):
    _install_fake(monkeypatch, [], broken=True)
    monkeypatch.setattr(settings, "require_openmed", True, raising=False)
    response = client.get("/api/v1/readyz")
    assert response.status_code == 503
    assert "openmed" in response.json()["missing"]


def test_categorize_uses_model_layer_and_refuses_residual_pii(client, monkeypatch):
    """Appel direct de /categorize : le faux modèle détecte un nom que la couche
    déterministe seule ne repère pas -> 422, aucune catégorisation."""
    _install_fake(monkeypatch, [_Entity("PATIENT", "Kervella-Estève", 0.95)])
    monkeypatch.setattr(settings, "require_openmed", True, raising=False)
    response = client.post(
        "/api/v1/categorize",
        json={"textAnonymized": "ECG :\nRythme sinusal. Vu avec Kervella-Estève ce jour."},
    )
    assert response.status_code == 422


def test_categorize_returns_503_when_model_required_but_unavailable(client, monkeypatch):
    _install_fake(monkeypatch, [], broken=True)
    monkeypatch.setattr(settings, "require_openmed", True, raising=False)
    response = client.post("/api/v1/categorize", json={"textAnonymized": "ECG :\nRythme sinusal."})
    assert response.status_code == 503
