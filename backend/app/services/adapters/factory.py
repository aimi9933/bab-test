from __future__ import annotations

from typing import Any

from .openai import OpenAIAdapter
from .claude import ClaudeAdapter
from . import BaseAdapter


class AdapterFactory:
    """Factory for creating provider adapters."""
    
    @staticmethod
    def create_adapter(provider_name: str, base_url: str, api_key: str) -> BaseAdapter:
        """Create appropriate adapter based on provider name."""
        provider_name_lower = provider_name.lower()
        
        if "openai" in provider_name_lower or "gpt" in provider_name_lower:
            return OpenAIAdapter(provider_name, base_url, api_key)
        elif "claude" in provider_name_lower or "anthropic" in provider_name_lower:
            return ClaudeAdapter(provider_name, base_url, api_key)
        else:
            # Default to OpenAI adapter for unknown providers
            return OpenAIAdapter(provider_name, base_url, api_key)