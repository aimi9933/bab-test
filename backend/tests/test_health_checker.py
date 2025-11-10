from __future__ import annotations

import asyncio
from typing import Any

import httpx

from backend.app.schemas.provider import ProviderCreate
from backend.app.services import providers as provider_service
from backend.app.services.health_checker import get_health_checker


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


def test_provider_starts_healthy(db_session):
    payload = ProviderCreate(**_sample_payload(name="Healthy Provider"))
    provider = provider_service.create_provider(db_session, payload)

    assert provider.is_healthy is True
    assert provider.consecutive_failures == 0
    assert provider.status == "unknown"


def test_health_override_endpoint(client):
    creation = client.post("/api/providers", json=_sample_payload(name="Override Provider"))
    provider_id = creation.json()["id"]
    assert creation.json()["is_healthy"] is True

    response = client.patch(
        f"/api/providers/{provider_id}/health",
        json={"is_healthy": False}
    )
    assert response.status_code == 200
    assert response.json()["is_healthy"] is False
    assert response.json()["consecutive_failures"] == 0

    response = client.patch(
        f"/api/providers/{provider_id}/health",
        json={"is_healthy": True}
    )
    assert response.status_code == 200
    assert response.json()["is_healthy"] is True


def test_health_checker_simulation_with_mock(db_session, monkeypatch, settings):
    payload = ProviderCreate(**_sample_payload(name="Mock Provider"))
    provider = provider_service.create_provider(db_session, payload)
    provider_id = provider.id

    class MockResponse:
        def __init__(self, status_code=200):
            self.status_code = status_code

        @property
        def is_success(self) -> bool:
            return 200 <= self.status_code < 300

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            self.call_count = 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None):
            self.call_count += 1
            return MockResponse(200)

    monkeypatch.setattr("backend.app.services.health_checker.httpx.AsyncClient", MockAsyncClient)

    async def run_check():
        health_checker = get_health_checker()
        await health_checker._run_checks()

    asyncio.run(run_check())

    db_session.refresh(provider)
    assert provider.status == "online"
    assert provider.consecutive_failures == 0
    assert provider.is_healthy is True


def test_health_checker_failure_accumulation(db_session, monkeypatch, settings):
    monkeypatch.setenv("BACKEND_HEALTH_CHECK_FAILURE_THRESHOLD", "3")

    from backend.app.core.config import reset_settings_cache
    reset_settings_cache()

    payload = ProviderCreate(**_sample_payload(name="Failing Provider"))
    provider = provider_service.create_provider(db_session, payload)
    provider_id = provider.id

    class FailingAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None):
            raise httpx.RequestError("Connection failed")

    monkeypatch.setattr("backend.app.services.health_checker.httpx.AsyncClient", FailingAsyncClient)

    async def run_check_multiple():
        health_checker = get_health_checker()
        for _ in range(3):
            await health_checker._run_checks()

    asyncio.run(run_check_multiple())

    db_session.refresh(provider)
    assert provider.status == "unreachable"
    assert provider.consecutive_failures == 3
    assert provider.is_healthy is False


def test_health_recovery_resets_failures(db_session, monkeypatch):
    payload = ProviderCreate(**_sample_payload(name="Recovery Provider"))
    provider = provider_service.create_provider(db_session, payload)
    provider.consecutive_failures = 5
    provider.is_healthy = False
    db_session.commit()

    class MockResponse:
        status_code = 200

        @property
        def is_success(self) -> bool:
            return True

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None):
            return MockResponse()

    monkeypatch.setattr("backend.app.services.health_checker.httpx.AsyncClient", MockAsyncClient)

    async def run_check():
        health_checker = get_health_checker()
        await health_checker._run_checks()

    asyncio.run(run_check())

    db_session.refresh(provider)
    assert provider.status == "online"
    assert provider.consecutive_failures == 0
    assert provider.is_healthy is True


def test_health_check_timeout_response(db_session, monkeypatch):
    payload = ProviderCreate(**_sample_payload(name="Timeout Provider"))
    provider = provider_service.create_provider(db_session, payload)

    class TimeoutAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None):
            raise httpx.TimeoutException("Timed out")

    monkeypatch.setattr("backend.app.services.health_checker.httpx.AsyncClient", TimeoutAsyncClient)

    async def run_check():
        health_checker = get_health_checker()
        await health_checker._run_checks()

    asyncio.run(run_check())

    db_session.refresh(provider)
    assert provider.status == "timeout"
    assert provider.latency_ms is None
    assert provider.consecutive_failures == 1


def test_provider_list_includes_health_fields(client):
    creation = client.post("/api/providers", json=_sample_payload(name="Health Fields"))
    provider_id = creation.json()["id"]

    response = client.get(f"/api/providers/{provider_id}")
    assert response.status_code == 200
    data = response.json()

    assert "is_healthy" in data
    assert "consecutive_failures" in data
    assert data["is_healthy"] is True
    assert data["consecutive_failures"] == 0


def test_health_fields_persist_in_backup_and_restore(db_session, settings):
    import json
    from backend.app.services.backup import restore_from_backup

    payload = ProviderCreate(**_sample_payload(name="Backup Test Provider"))
    provider = provider_service.create_provider(db_session, payload)

    provider.consecutive_failures = 2
    provider.is_healthy = False
    db_session.commit()

    backup_path = settings.backup_path
    backup = json.loads(backup_path.read_text())

    provider_backup = backup["providers"][0]
    assert provider_backup["consecutive_failures"] == 2
    assert provider_backup["is_healthy"] is False

    db_session.delete(provider)
    db_session.commit()

    restored = restore_from_backup(db_session)
    restored_provider = provider_service.list_providers(db_session)[0]

    assert restored_provider.consecutive_failures == 2
    assert restored_provider.is_healthy is False
