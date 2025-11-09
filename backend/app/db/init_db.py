from __future__ import annotations

from .base import Base
from .session import get_engine


def init_db() -> None:
    """Create database tables if they do not already exist."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
