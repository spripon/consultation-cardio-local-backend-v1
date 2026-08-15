"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1 import extract, transcribe

app = FastAPI(
    title="Comptes-rendus Cardiologie - API locale",
    description="Backend auto-hébergé pour OCR, anonymisation, catégorisation et transcription locale.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(extract.router, prefix=settings.api_v1_prefix)
app.include_router(transcribe.router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get(settings.api_v1_prefix + "/health")
def api_health() -> dict:
    return {"status": "ok", "version": "0.1.0"}
