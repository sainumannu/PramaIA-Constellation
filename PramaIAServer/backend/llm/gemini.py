# backend/llm/gemini.py
from .base import LLMProvider

class GeminiProvider(LLMProvider):
    def generate(self, prompt, **kwargs):
        # Qui va la logica per chiamare l'API di Google Gemini
        pass
