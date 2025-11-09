from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

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
