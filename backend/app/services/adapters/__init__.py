from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ...schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionError,
)


class BaseAdapter(ABC):
    """Base class for provider adapters implementing OpenAI-compatible interface."""
    
    def __init__(self, provider_name: str, base_url: str, api_key: str):
        self.provider_name = provider_name
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
    
    @abstractmethod
    async def chat_completion(
        self, request: ChatCompletionRequest, model: str
    ) -> ChatCompletionResponse:
        """Execute a chat completion request and return OpenAI-compatible response."""
        pass
    
    @abstractmethod
    def supports_model(self, model: str) -> bool:
        """Check if the adapter supports the given model."""
        pass
    
    def create_error_response(self, message: str, error_type: str = "invalid_request_error") -> ChatCompletionError:
        """Create a standardized error response."""
        return ChatCompletionError(
            error={
                "message": message,
                "type": error_type,
                "code": None
            }
        )