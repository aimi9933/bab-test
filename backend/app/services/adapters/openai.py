from __future__ import annotations

import time
import uuid
from typing import Any

import httpx

from ...schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionUsage,
    ChatMessage,
)
from . import BaseAdapter


class OpenAIAdapter(BaseAdapter):
    """Adapter for OpenAI-compatible APIs (direct passthrough)."""
    
    def __init__(self, provider_name: str, base_url: str, api_key: str):
        super().__init__(provider_name, base_url, api_key)
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def chat_completion(
        self, request: ChatCompletionRequest, model: str
    ) -> ChatCompletionResponse:
        """Forward request to OpenAI-compatible endpoint."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": [msg.model_dump() for msg in request.messages],
            "temperature": request.temperature,
            "stream": False,
        }
        
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            return ChatCompletionResponse(**data)
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError(f"Invalid API key for provider {self.provider_name}")
            elif e.response.status_code == 404:
                raise ValueError(f"Model {model} not found in provider {self.provider_name}")
            else:
                raise ValueError(f"HTTP error from {self.provider_name}: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise ValueError(f"Network error connecting to {self.provider_name}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing response from {self.provider_name}: {str(e)}")
    
    def supports_model(self, model: str) -> bool:
        """OpenAI adapter supports any model (validation happens at API level)."""
        return True
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()