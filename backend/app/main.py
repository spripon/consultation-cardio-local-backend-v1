"""Point d'entrée FastAPI — traitement 100 % local, aucun appel sortant."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import anonymize, categorize, extract, health, transcribe
from app.config import settings
from app.services.ocr import ensure_temp_root

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CardioConsult — API locale",
    description=(
        "Backend auto-hébergé : OCR, anonymisation et catégorisation locales. "
        "Aucune donnée patient ne quitte le serveur."
    ),
    version=health.VERSION,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None,
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

for router in (health.router, extract.router, anonymize.router, categorize.router, transcribe.router):
    app.include_router(router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
def on_startup() -> None:
    ensure_temp_root()
    logger.info(
        "startup env=%s policy=%s require_openmed=%s speech=%s",
        settings.app_env,
        settings.openmed_policy,
        settings.require_openmed,
        settings.enable_speech,
    )
    if settings.is_production and settings.allow_raw_ocr_debug:
        logger.warning("ALLOW_RAW_OCR_DEBUG ignoré : interdit en production.")