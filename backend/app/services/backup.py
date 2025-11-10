from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..db.models import ExternalAPI, ModelRoute, RouteNode


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
        "consecutive_failures": provider.consecutive_failures,
        "is_healthy": provider.is_healthy,
        "created_at": provider.created_at.isoformat() if provider.created_at else None,
        "updated_at": provider.updated_at.isoformat() if provider.updated_at else None,
    }


def _serialize_route_node(node: RouteNode) -> dict:
    provider = node.api
    return {
        "api_name": provider.name if provider else None,
        "models": node.models or [],
        "strategy": node.strategy,
        "priority": node.priority,
        "metadata": node.node_metadata or {},
    }


def _serialize_route(route: ModelRoute) -> dict:
    return {
        "name": route.name,
        "mode": route.mode,
        "config": route.config or {},
        "is_active": route.is_active,
        "nodes": [_serialize_route_node(node) for node in route.route_nodes],
        "created_at": route.created_at.isoformat() if route.created_at else None,
        "updated_at": route.updated_at.isoformat() if route.updated_at else None,
    }


def write_backup(session: Session) -> Path:
    settings = get_settings()
    backup_path = settings.backup_path
    providers: Iterable[ExternalAPI] = session.query(ExternalAPI).order_by(ExternalAPI.id).all()
    routes: Iterable[ModelRoute] = session.query(ModelRoute).order_by(ModelRoute.id).all()
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "providers": [_serialize_provider(provider) for provider in providers],
        "routes": [_serialize_route(route) for route in routes],
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


def restore_from_backup(session: Session) -> dict[str, int]:
    settings = get_settings()
    backup_path = settings.backup_path
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found at {backup_path}")

    data = json.loads(backup_path.read_text(encoding="utf-8"))
    providers = data.get("providers", [])
    routes = data.get("routes", [])
    restored = {"providers": 0, "routes": 0}

    provider_name_map: dict[str, ExternalAPI] = {}

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
            "consecutive_failures": item.get("consecutive_failures", 0),
            "is_healthy": item.get("is_healthy", True),
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
            restored["providers"] += 1
        else:
            for key, value in attrs.items():
                setattr(provider, key, value)
            restored["providers"] += 1
        provider_name_map[name] = provider

    session.flush()

    for item in routes:
        name = item.get("name")
        if not name:
            continue

        route: ModelRoute | None = (
            session.query(ModelRoute).filter(ModelRoute.name == name).one_or_none()
        )

        route_attrs = {
            "mode": item.get("mode", "auto"),
            "config": item.get("config", {}),
            "is_active": item.get("is_active", True),
        }

        if route is None:
            route = ModelRoute(name=name, **route_attrs)
            created_at = _parse_datetime(item.get("created_at"))
            updated_at = _parse_datetime(item.get("updated_at"))
            if created_at:
                route.created_at = created_at
            if updated_at:
                route.updated_at = updated_at
            session.add(route)
            session.flush()
            restored["routes"] += 1
        else:
            for key, value in route_attrs.items():
                setattr(route, key, value)
            session.query(RouteNode).filter(RouteNode.route_id == route.id).delete()
            session.flush()
            restored["routes"] += 1

        nodes = item.get("nodes", [])
        for node_item in nodes:
            api_name = node_item.get("api_name")
            if not api_name or api_name not in provider_name_map:
                continue

            provider = provider_name_map[api_name]
            node = RouteNode(
                route_id=route.id,
                api_id=provider.id,
                models=node_item.get("models", []),
                strategy=node_item.get("strategy", "round-robin"),
                priority=node_item.get("priority", 0),
                node_metadata=node_item.get("metadata", {}),
            )
            session.add(node)

    session.commit()
    write_backup(session)
    return restored
