"""Pengaturan (khusus Owner): akun staf, profil toko, database pelanggan, sinkronisasi data.

Semua endpoint di router ini dilindungi get_owner_user (RBAC). Profil toko juga diekspos publik (read-only)
lewat public_router untuk footer / struk.
"""
from __future__ import annotations

import re
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from audit import log_action
from auth import STAFF_ROLES, hash_password, verify_password
from auth import get_owner_user
from database import get_db
from finance import RECEIVABLE_FILTER, SOLD_FILTER, snapshot
from models import AuditLog, Expense, Order, OrderItem, Product, StockMovement, StoreProfile, User
from schemas import (
    CustomerAnalyticsOut, CustomersAnalyticsSummary, StaffCreateIn, StaffCredentialsIn, StoreProfileIn, StoreProfileOut, SyncCheck, SyncResultOut,
    UserOut,
)

router = APIRouter(prefix="/admin/settings", tags=["settings"])
public_router = APIRouter(prefix="/store", tags=["store"])

USERNAME_RE = re.compile(r"^[a-z0-9._-]{3,50}$")


# =============================== Profil Toko ===============================
async def get_or_create_profile(db: AsyncSession) -> StoreProfile:
    prof = (await db.execute(select(StoreProfile).where(StoreProfile.id == "default"))).scalar_one_or_none()
    if not prof:
        prof = StoreProfile(id="default", store_name="Semoyo Joyo", tagline="Solusi Belanja Terpercaya")
        db.add(prof)
        await db.flush()
    return prof


@public_router.get("/profile", response_model=StoreProfileOut)
async def public_store_profile(db: AsyncSession = Depends(get_db)):
    prof = await get_or_create_profile(db)
    await db.commit()
    out = StoreProfileOut.model_validate(prof)
    # data rekening tidak dipublikasikan
    out.bank_account = None
    out.bank_holder = None
    out.bank_name = None
    return out


@router.get("/store", response_model=StoreProfileOut)
async def get_store_profile(_: User = Depends(get_owner_user), db: AsyncSession = Depends(get_db)):
    prof = await get_or_create_profile(db)
    await db.commit()
    return StoreProfileOut.model_validate(prof)


@router.put("/store", response_model=StoreProfileOut)
async def update_store_profile(body: StoreProfileIn, owner: User = Depends(get_owner_user), db: AsyncSession = Depends(get_db)):
    prof = await get_or_create_profile(db)
    changed = []
    for field, val in body.model_dump().items():
        val = val.strip() if isinstance(val, str) else val
        val = val or None if field != "store_name" else val
        if getattr(prof, field) != val:
            changed.append(field)
            setattr(prof, field, val)
    prof.updated_by = owner.username
    log_action(db, owner, "update", "settings", "Memperbarui profil toko" + (f" ({', '.join(changed)})" if changed else " (tidak ada perubahan)"),
               entity_label="Profil Toko", meta={"changed": changed})
    await db.commit()
    await db.refresh(prof)
    return StoreProfileOut.model_validate(prof)


# =============================== Akun Staf ===============================
def _check_owner_password(owner: User, pw: str) -> None:
    if not verify_password(pw, owner.password_hash):
        raise HTTPException(403, "Password Owner salah. Konfirmasi dengan password akun Owner Anda saat ini.")


async def _ensure_username_free(db: AsyncSession, username: str, exclude_id: Optional[str] = None) -> None:
    if not USERNAME_RE.match(username):
        raise HTTPException(400, "Username hanya boleh huruf kecil, angka, titik, garis bawah, atau strip (3-50 karakter)")
    stmt = select(User.id).where(User.username == username)
    if exclude_id:
        stmt = stmt.where(User.id != exclude_id)
    if (await db.execute(stmt)).first():
        raise HTTPException(400, f"Username '{username}' sudah dipakai")


@router.get("/staff", response_model=list[UserOut])
async def list_staff(_: User = Depends(get_owner_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(User).where(User.role.in_(STAFF_ROLES)).order_by(User.role.desc(), User.username))).scalars().all()
    return [UserOut.model_validate(u) for u in rows]


