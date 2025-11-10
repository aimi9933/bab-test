from __future__ import annotations

import json
import time
from typing import Any, AsyncIterator

from ...schemas.openai import ChatCompletionRequest
from .base import ProviderAdapter


class GeminiAdapter(ProviderAdapter):
    """Adapter for Google Gemini API."""

    def build_request(
        self, request: ChatCompletionRequest, model: str
    ) -> tuple[str, dict[str, str], dict[str, Any]]:
        """Build Gemini-specific request."""
        stream_suffix = ":streamGenerateContent?alt=sse" if request.stream else ":generateContent"
        url = f"{self.base_url}/v1/models/{model}{stream_suffix}"
        
        headers = {
            "Content-Type": "application/json",
        }
        
        # Convert messages to Gemini format
        contents = []
        system_instruction = None
        
        for msg in request.messages:
            if msg.role == "system":
                system_instruction = {"parts": [{"text": msg.content or ""}]}
            else:
                role = "model" if msg.role == "assistant" else "user"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.content or ""}]
                })
        
        body = {
            "contents": contents,
        }
        
        if system_instruction:
            body["systemInstruction"] = system_instruction
        
        generation_config = {}
        if request.temperature is not None:
            generation_config["temperature"] = request.temperature
        if request.top_p is not None:
            generation_config["topP"] = request.top_p
        if request.max_tokens is not None:
            generation_config["maxOutputTokens"] = request.max_tokens
        if request.stop is not None:
            if isinstance(request.stop, str):
                generation_config["stopSequences"] = [request.stop]
            else:
                generation_config["stopSequences"] = request.stop
        
        if generation_config:
            body["generationConfig"] = generation_config
        
        # Add API key as query parameter
        url = f"{url}&key={self.api_key}"
        
        return url, headers, body

    def parse_response(self, response_data: dict[str, Any], model: str, request_id: str) -> dict[str, Any]:
        """Parse Gemini response into OpenAI format."""
        content = ""
        finish_reason = None
        
        if "candidates" in response_data and response_data["candidates"]:
            candidate = response_data["candidates"][0]
            
            if "content" in candidate and "parts" in candidate["content"]:
                for part in candidate["content"]["parts"]:
                    if "text" in part:
                        content += part["text"]
            
            if "finishReason" in candidate:
                finish_reason_map = {
                    "STOP": "stop",
                    "MAX_TOKENS": "length",
                    "SAFETY": "content_filter",
                    "RECITATION": "content_filter",
                }
                finish_reason = finish_reason_map.get(candidate["finishReason"], "stop")
        
        usage = None
        if "usageMetadata" in response_data:
            metadata = response_data["usageMetadata"]
            usage = {
                "prompt_tokens": metadata.get("promptTokenCount", 0),
                "completion_tokens": metadata.get("candidatesTokenCount", 0),
                "total_tokens": metadata.get("totalTokenCount", 0),
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
        """Parse Gemini SSE chunks into OpenAI format."""
        lines = chunk.decode("utf-8").strip().split("\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("data: "):
                data = line[6:]
                
                try:
                    event_data = json.loads(data)
                    
                    if "candidates" in event_data and event_data["candidates"]:
                        candidate = event_data["candidates"][0]
                        
                        content = ""
                        if "content" in candidate and "parts" in candidate["content"]:
                            for part in candidate["content"]["parts"]:
                                if "text" in part:
                                    content += part["text"]
                        
                        finish_reason = None
                        if "finishReason" in candidate:
                            finish_reason_map = {
                                "STOP": "stop",
                                "MAX_TOKENS": "length",
                                "SAFETY": "content_filter",
                                "RECITATION": "content_filter",
                            }
                            finish_reason = finish_reason_map.get(candidate["finishReason"], "stop")
                        
                        delta = {}
                        if content:
                            delta["content"] = content
                        
                        yield {
                            "id": request_id,
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": delta,
                                    "finish_reason": finish_reason,
                                }
                            ],
                        }
                
                except json.JSONDecodeError:
                    continue
