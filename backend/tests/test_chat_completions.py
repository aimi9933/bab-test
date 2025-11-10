from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.db.models import ExternalAPI, ModelRoute, RouteNode
from backend.app.main import app
from backend.app.schemas.openai import ChatCompletionRequest, ChatMessage
from backend.app.schemas.route import ModelRouteCreate, RouteNodeCreate
from backend.app.services.adapters import OpenAIAdapter, AnthropicAdapter, GeminiAdapter
from backend.app.services.chat_completions import (
    ChatCompletionError,
    process_chat_completion,
    stream_chat_completion,
    _get_adapter_for_provider,
)
from backend.app.services.routing import get_routing_service


@pytest.fixture
def provider_openai(db_session: Session) -> ExternalAPI:
    provider = ExternalAPI(
        name="OpenAI",
        base_url="https://api.openai.com/v1",
        api_key_encrypted="encrypted_openai_key",
        models=["gpt-4", "gpt-3.5-turbo"],
        is_active=True,
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    return provider


@pytest.fixture
def provider_anthropic(db_session: Session) -> ExternalAPI:
    provider = ExternalAPI(
        name="Anthropic",
        base_url="https://api.anthropic.com",
        api_key_encrypted="encrypted_anthropic_key",
        models=["claude-3-opus", "claude-3-sonnet"],
        is_active=True,
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    return provider


@pytest.fixture
def provider_gemini(db_session: Session) -> ExternalAPI:
    provider = ExternalAPI(
        name="Google Gemini",
        base_url="https://generativelanguage.googleapis.com",
        api_key_encrypted="encrypted_gemini_key",
        models=["gemini-pro"],
        is_active=True,
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    return provider


@pytest.fixture
def route_auto(db_session: Session, provider_openai: ExternalAPI) -> ModelRoute:
    routing_service = get_routing_service()
    payload = ModelRouteCreate(
        name="test-auto",
        mode="auto",
        nodes=[
            RouteNodeCreate(api_id=provider_openai.id, models=["gpt-4"]),
        ],
    )
    route = routing_service.create_route(db_session, payload)
    return route


@pytest.fixture
def route_multi(
    db_session: Session, provider_openai: ExternalAPI, provider_anthropic: ExternalAPI
) -> ModelRoute:
    routing_service = get_routing_service()
    payload = ModelRouteCreate(
        name="test-multi",
        mode="multi",
        nodes=[
            RouteNodeCreate(
                api_id=provider_openai.id,
                models=["gpt-4"],
                priority=1,
                strategy="failover",
            ),
            RouteNodeCreate(
                api_id=provider_anthropic.id,
                models=["claude-3-opus"],
                priority=2,
                strategy="failover",
            ),
        ],
    )
    route = routing_service.create_route(db_session, payload)
    return route


class TestAdapterDetection:
    def test_get_adapter_openai_by_name(self, provider_openai: ExternalAPI):
        with patch("backend.app.services.chat_completions.decrypt_api_key", return_value="test-key"):
            adapter = _get_adapter_for_provider(provider_openai, 30.0)
            assert isinstance(adapter, OpenAIAdapter)

    def test_get_adapter_anthropic_by_name(self, provider_anthropic: ExternalAPI):
        with patch("backend.app.services.chat_completions.decrypt_api_key", return_value="test-key"):
            adapter = _get_adapter_for_provider(provider_anthropic, 30.0)
            assert isinstance(adapter, AnthropicAdapter)

    def test_get_adapter_gemini_by_name(self, provider_gemini: ExternalAPI):
        with patch("backend.app.services.chat_completions.decrypt_api_key", return_value="test-key"):
            adapter = _get_adapter_for_provider(provider_gemini, 30.0)
            assert isinstance(adapter, GeminiAdapter)


class TestOpenAIAdapter:
    def test_build_request_basic(self):
        adapter = OpenAIAdapter("https://api.openai.com/v1", "test-key", 30.0)
        request = ChatCompletionRequest(
            model="gpt-4",
            messages=[
                ChatMessage(role="user", content="Hello"),
            ],
        )
        
        url, headers, body = adapter.build_request(request, "gpt-4")
        
        assert url == "https://api.openai.com/v1/chat/completions"
        assert headers["Authorization"] == "Bearer test-key"
        assert body["model"] == "gpt-4"
        assert len(body["messages"]) == 1
        assert body["messages"][0]["role"] == "user"

    def test_build_request_with_params(self):
        adapter = OpenAIAdapter("https://api.openai.com/v1", "test-key", 30.0)
        request = ChatCompletionRequest(
            model="gpt-4",
            messages=[
                ChatMessage(role="user", content="Hello"),
            ],
            temperature=0.7,
            max_tokens=100,
            stream=True,
        )
        
        url, headers, body = adapter.build_request(request, "gpt-4")
        
        assert body["temperature"] == 0.7
        assert body["max_tokens"] == 100
        assert body["stream"] is True

    def test_parse_response(self):
        adapter = OpenAIAdapter("https://api.openai.com/v1", "test-key", 30.0)
        response_data = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello there!",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
        }
        
        result = adapter.parse_response(response_data, "gpt-4", "req-123")
        
        assert result == response_data


class TestAnthropicAdapter:
    def test_build_request_basic(self):
        adapter = AnthropicAdapter("https://api.anthropic.com", "test-key", 30.0)
        request = ChatCompletionRequest(
            model="claude-3-opus",
            messages=[
                ChatMessage(role="system", content="You are helpful"),
                ChatMessage(role="user", content="Hello"),
            ],
        )
        
        url, headers, body = adapter.build_request(request, "claude-3-opus")
        
        assert url == "https://api.anthropic.com/v1/messages"
        assert headers["x-api-key"] == "test-key"
        assert "system" in body
        assert body["system"] == "You are helpful"
        assert len(body["messages"]) == 1
        assert body["messages"][0]["role"] == "user"

    def test_parse_response(self):
        adapter = AnthropicAdapter("https://api.anthropic.com", "test-key", 30.0)
        response_data = {
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "Hello there!",
                }
            ],
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 20,
            },
        }
        
        result = adapter.parse_response(response_data, "claude-3-opus", "req-123")
        
        assert result["object"] == "chat.completion"
        assert result["choices"][0]["message"]["content"] == "Hello there!"
        assert result["choices"][0]["finish_reason"] == "stop"
        assert result["usage"]["prompt_tokens"] == 10
        assert result["usage"]["completion_tokens"] == 20


