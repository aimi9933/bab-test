from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator


class ProviderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    base_url: AnyHttpUrl
    models: list[str] = Field(..., min_length=1)
    is_active: bool = True

    @field_validator("models")
    @classmethod
    def validate_models(cls, value: list[str]) -> list[str]:
        cleaned = [model.strip() for model in value if model and model.strip()]
        if not cleaned:
            raise ValueError("At least one model identifier is required")
        if len(cleaned) != len(value):
            raise ValueError("Model identifiers must be non-empty strings")
        return cleaned


class ProviderCreate(ProviderBase):
    api_key: str = Field(..., min_length=1)


class ProviderUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    base_url: Optional[AnyHttpUrl] = None
    models: Optional[list[str]] = Field(default=None, min_length=1)
    is_active: Optional[bool] = None
    api_key: Optional[str] = Field(default=None, min_length=1)

    @field_validator("models")
    @classmethod
    def validate_models(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return value
        cleaned = [model.strip() for model in value if model and model.strip()]
        if not cleaned:
            raise ValueError("At least one model identifier is required")
        if len(cleaned) != len(value):
            raise ValueError("Model identifiers must be non-empty strings")
        return cleaned


class ProviderRead(ProviderBase):
    id: int
    status: str
    latency_ms: Optional[float]
    last_tested_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ProviderTestResponse(BaseModel):
    status: str
    status_code: Optional[int]
    latency_ms: Optional[float]
    detail: Optional[str] = None


class RestoreResponse(BaseModel):
    restored: int
    detail: str
