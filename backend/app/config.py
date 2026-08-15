"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:8080,http://127.0.0.1:8080"
    max_upload_size: int = 20_971_520  # 20 MB

    # OCR
    tesseract_cmd: str | None = None
    tesseract_lang: str = "fra"
    ocr_engine: str = "tesseract"  # tesseract | mock

    # Categorisation / anonymisation
    anonymizer_engine: str = "rules"  # rules | mock
    categorizer_engine: str = "rules"  # rules | mock

    # Transcription
    whisper_model: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    transcription_engine: str = "whisper"  # whisper | mock

    # Persistence (disabled by default)
    enable_persistence: bool = False
    database_url: str | None = None
    encryption_key: str | None = None

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
