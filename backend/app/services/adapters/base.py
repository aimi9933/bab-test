from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

import httpx

from ...schemas.openai import ChatCompletionRequest


class ProviderAdapterError(Exception):
    """Base exception for provider adapter errors."""
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ProviderAdapter(ABC):
    """Base class for provider adapters that translate between OpenAI format and provider-specific APIs."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    @abstractmethod
    def build_request(
        self, request: ChatCompletionRequest, model: str
    ) -> tuple[str, dict[str, str], dict[str, Any]]:
        """
        Build provider-specific request.
        
        Returns:
            tuple of (url, headers, body)
        """
        pass

    @abstractmethod
    def parse_response(self, response_data: dict[str, Any], model: str, request_id: str) -> dict[str, Any]:
        """
        Parse provider response into OpenAI format.
        
        Returns:
            OpenAI-compatible response dict
        """
        pass

    @abstractmethod
    async def parse_stream_chunk(
        self, chunk: bytes, model: str, request_id: str
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Parse streaming chunk into OpenAI format.
        
        Yields:
            OpenAI-compatible chunk dicts
        """
        yield {}  # pragma: no cover

    async def call_provider(
        self, request: ChatCompletionRequest, model: str
    ) -> dict[str, Any]:
        """Make a non-streaming call to the provider."""
        url, headers, body = self.build_request(request, model)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, headers=headers, json=body)
                response.raise_for_status()
                response_data = response.json()
            except httpx.HTTPStatusError as e:
                detail = f"Provider returned status {e.response.status_code}"
                try:
                    error_data = e.response.json()
                    if "error" in error_data:
                        detail = f"{detail}: {error_data['error']}"
                except Exception:
                    pass
                raise ProviderAdapterError(detail, e.response.status_code) from e
            except httpx.RequestError as e:
                raise ProviderAdapterError(f"Failed to call provider: {str(e)}") from e

        import uuid
        import time
        request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        return self.parse_response(response_data, model, request_id)

    async def stream_provider(
        self, request: ChatCompletionRequest, model: str
    ) -> AsyncIterator[dict[str, Any]]:
        """Make a streaming call to the provider."""
        url, headers, body = self.build_request(request, model)
        
        import uuid
        request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async with client.stream("POST", url, headers=headers, json=body) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        if chunk:
                            async for parsed_chunk in self.parse_stream_chunk(chunk, model, request_id):
                                yield parsed_chunk
            except httpx.HTTPStatusError as e:
                detail = f"Provider returned status {e.response.status_code}"
                try:
                    error_data = await e.response.json()
                    if "error" in error_data:
                        detail = f"{detail}: {error_data['error']}"
                except Exception:
                    pass
                raise ProviderAdapterError(detail, e.response.status_code) from e
            except httpx.RequestError as e:
                raise ProviderAdapterError(f"Failed to stream from provider: {str(e)}") from e
