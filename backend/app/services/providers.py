from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Iterable

import httpx
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.security import decrypt_api_key, encrypt_api_key
from ..db.models import ExternalAPI
from ..schemas.provider import ProviderCreate, ProviderUpdate
from .backup import write_backup


def mask_api_key(api_key: str) -> str:
    """
    Mask an API key for display purposes.
    
    Shows the first few characters and last few characters with asterisks in between.
    For example: sk-1234567890abcdef -> sk-***...***cdef
    
    Args:
        api_key: The API key to mask
        
    Returns:
        The masked API key
    """
    if not api_key:
        return ""
    
    if len(api_key) <= 8:
        # For very short keys, just mask most of it
        return api_key[:2] + "***" + api_key[-2:] if len(api_key) > 4 else "***"
    
    # Show first 4-6 chars and last 4 chars
    prefix_len = min(6, len(api_key) // 4)
    suffix_len = 4
    
    return f"{api_key[:prefix_len]}***...***{api_key[-suffix_len:]}"


def normalize_base_url(url: str) -> str:
    """
    Normalize a base URL by removing trailing slashes.
    
    Args:
        url: The base URL to normalize
        
    Returns:
        The normalized URL without trailing slashes
        
    Examples:
        >>> normalize_base_url("https://api.example.com/v1")
        'https://api.example.com/v1'
        >>> normalize_base_url("https://api.example.com/v1/")
        'https://api.example.com/v1'
    """
    return url.rstrip('/')


def construct_api_url(base_url: str, endpoint: str) -> str:
    """
    Construct a full API URL from a base URL and endpoint.
    
    Args:
        base_url: The base URL (will be normalized)
        endpoint: The API endpoint (should start with /)
        
    Returns:
        The properly constructed URL
        
    Examples:
        >>> construct_api_url("https://api.example.com/v1", "/chat/completions")
        'https://api.example.com/v1/chat/completions'
        >>> construct_api_url("https://api.example.com/v1/", "/chat/completions")
        'https://api.example.com/v1/chat/completions'
    """
    normalized_base = normalize_base_url(base_url)
    # Ensure endpoint starts with / but doesn't have double slashes
    clean_endpoint = endpoint.lstrip('/')
    return f"{normalized_base}/{clean_endpoint}"


class ProviderNotFoundError(LookupError):
    pass


class ProviderServiceError(Exception):
    """Base exception for provider service errors."""


class ProviderConnectivityError(ProviderServiceError):
    def __init__(self, detail: str, status_code: int | None = None):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def list_providers(session: Session) -> Iterable[ExternalAPI]:
    stmt = select(ExternalAPI).order_by(ExternalAPI.id)
    return session.scalars(stmt).all()


def get_provider(session: Session, provider_id: int) -> ExternalAPI:
    provider = session.get(ExternalAPI, provider_id)
    if provider is None:
        raise ProviderNotFoundError(f"Provider with id {provider_id} not found")
    return provider


def create_provider(session: Session, payload: ProviderCreate) -> ExternalAPI:
    encrypted_key = encrypt_api_key(payload.api_key)
    provider = ExternalAPI(
        name=payload.name.strip(),
        base_url=str(payload.base_url),
        api_key_encrypted=encrypted_key,
        models=list(payload.models),
        is_active=payload.is_active,
    )
    session.add(provider)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ProviderServiceError("Provider with this name already exists") from exc
    session.refresh(provider)
    write_backup(session)
    return provider


def update_provider(session: Session, provider_id: int, payload: ProviderUpdate) -> ExternalAPI:
    provider = get_provider(session, provider_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "name" in update_data:
        provider.name = update_data["name"].strip()
    if "base_url" in update_data:
        provider.base_url = str(update_data["base_url"])
    if "models" in update_data and update_data["models"] is not None:
        provider.models = list(update_data["models"])
    if "is_active" in update_data and update_data["is_active"] is not None:
        provider.is_active = bool(update_data["is_active"])
    if "api_key" in update_data and update_data["api_key"]:
        provider.api_key_encrypted = encrypt_api_key(update_data["api_key"])

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ProviderServiceError("Provider with this name already exists") from exc
    session.refresh(provider)
    write_backup(session)
    return provider


def delete_provider(session: Session, provider_id: int) -> None:
    provider = get_provider(session, provider_id)
    session.delete(provider)
    session.commit()
    write_backup(session)


async def test_provider_connectivity(
    session: Session, provider_id: int, timeout: float | None = None
) -> dict:
    provider = get_provider(session, provider_id)
    settings = get_settings()
    request_timeout = timeout or settings.request_timeout_seconds

    decrypted_key = decrypt_api_key(provider.api_key_encrypted)
    headers = {"Authorization": f"Bearer {decrypted_key}"} if decrypted_key else {}

    url = normalize_base_url(provider.base_url)
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=request_timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
        latency_ms = (time.perf_counter() - start) * 1000
        provider.status = "online" if response.is_success else "degraded"
        provider.latency_ms = latency_ms
        provider.last_tested_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(provider)
        write_backup(session)
        result = {
            "status": provider.status,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
        }
        if not response.is_success:
            result["detail"] = f"Received status code {response.status_code}"
        return result
    except httpx.TimeoutException as exc:
        provider.status = "timeout"
        provider.latency_ms = None
        provider.last_tested_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(provider)
        write_backup(session)
        raise ProviderConnectivityError("Timed out while contacting provider") from exc
    except httpx.RequestError as exc:
        provider.status = "unreachable"
        provider.latency_ms = None
        provider.last_tested_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(provider)
        write_backup(session)
        raise ProviderConnectivityError("Failed to contact provider endpoint") from exc


async def test_provider_direct(
    base_url: str, api_key: str, timeout: float | None = None
) -> dict:
    """Test a provider configuration without saving to database."""
    settings = get_settings()
    request_timeout = timeout or settings.request_timeout_seconds

    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    url = normalize_base_url(base_url)
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=request_timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
        latency_ms = (time.perf_counter() - start) * 1000
        status = "online" if response.is_success else "degraded"
        result = {
            "status": status,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
        }
        if not response.is_success:
            result["detail"] = f"Received status code {response.status_code}"
        return result
    except httpx.TimeoutException as exc:
        raise ProviderConnectivityError("Timed out while contacting provider") from exc
    except httpx.RequestError as exc:
        raise ProviderConnectivityError("Failed to contact provider endpoint") from exc
