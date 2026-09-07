"""Admin endpoints: login, dashboard, CRUD kategori/produk, orders, upload gambar."""
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import create_token, get_admin_user, verify_password
from database import get_db
from models import Category, Order, Product, User
from routers.catalog import product_out
from schemas import (
    AdminLoginIn, CategoryIn, CategoryOut, DashboardOut, OrderOut, OrderStatusUpdateIn, ProductIn, ProductOut, TokenOut, UserOut,
)

router = APIRouter(prefix="/admin", tags=["admin"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9\s-]", "", text.lower().strip())
    return re.sub(r"[\s-]+", "-", s).strip("-") or "item"


async def unique_slug(db: AsyncSession, model, base: str, exclude_id: Optional[str] = None) -> str:
    slug = base
    i = 2
    while True:
        stmt = select(model.id).where(model.slug == slug)
        if exclude_id:
            stmt = stmt.where(model.id != exclude_id)
        if not (await db.execute(stmt)).first():
            return slug
        slug = f"{base}-{i}"
        i += 1


# ---------- Auth ----------
@router.post("/login", response_model=TokenOut)
async def admin_login(body: AdminLoginIn, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.username == body.username.strip().lower(), User.role == "admin"))).scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Username atau password salah")
    return TokenOut(access_token=create_token(user), user=UserOut.model_validate(user))


