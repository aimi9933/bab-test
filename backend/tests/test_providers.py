from __future__ import annotations

import json
from typing import Any

import httpx

from backend.app.core.security import decrypt_api_key
from backend.app.schemas.provider import ProviderCreate
from backend.app.services import providers as provider_service
from backend.app.services.backup import restore_from_backup


def _sample_payload(**overrides: Any) -> dict[str, Any]:
    data = {
        "name": "Test Provider",
        "base_url": "https://example.com/api",
        "api_key": "secret-key",
        "models": ["gpt-test"],
        "is_active": True,
    }
    data.update(overrides)
    return data


def test_create_provider_persists_and_updates_backup(db_session, settings):
    payload = ProviderCreate(**_sample_payload())
    provider = provider_service.create_provider(db_session, payload)

    backup_path = settings.backup_path
    assert backup_path.exists()

    backup = json.loads(backup_path.read_text())
    assert backup["providers"][0]["name"] == payload.name
    assert backup["providers"][0]["api_key_encrypted"] != payload.api_key
    assert decrypt_api_key(provider.api_key_encrypted) == payload.api_key


def test_restore_from_backup_repopulates_database(db_session, settings):
    payload = ProviderCreate(**_sample_payload())
    provider = provider_service.create_provider(db_session, payload)

    # Remove data without touching backup file to simulate data loss
    db_session.delete(provider)
    db_session.commit()

    restored = restore_from_backup(db_session)
    assert restored.get("providers", 0) == 1

    providers = provider_service.list_providers(db_session)
    assert len(providers) == 1
    assert providers[0].name == payload.name


def test_api_crud_flow(client):
    creation = client.post(
        "/api/providers",
        json=_sample_payload(name="API Provider", models=["model-a", "model-b"]),
    )
    assert creation.status_code == 201
    provider_id = creation.json()["id"]

    listing = client.get("/api/providers")
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    patch = client.patch(
        f"/api/providers/{provider_id}",
        json={"models": ["model-c"], "is_active": False},
    )
    assert patch.status_code == 200
    assert patch.json()["models"] == ["model-c"]
    assert patch.json()["is_active"] is False

    deletion = client.delete(f"/api/providers/{provider_id}")
    assert deletion.status_code == 204

    listing_after = client.get("/api/providers")
    assert listing_after.status_code == 200
    assert listing_after.json() == []


def test_test_endpoint_success(client, monkeypatch):
    creation = client.post("/api/providers", json=_sample_payload(name="Connectivity"))
    provider_id = creation.json()["id"]

    class DummyResponse:
        status_code = 200

        @property
        def is_success(self) -> bool:
            return True

    class DummyAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None):  # noqa: ARG002
            return DummyResponse()

    monkeypatch.setattr("backend.app.services.providers.httpx.AsyncClient", DummyAsyncClient)

    response = client.post(f"/api/providers/{provider_id}/test")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["status_code"] == 200
    assert "latency_ms" in data


def test_test_endpoint_failure_returns_502(client, monkeypatch):
    creation = client.post("/api/providers", json=_sample_payload(name="ConnectivityFail"))
    provider_id = creation.json()["id"]

    class FailingAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None):  # noqa: ARG002
            raise httpx.RequestError("boom")

    monkeypatch.setattr("backend.app.services.providers.httpx.AsyncClient", FailingAsyncClient)

    response = client.post(f"/api/providers/{provider_id}/test")
    assert response.status_code == 502
    assert response.json()["detail"] == "Failed to contact provider endpoint"


def test_test_direct_endpoint_success(client, monkeypatch):
    class DummyResponse:
        status_code = 200

        @property
        def is_success(self) -> bool:
            return True

    class DummyAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None):  # noqa: ARG002
            return DummyResponse()

    monkeypatch.setattr("backend.app.services.providers.httpx.AsyncClient", DummyAsyncClient)

    response = client.post(
        "/api/providers/test-direct",
        json={
            "base_url": "https://example.com/api",
            "api_key": "test-key",
            "models": ["model-1"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["status_code"] == 200
    assert "latency_ms" in data


def test_test_direct_endpoint_with_degraded_response(client, monkeypatch):
    class DummyResponse:
        status_code = 400

        @property
        def is_success(self) -> bool:
            return False

    class DummyAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None):  # noqa: ARG002
            return DummyResponse()

    monkeypatch.setattr("backend.app.services.providers.httpx.AsyncClient", DummyAsyncClient)

    response = client.post(
        "/api/providers/test-direct",
        json={
            "base_url": "https://example.com/api",
            "api_key": "test-key",
            "models": ["model-1"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["status_code"] == 400
    assert "Received status code 400" in data["detail"]


def test_test_direct_endpoint_timeout(client, monkeypatch):
    class TimeoutAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None):  # noqa: ARG002
            raise httpx.TimeoutException("timeout")

    monkeypatch.setattr("backend.app.services.providers.httpx.AsyncClient", TimeoutAsyncClient)

    response = client.post(
        "/api/providers/test-direct",
        json={
            "base_url": "https://example.com/api",
            "api_key": "test-key",
            "models": ["model-1"],
        },
    )
    assert response.status_code == 502
    assert response.json()["detail"] == "Timed out while contacting provider"


def test_test_direct_endpoint_network_error(client, monkeypatch):
    class FailingAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None):  # noqa: ARG002
            raise httpx.RequestError("network error")

    monkeypatch.setattr("backend.app.services.providers.httpx.AsyncClient", FailingAsyncClient)

    response = client.post(
        "/api/providers/test-direct",
        json={
            "base_url": "https://example.com/api",
            "api_key": "test-key",
            "models": ["model-1"],
        },
    )
    assert response.status_code == 502
    assert response.json()["detail"] == "Failed to contact provider endpoint"


def test_test_direct_endpoint_validation_error_empty_models(client):
    response = client.post(
        "/api/providers/test-direct",
        json={
            "base_url": "https://example.com/api",
            "api_key": "test-key",
            "models": [],
        },
    )
    assert response.status_code == 422


def test_test_direct_endpoint_validation_error_missing_api_key(client):
    response = client.post(
        "/api/providers/test-direct",
        json={
            "base_url": "https://example.com/api",
            "models": ["model-1"],
        },
    )
    assert response.status_code == 422


def test_test_direct_endpoint_validation_error_missing_url(client):
    response = client.post(
        "/api/providers/test-direct",
        json={
            "api_key": "test-key",
            "models": ["model-1"],
        },
    )
    assert response.status_code == 422


def test_test_direct_does_not_affect_database(client, monkeypatch, db_session):
    class DummyResponse:
        status_code = 200

        @property
        def is_success(self) -> bool:
            return True

    class DummyAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None):  # noqa: ARG002
            return DummyResponse()

    monkeypatch.setattr("backend.app.services.providers.httpx.AsyncClient", DummyAsyncClient)

    # Call test-direct endpoint
    response = client.post(
        "/api/providers/test-direct",
        json={
            "base_url": "https://example.com/api",
            "api_key": "test-key",
            "models": ["model-1"],
        },
    )
    assert response.status_code == 200

    # Verify database is empty (no provider was created)
    from backend.app.services import providers as provider_service

    providers = provider_service.list_providers(db_session)
    assert len(providers) == 0
