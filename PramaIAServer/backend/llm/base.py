# backend/llm/base.py
class LLMProvider:
    def generate(self, prompt, **kwargs):
        raise NotImplementedError
