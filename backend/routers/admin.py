"""Admin endpoints: login, dashboard, CRUD kategori/produk, orders, upload gambar."""
import re
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional

import asyncio

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from audit import log_action
from auth import STAFF_ROLES, create_token, get_admin_user, get_owner_user, is_owner, user_from_token, verify_password
from database import get_db
from events import broadcaster, sse_format
from finance import COST_EXPR, RECEIVABLE_FILTER, SOLD_FILTER, receivables_totals, snapshot
from models import AuditLog, Category, Expense, Order, OrderItem, PaymentTransaction, Product, StockMovement, User
from routers.expenses import monthly_expense_total
from routers.catalog import product_out
from schemas import (
    AdminLoginIn, AuditLogOut, CategoryIn, CategoryOut, DashboardOut, OrderOut, OrderStatusUpdateIn, OrderUpdateIn, ProductIn, ProductOut,
    ProductProfitOut, ReceivableCustomerOut, ReceivablesOut, SettleIn, StockAdjustIn, StockItemOut, StockMovementOut, StockSummaryOut, TokenOut, UserOut,
)

router = APIRouter(prefix="/admin", tags=["admin"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

# Definisi "terjual" terpusat di finance.py (SOLD_FILTER) agar Dashboard, Laporan & Sinkronisasi konsisten
PROFIT_FILTER = SOLD_FILTER


def stock_status(stock: int, min_order: int) -> str:
    if stock <= 0:
        return "habis"
    if stock <= max(min_order, 1) * 2:
        return "menipis"
    return "aman"


async def restore_stock_for_order(db: AsyncSession, o: Order, source: str, note: str, actor: Optional[str] = None) -> None:
    """Kembalikan stok item pesanan + catat mutasi stok."""
    for it in o.items:
        if not it.product_id:
            continue
        p = (await db.execute(select(Product).where(Product.id == it.product_id))).scalar_one_or_none()
        if not p:
            continue
        before = p.stock
        p.stock += it.qty
        db.add(StockMovement(product_id=p.id, product_name=p.name, movement_type="in", qty=it.qty, stock_before=before, stock_after=p.stock,
                             source=source, reference=o.order_number, note=note, created_by=actor))


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
    user = (await db.execute(select(User).where(User.username == body.username.strip().lower(), User.role.in_(STAFF_ROLES)))).scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Username atau password salah")
    log_action(db, user, "login", "auth", f"{user.full_name} ({user.role}) masuk ke panel admin")
    await db.commit()
    return TokenOut(access_token=create_token(user), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def admin_me(admin: User = Depends(get_admin_user)):
    return UserOut.model_validate(admin)


# ---------- Realtime (SSE) ----------
@router.get("/events")
async def admin_events(request: Request, token: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Server-Sent Events untuk panel admin/owner: pesanan baru, pembayaran lunas, dll."""
    user = await user_from_token(token, db)
    if not user or user.role not in STAFF_ROLES:
        raise HTTPException(403, "Akses khusus admin")
    queue = broadcaster.subscribe()

    async def stream():
        try:
            yield sse_format({"type": "connected", "data": {"user": user.username, "role": user.role}, "at": datetime.now(timezone.utc).isoformat()})
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15)
                    yield sse_format(payload)
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            broadcaster.unsubscribe(queue)

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}
    return StreamingResponse(stream(), media_type="text/event-stream", headers=headers)


# ---------- Audit Log (Owner) ----------
@router.get("/audit-logs", response_model=list[AuditLogOut])
async def audit_logs(
    actor: Optional[str] = None, action: Optional[str] = None, entity_type: Optional[str] = None, q: Optional[str] = None,
    limit: int = Query(default=100, le=500), _: User = Depends(get_owner_user), db: AsyncSession = Depends(get_db),
):
    stmt = select(AuditLog)
    if actor:
        stmt = stmt.where(AuditLog.actor_username == actor)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(AuditLog.description.ilike(like) | AuditLog.entity_label.ilike(like) | AuditLog.actor_username.ilike(like))
    rows = (await db.execute(stmt.order_by(AuditLog.created_at.desc()).limit(limit))).scalars().all()
    return [AuditLogOut.model_validate(r) for r in rows]


@router.get("/staff", response_model=list[UserOut])
async def staff_list(_: User = Depends(get_owner_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(User).where(User.role.in_(STAFF_ROLES)).order_by(User.role.desc(), User.username))).scalars().all()
    return [UserOut.model_validate(u) for u in rows]


# ---------- Dashboard ----------
@router.get("/dashboard", response_model=DashboardOut)
async def dashboard(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    total_orders = (await db.execute(select(func.count(Order.id)))).scalar() or 0
    orders_today = (await db.execute(select(func.count(Order.id)).where(Order.created_at >= start_today))).scalar() or 0
    pending_payments = (await db.execute(select(func.count(Order.id)).where(Order.payment_status == "pending"))).scalar() or 0
    total_products = (await db.execute(select(func.count(Product.id)))).scalar() or 0
    total_categories = (await db.execute(select(func.count(Category.id)))).scalar() or 0
    total_customers = (await db.execute(select(func.count(User.id)).where(User.role == "customer"))).scalar() or 0
    low_stock = (await db.execute(select(func.count(Product.id)).where(Product.stock <= Product.min_order * 2, Product.is_active.is_(True)))).scalar() or 0
    recent = (await db.execute(select(Order).order_by(Order.created_at.desc()).limit(8))).scalars().all()
    breakdown_rows = (await db.execute(select(Order.order_status, func.count(Order.id)).group_by(Order.order_status))).all()

    # ---- Keuangan: laba/rugi dari pesanan terjual (definisi terpusat di finance.py) ----
    profit_stmt = (
        select(
            OrderItem.product_id, func.max(OrderItem.product_name), func.sum(OrderItem.qty),
            func.sum(OrderItem.subtotal), func.sum(COST_EXPR * OrderItem.qty),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .outerjoin(Product, Product.id == OrderItem.product_id)
        .where(SOLD_FILTER)
        .group_by(OrderItem.product_id)
    )
    profit_rows = (await db.execute(profit_stmt)).all()
    profit_by_product: list[ProductProfitOut] = []
    for pid, pname, qty, rev, cost in profit_rows:
        rev_f, cost_f = float(rev or 0), float(cost or 0)
        profit_by_product.append(ProductProfitOut(
            product_id=pid, product_name=pname, qty_sold=int(qty or 0), revenue=rev_f, cost=cost_f, profit=rev_f - cost_f,
            margin_pct=round(((rev_f - cost_f) / rev_f) * 100, 1) if rev_f > 0 else 0.0,
        ))
    profit_by_product.sort(key=lambda r: r.profit, reverse=True)
    snap = await snapshot(db)
    expenses_month = await monthly_expense_total(db)

    total_cost, gross_profit, margin, stock_value = snap.sales_cost, snap.gross_profit, snap.margin_pct, snap.stock_value
    total_expenses, net_profit = snap.total_expenses, snap.net_profit
    if not is_owner(admin):
        # RBAC: admin biasa tidak melihat modal/laba murni
        total_cost, gross_profit, margin, stock_value, profit_by_product = 0.0, 0.0, 0.0, 0.0, []
        total_expenses, net_profit, expenses_month = 0.0, 0.0, 0.0

    return DashboardOut(
        total_orders=total_orders, orders_today=orders_today, pending_payments=pending_payments, revenue_paid=snap.sales_revenue,
        total_products=total_products, total_categories=total_categories, total_customers=total_customers, low_stock_products=low_stock,
        receivables_total=snap.receivables_total, receivables_count=snap.receivables_count,
        cost_paid=total_cost, gross_profit=gross_profit, margin_pct=margin, stock_value=float(stock_value), profit_by_product=profit_by_product[:10],
        total_expenses=total_expenses, expenses_month=expenses_month, net_profit=net_profit,
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
async def create_category(body: CategoryIn, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    cat = Category(name=body.name.strip(), slug=await unique_slug(db, Category, slugify(body.name)), description=body.description,
                   image_url=body.image_url or None, sort_order=body.sort_order, is_active=body.is_active)
    db.add(cat)
    await db.flush()
    log_action(db, admin, "create", "category", f"Menambah kategori '{cat.name}'", entity_id=cat.id, entity_label=cat.name)
    await db.commit()
    await db.refresh(cat)
    return CategoryOut.model_validate(cat)


@router.put("/categories/{cat_id}", response_model=CategoryOut)
async def update_category(cat_id: str, body: CategoryIn, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
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
    log_action(db, admin, "update", "category", f"Mengubah kategori '{cat.name}'", entity_id=cat.id, entity_label=cat.name)
    await db.commit()
    await db.refresh(cat)
    return CategoryOut.model_validate(cat)


@router.delete("/categories/{cat_id}")
async def delete_category(cat_id: str, admin: User = Depends(get_owner_user), db: AsyncSession = Depends(get_db)):
    cat = (await db.execute(select(Category).where(Category.id == cat_id))).scalar_one_or_none()
    if not cat:
        raise HTTPException(404, "Kategori tidak ditemukan")
    cnt = (await db.execute(select(func.count(Product.id)).where(Product.category_id == cat_id))).scalar() or 0
    if cnt:
        raise HTTPException(400, f"Kategori masih memiliki {cnt} produk. Pindahkan/hapus produk terlebih dahulu.")
    log_action(db, admin, "delete", "category", f"Menghapus kategori '{cat.name}'", entity_id=cat.id, entity_label=cat.name)
    await db.delete(cat)
    await db.commit()
    return {"ok": True}


# ---------- Products ----------
@router.get("/products", response_model=list[ProductOut])
async def admin_products(q: Optional[str] = None, category: Optional[str] = None, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    stmt = select(Product, Category.name).join(Category)
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q.strip()}%"))
    if category:
        stmt = stmt.where(Category.id == category)
    stmt = stmt.order_by(Category.sort_order, Product.name)
    rows = (await db.execute(stmt)).all()
    return [product_out(p, cname, include_cost=is_owner(admin)) for p, cname in rows]


@router.post("/products", response_model=ProductOut, status_code=201)
async def create_product(body: ProductIn, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    cat = (await db.execute(select(Category).where(Category.id == body.category_id))).scalar_one_or_none()
    if not cat:
        raise HTTPException(400, "Kategori tidak valid")
    p = Product(category_id=cat.id, name=body.name.strip(), slug=await unique_slug(db, Product, slugify(body.name)), description=body.description,
                price=body.price, cost_price=body.cost_price if is_owner(admin) else 0, unit=body.unit.strip(), min_order=body.min_order, stock=body.stock,
                image_url=body.image_url or None, is_active=body.is_active)
    db.add(p)
    await db.flush()
    if body.stock > 0:
        db.add(StockMovement(product_id=p.id, product_name=p.name, movement_type="in", qty=body.stock, stock_before=0, stock_after=body.stock,
                             source="manual", note="Stok awal produk baru", created_by=admin.username))
    log_action(db, admin, "create", "product", f"Menambah produk '{p.name}' (harga {float(p.price):,.0f}, stok {p.stock} {p.unit})",
               entity_id=p.id, entity_label=p.name, meta={"price": float(p.price), "stock": p.stock})
    await db.commit()
    await db.refresh(p)
    return product_out(p, cat.name, include_cost=is_owner(admin))


@router.put("/products/{product_id}", response_model=ProductOut)
async def update_product(product_id: str, body: ProductIn, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Produk tidak ditemukan")
    cat = (await db.execute(select(Category).where(Category.id == body.category_id))).scalar_one_or_none()
    if not cat:
        raise HTTPException(400, "Kategori tidak valid")
    if p.name != body.name.strip():
        p.slug = await unique_slug(db, Product, slugify(body.name), exclude_id=p.id)
    changes: dict[str, list] = {}
    for field, new in (("name", body.name.strip()), ("price", float(body.price)), ("stock", body.stock), ("is_active", body.is_active), ("unit", body.unit.strip())):
        old = getattr(p, field)
        old_cmp = float(old) if field == "price" else old
        if old_cmp != new:
            changes[field] = [old_cmp, new]
    if is_owner(admin) and float(p.cost_price or 0) != float(body.cost_price):
        changes["cost_price"] = [float(p.cost_price or 0), float(body.cost_price)]
    p.category_id = cat.id
    p.name = body.name.strip()
    p.description = body.description
    p.price = body.price
    if is_owner(admin):
        p.cost_price = body.cost_price  # admin biasa tidak boleh mengubah modal
    p.unit = body.unit.strip()
    p.min_order = body.min_order
    if p.stock != body.stock:
        db.add(StockMovement(product_id=p.id, product_name=p.name, movement_type="adjust", qty=body.stock - p.stock, stock_before=p.stock,
                             stock_after=body.stock, source="manual", note="Diubah dari form produk", created_by=admin.username))
        p.stock = body.stock
    p.image_url = body.image_url or None
    p.is_active = body.is_active
    log_action(db, admin, "update", "product", f"Mengubah produk '{p.name}'" + (f" ({', '.join(changes)})" if changes else ""),
               entity_id=p.id, entity_label=p.name, meta={"changes": changes})
    await db.commit()
    await db.refresh(p)
    return product_out(p, cat.name, include_cost=is_owner(admin))


@router.delete("/products/{product_id}")
async def delete_product(product_id: str, admin: User = Depends(get_owner_user), db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Produk tidak ditemukan")
    log_action(db, admin, "delete", "product", f"Menghapus produk '{p.name}'", entity_id=p.id, entity_label=p.name)
    await db.delete(p)  # order_items.product_id -> SET NULL
    await db.commit()
    return {"ok": True}


@router.post("/upload")
async def upload_image(file: UploadFile = File(...), _: User = Depends(get_admin_user)):  # noqa: B008
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
async def update_order_status(order_id: str, body: OrderStatusUpdateIn, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    o = (await db.execute(select(Order).where((Order.id == order_id) | (Order.order_number == order_id)))).scalar_one_or_none()
    if not o:
        raise HTTPException(404, "Pesanan tidak ditemukan")
    await _apply_order_changes(db, o, body.order_status, body.payment_status, admin)
    parts = [f"status pesanan -> {body.order_status}" if body.order_status else None, f"status bayar -> {body.payment_status}" if body.payment_status else None]
    log_action(db, admin, "status", "order", f"Mengubah pesanan {o.order_number}: " + ", ".join(x for x in parts if x),
               entity_id=o.id, entity_label=o.order_number, meta=body.model_dump(exclude_none=True))
    await db.commit()
    await db.refresh(o)
    broadcaster.publish("order.updated", {"order_number": o.order_number, "order_status": o.order_status, "payment_status": o.payment_status, "by": admin.username})
    return OrderOut.model_validate(o)


async def _apply_order_changes(db: AsyncSession, o: Order, order_status: Optional[str], payment_status: Optional[str], admin: User) -> None:
    if order_status:
        if order_status == "dibatalkan" and o.order_status != "dibatalkan":
            await restore_stock_for_order(db, o, source="cancel", note="Pesanan dibatalkan", actor=admin.username)
        elif o.order_status == "dibatalkan" and order_status != "dibatalkan":
            # diaktifkan kembali -> kurangi stok lagi
            for it in o.items:
                if not it.product_id:
                    continue
                p = (await db.execute(select(Product).where(Product.id == it.product_id))).scalar_one_or_none()
                if p:
                    before = p.stock
                    p.stock = max(0, p.stock - it.qty)
                    db.add(StockMovement(product_id=p.id, product_name=p.name, movement_type="out", qty=-(before - p.stock), stock_before=before,
                                         stock_after=p.stock, source="order", reference=o.order_number, note="Pesanan diaktifkan kembali", created_by=admin.username))
        o.order_status = order_status
    if payment_status:
        o.payment_status = payment_status
        if payment_status == "paid" and not o.paid_at:
            o.paid_at = datetime.now(timezone.utc)


@router.put("/orders/{order_id}", response_model=OrderOut)
async def update_order(order_id: str, body: OrderUpdateIn, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Edit data pesanan (pelanggan, alamat, catatan, ongkir, status)."""
    o = (await db.execute(select(Order).where((Order.id == order_id) | (Order.order_number == order_id)))).scalar_one_or_none()
    if not o:
        raise HTTPException(404, "Pesanan tidak ditemukan")
    if body.customer_name is not None:
        o.customer_name = body.customer_name.strip()
    if body.phone is not None:
        o.phone = body.phone.strip()
    if body.address is not None:
        o.address = body.address.strip()
    if body.notes is not None:
        o.notes = body.notes.strip() or None
    if body.shipping_fee is not None:
        o.shipping_fee = body.shipping_fee
        o.total = o.subtotal + Decimal(str(body.shipping_fee))
    await _apply_order_changes(db, o, body.order_status, body.payment_status, admin)
    log_action(db, admin, "update", "order", f"Mengedit data pesanan {o.order_number} ({', '.join(body.model_dump(exclude_none=True).keys())})",
               entity_id=o.id, entity_label=o.order_number, meta=body.model_dump(exclude_none=True))
    await db.commit()
    await db.refresh(o)
    return OrderOut.model_validate(o)


@router.delete("/orders/{order_id}")
async def delete_order(order_id: str, admin: User = Depends(get_owner_user), db: AsyncSession = Depends(get_db)):
    """Hapus pesanan permanen. Stok dikembalikan bila pesanan belum dibatalkan."""
    o = (await db.execute(select(Order).where((Order.id == order_id) | (Order.order_number == order_id)))).scalar_one_or_none()
    if not o:
        raise HTTPException(404, "Pesanan tidak ditemukan")
    if o.order_status != "dibatalkan":
        await restore_stock_for_order(db, o, source="cancel", note=f"Pesanan {o.order_number} dihapus admin", actor=admin.username)
    log_action(db, admin, "delete", "order", f"Menghapus pesanan {o.order_number} ({o.customer_name}, total {float(o.total):,.0f})",
               entity_id=o.id, entity_label=o.order_number, meta={"total": float(o.total), "status": o.order_status})
    await db.delete(o)  # items & transactions cascade
    await db.commit()
    return {"ok": True, "order_number": o.order_number}



# ---------- Piutang (Accounts Receivable) ----------
@router.get("/receivables", response_model=ReceivablesOut)
async def receivables(q: Optional[str] = Query(default=None), _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Daftar piutang (pesanan belum bayar / kasbon) + rekap per pelanggan."""
    stmt = select(Order).where(RECEIVABLE_FILTER)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(Order.order_number.ilike(like) | Order.customer_name.ilike(like) | Order.phone.ilike(like))
    rows = (await db.execute(stmt.order_by(Order.created_at.asc()))).scalars().all()
    total, count = await receivables_totals(db)
    cutoff = datetime.now(timezone.utc) - timedelta(days=14)
    overdue = sum(1 for o in rows if o.created_at < cutoff)
    by: dict[str, ReceivableCustomerOut] = {}
    for o in rows:
        key = o.user_id or o.phone
        c = by.get(key)
        if not c:
            by[key] = ReceivableCustomerOut(user_id=o.user_id, customer_name=o.customer_name, phone=o.phone, orders=0, total=0.0, oldest_at=o.created_at)
            c = by[key]
        c.orders += 1
        c.total += float(o.total)
        c.oldest_at = min(c.oldest_at, o.created_at)
    settled_total, settled_count = (await db.execute(
        select(func.coalesce(func.sum(Order.total), 0), func.count(Order.id)).where(Order.payment_method == "piutang", Order.payment_status == "paid")
    )).one()
    return ReceivablesOut(total=total, count=count, overdue_count=overdue, settled_total=float(settled_total or 0), settled_count=int(settled_count or 0),
                          by_customer=sorted(by.values(), key=lambda c: c.total, reverse=True), orders=[OrderOut.model_validate(o) for o in rows])


@router.post("/orders/{order_id}/settle", response_model=OrderOut)
async def settle_order(order_id: str, body: SettleIn, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Tandai pesanan LUNAS (pelunasan piutang / COD / pembayaran manual) + catat transaksi manual."""
    o = (await db.execute(select(Order).where((Order.id == order_id) | (Order.order_number == order_id)))).scalar_one_or_none()
    if not o:
        raise HTTPException(404, "Pesanan tidak ditemukan")
    if o.order_status == "dibatalkan":
        raise HTTPException(400, "Pesanan sudah dibatalkan")
    if o.payment_status == "paid":
        raise HTTPException(400, "Pesanan sudah lunas")
    was = o.payment_status
    o.payment_status = "paid"
    o.paid_at = body.paid_at or datetime.now(timezone.utc)
    if o.order_status == "baru":
        o.order_status = "diproses"
    o.payment_payload = {**(o.payment_payload or {}), "settled": {"method": body.method, "note": body.note, "by": admin.username, "at": o.paid_at.isoformat()}}
    db.add(PaymentTransaction(order_id=o.id, provider="manual", method=body.method, channel=None, status="paid", amount=o.total,
                              reference=f"SETTLE-{o.order_number}", raw={"from_status": was, "note": body.note, "by": admin.username}))
    log_action(db, admin, "settle", "order", f"Pelunasan {'piutang ' if was == 'piutang' else ''}pesanan {o.order_number} ({o.customer_name}) Rp {float(o.total):,.0f} via {body.method}"
               + (f" - {body.note.strip()}" if body.note and body.note.strip() else ""), entity_id=o.id, entity_label=o.order_number,
               meta={"from": was, "method": body.method, "amount": float(o.total)})
    await db.commit()
    await db.refresh(o)
    broadcaster.publish("payment.paid", {"order_id": o.id, "order_number": o.order_number, "customer_name": o.customer_name, "total": float(o.total), "payment_method": o.payment_method})
    return OrderOut.model_validate(o)


# ---------- Stok Barang ----------
@router.get("/stock", response_model=StockSummaryOut)
async def stock_summary(q: Optional[str] = None, status: Optional[str] = Query(default=None, description="habis|menipis|aman"),
                        admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    owner = is_owner(admin)
    last_mv = (select(StockMovement.product_id, func.max(StockMovement.created_at).label("last_at")).group_by(StockMovement.product_id)).subquery()
    stmt = (select(Product, Category.name, last_mv.c.last_at).join(Category).outerjoin(last_mv, last_mv.c.product_id == Product.id)
            .order_by(Category.sort_order, Product.name))
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q.strip()}%"))
    rows = (await db.execute(stmt)).all()
    items: list[StockItemOut] = []
    total_units = 0
    total_value = 0.0
    out_cnt = low_cnt = 0
    for p, cname, last_at in rows:
        st = stock_status(p.stock, p.min_order)
        if status and st != status:
            continue
        val = float(p.stock * (p.cost_price or 0)) if owner else 0.0
        total_units += p.stock
        total_value += val
        out_cnt += st == "habis"
        low_cnt += st == "menipis"
        items.append(StockItemOut(
            id=p.id, name=p.name, slug=p.slug, category_id=p.category_id, category_name=cname, unit=p.unit, min_order=p.min_order,
            stock=p.stock, price=float(p.price), cost_price=float(p.cost_price or 0) if owner else 0.0, stock_value=val, status=st, is_active=p.is_active,
            image_url=p.image_url, last_movement_at=last_at,
        ))
    return StockSummaryOut(total_products=len(items), total_units=total_units, total_stock_value=total_value, out_of_stock=out_cnt, low_stock=low_cnt, items=items)


@router.post("/stock/{product_id}/adjust", response_model=StockItemOut)
async def adjust_stock(product_id: str, body: StockAdjustIn, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Tambah (in) / kurangi (out) / set manual (adjust) stok produk + catat riwayat."""
    row = (await db.execute(select(Product, Category.name).join(Category).where(Product.id == product_id))).first()
    if not row:
        raise HTTPException(404, "Produk tidak ditemukan")
    p, cname = row
    before = p.stock
    if body.movement_type == "in":
        if body.qty <= 0:
            raise HTTPException(400, "Jumlah stok masuk harus lebih dari 0")
        after = before + body.qty
    elif body.movement_type == "out":
        if body.qty <= 0:
            raise HTTPException(400, "Jumlah stok keluar harus lebih dari 0")
        if body.qty > before:
            raise HTTPException(400, f"Stok tidak cukup. Stok saat ini {before} {p.unit}")
        after = before - body.qty
    else:  # adjust -> set nilai baru
        after = body.qty
    if after != before:
        db.add(StockMovement(product_id=p.id, product_name=p.name, movement_type=body.movement_type, qty=after - before, stock_before=before,
                             stock_after=after, source="manual", note=(body.note or "").strip() or None, created_by=admin.username))
        p.stock = after
    if body.movement_type == "in" and body.expense_amount and body.expense_amount > 0:
        desc = (body.expense_description or "").strip() or f"Ongkos angkut stok masuk {p.name} ({body.qty} {p.unit})"
        db.add(Expense(expense_date=datetime.now(timezone(timedelta(hours=7))).date(), category="angkut", description=desc, amount=body.expense_amount,
                       payment_method="cash", reference=p.name, note=(body.note or "").strip() or None, source="stock_in", created_by=admin.username))
    label = {"in": "menambah", "out": "mengurangi", "adjust": "menyetel"}[body.movement_type]
    log_action(db, admin, "stock_adjust", "stock", f"{label.capitalize()} stok '{p.name}': {before} -> {after} {p.unit}" + (f" ({body.note.strip()})" if body.note and body.note.strip() else ""),
               entity_id=p.id, entity_label=p.name, meta={"type": body.movement_type, "before": before, "after": after})
    await db.commit()
    await db.refresh(p)
    owner = is_owner(admin)
    return StockItemOut(
        id=p.id, name=p.name, slug=p.slug, category_id=p.category_id, category_name=cname, unit=p.unit, min_order=p.min_order, stock=p.stock,
        price=float(p.price), cost_price=float(p.cost_price or 0) if owner else 0.0, stock_value=float(p.stock * (p.cost_price or 0)) if owner else 0.0,
        status=stock_status(p.stock, p.min_order), is_active=p.is_active, image_url=p.image_url, last_movement_at=datetime.now(timezone.utc),
    )


@router.get("/stock/movements", response_model=list[StockMovementOut])
async def stock_movements(product_id: Optional[str] = None, limit: int = Query(default=50, le=500), _: User = Depends(get_admin_user),
                          db: AsyncSession = Depends(get_db)):
    stmt = select(StockMovement)
    if product_id:
        stmt = stmt.where(StockMovement.product_id == product_id)
    rows = (await db.execute(stmt.order_by(StockMovement.created_at.desc()).limit(limit))).scalars().all()
    return [StockMovementOut.model_validate(m) for m in rows]


@router.get("/customers", response_model=list[UserOut])
async def admin_customers(_: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(User).where(User.role == "customer").order_by(User.created_at.desc()))).scalars().all()
    return [UserOut.model_validate(u) for u in rows]