# ---------- Dashboard ----------
@router.get("/dashboard", response_model=DashboardOut)
async def dashboard(_: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    total_orders = (await db.execute(select(func.count(Order.id)))).scalar() or 0
    orders_today = (await db.execute(select(func.count(Order.id)).where(Order.created_at >= start_today))).scalar() or 0
    pending_payments = (await db.execute(select(func.count(Order.id)).where(Order.payment_status == "pending"))).scalar() or 0
    revenue = (await db.execute(select(func.coalesce(func.sum(Order.total), 0)).where(Order.payment_status == "paid"))).scalar() or 0
    total_products = (await db.execute(select(func.count(Product.id)))).scalar() or 0
    total_categories = (await db.execute(select(func.count(Category.id)))).scalar() or 0
    total_customers = (await db.execute(select(func.count(User.id)).where(User.role == "customer"))).scalar() or 0
    low_stock = (await db.execute(select(func.count(Product.id)).where(Product.stock <= Product.min_order * 2, Product.is_active.is_(True)))).scalar() or 0
    recent = (await db.execute(select(Order).order_by(Order.created_at.desc()).limit(8))).scalars().all()
    breakdown_rows = (await db.execute(select(Order.order_status, func.count(Order.id)).group_by(Order.order_status))).all()
    return DashboardOut(
        total_orders=total_orders, orders_today=orders_today, pending_payments=pending_payments, revenue_paid=float(revenue),
        total_products=total_products, total_categories=total_categories, total_customers=total_customers, low_stock_products=low_stock,
        recent_orders=[OrderOut.model_validate(o) for o in recent], status_breakdown={k: v for k, v in breakdown_rows},
    )


# ---------- Categories ----------
@router.get("/categories", response_model=list[CategoryOut])
async def admin_categories(_: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    stmt = (select(Category, func.count(Product.id)).outerjoin(Product, Product.category_id == Category.id)
            .group_by(Category.id).order_by(Category.sort_order, Category.name))
    rows = (await db.execute(stmt)).all()
    out = []
    for c, cnt in rows:
        co = CategoryOut.model_validate(c)
        co.product_count = cnt
        out.append(co)
    return out


@router.post("/categories", response_model=CategoryOut, status_code=201)
async def create_category(body: CategoryIn, _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    cat = Category(name=body.name.strip(), slug=await unique_slug(db, Category, slugify(body.name)), description=body.description,
                   image_url=body.image_url or None, sort_order=body.sort_order, is_active=body.is_active)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return CategoryOut.model_validate(cat)


@router.put("/categories/{cat_id}", response_model=CategoryOut)
async def update_category(cat_id: str, body: CategoryIn, _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    cat = (await db.execute(select(Category).where(Category.id == cat_id))).scalar_one_or_none()
    if not cat:
        raise HTTPException(404, "Kategori tidak ditemukan")
    if cat.name != body.name.strip():
        cat.slug = await unique_slug(db, Category, slugify(body.name), exclude_id=cat.id)
    cat.name = body.name.strip()
    cat.description = body.description
    cat.image_url = body.image_url or None
    cat.sort_order = body.sort_order
    cat.is_active = body.is_active
    await db.commit()
    await db.refresh(cat)
    return CategoryOut.model_validate(cat)


@router.delete("/categories/{cat_id}")
async def delete_category(cat_id: str, _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    cat = (await db.execute(select(Category).where(Category.id == cat_id))).scalar_one_or_none()
    if not cat:
        raise HTTPException(404, "Kategori tidak ditemukan")
    cnt = (await db.execute(select(func.count(Product.id)).where(Product.category_id == cat_id))).scalar() or 0
    if cnt:
        raise HTTPException(400, f"Kategori masih memiliki {cnt} produk. Pindahkan/hapus produk terlebih dahulu.")
    await db.delete(cat)
    await db.commit()
    return {"ok": True}


# ---------- Products ----------
@router.get("/products", response_model=list[ProductOut])
async def admin_products(q: Optional[str] = None, category: Optional[str] = None, _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    stmt = select(Product, Category.name).join(Category)
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q.strip()}%"))
    if category:
        stmt = stmt.where(Category.id == category)
    stmt = stmt.order_by(Category.sort_order, Product.name)
    rows = (await db.execute(stmt)).all()
    return [product_out(p, cname) for p, cname in rows]


@router.post("/products", response_model=ProductOut, status_code=201)
async def create_product(body: ProductIn, _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    cat = (await db.execute(select(Category).where(Category.id == body.category_id))).scalar_one_or_none()
    if not cat:
        raise HTTPException(400, "Kategori tidak valid")
    p = Product(category_id=cat.id, name=body.name.strip(), slug=await unique_slug(db, Product, slugify(body.name)), description=body.description,
                price=body.price, unit=body.unit.strip(), min_order=body.min_order, stock=body.stock, image_url=body.image_url or None, is_active=body.is_active)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return product_out(p, cat.name)


@router.put("/products/{product_id}", response_model=ProductOut)
async def update_product(product_id: str, body: ProductIn, _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Produk tidak ditemukan")
    cat = (await db.execute(select(Category).where(Category.id == body.category_id))).scalar_one_or_none()
    if not cat:
        raise HTTPException(400, "Kategori tidak valid")
    if p.name != body.name.strip():
        p.slug = await unique_slug(db, Product, slugify(body.name), exclude_id=p.id)
    p.category_id = cat.id
    p.name = body.name.strip()
    p.description = body.description
    p.price = body.price
    p.unit = body.unit.strip()
    p.min_order = body.min_order
    p.stock = body.stock
    p.image_url = body.image_url or None
    p.is_active = body.is_active
    await db.commit()
    await db.refresh(p)
    return product_out(p, cat.name)


@router.delete("/products/{product_id}")
async def delete_product(product_id: str, _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Produk tidak ditemukan")
    await db.delete(p)  # order_items.product_id -> SET NULL
    await db.commit()
    return {"ok": True}


@router.post("/upload")
async def upload_image(file: UploadFile = File(...), _: User = Depends(get_admin_user)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, "Format gambar harus JPG, PNG, WEBP, atau GIF")
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(400, "Ukuran gambar maksimal 5 MB")
    name = f"{uuid.uuid4().hex}{ext}"
    (UPLOAD_DIR / name).write_bytes(data)
    return {"url": f"/api/uploads/{name}", "filename": name}


# ---------- Orders ----------
@router.get("/orders", response_model=list[OrderOut])
async def admin_orders(
    status: Optional[str] = Query(default=None), payment_status: Optional[str] = Query(default=None), q: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=500), _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db),
):
    stmt = select(Order)
    if status:
        stmt = stmt.where(Order.order_status == status)
    if payment_status:
        stmt = stmt.where(Order.payment_status == payment_status)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(Order.order_number.ilike(like) | Order.customer_name.ilike(like) | Order.phone.ilike(like))
    rows = (await db.execute(stmt.order_by(Order.created_at.desc()).limit(limit))).scalars().all()
    return [OrderOut.model_validate(o) for o in rows]


@router.get("/orders/{order_id}", response_model=OrderOut)
async def admin_order_detail(order_id: str, _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    o = (await db.execute(select(Order).where((Order.id == order_id) | (Order.order_number == order_id)))).scalar_one_or_none()
    if not o:
        raise HTTPException(404, "Pesanan tidak ditemukan")
    return OrderOut.model_validate(o)


@router.patch("/orders/{order_id}/status", response_model=OrderOut)
async def update_order_status(order_id: str, body: OrderStatusUpdateIn, _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    o = (await db.execute(select(Order).where((Order.id == order_id) | (Order.order_number == order_id)))).scalar_one_or_none()
    if not o:
        raise HTTPException(404, "Pesanan tidak ditemukan")
    if body.order_status:
        if body.order_status == "dibatalkan" and o.order_status != "dibatalkan":
            # restore stock
            for it in o.items:
                if it.product_id:
                    p = (await db.execute(select(Product).where(Product.id == it.product_id))).scalar_one_or_none()
                    if p:
                        p.stock += it.qty
        o.order_status = body.order_status
    if body.payment_status:
        o.payment_status = body.payment_status
        if body.payment_status == "paid" and not o.paid_at:
            o.paid_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(o)
    return OrderOut.model_validate(o)


@router.get("/customers", response_model=list[UserOut])
async def admin_customers(_: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(User).where(User.role == "customer").order_by(User.created_at.desc()))).scalars().all()
    return [UserOut.model_validate(u) for u in rows]
