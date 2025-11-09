from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..db.models import ExternalAPI


def _serialize_provider(provider: ExternalAPI) -> dict:
    return {
        "name": provider.name,
        "base_url": provider.base_url,
        "api_key_encrypted": provider.api_key_encrypted,
        "models": provider.models or [],
        "is_active": provider.is_active,
        "status": provider.status,
        "latency_ms": provider.latency_ms,
        "last_tested_at": provider.last_tested_at.isoformat() if provider.last_tested_at else None,
        "created_at": provider.created_at.isoformat() if provider.created_at else None,
        "updated_at": provider.updated_at.isoformat() if provider.updated_at else None,
    }


def write_backup(session: Session) -> Path:
    settings = get_settings()
    backup_path = settings.backup_path
    providers: Iterable[ExternalAPI] = session.query(ExternalAPI).order_by(ExternalAPI.id).all()
    payload = {
        "generated_at": datetime.utcnow().isoformat(),
        "providers": [_serialize_provider(provider) for provider in providers],
    }
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return backup_path


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def restore_from_backup(session: Session) -> int:
    settings = get_settings()
    backup_path = settings.backup_path
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found at {backup_path}")

    data = json.loads(backup_path.read_text(encoding="utf-8"))
    providers = data.get("providers", [])
    restored = 0

    for item in providers:
        name = item.get("name")
        if not name:
            continue
        provider: ExternalAPI | None = (
            session.query(ExternalAPI).filter(ExternalAPI.name == name).one_or_none()
        )
        attrs = {
            "base_url": item.get("base_url"),
            "api_key_encrypted": item.get("api_key_encrypted"),
            "models": item.get("models") or [],
            "is_active": item.get("is_active", True),
            "status": item.get("status", "unknown"),
            "latency_ms": item.get("latency_ms"),
            "last_tested_at": _parse_datetime(item.get("last_tested_at")),
        }
        if provider is None:
            provider = ExternalAPI(name=name, **attrs)
            created_at = _parse_datetime(item.get("created_at"))
            updated_at = _parse_datetime(item.get("updated_at"))
            if created_at:
                provider.created_at = created_at
            if updated_at:
                provider.updated_at = updated_at
            session.add(provider)
            restored += 1
        else:
            for key, value in attrs.items():
                setattr(provider, key, value)
            restored += 1

    session.commit()
    write_backup(session)
    return restored
