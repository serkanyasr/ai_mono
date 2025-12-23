from typing import Optional
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIChatModel
import openai
from ..config.settings import settings




def get_openai_chat_model(model_choice: Optional[str] = None) -> OpenAIChatModel:
    """
    Get OpenAI model configuration based on environment variables.

    Args:
        model_choice: Optional override for model choice

    Returns:
        Configured OpenAI-compatible model
    """
    llm_model = model_choice or settings.llm.openai_model
    api_key = settings.llm.openai_api_key
    base_url = settings.llm.openai_base_url
    

    provider = OpenAIProvider(api_key=api_key,base_url=base_url)
    return OpenAIChatModel(llm_model, provider=provider)


def get_openai_client() -> openai.AsyncOpenAI:
    """
    Get OpenAI client configuration based on environment variables.

    Returns:
        Configured OpenAI-compatible client
    """
    api_key = settings.llm.openai_api_key
    base_url = settings.llm.openai_base_url

    return openai.AsyncOpenAI(api_key=api_key,base_url=base_url)


def get_openai_embedding_model() -> str:
    """
    Get OpenAI embedding model name from environment.

    Returns:
        Embedding model name
    """
    return settings.llm.openai_embedding_model


def get_openai_embedding_client() -> openai.AsyncOpenAI:
    """
    Get OpenAI embedding client configuration based on environment variables.

    Returns:
        Configured OpenAI-compatible client for embeddings
    """
    api_key = settings.llm.openai_api_key

    return openai.AsyncOpenAI(api_key=api_key)


