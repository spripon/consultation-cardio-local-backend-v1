"""Test OCR bout-en-bout sur une image SYNTHÉTIQUE générée à la volée."""

import io

import pytest
from PIL import Image, ImageDraw

from app.services.ocr import ocr_image_bytes, tesseract_available


def _synthetic_document() -> bytes:
    image = Image.new("RGB", (1400, 400), "white")
    draw = ImageDraw.Draw(image)
    draw.text((30, 60), "Conclusion : patient stable", fill="black")
    draw.text((30, 140), "ECG : rythme sinusal", fill="black")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.skipif(not tesseract_available(), reason="tesseract non installé")
def test_ocr_reads_synthetic_image():
    result = ocr_image_bytes(_synthetic_document(), "image/png")
    assert result.source == "tesseract"
    assert "conclusion" in result.text.lower() or "ecg" in result.text.lower()