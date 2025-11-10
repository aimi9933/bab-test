from __future__ import annotations

from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Represents a chat message in the conversation."""
    role: Literal["system", "user", "assistant", "function"] = Field(...)
    content: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    function_call: Optional[dict[str, Any]] = Field(default=None)


class FunctionCall(BaseModel):
    """Function call parameters."""
    name: str
    arguments: str


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""
    model: str = Field(..., description="Model name or route name to use")
    messages: list[ChatMessage] = Field(..., min_length=1)
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    n: Optional[int] = Field(default=1, ge=1)
    stream: Optional[bool] = Field(default=False)
    stop: Optional[Union[str, list[str]]] = Field(default=None)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    logit_bias: Optional[dict[str, float]] = Field(default=None)
    user: Optional[str] = Field(default=None)
    functions: Optional[list[dict[str, Any]]] = Field(default=None)
    function_call: Optional[Union[str, dict[str, str]]] = Field(default=None)


class ChatCompletionUsage(BaseModel):
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionMessage(BaseModel):
    """Message in a chat completion response."""
    role: str
    content: Optional[str] = None
    function_call: Optional[FunctionCall] = None


class ChatCompletionChoice(BaseModel):
    """A single completion choice."""
    index: int
    message: ChatCompletionMessage
    finish_reason: Optional[str] = None


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: Optional[ChatCompletionUsage] = None
    system_fingerprint: Optional[str] = None


class ChatCompletionChunkDelta(BaseModel):
    """Delta content in a streaming chunk."""
    role: Optional[str] = None
    content: Optional[str] = None
    function_call: Optional[dict[str, Any]] = None


class ChatCompletionChunkChoice(BaseModel):
    """A single choice in a streaming chunk."""
    index: int
    delta: ChatCompletionChunkDelta
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    """OpenAI-compatible streaming chunk."""
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: list[ChatCompletionChunkChoice]
    system_fingerprint: Optional[str] = None
