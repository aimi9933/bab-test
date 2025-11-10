from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Integer, String, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from sqlalchemy.ext.mutable import MutableList, MutableDict

from .base import Base


class ExternalAPI(Base):
    __tablename__ = "external_apis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_encrypted: Mapped[str] = mapped_column(String, nullable=False)
    models: Mapped[list[str]] = mapped_column(MutableList.as_mutable(JSON), nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_healthy: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    route_nodes: Mapped[list[RouteNode]] = relationship("RouteNode", back_populates="api", cascade="all, delete-orphan")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "base_url": self.base_url,
            "api_key_encrypted": self.api_key_encrypted,
            "models": list(self.models) if self.models else [],
            "is_active": self.is_active,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "last_tested_at": self.last_tested_at.isoformat() if self.last_tested_at else None,
            "consecutive_failures": self.consecutive_failures,
            "is_healthy": self.is_healthy,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ModelRoute(Base):
    __tablename__ = "model_routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(MutableDict.as_mutable(JSON), nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    route_nodes: Mapped[list[RouteNode]] = relationship("RouteNode", back_populates="route", cascade="all, delete-orphan")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "mode": self.mode,
            "config": dict(self.config) if self.config else {},
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class RouteNode(Base):
    __tablename__ = "route_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    route_id: Mapped[int] = mapped_column(Integer, ForeignKey("model_routes.id"), nullable=False, index=True)
    api_id: Mapped[int] = mapped_column(Integer, ForeignKey("external_apis.id"), nullable=False, index=True)
    models: Mapped[list[str]] = mapped_column(MutableList.as_mutable(JSON), nullable=False, default=list)
    strategy: Mapped[str] = mapped_column(String(50), nullable=False, default="round-robin")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    node_metadata: Mapped[dict[str, Any]] = mapped_column(MutableDict.as_mutable(JSON), nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    route: Mapped[ModelRoute] = relationship("ModelRoute", back_populates="route_nodes")
    api: Mapped[ExternalAPI] = relationship("ExternalAPI", back_populates="route_nodes")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "route_id": self.route_id,
            "api_id": self.api_id,
            "models": list(self.models) if self.models else [],
            "strategy": self.strategy,
            "priority": self.priority,
            "metadata": dict(self.node_metadata) if self.node_metadata else {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
