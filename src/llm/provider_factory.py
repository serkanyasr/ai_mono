from typing import Literal, Optional
from .openai_provider import get_openai_chat_model
from .ollama_provider import get_ollama_chat_model


def get_llm_model(provider_name:Literal["openai","ollama"],model_choice: Optional[str] = None):

    if provider_name == "openai":
        return get_openai_chat_model(model_choice)
    elif provider_name == "ollama":
        return get_ollama_chat_model(model_choice)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}")