from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


def resolve_database_url(url: str) -> str:
    """Canonicalize relative sqlite paths to the backend directory."""
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////") and ":memory:" not in url:
        db_path = url[len("sqlite:///"):]
        if db_path.startswith("./"):
            db_path = db_path[2:]
        canonical_path = (_BACKEND_DIR / db_path).resolve()
        return f"sqlite:///{canonical_path}"
    return url


database_url = resolve_database_url(settings.database_url)
engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
