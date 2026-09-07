"""Database engine/session setup (SQLAlchemy 2.0 async + asyncpg).

DATABASE_URL is read from environment. Example:
  postgresql+asyncpg://user:pass@host:5432/dbname
"""
import os
import subprocess
import logging
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

logger = logging.getLogger("mbg.db")

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL belum diset di environment (.env)")

# Normalize common URL forms (Coolify / Heroku style) to asyncpg driver
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)


def ensure_local_postgres() -> None:
    """Dev-only: start the embedded PostgreSQL if DATABASE_URL points to localhost."""
    if os.environ.get("AUTO_START_LOCAL_PG", "false").lower() != "true":
        return
    if "localhost" not in DATABASE_URL and "127.0.0.1" not in DATABASE_URL:
        return
    script = ROOT_DIR / "scripts" / "ensure_postgres.sh"
    if not script.exists():
        return
    try:
        result = subprocess.run(["bash", str(script)], capture_output=True, text=True, timeout=240)
        for line in (result.stdout or "").splitlines():
            logger.info(line)
        if result.returncode != 0:
            logger.error(result.stderr)
    except Exception as exc:  # pragma: no cover
        logger.error("ensure_postgres failed: %s", exc)


class Base(DeclarativeBase):
    pass


engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True, pool_size=10, max_overflow=20)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
