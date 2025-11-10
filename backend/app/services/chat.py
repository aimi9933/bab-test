from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from ..db.models import ExternalAPI
from ..schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionError,
)
from ..services.adapters.factory import AdapterFactory
from ..services.routing import get_routing_service, RouteServiceError
from ..core.security import decrypt_api_key


logger = logging.getLogger(__name__)


class ChatCompletionError(Exception):
    """Base exception for chat completion errors."""
    pass


class ChatCompletionService:
    """Service for handling chat completions with routing and adapter management."""
    
    def __init__(self):
        self.routing_service = get_routing_service()
    
    async def complete_chat(
        self, 
        session: Session, 
        request: ChatCompletionRequest,
        route_id: int | None = None
    ) -> ChatCompletionResponse:
        """
        Process a chat completion request using routing service.
        
        Args:
            session: Database session
            request: Chat completion request
            route_id: Optional route ID to use (defaults to finding by model)
            
        Returns:
            OpenAI-compatible chat completion response
            
        Raises:
            ChatCompletionError: If completion fails
        """
        if route_id is None:
            # Try to find a route for the model
            route_id = self._find_route_for_model(session, request.model)
        
        # Get provider and model from routing service
        try:
            api_id, selected_model = self.routing_service.select_provider_and_model(
                session, route_id, request.model
            )
        except RouteServiceError as e:
            logger.error(f"Routing error for model {request.model}: {e}")
            raise ChatCompletionError(f"Routing failed: {e}")
        
        # Get provider details
        provider = session.get(ExternalAPI, api_id)
        if not provider:
            raise ChatCompletionError(f"Provider with id {api_id} not found")
        
        # Create adapter and process request
        adapter = AdapterFactory.create_adapter(
            provider.name, 
            provider.base_url, 
            decrypt_api_key(provider.api_key_encrypted)
        )
        
        try:
            async with adapter:
                response = await adapter.chat_completion(request, selected_model)
                logger.info(f"Successfully completed chat with {provider.name} using model {selected_model}")
                return response
        except Exception as e:
            logger.error(f"Error completing chat with {provider.name}: {e}")
            
            # Try fallback providers if available
            return await self._try_fallback_providers(session, request, route_id, api_id, selected_model)
    
    async def _try_fallback_providers(
        self,
        session: Session,
        request: ChatCompletionRequest,
        route_id: int,
        failed_api_id: int,
        failed_model: str
    ) -> ChatCompletionResponse:
        """Try alternative providers in the route after a failure."""
        max_retries = 3
        attempts = 0
        
        while attempts < max_retries:
            try:
                api_id, selected_model = self.routing_service.select_provider_and_model(
                    session, route_id, request.model
                )
                
                # Skip the failed provider
                if api_id == failed_api_id:
                    attempts += 1
                    continue
                
                provider = session.get(ExternalAPI, api_id)
                if not provider:
                    attempts += 1
                    continue
                
                adapter = AdapterFactory.create_adapter(
                    provider.name,
                    provider.base_url,
                    decrypt_api_key(provider.api_key_encrypted)
                )
                
                async with adapter:
                    response = await adapter.chat_completion(request, selected_model)
                    logger.info(f"Fallback successful with {provider.name} using model {selected_model}")
                    return response
                    
            except Exception as e:
                logger.warning(f"Fallback attempt {attempts + 1} failed: {e}")
                attempts += 1
        
        raise ChatCompletionError(f"All providers failed for model {request.model}")
    
    def _find_route_for_model(self, session: Session, model: str) -> int:
        """Find a route that supports the given model."""
        routes = self.routing_service.list_routes(session)
        
        for route in routes:
            if not route.is_active:
                continue
                
            # Check if any provider in this route supports the model
            for node in route.route_nodes:
                provider = session.get(ExternalAPI, node.api_id)
                if provider and provider.is_active:
                    node_models = node.models or provider.models or []
                    if model in node_models:
                        return route.id
        
        raise ChatCompletionError(f"No active route found for model {model}")


_chat_completion_service = ChatCompletionService()


def get_chat_completion_service() -> ChatCompletionService:
    return _chat_completion_service