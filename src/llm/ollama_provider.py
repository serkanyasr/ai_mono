from typing import Optional
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIChatModel
from src.config.settings import settings
import openai

def get_ollama_chat_model(model_choice: Optional[str] = None) -> OpenAIChatModel:
    """
    Get Ollama model configuration from local server.

    Args:
        model_choice: Optional override for model choice 

    Returns:
        Configured Ollama model via OpenAI-compatible endpoint
    """
    
    llm_model = model_choice or settings.llm.ollama_model
    
    base_url = settings.llm.ollama_base_url
    
    api_key = settings.llm.ollama_api_key

    provider = OpenAIProvider(api_key=api_key, base_url=base_url)
    
    return OpenAIChatModel(llm_model, provider=provider)


def get_ollama_client() -> openai.AsyncOpenAI:
    """
    Get Ollama embedding client configuration from local server.

    Returns:
        Configured Ollama client via OpenAI-compatible endpoint
    """
    base_url = settings.llm.ollama_base_url 
    
    api_key = settings.llm.ollama_api_key

    return openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
