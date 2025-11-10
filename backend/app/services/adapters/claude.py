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


class ClaudeAdapter(BaseAdapter):
    """Adapter for Claude/Anthropic API to OpenAI-compatible format."""
    
    def __init__(self, provider_name: str, base_url: str, api_key: str):
        super().__init__(provider_name, base_url, api_key)
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def chat_completion(
        self, request: ChatCompletionRequest, model: str
    ) -> ChatCompletionResponse:
        """Convert OpenAI request to Claude format and convert response back."""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        
        # Convert OpenAI messages to Claude format
        claude_messages = self._convert_messages_to_claude(request.messages)
        
        payload = {
            "model": model,
            "messages": claude_messages,
            "max_tokens": request.max_tokens or 1024,
            "temperature": request.temperature,
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            return self._convert_claude_response_to_openai(data, model)
            
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
    
    def _convert_messages_to_claude(self, messages: list[ChatMessage]) -> list[dict[str, Any]]:
        """Convert OpenAI message format to Claude format."""
        claude_messages = []
        system_message = None
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            elif msg.role == "user":
                claude_messages.append({
                    "role": "user",
                    "content": msg.content
                })
            elif msg.role == "assistant":
                claude_messages.append({
                    "role": "assistant", 
                    "content": msg.content
                })
        
        # Claude expects system message as a separate field
        if system_message:
            # Insert system message at the beginning
            claude_messages.insert(0, {
                "role": "user",
                "content": f"System: {system_message}\n\nPlease follow these system instructions in your response."
            })
        
        return claude_messages
    
    def _convert_claude_response_to_openai(self, claude_response: dict[str, Any], model: str) -> ChatCompletionResponse:
        """Convert Claude response format to OpenAI format."""
        created = int(time.time())
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
        
        # Extract content from Claude response
        content = claude_response.get("content", [])
        if content and isinstance(content, list):
            text_content = content[0].get("text", "")
        else:
            text_content = str(content)
        
        # Create OpenAI-compatible choice
        choice = ChatCompletionChoice(
            index=0,
            message=ChatMessage(role="assistant", content=text_content),
            finish_reason="stop"
        )
        
        # Estimate usage (Claude doesn't always provide exact counts)
        usage = ChatCompletionUsage(
            prompt_tokens=claude_response.get("usage", {}).get("input_tokens", 0),
            completion_tokens=claude_response.get("usage", {}).get("output_tokens", 0),
            total_tokens=claude_response.get("usage", {}).get("input_tokens", 0) + claude_response.get("usage", {}).get("output_tokens", 0)
        )
        
        return ChatCompletionResponse(
            id=completion_id,
            created=created,
            model=model,
            choices=[choice],
            usage=usage
        )
    
    def supports_model(self, model: str) -> bool:
        """Check if model is a Claude model."""
        return model.startswith(("claude-", "anthropic-"))
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()