@router.post("/staff", response_model=UserOut, status_code=201)
async def create_staff(body: StaffCreateIn, owner: User = Depends(get_owner_user), db: AsyncSession = Depends(get_db)):
    """Tambah akun Admin baru (role admin)."""
    _check_owner_password(owner, body.owner_password)
    username = body.username.strip().lower()
    await _ensure_username_free(db, username)
    u = User(full_name=body.full_name.strip(), username=username, role="admin", password_hash=hash_password(body.password))
    db.add(u)
    await db.flush()
    log_action(db, owner, "create", "staff", f"Menambah akun admin '{username}' ({u.full_name})", entity_id=u.id, entity_label=username)
    await db.commit()
    await db.refresh(u)
    return UserOut.model_validate(u)


@router.put("/staff/{user_id}/credentials", response_model=UserOut)
async def update_staff_credentials(user_id: str, body: StaffCredentialsIn, owner: User = Depends(get_owner_user), db: AsyncSession = Depends(get_db)):
    """Ubah username (ID login), password, dan/atau nama tampilan akun Admin/Owner."""
    _check_owner_password(owner, body.owner_password)
    u = (await db.execute(select(User).where(User.id == user_id, User.role.in_(STAFF_ROLES)))).scalar_one_or_none()
    if not u:
        raise HTTPException(404, "Akun staf tidak ditemukan")
    if not (body.username or body.password or body.full_name):
        raise HTTPException(400, "Tidak ada perubahan: isi username baru, password baru, atau nama")
    changed = []
    if body.username:
        new_un = body.username.strip().lower()
        if new_un != u.username:
            await _ensure_username_free(db, new_un, exclude_id=u.id)
            changed.append(f"username {u.username} -> {new_un}")
            u.username = new_un
    if body.password:
        u.password_hash = hash_password(body.password)
        changed.append("password")
    if body.full_name and body.full_name.strip() != u.full_name:
        u.full_name = body.full_name.strip()
        changed.append("nama")
    if not changed:
        raise HTTPException(400, "Tidak ada perubahan yang tersimpan")
    log_action(db, owner, "update", "staff", f"Mengubah kredensial akun {u.role} '{u.username}': {', '.join(changed)}", entity_id=u.id, entity_label=u.username,
               meta={"changed": changed})
    await db.commit()
    await db.refresh(u)
    return UserOut.model_validate(u)


@router.delete("/staff/{user_id}")
async def delete_staff(user_id: str, owner: User = Depends(get_owner_user), db: AsyncSession = Depends(get_db)):
    u = (await db.execute(select(User).where(User.id == user_id, User.role.in_(STAFF_ROLES)))).scalar_one_or_none()
    if not u:
        raise HTTPException(404, "Akun staf tidak ditemukan")
    if u.role == "owner":
        raise HTTPException(400, "Akun Owner tidak dapat dihapus")
    log_action(db, owner, "delete", "staff", f"Menghapus akun admin '{u.username}'", entity_id=u.id, entity_label=u.username)
    await db.delete(u)
    await db.commit()
    return {"ok": True}