class TestGeminiAdapter:
    def test_build_request_basic(self):
        adapter = GeminiAdapter("https://generativelanguage.googleapis.com", "test-key", 30.0)
        request = ChatCompletionRequest(
            model="gemini-pro",
            messages=[
                ChatMessage(role="user", content="Hello"),
            ],
        )
        
        url, headers, body = adapter.build_request(request, "gemini-pro")
        
        assert "gemini-pro" in url
        assert ":generateContent" in url
        assert "key=test-key" in url
        assert len(body["contents"]) == 1
        assert body["contents"][0]["role"] == "user"

    def test_parse_response(self):
        adapter = GeminiAdapter("https://generativelanguage.googleapis.com", "test-key", 30.0)
        response_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "Hello there!",
                            }
                        ],
                        "role": "model",
                    },
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 10,
                "candidatesTokenCount": 20,
                "totalTokenCount": 30,
            },
        }
        
        result = adapter.parse_response(response_data, "gemini-pro", "req-123")
        
        assert result["object"] == "chat.completion"
        assert result["choices"][0]["message"]["content"] == "Hello there!"
        assert result["choices"][0]["finish_reason"] == "stop"
        assert result["usage"]["prompt_tokens"] == 10


class TestChatCompletionService:
    @pytest.mark.asyncio
    async def test_process_chat_completion_success(
        self, db_session: Session, route_auto: ModelRoute, provider_openai: ExternalAPI
    ):
        request = ChatCompletionRequest(
            model="test-auto",
            messages=[
                ChatMessage(role="user", content="Hello"),
            ],
        )
        
        mock_response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello there!",
                    },
                    "finish_reason": "stop",
                }
            ],
        }
        
        with patch("backend.app.services.chat_completions.decrypt_api_key", return_value="test-key"):
            with patch.object(OpenAIAdapter, "call_provider", new_callable=AsyncMock) as mock_call:
                mock_call.return_value = mock_response
                
                response = await process_chat_completion(db_session, request)
                
                assert response["id"] == "chatcmpl-123"
                assert response["choices"][0]["message"]["content"] == "Hello there!"
                mock_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_chat_completion_route_not_found(self, db_session: Session):
        request = ChatCompletionRequest(
            model="nonexistent-route",
            messages=[
                ChatMessage(role="user", content="Hello"),
            ],
        )
        
        with pytest.raises(ChatCompletionError) as exc_info:
            await process_chat_completion(db_session, request)
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_process_chat_completion_with_failover(
        self, db_session: Session, route_multi: ModelRoute, provider_openai: ExternalAPI, provider_anthropic: ExternalAPI
    ):
        # Mark first provider as inactive so routing picks the second one
        provider_openai.is_active = False
        db_session.commit()
        
        request = ChatCompletionRequest(
            model="test-multi",
            messages=[
                ChatMessage(role="user", content="Hello"),
            ],
        )
        
        mock_response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "claude-3-opus",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello from Claude!",
                    },
                    "finish_reason": "stop",
                }
            ],
        }
        
        async def mock_call_provider(self, request, model):
            return mock_response
        
        with patch("backend.app.services.chat_completions.decrypt_api_key", return_value="test-key"):
            with patch("backend.app.services.adapters.base.ProviderAdapter.call_provider", new=mock_call_provider):
                response = await process_chat_completion(db_session, request, max_retries=3)
                assert response["choices"][0]["message"]["content"] == "Hello from Claude!"

    @pytest.mark.asyncio
    async def test_stream_chat_completion_success(
        self, db_session: Session, route_auto: ModelRoute, provider_openai: ExternalAPI
    ):
        request = ChatCompletionRequest(
            model="test-auto",
            messages=[
                ChatMessage(role="user", content="Hello"),
            ],
            stream=True,
        )
        
        mock_chunks = [
            {
                "id": "chatcmpl-123",
                "object": "chat.completion.chunk",
                "created": 1234567890,
                "model": "gpt-4",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant"},
                        "finish_reason": None,
                    }
                ],
            },
            {
                "id": "chatcmpl-123",
                "object": "chat.completion.chunk",
                "created": 1234567890,
                "model": "gpt-4",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": "Hello"},
                        "finish_reason": None,
                    }
                ],
            },
            {
                "id": "chatcmpl-123",
                "object": "chat.completion.chunk",
                "created": 1234567890,
                "model": "gpt-4",
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop",
                    }
                ],
            },
        ]
        
        async def mock_stream_provider(self, request, model):
            for chunk in mock_chunks:
                yield chunk
        
        with patch("backend.app.services.chat_completions.decrypt_api_key", return_value="test-key"):
            with patch("backend.app.services.adapters.base.ProviderAdapter.stream_provider", new=mock_stream_provider):
                chunks = []
                async for chunk in stream_chat_completion(db_session, request):
                    chunks.append(chunk)
                
                assert len(chunks) == 3
                assert chunks[0]["choices"][0]["delta"]["role"] == "assistant"
                assert chunks[1]["choices"][0]["delta"]["content"] == "Hello"
                assert chunks[2]["choices"][0]["finish_reason"] == "stop"


