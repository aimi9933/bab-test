from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings, reset_settings_cache
from backend.app.db.init_db import init_db
from backend.app.db.session import dispose_engine, get_db, get_sessionmaker
from backend.app.main import app


@pytest.fixture(autouse=True)
def _configure_test_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    db_file = tmp_path / "test.sqlite3"
    backup_file = tmp_path / "backup.json"

    monkeypatch.setenv("BACKEND_DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("BACKEND_BACKUP_FILE", str(backup_file))
    monkeypatch.setenv("BACKEND_API_KEY_SECRET", "tests-secret-key")
    monkeypatch.setenv("BACKEND_HEALTH_CHECK_ENABLED", "false")

    reset_settings_cache()
    dispose_engine()
    init_db()

    yield

    dispose_engine()
    reset_settings_cache()


@pytest.fixture()
def db_session() -> Generator:
    SessionLocal = get_sessionmaker()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    SessionLocal = get_sessionmaker()

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def settings():
    return get_settings()
