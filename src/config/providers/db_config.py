from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()


class DBConfig(BaseSettings):
    # Memory DB
    memory_vector_store_provider: str = Field(
        default="pgvector", env="MEMORY_VECTOR_STORE_PROVIDER")
    memory_db_user: str = Field(..., env="MEMORY_DB_USER")
    memory_db_password: str = Field(..., env="MEMORY_DB_PASSWORD")
    memory_db_host: str = Field(default="localhost", env="MEMORY_DB_HOST")
    memory_db_port: int = Field(default=5432, env="MEMORY_DB_PORT")
    memory_db_name: str = Field(default="memory_db", env="MEMORY_DB_NAME")
    memory_llm_provider: str = Field(
        default="openai", env="MEMORY_LLM_PROVIDER")
    memory_llm_model: str = Field(default="gpt-4", env="MEMORY_LLM_MODEL")
    memory_embedding_provider: str = Field(
        default="openai", env="MEMORY_EMBEDDING_PROVIDER")
    memory_embedding_model: str = Field(
        default="text-embedding-3-small", env="MEMORY_EMBEDDING_MODEL")
    memory_embedding_dims: int = Field(
        default=1536, env="MEMORY_EMBEDDING_DIMS")

    @property
    def memory_database_url(self) -> str:
        """Construct Memory database URL from components"""
        return f"postgresql+asyncpg://{self.memory_db_user}:{self.memory_db_password}@{self.memory_db_host}:{self.memory_db_port}/{self.memory_db_name}"

    # RAG DB
    rag_db_user: str = Field(..., env="RAG_DB_USER")
    rag_db_password: str = Field(..., env="RAG_DB_PASSWORD")
    rag_db_host: str = Field(default="localhost", env="RAG_DB_HOST")
    rag_db_port: int = Field(default=5432, env="RAG_DB_PORT")
    rag_db_name: str = Field(default="rag_db", env="RAG_DB_NAME")
    rag_db_min_connection: int = Field(default=5, env="RAG_DB_MIN_CONNECTION")
    rag_db_max_connection: int = Field(default=20, env="RAG_DB_MAX_CONNECTION")
    rag_db_connection_timeout: int = Field(
        default=60, env="RAG_DB_CONNECTION_TIMEOUT")
    rag_db_max_inactive_lifetime: int = Field(
        default=300, env="RAG_DB_MAX_INACTIVE_LIFETIME")

    @property
    def rag_database_url(self) -> str:
        """Construct RAG database URL from components"""
        return f"postgresql+asyncpg://{self.rag_db_user}:{self.rag_db_password}@{self.rag_db_host}:{self.rag_db_port}/{self.rag_db_name}"

    # Redis Settings
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_cache_ttl: int = Field(default=3600, env="REDIS_CACHE_TTL")


memory_db_config = DBConfig()
