"""Application settings using Pydantic Settings."""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "IGORS"
    app_version: str = "2.0.0"
    environment: str = "development"

    # Database (PostgreSQL 15+)
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "igors_db"
    database_user: str = "igors_user"
    database_password: str = "changeme_in_production"

    @property
    def database_url(self) -> str:
        """Get PostgreSQL database URL."""
        return (
            f"postgresql://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

    @property
    def async_database_url(self) -> str:
        """Get async PostgreSQL database URL."""
        return (
            f"postgresql+asyncpg://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    bcrypt_rounds: int = 12
    session_timeout_minutes: int = 30

    # OTP Settings
    otp_issuer: str = "IGORS_CNTS"
    otp_digits: int = 6
    otp_interval: int = 30

    # Encryption (AES-256)
    encryption_key: str = "change-this-to-32-bytes-key!!!"

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    jwt_expiry_hours: int = 8

    # File paths
    data_dir: str = "./data"
    logs_dir: str = "./logs"
    backups_dir: str = "./backups"
    resources_dir: str = "./resources"

    # SMTP (for notifications)
    smtp_host: Optional[str] = "localhost"
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None

    # SNIS Transmission
    snis_api_url: Optional[str] = None
    snis_api_key: Optional[str] = None

    def validate_encryption_key(self) -> bytes:
        """Validate and return encryption key as bytes."""
        key = self.encryption_key.encode()
        if len(key) != 32:
            raise ValueError("Encryption key must be exactly 32 bytes")
        return key


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
