"""MBG B2B E-Commerce + Mini ERP — FastAPI entrypoint.

Stack: FastAPI + SQLAlchemy 2 (async) + PostgreSQL. All routes are prefixed with /api.
"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from fastapi import APIRouter, Depends, FastAPI  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402
from starlette.middleware.cors import CORSMiddleware  # noqa: E402

from database import AsyncSessionLocal, Base, engine, ensure_local_postgres, get_db  # noqa: E402
import models  # noqa: E402,F401  (register tables)
from payments.midtrans import midtrans  # noqa: E402
from routers import admin, catalog, customer, payments  # noqa: E402
from seed import seed_if_empty  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mbg")


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_local_postgres()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await seed_if_empty(session)
    logger.info("MBG backend ready. Payment mode: %s", midtrans.mode)
    yield
    await engine.dispose()


app = FastAPI(title="MBG Supplier B2B API", version="1.0.0", lifespan=lifespan)

api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"message": "MBG Supplier B2B API", "version": "1.0.0"}


@api_router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:  # pragma: no cover
        logger.error("health db check failed: %s", exc)
    return {"status": "ok" if db_ok else "degraded", "database": "postgresql", "db_connected": db_ok, "payment_mode": midtrans.mode}


api_router.include_router(catalog.router)
api_router.include_router(customer.router)
api_router.include_router(payments.router)
api_router.include_router(admin.router)
app.include_router(api_router)

UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
