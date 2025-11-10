from __future__ import annotations

import json
import time
import uuid
from typing import Any, AsyncIterator

from ...schemas.openai import ChatCompletionRequest
from .base import ProviderAdapter


class AnthropicAdapter(ProviderAdapter):
    """Adapter for Anthropic Claude API."""

    def build_request(
        self, request: ChatCompletionRequest, model: str
    ) -> tuple[str, dict[str, str], dict[str, Any]]:
        """Build Anthropic-specific request."""
        url = f"{self.base_url}/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        
        # Convert messages to Anthropic format
        system_message = None
        messages = []
        for msg in request.messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                messages.append({
                    "role": msg.role,
                    "content": msg.content or ""
                })
        
        body = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens or 1024,
        }
        
        if system_message:
            body["system"] = system_message
        
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.top_p is not None:
            body["top_p"] = request.top_p
        if request.stop is not None:
            if isinstance(request.stop, str):
                body["stop_sequences"] = [request.stop]
            else:
                body["stop_sequences"] = request.stop
        if request.stream:
            body["stream"] = True
        
        return url, headers, body

    def parse_response(self, response_data: dict[str, Any], model: str, request_id: str) -> dict[str, Any]:
        """Parse Anthropic response into OpenAI format."""
        content = ""
        if "content" in response_data and response_data["content"]:
            for block in response_data["content"]:
                if block.get("type") == "text":
                    content += block.get("text", "")
        
        finish_reason = None
        if "stop_reason" in response_data:
            stop_reason_map = {
                "end_turn": "stop",
                "max_tokens": "length",
                "stop_sequence": "stop",
            }
            finish_reason = stop_reason_map.get(response_data["stop_reason"], response_data["stop_reason"])
        
        usage = None
        if "usage" in response_data:
            usage = {
                "prompt_tokens": response_data["usage"].get("input_tokens", 0),
                "completion_tokens": response_data["usage"].get("output_tokens", 0),
                "total_tokens": response_data["usage"].get("input_tokens", 0) + response_data["usage"].get("output_tokens", 0),
            }
        
        return {
            "id": request_id,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content,
                    },
                    "finish_reason": finish_reason,
                }
            ],
            "usage": usage,
        }

    async def parse_stream_chunk(
        self, chunk: bytes, model: str, request_id: str
    ) -> AsyncIterator[dict[str, Any]]:
        """Parse Anthropic SSE chunks into OpenAI format."""
        lines = chunk.decode("utf-8").strip().split("\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("data: "):
                data = line[6:]
                
                try:
                    event_data = json.loads(data)
                    event_type = event_data.get("type")
                    
                    if event_type == "content_block_delta":
                        delta = event_data.get("delta", {})
                        if delta.get("type") == "text_delta":
                            text = delta.get("text", "")
                            if text:
                                yield {
                                    "id": request_id,
                                    "object": "chat.completion.chunk",
                                    "created": int(time.time()),
                                    "model": model,
                                    "choices": [
                                        {
                                            "index": 0,
                                            "delta": {
                                                "content": text,
                                            },
                                            "finish_reason": None,
                                        }
                                    ],
                                }
                    
                    elif event_type == "message_start":
                        yield {
                            "id": request_id,
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {
                                        "role": "assistant",
                                    },
                                    "finish_reason": None,
                                }
                            ],
                        }
                    
                    elif event_type == "message_delta":
                        delta = event_data.get("delta", {})
                        stop_reason = delta.get("stop_reason")
                        if stop_reason:
                            stop_reason_map = {
                                "end_turn": "stop",
                                "max_tokens": "length",
                                "stop_sequence": "stop",
                            }
                            finish_reason = stop_reason_map.get(stop_reason, stop_reason)
                            yield {
                                "id": request_id,
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": model,
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": {},
                                        "finish_reason": finish_reason,
                                    }
                                ],
                            }
                
                except json.JSONDecodeError:
                    continue
