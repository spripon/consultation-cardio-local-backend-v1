"""Test OCR bout-en-bout sur une image SYNTHÉTIQUE générée à la volée."""

import io

import pytest
from PIL import Image, ImageDraw

from app.config import settings
from app.services.ocr import PdfTooLong, ocr_image_bytes, ocr_pdf_bytes, tesseract_available


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


def _synthetic_pdf(pages: int) -> bytes:
    """PDF SYNTHÉTIQUE (aucune donnée patient) de `pages` pages."""
    sheets = [Image.new("RGB", (600, 800), "white") for _ in range(pages)]
    buffer = io.BytesIO()
    sheets[0].save(buffer, format="PDF", save_all=True, append_images=sheets[1:])
    return buffer.getvalue()


def test_pdf_over_page_limit_is_refused():
    """Un PDF trop long est refusé : pas de troncature silencieuse."""
    oversized = _synthetic_pdf(settings.max_pdf_pages + 2)
    with pytest.raises(PdfTooLong):
        ocr_pdf_bytes(oversized)