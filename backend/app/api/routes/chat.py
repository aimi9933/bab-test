from __future__ import annotations

import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...db.session import get_db
from ...schemas.openai import ChatCompletionRequest
from ...services.chat_completions import (
    ChatCompletionError,
    process_chat_completion,
    stream_chat_completion,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["OpenAI Chat Completions"])


async def validate_api_key(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """
    Optional API key validation.
    
    For now, this is a placeholder. In production, you would validate the key
    against a database of API keys, check quotas, etc.
    """
    if not authorization:
        return None
    
    if authorization.startswith("Bearer "):
        return authorization[7:]
    
    return authorization


@router.post("/chat/completions", response_model=None)
async def create_chat_completion(
    request: ChatCompletionRequest,
    db: Session = Depends(get_db),
    api_key: Optional[str] = Depends(validate_api_key),
) -> Any:
    """
    Create a chat completion using the routing engine.
    
    This endpoint is OpenAI-compatible and supports both streaming and non-streaming modes.
    
    The `model` parameter in the request body should reference a route name configured
    in the routing engine. The routing engine will select an appropriate provider/model
    based on the route configuration.
    
    For streaming requests, set `stream: true` in the request body.
    """
    settings = get_settings()
    
    try:
        if request.stream:
            # Streaming response
            async def generate():
                try:
                    async for chunk in stream_chat_completion(
                        db,
                        request,
                        timeout=settings.request_timeout_seconds,
                    ):
                        # Format as SSE
                        chunk_json = json.dumps(chunk)
                        yield f"data: {chunk_json}\n\n"
                    
                    # Send final [DONE] message
                    yield "data: [DONE]\n\n"
                
                except ChatCompletionError as e:
                    logger.error(f"Streaming error: {e.message}")
                    error_chunk = {
                        "error": {
                            "message": e.message,
                            "type": "provider_error",
                            "code": e.status_code,
                        }
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"
                except Exception as e:
                    logger.error(f"Unexpected streaming error: {str(e)}")
                    error_chunk = {
                        "error": {
                            "message": str(e),
                            "type": "internal_error",
                            "code": 500,
                        }
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
            )
        else:
            # Non-streaming response
            response = await process_chat_completion(
                db,
                request,
                timeout=settings.request_timeout_seconds,
            )
            return response
    
    except ChatCompletionError as e:
        logger.error(f"Chat completion error: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise ChatCompletionError(str(e), 500) from e
