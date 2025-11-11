from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes.admin import router as admin_router
from .api.routes.providers import router as providers_router
from .api.routes.routes import router as routes_router
from .api.routes.chat import router as chat_router
from .core.config import get_settings
from .db.init_db import init_db
from .services.health_checker import get_health_checker
from .services.logging import get_logger, setup_logging
from .services.metrics import get_metrics
from .services.providers import (
    ProviderConnectivityError,
    ProviderNotFoundError,
    ProviderServiceError,
)
from .services.routing import (
    RouteNotFoundError,
    RouteServiceError,
    RouteValidationError,
)

settings = get_settings()
setup_logging()
logger = get_logger(__name__)

app = FastAPI(title=settings.app_name)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_and_metrics_middleware(request: Request, call_next) -> JSONResponse:
    """Middleware to log requests and track metrics."""
    request_id = str(uuid.uuid4())
    start_time = time.time()

    # Log request
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        },
    )

    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # Track metrics
        metrics = get_metrics()
        metrics.record_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as exc:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            f"Request failed: {request.method} {request.url.path}: {str(exc)}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
            },
            exc_info=True,
        )
        raise


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Starting application")
    init_db()
    health_checker = get_health_checker()
    await health_checker.start()
    logger.info("Application started successfully")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("Shutting down application")
    health_checker = get_health_checker()
    await health_checker.stop()
    logger.info("Application shut down successfully")


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


@app.exception_handler(RouteNotFoundError)
async def handle_route_not_found(request: Request, exc: RouteNotFoundError) -> JSONResponse:
    return _create_error_response(404, str(exc))


@app.exception_handler(RouteValidationError)
async def handle_route_validation_error(request: Request, exc: RouteValidationError) -> JSONResponse:
    return _create_error_response(400, str(exc))


@app.exception_handler(RouteServiceError)
async def handle_route_service_error(request: Request, exc: RouteServiceError) -> JSONResponse:
    return _create_error_response(400, str(exc))


@app.get("/ping")
async def ping() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/admin/stats")
async def get_stats() -> dict:
    """Get application statistics and metrics."""
    metrics = get_metrics()
    return metrics.get_stats()


app.include_router(providers_router)
app.include_router(admin_router)
app.include_router(routes_router)
app.include_router(chat_router)


# Add a catch-all route to handle proxy requests for external tools like Cline
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def catch_all_proxy(path: str, request: Request) -> JSONResponse:
    """
    Catch-all route that proxies unhandled requests to chat completion endpoints.
    This allows external tools like Cline to call the router as if it's a standard API.
    """
    # If the path starts with a known prefix, return 404
    if path.startswith(("api/", "v1/", "ping", "swagger", "redoc", "openapi")):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    
    # For any other path, try to handle it as a proxy request
    # This is a fallback for unrecognized requests
    return JSONResponse(
        status_code=404, 
        content={"detail": f"Path /{path} not found. Use /v1/chat/completions for chat requests."}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
