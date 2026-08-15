"""OCR service with Tesseract as primary engine and a mock fallback."""

import io
import logging

from PIL import Image
from app.config import settings

logger = logging.getLogger(__name__)


def _extract_from_image(image_bytes: bytes, engine: str) -> str:
    image = Image.open(io.BytesIO(image_bytes))
    # Convert to RGB if necessary
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    if engine == "tesseract":
        try:
            import pytesseract
            if settings.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
            return pytesseract.image_to_string(image, lang=settings.tesseract_lang)
        except Exception as exc:
            logger.warning("Tesseract failed, switching to mock: %s", exc)
            return _mock_ocr(image)

    return _mock_ocr(image)


def _extract_from_pdf(pdf_bytes: bytes, engine: str) -> str:
    try:
        from pdf2image import convert_from_bytes
    except ImportError as exc:
        logger.warning("pdf2image not installed: %s", exc)
        return ""

    pages = convert_from_bytes(pdf_bytes, dpi=200)
    texts = []
    for page in pages:
        if engine == "tesseract":
            try:
                import pytesseract
                if settings.tesseract_cmd:
                    pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
                texts.append(pytesseract.image_to_string(page, lang=settings.tesseract_lang))
            except Exception as exc:
                logger.warning("Tesseract failed on PDF page: %s", exc)
                texts.append(_mock_ocr(page))
        else:
            texts.append(_mock_ocr(page))
    return "\n\n".join(texts)


def _mock_ocr(image: Image.Image) -> str:
    return (
        "[OCR mock] Aucun moteur OCR local n'est configuré. "
        "Installez Tesseract et définissez OCR_ENGINE=tesseract."
    )


def extract_text(content: bytes, content_type: str, engine: str = settings.ocr_engine) -> str:
    if content_type == "application/pdf":
        return _extract_from_pdf(content, engine)
    return _extract_from_image(content, engine)
