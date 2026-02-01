"""Configuration management for GoUP."""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Apify
    apify_api_token: str = Field(..., description="Apify API token")

    # Hunter.io
    hunter_api_key: str = Field(..., description="Hunter.io API key")

    # Google Gemini
    google_api_key: str = Field(..., description="Google Gemini API key")

    # Google Sheets (OAuth)
    google_credentials_file: Optional[str] = Field(
        default="config/credentials.json",
        description="Path to Google OAuth credentials file",
    )
    google_token_file: Optional[str] = Field(
        default="config/token.json",
        description="Path to store OAuth token",
    )
    google_sheet_id: Optional[str] = Field(
        default=None,
        description="Target Google Sheet ID",
    )

    # Paths
    data_dir: Path = Field(default=Path("data"), description="Data directory")
    config_dir: Path = Field(default=Path("config"), description="Config directory")

    @property
    def raw_data_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def enriched_data_dir(self) -> Path:
        return self.data_dir / "enriched"

    @property
    def output_data_dir(self) -> Path:
        return self.data_dir / "output"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