# =============================== Database Pelanggan ===============================
@router.get("/customers", response_model=CustomersAnalyticsSummary)
async def customers_analytics(_: User = Depends(get_owner_user), db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    users = (await db.execute(select(User).where(User.role == "customer").order_by(User.created_at.desc()))).scalars().all()

    # Agregasi per pelanggan
    agg = (
        select(
            Order.user_id,
            func.count(Order.id).filter(Order.order_status != "dibatalkan"),
            func.coalesce(func.sum(Order.total).filter(Order.order_status != "dibatalkan"), 0),
            func.count(Order.id).filter(SOLD_FILTER),
            func.coalesce(func.sum(Order.total).filter(SOLD_FILTER), 0),
            func.count(Order.id).filter(RECEIVABLE_FILTER),
            func.coalesce(func.sum(Order.total).filter(RECEIVABLE_FILTER), 0),
            func.min(Order.created_at),
            func.max(Order.created_at),
        ).group_by(Order.user_id)
    )
    stats = {row[0]: row for row in (await db.execute(agg)).all()}

    out: list[CustomerAnalyticsOut] = []
    regular = new_month = with_recv = 0
    for u in users:
        s = stats.get(u.id)
        n_all = int(s[1]) if s else 0
        total_all = float(s[2]) if s else 0.0
        n_sold = int(s[3]) if s else 0
        total_sold = float(s[4]) if s else 0.0
        n_recv = int(s[5]) if s else 0
        total_recv = float(s[6]) if s else 0.0
        first_at = s[7] if s else None
        last_at = s[8] if s else None
        if n_all >= 3:
            segment = "tetap"
        elif last_at and last_at >= now - timedelta(days=30):
            segment = "aktif"
        elif u.created_at >= now - timedelta(days=30):
            segment = "baru"
        else:
            segment = "pasif"
        regular += segment == "tetap"
        new_month += u.created_at >= month_start
        with_recv += n_recv > 0
        out.append(CustomerAnalyticsOut(
            id=u.id, full_name=u.full_name, username=u.username, phone=u.phone, address=u.address, created_at=u.created_at,
            order_count=n_all, paid_orders=n_sold, total_spent=total_sold, total_all_orders=total_all, receivable_total=total_recv, receivable_count=n_recv,
            first_order_at=first_at, last_order_at=last_at, avg_order_value=round(total_all / n_all, 2) if n_all else 0.0, segment=segment,
        ))
    out.sort(key=lambda c: (c.order_count, c.total_all_orders), reverse=True)
    return CustomersAnalyticsSummary(total_customers=len(users), regular_customers=regular, new_this_month=new_month, with_receivables=with_recv, customers=out)


# =============================== Sinkronisasi Data ===============================
@router.get("/sync/last", response_model=Optional[SyncResultOut])
async def last_sync(_: User = Depends(get_owner_user), db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(AuditLog).where(AuditLog.action == "sync").order_by(AuditLog.created_at.desc()).limit(1))).scalar_one_or_none()
    if not row or not row.meta:
        return None
    try:
        return SyncResultOut(**row.meta)
    except Exception:  # noqa: BLE001
        return None


