"""
Configuration settings
"""

from typing import ClassVar, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config.providers import MCPConfig, DBConfig, LLMConfig,APIConfig


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # =====================
    # Agent Cache
    # =====================
    agent_cache_max_size:int = Field(1000,validation_alias="AGENT_CACHE_MAX_SIZE")
    agent_cache_ttl_seconds:int = Field(3600,validation_alias="AGENT_CACHE_TTL_SECONDS")
    
    # =====================
    # Application Settings
    # =====================
    app_name: str = Field(
        default="AI Multi-Agent Enterprise System",
        validation_alias="APP_NAME",
    )
    app_description: str = Field(default="Agent Tiers",validation_alias ="APP_DESCRIPTION" )
    app_version: str = Field(default="0.1.0", validation_alias="APP_VERSION")
    
    debug: bool = Field(default=False, validation_alias="DEBUG")

    secret_key: str = Field(default="default-secret-key-change-in-production", validation_alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", validation_alias="ALGORITHM")

    access_token_expire_minutes: int = Field(
        default=30,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        validation_alias="REFRESH_TOKEN_EXPIRE_DAYS",
    )
    BASE_DIR: ClassVar[str] = "src"

    # =====================
    # Nested provider configs
    # (default_factory to avoid import-time side effects)
    # =====================
    llm: LLMConfig = Field(default_factory=LLMConfig)
    db: DBConfig = Field(default_factory=DBConfig) # type: ignore
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    api: APIConfig = Field (default_factory=APIConfig)

    # =====================
    # Redis Settings
    # =====================
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    redis_cache_ttl: int = Field(default=3600, validation_alias="REDIS_CACHE_TTL")

    # =====================
    # File Upload Settings
    # =====================
    max_file_size: int = Field(default=10 * 1024 * 1024, validation_alias="MAX_FILE_SIZE")  # 10MB
    upload_dir: str = Field(default="uploads", validation_alias="UPLOAD_DIR")

    # =====================
    # Vector Settings
    # =====================
    embedding_model: str = Field(
        default="text-embedding-3-small",
        validation_alias="EMBEDDING_MODEL",
    )
    embedding_dimension: int = Field(default=1536, validation_alias="EMBEDDING_DIMENSION")
    chunk_size: int = Field(default=1000, validation_alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, validation_alias="CHUNK_OVERLAP")

    # =====================
    # Logging Settings
    # =====================
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_format: str = Field(default="json", validation_alias="LOG_FORMAT")  # json or text

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        vv = (v or "").upper()
        if vv not in valid_levels:
            raise ValueError(f"log_level must be one of {sorted(valid_levels)}")
        return vv


# Create a global settings instance
settings = Settings() # type: ignore
