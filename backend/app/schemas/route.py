from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RouteNodeBase(BaseModel):
    api_id: int = Field(..., gt=0)
    models: list[str] = Field(default_factory=list)
    strategy: str = Field(default="round-robin")
    priority: int = Field(default=0, ge=0)
    node_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, value: str) -> str:
        valid_strategies = ["round-robin", "failover"]
        if value not in valid_strategies:
            raise ValueError(f"Strategy must be one of {valid_strategies}")
        return value


class RouteNodeCreate(RouteNodeBase):
    pass


class RouteNodeUpdate(BaseModel):
    api_id: Optional[int] = Field(default=None, gt=0)
    models: Optional[list[str]] = None
    strategy: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=0)
    node_metadata: Optional[dict[str, Any]] = None

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        valid_strategies = ["round-robin", "failover"]
        if value not in valid_strategies:
            raise ValueError(f"Strategy must be one of {valid_strategies}")
        return value


class RouteNodeRead(RouteNodeBase):
    id: int
    route_id: int
    api_name: Optional[str] = None
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ModelRouteBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    mode: str = Field(...)
    is_active: bool = True
    config: dict[str, Any] = Field(default_factory=dict)

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        valid_modes = ["auto", "specific", "multi"]
        if value not in valid_modes:
            raise ValueError(f"Mode must be one of {valid_modes}")
        return value


class ModelRouteCreate(ModelRouteBase):
    nodes: list[RouteNodeCreate] = Field(default_factory=list)


class ModelRouteUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    mode: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[dict[str, Any]] = None
    nodes: Optional[list[RouteNodeCreate]] = None

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        valid_modes = ["auto", "specific", "multi"]
        if value not in valid_modes:
            raise ValueError(f"Mode must be one of {valid_modes}")
        return value


class ModelRouteRead(ModelRouteBase):
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    nodes: list[RouteNodeRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class RoutingSelectionResponse(BaseModel):
    provider_id: int
    provider_name: str
    model: str


class RoutingStateResponse(BaseModel):
    route_id: int
    route_name: str
    state: dict[str, Any]
