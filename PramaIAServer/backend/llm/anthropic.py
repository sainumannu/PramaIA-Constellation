# backend/llm/anthropic.py
from .base import LLMProvider

class AnthropicProvider(LLMProvider):
    def generate(self, prompt, **kwargs):
        # Qui va la logica per chiamare l'API di Anthropic (Claude)
        pass
