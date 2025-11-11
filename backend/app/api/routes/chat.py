from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...services.routing import get_routing_service

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    # Add other OpenAI-compatible parameters as needed
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[List[str]] | Optional[str] = None


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class UsageInfo(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


def get_default_route_id() -> int:
    """
    Get the default route ID for unified API access.
    For now, we'll use the first active route found.
    In the future, this could be configurable.
    """
    from ...db.models import ModelRoute
    from ...db.session import get_sessionmaker
    
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        route = db.query(ModelRoute).filter(ModelRoute.is_active == True).first()
        if not route:
            raise HTTPException(
                status_code=503,
                detail="No active routes configured. Please configure a route first."
            )
        return route.id


@router.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    http_request: Request,
    db: Session = Depends(get_db)
) -> ChatCompletionResponse:
    """
    Unified chat completions endpoint compatible with OpenAI API.
    
    This endpoint routes requests to configured providers using the routing system.
    """
    from ...services.providers import decrypt_api_key, construct_api_url
    
    # Get the routing service
    routing_service = get_routing_service()
    
    # Get default route ID (could be made configurable)
    try:
        route_id = get_default_route_id()
    except HTTPException:
        raise
    
    # Select provider and model using routing service
    try:
        provider_id, selected_model = routing_service.select_provider_and_model(
            db, route_id, request.model
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Routing failed: {str(e)}"
        )
    
    # Get provider details
    from ...db.models import ExternalAPI
    provider = db.query(ExternalAPI).filter(ExternalAPI.id == provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=503,
            detail="Selected provider not found"
        )
    
    # Check if provider is healthy
    if not provider.is_healthy:
        raise HTTPException(
            status_code=503,
            detail=f"Provider {provider.name} is currently unhealthy"
        )
    
    # Prepare request to external provider
    decrypted_key = decrypt_api_key(provider.api_key_encrypted)
    headers = {
        "Authorization": f"Bearer {decrypted_key}",
        "Content-Type": "application/json",
    }
    
    # Construct the request payload
    payload = {
        "model": selected_model,
        "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
    }
    
    # Add optional parameters if provided
    if request.temperature is not None:
        payload["temperature"] = request.temperature
    if request.max_tokens is not None:
        payload["max_tokens"] = request.max_tokens
    if request.stream is not None:
        payload["stream"] = request.stream
    if request.top_p is not None:
        payload["top_p"] = request.top_p
    if request.frequency_penalty is not None:
        payload["frequency_penalty"] = request.frequency_penalty
    if request.presence_penalty is not None:
        payload["presence_penalty"] = request.presence_penalty
    if request.stop is not None:
        payload["stop"] = request.stop
    
    # Make request to external provider
    url = construct_api_url(provider.base_url, "/chat/completions")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Provider request failed: {str(e)}"
        )
    
    # Transform response to match OpenAI format
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created = int(time.time())
    
    # Map the response
    choices = []
    for choice in result.get("choices", []):
        choices.append({
            "index": choice.get("index", 0),
            "message": {
                "role": choice.get("message", {}).get("role", "assistant"),
                "content": choice.get("message", {}).get("content", "")
            },
            "finish_reason": choice.get("finish_reason", "stop")
        })
    
    usage = result.get("usage", {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0
    })
    
    return ChatCompletionResponse(
        id=completion_id,
        created=created,
        model=selected_model,
        choices=choices,
        usage=usage
    )


@router.get("/v1/models")
async def list_models(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    List available models from all active providers.
    """
    from ...db.models import ExternalAPI
    
    providers = db.query(ExternalAPI).filter(
        ExternalAPI.is_active == True,
        ExternalAPI.is_healthy == True
    ).all()
    
    models = []
    for provider in providers:
        for model in provider.models:
            models.append({
                "id": model,
                "object": "model",
                "created": int(provider.created_at.timestamp()) if provider.created_at else 0,
                "owned_by": provider.name
            })
    
    return {
        "object": "list",
        "data": models
    }