"""Centralized Pydantic BaseSettings configuration for Meridian AI."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application-level settings."""
    model_config = SettingsConfigDict(env_prefix="APP_")

    name: str = Field(default="meridian-ai", description="Application name")
    version: str = Field(default="1.0.0", description="Application version")
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    log_level: str = Field(default="INFO", description="Logging level")
    reload: bool = Field(default=False, description="Enable auto-reload in dev")


class DataHubSettings(BaseSettings):
    """DataHub integration settings."""
    model_config = SettingsConfigDict(env_prefix="DATAHUB_")

    mock: bool = Field(default=True, description="Use mock DataHub client")
    gms_url: str = Field(default="http://localhost:8080/api/gms", description="DataHub GMS URL")
    gms_token: str = Field(default="", description="DataHub GMS auth token")


class GroqSettings(BaseSettings):
    """Groq API settings."""
    model_config = SettingsConfigDict(env_prefix="GROQ_")

    api_key: str = Field(default="", description="Groq API key")
    model: str = Field(default="llama3-8b-8192", description="Groq model name")
    max_tokens: int = Field(default=1024, description="Max tokens per response")
    temperature: float = Field(default=0.7, description="Sampling temperature")


class AuthSettings(BaseSettings):
    """JWT authentication settings."""
    model_config = SettingsConfigDict(env_prefix="AUTH_")

    enabled: bool = Field(default=False, description="Enable JWT authentication")
    secret_key: str = Field(default="change-me-in-production", description="JWT secret key")
    algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Token expiry in minutes")
    public_paths: list[str] = Field(
        default=["/health", "/health/ready", "/health/live", "/docs", "/openapi.json", "/redoc"],
        description="Paths that bypass authentication",
    )


class CORSSettings(BaseSettings):
    """CORS settings."""
    model_config = SettingsConfigDict(env_prefix="CORS_")

    allow_origins: list[str] = Field(default=["*"], description="Allowed origins")
    allow_credentials: bool = Field(default=False, description="Allow credentials")
    allow_methods: list[str] = Field(default=["*"], description="Allowed methods")
    allow_headers: list[str] = Field(default=["*"], description="Allowed headers")


class PersistenceSettings(BaseSettings):
    """Persistence / storage settings."""
    model_config = SettingsConfigDict(env_prefix="PERSIST_")

    backend: str = Field(default="memory", description="Storage backend: memory, sqlite, postgres")
    sqlite_path: str = Field(default="data/meridian.db", description="SQLite database path")
    postgres_url: str = Field(default="", description="PostgreSQL connection URL")
    max_incidents: int = Field(default=1000, description="Max incidents to retain")


class Settings(BaseSettings):
    """Top-level settings aggregating all groups."""

    app: AppSettings = Field(default_factory=AppSettings)
    datahub: DataHubSettings = Field(default_factory=DataHubSettings)
    groq: GroqSettings = Field(default_factory=GroqSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    persistence: PersistenceSettings = Field(default_factory=PersistenceSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
