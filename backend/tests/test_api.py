import io

from tests.fixtures import SYNTHETIC_REPORT


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert set(body) == {"status", "version", "ocr", "openmed", "speech", "policy", "environment"}
    # Le health ne doit révéler aucun chemin ni secret.
    assert "/" not in body["policy"]


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