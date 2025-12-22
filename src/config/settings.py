"""
Configuration settings
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from src.config.providers import MCPConfig, DBConfig, LLMConfig

class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application Settings
    app_name: str = Field(
        default="AI Multi-Agent Enterprise System", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(
        default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    llm: LLMConfig = LLMConfig()
    db: DBConfig = DBConfig()
    mcp: MCPConfig = MCPConfig()

    # Redis Settings
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_cache_ttl: int = Field(default=3600, env="REDIS_CACHE_TTL")

    # CORS Settings
    cors_origins: list[str] = Field(default=["*"], env="CORS_ORIGINS")

    @field_validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # File Upload Settings
    max_file_size: int = Field(
        default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")

    # Vector Settings
    embedding_model: str = Field(
        default="text-embedding-3-small", env="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=1536, env="EMBEDDING_DIMENSION")
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")

    # Logging Settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json or text

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @field_validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()


# Create a global settings instance
settings = Settings()
