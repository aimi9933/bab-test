from __future__ import annotations

import json
import time
from typing import Any, AsyncIterator

from ...schemas.openai import ChatCompletionRequest
from .base import ProviderAdapter


class OpenAIAdapter(ProviderAdapter):
    """Adapter for OpenAI-compatible APIs (OpenAI, Azure OpenAI, etc.)."""

    def build_request(
        self, request: ChatCompletionRequest, model: str
    ) -> tuple[str, dict[str, str], dict[str, Any]]:
        """Build OpenAI-compatible request."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        body = {
            "model": model,
            "messages": [msg.model_dump(exclude_none=True) for msg in request.messages],
        }
        
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.top_p is not None:
            body["top_p"] = request.top_p
        if request.n is not None:
            body["n"] = request.n
        if request.stream is not None:
            body["stream"] = request.stream
        if request.stop is not None:
            body["stop"] = request.stop
        if request.max_tokens is not None:
            body["max_tokens"] = request.max_tokens
        if request.presence_penalty is not None:
            body["presence_penalty"] = request.presence_penalty
        if request.frequency_penalty is not None:
            body["frequency_penalty"] = request.frequency_penalty
        if request.logit_bias is not None:
            body["logit_bias"] = request.logit_bias
        if request.user is not None:
            body["user"] = request.user
        if request.functions is not None:
            body["functions"] = request.functions
        if request.function_call is not None:
            body["function_call"] = request.function_call
        
        return url, headers, body

    def parse_response(self, response_data: dict[str, Any], model: str, request_id: str) -> dict[str, Any]:
        """Parse OpenAI response - mostly passthrough."""
        return response_data

    async def parse_stream_chunk(
        self, chunk: bytes, model: str, request_id: str
    ) -> AsyncIterator[dict[str, Any]]:
        """Parse OpenAI SSE chunks."""
        lines = chunk.decode("utf-8").strip().split("\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("data: "):
                data = line[6:]
                
                if data == "[DONE]":
                    continue
                
                try:
                    chunk_data = json.loads(data)
                    yield chunk_data
                except json.JSONDecodeError:
                    continue
