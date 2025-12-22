
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional
load_dotenv()


class LLMConfig(BaseSettings):

    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_base_url: Optional[str] = Field(default=None, env="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_emmbedding_model: str = Field(
        default="text-embedding-3-small", env="OPENAI_EMBEDDING_MODEL")
    
    ollama_api_key: Optional[str] = Field(default="ollama", env="OLLAMA_API_KEY")
    ollama_base_url: str = Field(
        default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3", env="OLLAMA_MODEL")


llm_config = LLMConfig()
