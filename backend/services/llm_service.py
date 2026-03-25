import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from openai import OpenAI
from typing import List, Dict, Any, Optional
from config import settings

class LLMService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_URL
        )
        self.model = settings.OPENAI_API_MODEL

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None,
        response_format: Dict[str, str] = None
    ) -> str:
        kwargs = {
            "model": self.model,
            "messages": messages
        }
        
        if tools:
            kwargs["tools"] = tools
        
        if response_format:
            kwargs["response_format"] = response_format
        
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message

_llm_service: Optional[LLMService] = None

def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
