from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

# Create SQLAlchemy Engine
# pool_pre_ping=True tests connection health before executing statements to prevent stale connection errors
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

# Session factory for creating database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a database session per request.
    Automatically closes session after request handling finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
