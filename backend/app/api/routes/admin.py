from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...schemas.provider import RestoreResponse
from ...services.backup import restore_from_backup

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/providers/restore", response_model=RestoreResponse)
def restore_providers(db: Session = Depends(get_db)) -> RestoreResponse:
    restored = restore_from_backup(db)
    detail = "Providers restored from backup" if restored else "No providers were restored"
    return RestoreResponse(restored=restored, detail=detail)
