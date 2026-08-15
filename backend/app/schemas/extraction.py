"""Schémas d'échange des endpoints d'extraction / anonymisation / catégorisation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedFields(BaseModel):
    previousHistory: str = ""
    currentTreatment: str = ""
    interrogation: str = ""
    clinicalExamination: str = ""
    ecg: str = ""
    lastBiologyResults: str = ""
    conclusion: str = ""
    treatmentPlan: str = ""


class Entity(BaseModel):
    type: str
    placeholder: str
    source: str = "deterministic"  # deterministic | openmed | safety_sweep
    confidence: float = 0.0


class ConfidenceBlock(BaseModel):
    ocr: float = 0.0
    anonymization: float = 0.0
    categorization: float = 0.0


class ExtractionResponse(BaseModel):
    fields: ExtractedFields = Field(default_factory=ExtractedFields)
    rawTextAnonymized: str = ""
    entities: list[Entity] = Field(default_factory=list)
    confidence: ConfidenceBlock = Field(default_factory=ConfidenceBlock)
    warnings: list[str] = Field(default_factory=list)
    requiresHumanValidation: bool = True
    #: Défaut volontairement restrictif : aucune injection sans validation explicite.
    safeToInject: bool = False
    #: Uniquement hors production et si ALLOW_RAW_OCR_DEBUG=true.
    debugRawText: str | None = None


class AnonymizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200_000)


class AnonymizeResponse(BaseModel):
    textAnonymized: str
    entities: list[Entity] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    requiresHumanValidation: bool = True
    safeToInject: bool = False


class CategorizeRequest(BaseModel):
    """Le texte fourni DOIT déjà être anonymisé."""

    textAnonymized: str = Field(min_length=1, max_length=200_000)


class CategorizeResponse(BaseModel):
    fields: ExtractedFields
    confidence: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    requiresHumanValidation: bool = True


class HealthResponse(BaseModel):
    status: str
    version: str
    ocr: bool
    openmed: bool
    speech: bool
    policy: str
    environment: str
    ready: bool = False
    missing: list[str] = Field(default_factory=list)