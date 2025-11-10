from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Optional

from sqlalchemy.orm import Session

from ..core.security import decrypt_api_key
from ..db.models import ExternalAPI
from ..schemas.openai import ChatCompletionRequest
from .adapters import AnthropicAdapter, GeminiAdapter, OpenAIAdapter, ProviderAdapter
from .adapters.base import ProviderAdapterError
from .routing import RouteServiceError, get_routing_service

logger = logging.getLogger(__name__)


class ChatCompletionError(Exception):
    """Base exception for chat completion errors."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _get_adapter_for_provider(provider: ExternalAPI, timeout: float) -> ProviderAdapter:
    """Get the appropriate adapter based on provider type."""
    api_key = decrypt_api_key(provider.api_key_encrypted)
    base_url = provider.base_url
    
    # Detect provider type by base URL or name
    name_lower = provider.name.lower()
    url_lower = base_url.lower()
    
    if "anthropic" in name_lower or "anthropic.com" in url_lower or "claude" in name_lower:
        return AnthropicAdapter(base_url, api_key, timeout)
    elif "gemini" in name_lower or "googleapis.com" in url_lower or "google" in name_lower:
        return GeminiAdapter(base_url, api_key, timeout)
    else:
        # Default to OpenAI-compatible adapter
        return OpenAIAdapter(base_url, api_key, timeout)


async def process_chat_completion(
    session: Session,
    request: ChatCompletionRequest,
    route_name: Optional[str] = None,
    timeout: float = 30.0,
    max_retries: int = 3,
) -> dict[str, Any]:
    """
    Process a chat completion request using the routing engine.
    
    Args:
        session: Database session
        request: Chat completion request
        route_name: Optional route name to use (defaults to request.model)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
    
    Returns:
        OpenAI-compatible response dict
    
    Raises:
        ChatCompletionError: If all providers fail
    """
    routing_service = get_routing_service()
    
    # Determine which route to use
    effective_route_name = route_name or request.model
    
    # Try to find route by name
    routes = routing_service.list_routes(session)
    route = None
    for r in routes:
        if r.name == effective_route_name:
            route = r
            break
    
    if not route:
        raise ChatCompletionError(f"Route '{effective_route_name}' not found", 404)
    
    if not route.is_active:
        raise ChatCompletionError(f"Route '{effective_route_name}' is not active", 400)
    
    # Track attempted providers to avoid retrying the same one
    attempted_providers = set()
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Select provider/model via routing engine
            provider_id, model = routing_service.select_provider_and_model(
                session, route.id, request.model if route_name else None
            )
            
            # Skip if we've already tried this provider
            if provider_id in attempted_providers:
                logger.warning(f"Skipping already attempted provider {provider_id}")
                continue
            
            attempted_providers.add(provider_id)
            
            # Get provider details
            provider = session.get(ExternalAPI, provider_id)
            if not provider:
                logger.error(f"Provider {provider_id} not found")
                continue
            
            logger.info(f"Attempt {attempt + 1}: Using provider {provider.name} with model {model}")
            
            # Get appropriate adapter
            adapter = _get_adapter_for_provider(provider, timeout)
            
            # Make the call
            response = await adapter.call_provider(request, model)
            logger.info(f"Successfully completed request with provider {provider.name}")
            return response
        
        except (RouteServiceError, ProviderAdapterError) as e:
            last_error = e
            status_code = getattr(e, "status_code", None) or 500
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            
            # If this is a 4xx error from the provider, don't retry
            if status_code >= 400 and status_code < 500:
                raise ChatCompletionError(str(e), status_code) from e
            
            # Continue to next attempt
            continue
        
        except Exception as e:
            last_error = e
            logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
            continue
    
    # All retries exhausted
    error_msg = f"All providers failed after {max_retries} attempts"
    if last_error:
        error_msg += f": {str(last_error)}"
    
    status_code = getattr(last_error, "status_code", None) or 502
    raise ChatCompletionError(error_msg, status_code)


async def stream_chat_completion(
    session: Session,
    request: ChatCompletionRequest,
    route_name: Optional[str] = None,
    timeout: float = 30.0,
    max_retries: int = 3,
) -> AsyncIterator[dict[str, Any]]:
    """
    Process a streaming chat completion request using the routing engine.
    
    Args:
        session: Database session
        request: Chat completion request
        route_name: Optional route name to use (defaults to request.model)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
    
    Yields:
        OpenAI-compatible chunk dicts
    
    Raises:
        ChatCompletionError: If all providers fail
    """
    routing_service = get_routing_service()
    
    # Determine which route to use
    effective_route_name = route_name or request.model
    
    # Try to find route by name
    routes = routing_service.list_routes(session)
    route = None
    for r in routes:
        if r.name == effective_route_name:
            route = r
            break
    
    if not route:
        raise ChatCompletionError(f"Route '{effective_route_name}' not found", 404)
    
    if not route.is_active:
        raise ChatCompletionError(f"Route '{effective_route_name}' is not active", 400)
    
    # Track attempted providers to avoid retrying the same one
    attempted_providers = set()
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Select provider/model via routing engine
            provider_id, model = routing_service.select_provider_and_model(
                session, route.id, request.model if route_name else None
            )
            
            # Skip if we've already tried this provider
            if provider_id in attempted_providers:
                logger.warning(f"Skipping already attempted provider {provider_id}")
                continue
            
            attempted_providers.add(provider_id)
            
            # Get provider details
            provider = session.get(ExternalAPI, provider_id)
            if not provider:
                logger.error(f"Provider {provider_id} not found")
                continue
            
            logger.info(f"Attempt {attempt + 1}: Streaming from provider {provider.name} with model {model}")
            
            # Get appropriate adapter
            adapter = _get_adapter_for_provider(provider, timeout)
            
            # Stream the response
            async for chunk in adapter.stream_provider(request, model):
                yield chunk
            
            logger.info(f"Successfully completed streaming request with provider {provider.name}")
            return
        
        except (RouteServiceError, ProviderAdapterError) as e:
            last_error = e
            status_code = getattr(e, "status_code", None) or 500
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            
            # If this is a 4xx error from the provider, don't retry
            if status_code >= 400 and status_code < 500:
                raise ChatCompletionError(str(e), status_code) from e
            
            # Continue to next attempt
            continue
        
        except Exception as e:
            last_error = e
            logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
            continue
    
    # All retries exhausted
    error_msg = f"All providers failed after {max_retries} attempts"
    if last_error:
        error_msg += f": {str(last_error)}"
    
    status_code = getattr(last_error, "status_code", None) or 502
    raise ChatCompletionError(error_msg, status_code)
