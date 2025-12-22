from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # =====================
    # Memory DB
    # =====================
    memory_vector_store_provider: str = Field(
        default="pgvector",
        validation_alias="MEMORY_VECTOR_STORE_PROVIDER",
    )
    memory_db_user: str = Field(..., validation_alias="MEMORY_DB_USER")
    memory_db_password: str = Field(..., validation_alias="MEMORY_DB_PASSWORD")
    memory_db_host: str = Field(default="localhost", validation_alias="MEMORY_DB_HOST")
    memory_db_port: int = Field(default=5432, validation_alias="MEMORY_DB_PORT")
    memory_db_name: str = Field(default="memory_db", validation_alias="MEMORY_DB_NAME")

    memory_llm_provider: str = Field(default="openai", validation_alias="MEMORY_LLM_PROVIDER")
    memory_llm_model: str = Field(default="gpt-4", validation_alias="MEMORY_LLM_MODEL")

    memory_embedding_provider: str = Field(default="openai", validation_alias="MEMORY_EMBEDDING_PROVIDER")
    memory_embedding_model: str = Field(
        default="text-embedding-3-small",
        validation_alias="MEMORY_EMBEDDING_MODEL",
    )
    memory_embedding_dims: int = Field(default=1536, validation_alias="MEMORY_EMBEDDING_DIMS")

    @computed_field
    @property
    def memory_database_url(self) -> str:
        """Construct Memory database URL from components (Pydantic-aware)."""
        return (
            f"postgresql+asyncpg://{self.memory_db_user}:{self.memory_db_password}"
            f"@{self.memory_db_host}:{self.memory_db_port}/{self.memory_db_name}"
        )

    # =====================
    # RAG DB
    # =====================
    rag_db_user: str = Field(..., validation_alias="RAG_DB_USER")
    rag_db_password: str = Field(..., validation_alias="RAG_DB_PASSWORD")
    rag_db_host: str = Field(default="localhost", validation_alias="RAG_DB_HOST")
    rag_db_port: int = Field(default=5432, validation_alias="RAG_DB_PORT")
    rag_db_name: str = Field(default="rag_db", validation_alias="RAG_DB_NAME")

    rag_db_min_connection: int = Field(default=5, validation_alias="RAG_DB_MIN_CONNECTION")
    rag_db_max_connection: int = Field(default=20, validation_alias="RAG_DB_MAX_CONNECTION")
    rag_db_connection_timeout: int = Field(default=60, validation_alias="RAG_DB_CONNECTION_TIMEOUT")
    rag_db_max_inactive_lifetime: int = Field(default=300, validation_alias="RAG_DB_MAX_INACTIVE_LIFETIME")

    @computed_field
    @property
    def rag_database_url(self) -> str:
        """Construct RAG database URL from components (Pydantic-aware)."""
        return (
            f"postgresql+asyncpg://{self.rag_db_user}:{self.rag_db_password}"
            f"@{self.rag_db_host}:{self.rag_db_port}/{self.rag_db_name}"
        )

    # =====================
    # Redis
    # =====================
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    redis_cache_ttl: int = Field(default=3600, validation_alias="REDIS_CACHE_TTL")


db_config = DBConfig() # type: ignore
