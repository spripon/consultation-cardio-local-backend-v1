"""Schemas shared by the extraction endpoints."""

from pydantic import BaseModel
from typing import Any


class ExtractedFields(BaseModel):
    previousHistory: str | None = None
    currentTreatment: str | None = None
    interrogation: str | None = None
    clinicalExamination: str | None = None
    ecg: str | None = None
    lastBiologyResults: str | None = None
    conclusion: str | None = None
    treatmentPlan: str | None = None


class ExtractionResponse(BaseModel):
    fields: ExtractedFields
    rawTextAnonymized: str
    entities: list[dict[str, Any]]
    confidence: dict[str, Any]
    warnings: list[str]