class TestChatCompletionsEndpoint:
    def test_create_chat_completion_non_streaming(
        self, db_session: Session, route_auto: ModelRoute, provider_openai: ExternalAPI
    ):
        client = TestClient(app)
        
        mock_response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello there!",
                    },
                    "finish_reason": "stop",
                }
            ],
        }
        
        with patch("backend.app.services.chat_completions.decrypt_api_key", return_value="test-key"):
            with patch.object(OpenAIAdapter, "call_provider", new_callable=AsyncMock) as mock_call:
                mock_call.return_value = mock_response
                
                response = client.post(
                    "/v1/chat/completions",
                    json={
                        "model": "test-auto",
                        "messages": [
                            {"role": "user", "content": "Hello"},
                        ],
                    },
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == "chatcmpl-123"
                assert data["choices"][0]["message"]["content"] == "Hello there!"

    def test_create_chat_completion_with_auth_header(
        self, db_session: Session, route_auto: ModelRoute, provider_openai: ExternalAPI
    ):
        client = TestClient(app)
        
        mock_response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello there!",
                    },
                    "finish_reason": "stop",
                }
            ],
        }
        
        with patch("backend.app.services.chat_completions.decrypt_api_key", return_value="test-key"):
            with patch.object(OpenAIAdapter, "call_provider", new_callable=AsyncMock) as mock_call:
                mock_call.return_value = mock_response
                
                response = client.post(
                    "/v1/chat/completions",
                    headers={"Authorization": "Bearer my-secret-key"},
                    json={
                        "model": "test-auto",
                        "messages": [
                            {"role": "user", "content": "Hello"},
                        ],
                    },
                )
                
                assert response.status_code == 200

    def test_create_chat_completion_route_not_found(self, db_session: Session):
        client = TestClient(app)
        
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "nonexistent-route",
                "messages": [
                    {"role": "user", "content": "Hello"},
                ],
            },
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
