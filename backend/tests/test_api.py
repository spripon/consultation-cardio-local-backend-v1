import io

from tests.fixtures import SYNTHETIC_REPORT


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    # `status` vaut « degraded » si un composant local obligatoire manque
    # (c'est le cas dans un environnement de test sans Tesseract ni modèle PII).
    assert body["status"] in {"ok", "degraded"}
    assert set(body) == {
        "status",
        "version",
        "ocr",
        "openmed",
        "speech",
        "policy",
        "environment",
        "ready",
        "missing",
    }
    assert body["ready"] is (body["missing"] == [])
    # Le health ne doit révéler aucun chemin ni secret.
    assert "/" not in body["policy"]
    # Aucun chemin de modèle ne doit filtrer dans la liste des manquants.
    assert all("/" not in item for item in body["missing"])


def test_readyz_fails_closed_when_local_components_missing(client):
    response = client.get("/api/v1/readyz")
    body = response.json()
    if body["ready"]:
        assert response.status_code == 200
    else:
        # Fail-closed : jamais 200 tant qu'un composant local requis est absent.
        assert response.status_code == 503
        assert body["missing"]


def test_anonymize_preserves_clinical_sections(client):
    """L'anonymisation ne doit pas engloutir les rubriques cliniques voisines."""
    body = client.post("/api/v1/anonymize", json={"text": SYNTHETIC_REPORT}).json()
    text = body["textAnonymized"]
    for section in ("Interrogatoire", "Examen clinique", "ECG", "Conclusion"):
        assert section in text
    # Les valeurs cliniques utiles restent lisibles.
    assert "NYHA II" in text
    assert "132/78" in text
    # Aucun résidu identifiant critique ne doit subsister.
    assert body["safeToInject"] is True


def test_anonymize_endpoint(client):
    response = client.post("/api/v1/anonymize", json={"text": SYNTHETIC_REPORT})
    assert response.status_code == 200
    body = response.json()
    assert "dupont" not in body["textAnonymized"].lower()
    assert body["requiresHumanValidation"] is True
    assert body["entities"]


def test_categorize_rejects_non_anonymized_text(client):
    response = client.post(
        "/api/v1/categorize", json={"textAnonymized": "Email : residu@example.invalid"}
    )
    assert response.status_code == 422


def test_categorize_accepts_anonymized_text(client):
    anonymized = client.post("/api/v1/anonymize", json={"text": SYNTHETIC_REPORT}).json()[
        "textAnonymized"
    ]
    response = client.post("/api/v1/categorize", json={"textAnonymized": anonymized})
    assert response.status_code == 200
    assert response.json()["fields"]["ecg"]


def test_extract_rejects_unsupported_mime(client):
    response = client.post(
        "/api/v1/extract",
        files={"file": ("note.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 415


def test_extract_rejects_empty_file(client):
    response = client.post(
        "/api/v1/extract",
        files={"file": ("scan.png", io.BytesIO(b""), "image/png")},
    )
    assert response.status_code == 400


def test_extract_rejects_oversized_file(client):
    from app.config import settings

    payload = b"\x89PNG\r\n\x1a\n" + b"0" * (settings.max_upload_size + 10)
    response = client.post(
        "/api/v1/extract",
        files={"file": ("scan.png", io.BytesIO(payload), "image/png")},
    )
    assert response.status_code == 413


def test_transcribe_disabled_returns_503(client):
    response = client.post(
        "/api/v1/transcribe",
        files={"audio": ("dictee.webm", io.BytesIO(b"0" * 32), "audio/webm")},
    )
    assert response.status_code == 503