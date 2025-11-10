from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionError,
)
from ...services.chat import get_chat_completion_service, ChatCompletionError as ChatServiceError


router = APIRouter()


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    db: Session = Depends(get_db),
) -> ChatCompletionResponse:
    """
    OpenAI-compatible chat completions endpoint.
    
    This endpoint accepts OpenAI-formatted requests and routes them through
    the configured providers based on model selection and routing rules.
    """
    if request.stream:
        raise HTTPException(
            status_code=400,
            detail="Streaming is not yet supported. Set stream=false."
        )
    
    chat_service = get_chat_completion_service()
    
    try:
        response = await chat_service.complete_chat(db, request)
        return response
    except ChatServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")