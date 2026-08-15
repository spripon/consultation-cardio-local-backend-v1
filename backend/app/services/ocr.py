"""OCR strictement local : Tesseract pour les images, pdfplumber/OCRmyPDF pour les PDF.

Aucun repli cloud. Si un composant local manque, une erreur explicite est levée.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from app.config import settings
from app.services.preprocess import UnsupportedFormat, open_image, preprocess_image

logger = logging.getLogger(__name__)


class OcrUnavailable(RuntimeError):
    """Un moteur OCR local requis est absent."""


class PdfTooLong(ValueError):
    """Le PDF dépasse MAX_PDF_PAGES : refus explicite, jamais de troncature."""


@dataclass
class OcrResult:
    text: str
    confidence: float
    source: str  # tesseract | pdf_text_layer | ocrmypdf
    pages: int = 1
    warnings: list[str] = field(default_factory=list)


def ensure_temp_root() -> str:
    root = Path(settings.temp_dir)
    root.mkdir(parents=True, exist_ok=True)
    try:
        root.chmod(0o700)
    except OSError:  # pragma: no cover
        pass
    return str(root)


def _pytesseract():
    try:
        import pytesseract  # type: ignore
    except Exception as exc:
        raise OcrUnavailable("pytesseract n'est pas installé sur ce serveur.") from exc
    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
    if not shutil.which(pytesseract.pytesseract.tesseract_cmd):
        raise OcrUnavailable(
            "Binaire tesseract introuvable. Installez tesseract-ocr, tesseract-ocr-fra, tesseract-ocr-eng."
        )
    return pytesseract


def tesseract_available() -> bool:
    try:
        _pytesseract()
        return True
    except OcrUnavailable:
        return False


def _ocr_image_object(image) -> tuple[str, float]:
    pytesseract = _pytesseract()
    lang = settings.tesseract_lang
    try:
        data = pytesseract.image_to_data(
            image,
            lang=lang,
            output_type=pytesseract.Output.DICT,
            timeout=settings.ocr_timeout_seconds,
        )
        text = pytesseract.image_to_string(image, lang=lang, timeout=settings.ocr_timeout_seconds)
    except Exception as exc:
        message = str(exc).lower()
        if "language" in message or "tessdata" in message:
            raise OcrUnavailable(
                f"Pack de langue Tesseract manquant ({lang}). Installez tesseract-ocr-fra et tesseract-ocr-eng."
            ) from exc
        raise

    scores: list[float] = []
    for word, conf in zip(data.get("text", []), data.get("conf", [])):
        if not word or not word.strip():
            continue
        try:
            value = float(conf)
        except (TypeError, ValueError):
            continue
        if value >= 0:
            scores.append(value / 100.0)

    confidence = round(sum(scores) / len(scores), 3) if scores else 0.0
    return text.strip(), confidence


def ocr_image_bytes(data: bytes, content_type: str) -> OcrResult:
    image = open_image(data, content_type)
    prepared = preprocess_image(image)
    text, confidence = _ocr_image_object(prepared)
    return OcrResult(text=text, confidence=confidence, source="tesseract", pages=1)


def _pdf_page_count(pdf_path: Path) -> int:
    try:
        import pdfplumber  # type: ignore
    except Exception as exc:
        raise OcrUnavailable("pdfplumber n'est pas installé sur ce serveur.") from exc
    with pdfplumber.open(str(pdf_path)) as pdf:
        return len(pdf.pages)


def _ensure_page_budget(pdf_path: Path) -> int:
    """Refuse un PDF trop long AVANT extraction (aucun compte rendu partiel)."""
    total = _pdf_page_count(pdf_path)
    if total > settings.max_pdf_pages:
        raise PdfTooLong(
            f"PDF de {total} pages : la limite est de {settings.max_pdf_pages} pages. "
            "Le document est refusé pour éviter toute extraction partielle silencieuse."
        )
    return total


def _pdf_text_layer(pdf_path: Path) -> tuple[str, int]:
    try:
        import pdfplumber  # type: ignore
    except Exception as exc:
        raise OcrUnavailable("pdfplumber n'est pas installé sur ce serveur.") from exc

    chunks: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        pages = pdf.pages
        total = len(pages)
        for page in pages:
            chunks.append(page.extract_text() or "")
    return "\n\n".join(chunk for chunk in chunks if chunk).strip(), total


def _ocrmypdf(pdf_path: Path, workdir: Path) -> Path:
    if not shutil.which("ocrmypdf"):
        raise OcrUnavailable(
            "PDF scanné détecté mais ocrmypdf n'est pas installé sur ce serveur (paquet ocrmypdf requis)."
        )
    output = workdir / "ocr.pdf"
    command = [
        "ocrmypdf",
        "--force-ocr",
        "--optimize",
        "0",
        "--language",
        settings.tesseract_lang,
        "--pages",
        f"1-{settings.max_pdf_pages}",
        str(pdf_path),
        str(output),
    ]
    process = subprocess.run(
        command, capture_output=True, timeout=settings.ocr_timeout_seconds, check=False
    )
    if process.returncode != 0 or not output.exists():
        raise OcrUnavailable("Échec de l'OCR local du PDF scanné (ocrmypdf).")
    return output


def ocr_pdf_bytes(data: bytes) -> OcrResult:
    """PDF : couche texte si présente, sinon OCR local via ocrmypdf."""
    warnings: list[str] = []
    workdir = Path(tempfile.mkdtemp(prefix="pdf-", dir=ensure_temp_root()))
    pdf_path = workdir / "input.pdf"
    try:
        pdf_path.write_bytes(data)
        _ensure_page_budget(pdf_path)
        text, pages = _pdf_text_layer(pdf_path)
        if len(text) >= 200:
            return OcrResult(text=text, confidence=0.98, source="pdf_text_layer", pages=pages)

        ocr_pdf = _ocrmypdf(pdf_path, workdir)
        text, pages = _pdf_text_layer(ocr_pdf)
        if not text:
            warnings.append("Aucun texte exploitable extrait du PDF.")
        return OcrResult(
            text=text,
            confidence=0.85 if text else 0.0,
            source="ocrmypdf",
            pages=pages,
            warnings=warnings,
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def run_ocr(data: bytes, content_type: str) -> OcrResult:
    if content_type == "application/pdf":
        return ocr_pdf_bytes(data)
    return ocr_image_bytes(data, content_type)


__all__ = [
    "OcrResult",
    "OcrUnavailable",
    "PdfTooLong",
    "UnsupportedFormat",
    "ensure_temp_root",
    "ocr_image_bytes",
    "ocr_pdf_bytes",
    "run_ocr",
    "tesseract_available",
]