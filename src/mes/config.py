"""Configuration management for the custom MES service."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class QMIBConnectionSettings(BaseModel):
    """Connection settings required for interacting with system:inmation QMIB."""

    base_url: HttpUrl = Field(
        ...,
        description=(
            "Base URL of the QMIB REST endpoint. Provide the protocol and port,"
            " e.g. https://inmation-gateway:443/api/qmib."
        ),
    )
    username: str = Field(..., description="Service account used for authentication against QMIB.")
    password: str = Field(..., description="Password for the service account.")
    verify_ssl: bool = Field(
        True,
        description="Set to False when targeting a development QMIB environment with self-signed certificates.",
    )
    timeout_seconds: float = Field(30.0, description="Request timeout when communicating with QMIB.")

    @validator("username", "password")
    def _non_empty(cls, value: str) -> str:  # pylint: disable=no-self-argument
        if not value:
            raise ValueError("QMIB credentials must not be empty")
        return value


class DatabaseSettings(BaseModel):
    """Connection information for the MES persistence layer."""

    url: str = Field(
        "sqlite+aiosqlite:///./mes.db",
        description="SQLAlchemy connection string for the MES data store.",
    )


class MESSettings(BaseSettings):
    """Application level configuration."""

    model_config = SettingsConfigDict(env_file=('.env',), env_prefix="MES_", env_nested_delimiter="__")

    environment: str = Field(
        "development",
        description="Deployment environment identifier (development/staging/production).",
    )
    qmib: QMIBConnectionSettings
    database: DatabaseSettings = DatabaseSettings()
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["*"],
        description="CORS allowed origins for the API.",
    )

    class Config:
        """Support loading from a YAML configuration file when provided."""

        env_file = ".env"

    @classmethod
    def from_yaml(cls, path: Path | str) -> "MESSettings":
        """Load configuration from a YAML file."""

        import yaml

        with Path(path).expanduser().resolve().open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        return cls(**data)


@lru_cache
def get_settings(config_path: Optional[Path] = None) -> MESSettings:
    """Return cached application settings."""

    if config_path:
        return MESSettings.from_yaml(config_path)
    return MESSettings()


__all__ = ["MESSettings", "QMIBConnectionSettings", "DatabaseSettings", "get_settings"]
