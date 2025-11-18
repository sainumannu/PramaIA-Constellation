# backend/llm/openai.py
from .base import LLMProvider
from openai import OpenAI
from backend.core.config import OPENAI_API_KEY
import logging

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
    
    def generate(self, prompt, model="gpt-4o", system_prompt=None, **kwargs):
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            logger.info(f"OpenAI: Sending request with model {model}")
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=kwargs.get('max_tokens', 1000),
                temperature=kwargs.get('temperature', 0.7)
            )
            
            answer = response.choices[0].message.content
            logger.info(f"OpenAI: Response received, length: {len(answer) if answer else 0}")
            return answer
            
        except Exception as e:
            logger.error(f"Error in OpenAI generate: {e}")
            return f"Errore nella generazione della risposta: {str(e)}"