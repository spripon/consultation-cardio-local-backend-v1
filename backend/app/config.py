"""Configuration de l'application (variables d'environnement uniquement).

Aucune valeur par défaut ne doit permettre l'envoi de données vers un service
externe : le runtime est volontairement « fail-closed ».
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    app_env: str = "development"  # development | production
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:8080,http://127.0.0.1:8080"

    # --- Limites d'upload ---
    max_upload_size: int = 20_971_520  # 20 Mo
    max_pdf_pages: int = 20
    ocr_timeout_seconds: int = 120
    temp_dir: str = "/tmp/consultation-cardio"

    # --- OCR local ---
    tesseract_cmd: str | None = None
    tesseract_lang: str = "fra+eng"
    ocr_dpi: int = 300
    enable_heic: bool = True

    # --- Anonymisation ---
    # strict_no_leak : supprime aussi âge / sexe / dates cliniques
    # gdpr_pseudonymization : conserve âge / sexe / dates cliniques (défaut cardio)
    openmed_policy: str = "gdpr_pseudonymization"
    openmed_pii_model: str = "/models/openmed-pii-fr"
    openmed_language: str = "fr"
    openmed_confidence_threshold: float = 0.35
    openmed_offline: bool = True
    #: None = valeur déduite de l'environnement (obligatoire en production).
    require_openmed: bool | None = None
    redact_doctor_names: bool = True
    hf_hub_offline: bool = True

    # --- Transcription locale ---
    enable_speech: bool = False
    whisper_model_path: str = "/models/faster-whisper-small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_language: str = "fr"

    # --- Débogage ---
    # Interdit en production (voir `debug_raw_ocr_allowed`).
    allow_raw_ocr_debug: bool = False

    # --- Réservé V2 : jamais appelé en V1 ---
    local_llm_url: str | None = None
    enable_local_llm: bool = False

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}

    @property
    def openmed_required(self) -> bool:
        """OpenMed est obligatoire en production sauf désactivation explicite."""
        if self.require_openmed is None:
            return self.is_production
        return self.require_openmed

    @property
    def ocr_required(self) -> bool:
        """L'OCR local est indispensable au service : jamais de repli."""
        return True

    @property
    def debug_raw_ocr_allowed(self) -> bool:
        return self.allow_raw_ocr_debug and not self.is_production

    @property
    def strict_policy(self) -> bool:
        return self.openmed_policy == "strict_no_leak"

    @property
    def allowed_cors_origins(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if self.is_production:
            origins = [o for o in origins if o != "*"]
        return origins


settings = Settings()