@router.post("/sync", response_model=SyncResultOut)
async def sync_data(owner: User = Depends(get_owner_user), db: AsyncSession = Depends(get_db)):
    """Validasi & hitung ulang angka turunan agar Penjualan, Piutang, Pengeluaran, Keuangan, Laporan, Riwayat konsisten.

    Aman dijalankan kapan saja: hanya memperbaiki nilai TURUNAN yang deterministik (subtotal item = harga x qty,
    subtotal pesanan = jumlah item, total = subtotal + ongkir, paid_at, snapshot HPP, status bayar COD/piutang).
    Data utama (item, harga, qty, stok, pesanan) TIDAK diubah/dihapus - anomali stok hanya dilaporkan.
    """
    t0 = time.perf_counter()
    checks: list[SyncCheck] = []

    def add(key: str, label: str, checked: int, fixed: int, warnings: list[str]) -> None:
        status = "warning" if warnings else ("fixed" if fixed else "ok")
        checks.append(SyncCheck(key=key, label=label, checked=checked, fixed=fixed, warnings=warnings[:20], status=status))

    # 1) Item pesanan: subtotal = harga x qty; snapshot HPP kosong -> harga beli produk saat ini
    items = (await db.execute(select(OrderItem, Product.cost_price).outerjoin(Product, Product.id == OrderItem.product_id))).all()
    fixed = 0
    warns: list[str] = []
    for it, prod_cost in items:
        expected = (Decimal(it.price) * it.qty).quantize(Decimal("0.01"))
        if Decimal(it.subtotal or 0).quantize(Decimal("0.01")) != expected:
            it.subtotal = expected
            fixed += 1
        if it.cost_price is None:
            if prod_cost is not None:
                it.cost_price = prod_cost
                fixed += 1
            else:
                warns.append(f"Item '{it.product_name}' tanpa modal (produk sudah dihapus) - HPP dihitung 0")
    add("order_items", "Item pesanan (subtotal & snapshot modal)", len(items), fixed, warns)

    # 2) Pesanan: subtotal = jumlah item, total = subtotal + ongkir, paid_at & konsistensi status bayar
    orders = (await db.execute(select(Order))).scalars().all()
    fixed = 0
    warns = []
    for o in orders:
        item_sum = sum((Decimal(i.subtotal) for i in o.items), Decimal("0")).quantize(Decimal("0.01"))
        if not o.items:
            warns.append(f"Pesanan {o.order_number} tidak memiliki item")
        elif Decimal(o.subtotal or 0).quantize(Decimal("0.01")) != item_sum:
            o.subtotal = item_sum
            fixed += 1
        expected_total = (Decimal(o.subtotal or 0) + Decimal(o.shipping_fee or 0)).quantize(Decimal("0.01"))
        if Decimal(o.total or 0).quantize(Decimal("0.01")) != expected_total:
            o.total = expected_total
            fixed += 1
        if o.payment_status == "paid" and not o.paid_at:
            o.paid_at = o.updated_at or o.created_at
            fixed += 1
        if o.payment_status != "paid" and o.paid_at:
            o.paid_at = None
            fixed += 1
        if o.payment_method == "cod" and o.payment_status == "pending":
            o.payment_status = "cod"
            fixed += 1
        if o.payment_method == "piutang" and o.payment_status == "pending":
            o.payment_status = "piutang"
            fixed += 1
        if o.payment_status == "paid" and o.order_status == "baru":
            o.order_status = "diproses"
            fixed += 1
    add("orders", "Pesanan (subtotal, total, tanggal lunas, status bayar)", len(orders), fixed, warns)

    # 3) Produk & stok: harga beli kosong -> 0; stok negatif; stok vs mutasi terakhir (laporan saja)
    products = (await db.execute(select(Product))).scalars().all()
    last_mv_sub = select(StockMovement.product_id, func.max(StockMovement.created_at).label("last_at")).group_by(StockMovement.product_id).subquery()
    last_rows = (await db.execute(
        select(StockMovement.product_id, StockMovement.stock_after).join(last_mv_sub, (last_mv_sub.c.product_id == StockMovement.product_id) & (last_mv_sub.c.last_at == StockMovement.created_at))
    )).all()
    last_after = {pid: after for pid, after in last_rows}
    fixed = 0
    warns = []
    for p in products:
        if p.cost_price is None:
            p.cost_price = Decimal("0")
            fixed += 1
        if p.stock < 0:
            warns.append(f"Stok '{p.name}' negatif ({p.stock}) - periksa & sesuaikan di Stok Barang")
        if p.id in last_after and last_after[p.id] != p.stock:
            warns.append(f"Stok '{p.name}' = {p.stock}, mutasi terakhir mencatat {last_after[p.id]} - cek riwayat stok")
    add("products", "Produk & stok (modal, stok negatif, kecocokan mutasi)", len(products), fixed, warns)

    # 4) Pengeluaran: nominal valid
    expenses = (await db.execute(select(Expense))).scalars().all()
    warns = [f"Pengeluaran '{e.description}' bernilai <= 0" for e in expenses if float(e.amount) <= 0]
    add("expenses", "Pengeluaran (nominal valid)", len(expenses), 0, warns)

    # 5) Pelanggan: pesanan tanpa akun pelanggan
    orphan = (await db.execute(select(func.count(Order.id)).outerjoin(User, User.id == Order.user_id).where(User.id.is_(None)))).scalar() or 0
    n_users = (await db.execute(select(func.count(User.id)).where(User.role == "customer"))).scalar() or 0
    add("customers", "Database pelanggan (relasi pesanan)", int(n_users), 0, [f"{orphan} pesanan tanpa akun pelanggan"] if orphan else [])

    # 6) Piutang: status piutang tapi metode bukan piutang/cod -> laporkan; pesanan dibatalkan dengan status piutang -> tidak dihitung
    recv_rows = (await db.execute(select(Order).where(Order.payment_status == "piutang"))).scalars().all()
    warns = [f"Pesanan {o.order_number} berstatus piutang dengan metode {o.payment_method}" for o in recv_rows if o.payment_method not in ("piutang", "cod", "bank_transfer", "qris", "ewallet")]
    add("receivables", "Piutang (status & metode)", len(recv_rows), 0, warns)

    await db.flush()

    # 7) Snapshot angka final dari sumber tunggal (dipakai Dashboard, Laporan, Piutang, Pengeluaran)
    snap = await snapshot(db)
    duration = int((time.perf_counter() - t0) * 1000)
    result = SyncResultOut(
        ran_at=datetime.now(timezone.utc), duration_ms=duration, total_checked=sum(c.checked for c in checks), total_fixed=sum(c.fixed for c in checks),
        total_warnings=sum(len(c.warnings) for c in checks), checks=checks, snapshot=snap.dict(),
    )
    log_action(db, owner, "sync", "settings", f"Sinkronisasi data: {result.total_checked} record diperiksa, {result.total_fixed} diperbaiki, {result.total_warnings} peringatan",
               entity_label="Sinkronisasi Data", meta=result.model_dump(mode="json"))
    await db.commit()
    return result
