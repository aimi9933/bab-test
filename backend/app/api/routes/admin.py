from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...db.session import get_db
from ...schemas.provider import RestoreResponse
from ...services.backup import restore_from_backup

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/providers/restore", response_model=RestoreResponse)
def restore_providers(db: Session = Depends(get_db)) -> RestoreResponse:
    restored_counts = restore_from_backup(db)
    total = restored_counts.get("providers", 0) + restored_counts.get("routes", 0)
    detail = f"Restored {restored_counts.get('providers', 0)} providers and {restored_counts.get('routes', 0)} routes"
    return RestoreResponse(restored=total, detail=detail)


@router.get("/logs")
def get_logs(limit: int = Query(100, ge=1, le=1000)) -> dict:
    """Get recent application logs."""
    settings = get_settings()
    log_file = Path("backend/logs/app.log")

    if not log_file.exists():
        return {"logs": [], "total": 0}

    logs = []
    try:
        with open(log_file, "r") as f:
            lines = f.readlines()
            # Get the last `limit` lines
            for line in lines[-limit:]:
                try:
                    logs.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    # Skip malformed lines
                    pass
    except Exception:
        pass

    return {"logs": logs, "total": len(logs)}
