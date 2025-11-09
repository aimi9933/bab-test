from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .api.routes.admin import router as admin_router
from .api.routes.providers import router as providers_router
from .core.config import get_settings
from .db.init_db import init_db
from .services.providers import (
    ProviderConnectivityError,
    ProviderNotFoundError,
    ProviderServiceError,
)

settings = get_settings()

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def _create_error_response(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


@app.exception_handler(ProviderNotFoundError)
async def handle_not_found(request: Request, exc: ProviderNotFoundError) -> JSONResponse:
    return _create_error_response(404, str(exc))


@app.exception_handler(ProviderServiceError)
async def handle_service_error(request: Request, exc: ProviderServiceError) -> JSONResponse:
    return _create_error_response(400, str(exc))


@app.exception_handler(ProviderConnectivityError)
async def handle_connectivity_error(
    request: Request, exc: ProviderConnectivityError
) -> JSONResponse:
    status_code = exc.status_code or 502
    if status_code < 400:
        status_code = 502
    return _create_error_response(status_code, exc.detail)


@app.exception_handler(FileNotFoundError)
async def handle_file_not_found(request: Request, exc: FileNotFoundError) -> JSONResponse:
    return _create_error_response(404, str(exc))


@app.get("/ping")
async def ping() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(providers_router)
app.include_router(admin_router)
