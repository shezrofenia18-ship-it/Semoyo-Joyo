"""Modul Pengeluaran (Expenses): biaya operasional yang mengurangi laba bersih.

Admin & Owner boleh mencatat/mengubah; hapus hanya Owner.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from audit import log_action
from auth import get_admin_user, get_owner_user
from database import get_db
from models import Expense, User
from schemas import ExpenseCategoryTotal, ExpenseIn, ExpenseOut, ExpenseSummaryOut

router = APIRouter(prefix="/admin/expenses", tags=["expenses"])

WIB = timezone(timedelta(hours=7))

CATEGORY_LABEL = {
    "angkut": "Ongkos Angkut / Kirim", "operasional": "Operasional", "gaji": "Gaji / Upah", "sewa": "Sewa",
    "listrik_air": "Listrik & Air", "perlengkapan": "Perlengkapan", "pembelian": "Pembelian Barang", "lainnya": "Lainnya",
}


def _parse_range(start: Optional[str], end: Optional[str]) -> tuple[date, date]:
    today = datetime.now(WIB).date()
    try:
        s = date.fromisoformat(start) if start else today.replace(day=1)
        e = date.fromisoformat(end) if end else today
    except ValueError:
        raise HTTPException(400, "Format tanggal harus YYYY-MM-DD")
    if s > e:
        raise HTTPException(400, "Tanggal mulai tidak boleh setelah tanggal akhir")
    return s, e


@router.get("", response_model=ExpenseSummaryOut)
async def list_expenses(start: Optional[str] = Query(default=None), end: Optional[str] = Query(default=None), category: Optional[str] = None,
                        q: Optional[str] = None, _: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    s, e = _parse_range(start, end)
    stmt = select(Expense).where(Expense.expense_date >= s, Expense.expense_date <= e)
    if category and category != "all":
        stmt = stmt.where(Expense.category == category)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(Expense.description.ilike(like) | Expense.reference.ilike(like) | Expense.note.ilike(like))
    rows = (await db.execute(stmt.order_by(Expense.expense_date.desc(), Expense.created_at.desc()))).scalars().all()
    by_cat: dict[str, ExpenseCategoryTotal] = {}
    total = 0.0
    for r in rows:
        amt = float(r.amount)
        total += amt
        c = by_cat.setdefault(r.category, ExpenseCategoryTotal(category=r.category, total=0.0, count=0))
        c.total += amt
        c.count += 1
    return ExpenseSummaryOut(start_date=s, end_date=e, total=total, count=len(rows),
                             by_category=sorted(by_cat.values(), key=lambda c: c.total, reverse=True), items=[ExpenseOut.model_validate(r) for r in rows])


@router.get("/categories")
async def expense_categories(_: User = Depends(get_admin_user)):
    return [{"key": k, "label": v} for k, v in CATEGORY_LABEL.items()]


@router.post("", response_model=ExpenseOut, status_code=201)
async def create_expense(body: ExpenseIn, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    if body.expense_date > datetime.now(WIB).date() + timedelta(days=1):
        raise HTTPException(400, "Tanggal pengeluaran tidak boleh di masa depan")
    ex = Expense(expense_date=body.expense_date, category=body.category, description=body.description.strip(), amount=body.amount,
                 payment_method=body.payment_method, reference=(body.reference or "").strip() or None, note=(body.note or "").strip() or None,
                 source="manual", created_by=admin.username)
    db.add(ex)
    await db.flush()
    log_action(db, admin, "create", "expense", f"Mencatat pengeluaran '{ex.description}' Rp {float(ex.amount):,.0f} ({CATEGORY_LABEL.get(ex.category, ex.category)})",
               entity_id=ex.id, entity_label=ex.description, meta={"amount": float(ex.amount), "category": ex.category, "date": ex.expense_date.isoformat()})
    await db.commit()
    await db.refresh(ex)
    return ExpenseOut.model_validate(ex)


@router.put("/{expense_id}", response_model=ExpenseOut)
async def update_expense(expense_id: str, body: ExpenseIn, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    ex = (await db.execute(select(Expense).where(Expense.id == expense_id))).scalar_one_or_none()
    if not ex:
        raise HTTPException(404, "Pengeluaran tidak ditemukan")
    changes = {}
    for field, new in (("amount", float(body.amount)), ("category", body.category), ("description", body.description.strip()), ("expense_date", body.expense_date.isoformat())):
        old = getattr(ex, field)
        old_cmp = float(old) if field == "amount" else (old.isoformat() if field == "expense_date" else old)
        if old_cmp != new:
            changes[field] = [old_cmp, new]
    ex.expense_date = body.expense_date
    ex.category = body.category
    ex.description = body.description.strip()
    ex.amount = body.amount
    ex.payment_method = body.payment_method
    ex.reference = (body.reference or "").strip() or None
    ex.note = (body.note or "").strip() or None
    log_action(db, admin, "update", "expense", f"Mengubah pengeluaran '{ex.description}'" + (f" ({', '.join(changes)})" if changes else ""),
               entity_id=ex.id, entity_label=ex.description, meta={"changes": changes})
    await db.commit()
    await db.refresh(ex)
    return ExpenseOut.model_validate(ex)


@router.delete("/{expense_id}")
async def delete_expense(expense_id: str, owner: User = Depends(get_owner_user), db: AsyncSession = Depends(get_db)):
    ex = (await db.execute(select(Expense).where(Expense.id == expense_id))).scalar_one_or_none()
    if not ex:
        raise HTTPException(404, "Pengeluaran tidak ditemukan")
    log_action(db, owner, "delete", "expense", f"Menghapus pengeluaran '{ex.description}' Rp {float(ex.amount):,.0f}", entity_id=ex.id, entity_label=ex.description,
               meta={"amount": float(ex.amount), "category": ex.category})
    await db.delete(ex)
    await db.commit()
    return {"ok": True}


async def monthly_expense_total(db: AsyncSession) -> float:
    today = datetime.now(WIB).date()
    stmt = select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.expense_date >= today.replace(day=1), Expense.expense_date <= today)
    return float((await db.execute(stmt)).scalar() or 0)
