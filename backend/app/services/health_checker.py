from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.security import decrypt_api_key
from ..db.models import ExternalAPI
from ..db.session import get_sessionmaker
from .backup import write_backup

logger = logging.getLogger(__name__)


class HealthChecker:
    """Manages periodic health checks for configured providers."""

    def __init__(self):
        self._check_task: Optional[asyncio.Task] = None
        self._shutdown_event: Optional[asyncio.Event] = None

    async def start(self) -> None:
        """Start the health check background task."""
        settings = get_settings()
        if not settings.health_check_enabled:
            logger.info("Health checks are disabled")
            return

        self._shutdown_event = asyncio.Event()
        self._check_task = asyncio.create_task(self._check_loop())
        logger.info("Health checker started")

    async def stop(self) -> None:
        """Stop the health check background task."""
        if self._shutdown_event:
            self._shutdown_event.set()
        if self._check_task:
            try:
                await asyncio.wait_for(self._check_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Health check task did not stop within timeout")
                self._check_task.cancel()
        logger.info("Health checker stopped")

    async def _check_loop(self) -> None:
        """Main health check loop."""
        settings = get_settings()
        interval = settings.health_check_interval_seconds

        while not self._shutdown_event.is_set():
            try:
                await self._run_checks()
            except Exception as e:
                logger.error(f"Error in health check loop: {e}", exc_info=True)

            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=interval
                )
                break
            except asyncio.TimeoutError:
                pass

    async def _run_checks(self) -> None:
        """Run health checks for all active providers."""
        SessionLocal = get_sessionmaker()
        session = SessionLocal()
        try:
            stmt = select(ExternalAPI).where(ExternalAPI.is_active == True)
            providers = session.scalars(stmt).all()

            tasks = [self._check_provider_health(session, provider) for provider in providers]
            await asyncio.gather(*tasks, return_exceptions=True)

            session.commit()
            write_backup(session)
        except Exception as e:
            logger.error(f"Error running health checks: {e}", exc_info=True)
            session.rollback()
        finally:
            session.close()

    async def _check_provider_health(self, session: Session, provider: ExternalAPI) -> None:
        """Check health of a single provider."""
        settings = get_settings()
        timeout = settings.health_check_timeout_seconds
        failure_threshold = settings.health_check_failure_threshold

        decrypted_key = decrypt_api_key(provider.api_key_encrypted)
        headers = {"Authorization": f"Bearer {decrypted_key}"} if decrypted_key else {}

        from .providers import construct_api_url
        # Test the /models endpoint instead of base URL
        url = construct_api_url(provider.base_url, "/models")
        start = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)

            latency_ms = (time.perf_counter() - start) * 1000
            provider.latency_ms = latency_ms
            provider.last_tested_at = datetime.now(timezone.utc)

            if response.is_success:
                provider.status = "online"
                provider.consecutive_failures = 0
                provider.is_healthy = True
            else:
                provider.status = "degraded"
                provider.consecutive_failures += 1
                provider.is_healthy = provider.consecutive_failures < failure_threshold

        except httpx.TimeoutException:
            provider.status = "timeout"
            provider.latency_ms = None
            provider.last_tested_at = datetime.now(timezone.utc)
            provider.consecutive_failures += 1
            provider.is_healthy = provider.consecutive_failures < failure_threshold

        except httpx.RequestError:
            provider.status = "unreachable"
            provider.latency_ms = None
            provider.last_tested_at = datetime.now(timezone.utc)
            provider.consecutive_failures += 1
            provider.is_healthy = provider.consecutive_failures < failure_threshold

        except Exception as e:
            logger.error(f"Unexpected error checking provider {provider.name}: {e}")
            provider.status = "error"
            provider.latency_ms = None
            provider.last_tested_at = datetime.now(timezone.utc)
            provider.consecutive_failures += 1
            provider.is_healthy = provider.consecutive_failures < failure_threshold


_health_checker = HealthChecker()


def get_health_checker() -> HealthChecker:
    return _health_checker
