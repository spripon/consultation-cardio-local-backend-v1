"""Prétraitement d'images avant OCR local (aucun réseau, aucune persistance)."""

from __future__ import annotations

import io
import logging

from PIL import Image, ImageOps

from app.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_MIME = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/tiff",
    "image/heic",
    "image/heif",
}


class UnsupportedFormat(RuntimeError):
    pass


def _register_heif() -> bool:
    try:
        import pillow_heif  # type: ignore

        pillow_heif.register_heif_opener()
        return True
    except Exception:
        return False


def open_image(data: bytes, content_type: str) -> Image.Image:
    is_heic = content_type in {"image/heic", "image/heif"}
    if is_heic:
        if not settings.enable_heic or not _register_heif():
            raise UnsupportedFormat(
                "Format HEIC non pris en charge sur ce serveur (pillow-heif absent). "
                "Merci de convertir le document en JPEG ou PNG."
            )
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception as exc:
        raise UnsupportedFormat("Image illisible ou corrompue.") from exc
    return image


def _deskew(image: Image.Image) -> Image.Image:
    """Redressement léger basé sur OpenCV ; sans effet si OpenCV est absent."""
    try:
        import cv2  # type: ignore
        import numpy as np
    except Exception:
        return image

    try:
        array = np.array(image.convert("L"))
        inverted = cv2.bitwise_not(array)
        threshold = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        coords = cv2.findNonZero(threshold)
        if coords is None:
            return image
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        if abs(angle) < 0.5 or abs(angle) > 15:
            return image
        height, width = array.shape
        matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
        rotated = cv2.warpAffine(
            array, matrix, (width, height), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
        )
        return Image.fromarray(rotated)
    except Exception as exc:  # pragma: no cover
        logger.debug("deskew skipped: %s", exc.__class__.__name__)
        return image


def preprocess_image(image: Image.Image) -> Image.Image:
    """Orientation EXIF -> niveaux de gris -> autocontraste -> deskew."""
    image = ImageOps.exif_transpose(image)
    if image.mode not in ("L", "RGB"):
        image = image.convert("RGB")
    grayscale = ImageOps.grayscale(image)
    grayscale = ImageOps.autocontrast(grayscale)
    if min(grayscale.size) < 1000:
        factor = max(1, int(1200 / max(1, min(grayscale.size))))
        if factor > 1:
            grayscale = grayscale.resize(
                (grayscale.width * factor, grayscale.height * factor), Image.LANCZOS
            )
    return _deskew(grayscale)