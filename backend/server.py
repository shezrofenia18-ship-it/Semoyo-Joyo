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
from routers import admin, catalog, customer, payments, reports  # noqa: E402
from seed import seed_if_empty  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mbg")


async def _run_light_migrations(conn) -> None:
    """Additive, idempotent schema changes for existing databases (create_all never alters tables)."""
    has_cost = (await conn.execute(text(
        "SELECT 1 FROM information_schema.columns WHERE table_name='products' AND column_name='cost_price'"
    ))).first()
    if not has_cost:
        await conn.execute(text("ALTER TABLE products ADD COLUMN cost_price NUMERIC(14,2) NOT NULL DEFAULT 0"))
        # Produk lama tanpa modal: isi default 80% harga jual (sekali saja) agar laba/rugi langsung terlihat
        await conn.execute(text("UPDATE products SET cost_price = ROUND(price * 0.8, 0) WHERE price > 0"))
    await conn.execute(text("ALTER TABLE order_items ADD COLUMN IF NOT EXISTS cost_price NUMERIC(14,2)"))


async def _init_db_with_retry(attempts: int = 8) -> None:
    """Start local PG (dev), create tables, seed. Retries so a slow DB boot never kills the API."""
    import asyncio

    last_exc: Exception | None = None
    for i in range(1, attempts + 1):
        try:
            ensure_local_postgres()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                await _run_light_migrations(conn)
            async with AsyncSessionLocal() as session:
                await seed_if_empty(session)
            return
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            logger.warning("DB init attempt %s/%s failed: %s", i, attempts, str(exc).splitlines()[-1][:200])
            await asyncio.sleep(min(2 * i, 10))
    raise RuntimeError(f"Database tidak dapat dihubungi setelah {attempts} percobaan: {last_exc}")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await _init_db_with_retry()
    logger.info("MBG backend ready. Payment mode: %s", midtrans.mode)
    yield
    await engine.dispose()


app = FastAPI(title="Semoyo Joyo B2B API", version="2.0.0", lifespan=lifespan)

api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"message": "Semoyo Joyo B2B API", "version": "2.0.0"}


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
api_router.include_router(reports.router)
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
    expose_headers=["Content-Disposition"],
)
