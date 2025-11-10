from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...schemas.provider import (
    ProviderCreate,
    ProviderRead,
    ProviderTestDirect,
    ProviderTestResponse,
    ProviderUpdate,
)
from ...services import providers as provider_service
from ...services.backup import write_backup


class HealthOverrideRequest(BaseModel):
    is_healthy: bool

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("", response_model=list[ProviderRead])
def list_providers(db: Session = Depends(get_db)) -> list[ProviderRead]:
    providers = provider_service.list_providers(db)
    return list(providers)


@router.post("", response_model=ProviderRead, status_code=201)
def create_provider(payload: ProviderCreate, db: Session = Depends(get_db)) -> ProviderRead:
    provider = provider_service.create_provider(db, payload)
    return provider


@router.get("/{provider_id}", response_model=ProviderRead)
def get_provider(provider_id: int, db: Session = Depends(get_db)) -> ProviderRead:
    provider = provider_service.get_provider(db, provider_id)
    return provider


@router.patch("/{provider_id}", response_model=ProviderRead)
def update_provider(
    provider_id: int,
    payload: ProviderUpdate,
    db: Session = Depends(get_db),
) -> ProviderRead:
    provider = provider_service.update_provider(db, provider_id, payload)
    return provider


@router.delete("/{provider_id}", status_code=204)
def delete_provider(provider_id: int, db: Session = Depends(get_db)) -> Response:
    provider_service.delete_provider(db, provider_id)
    return Response(status_code=204)


@router.post("/test-direct", response_model=ProviderTestResponse)
async def test_provider_direct(
    payload: ProviderTestDirect,
    timeout: float | None = Query(default=None, ge=0.1, description="Override request timeout in seconds"),
) -> ProviderTestResponse:
    result = await provider_service.test_provider_direct(str(payload.base_url), payload.api_key, timeout)
    return ProviderTestResponse(**result)


@router.post("/{provider_id}/test", response_model=ProviderTestResponse)
async def test_provider(
    provider_id: int,
    timeout: float | None = Query(default=None, ge=0.1, description="Override request timeout in seconds"),
    db: Session = Depends(get_db),
) -> ProviderTestResponse:
    result = await provider_service.test_provider_connectivity(db, provider_id, timeout)
    return ProviderTestResponse(**result)


@router.patch("/{provider_id}/health", response_model=ProviderRead)
def set_provider_health(
    provider_id: int,
    payload: HealthOverrideRequest,
    db: Session = Depends(get_db),
) -> ProviderRead:
    provider = provider_service.get_provider(db, provider_id)
    provider.is_healthy = payload.is_healthy
    provider.consecutive_failures = 0
    db.commit()
    db.refresh(provider)
    write_backup(db)
    return provider
