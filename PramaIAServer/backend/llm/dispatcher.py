# backend/llm/dispatcher.py
from .openai import OpenAIProvider
from .ollama import OllamaProvider
from .anthropic import AnthropicProvider
from .gemini import GeminiProvider

def get_provider(name):
    if name == "openai":
        return OpenAIProvider()
    elif name == "ollama":
        return OllamaProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "gemini":
        return GeminiProvider()
    else:
        raise ValueError(f"Provider LLM sconosciuto: {name}")