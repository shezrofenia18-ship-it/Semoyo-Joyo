"""Sumber tunggal (single source of truth) untuk definisi & perhitungan keuangan.

Dipakai oleh Dashboard, Laporan, Piutang, dan Sinkronisasi Data agar semua angka konsisten.

Definisi "terjual" (pendapatan diakui):
  - payment_status = paid (lunas), ATAU
  - metode COD dan pesanan selesai, ATAU
  - metode Piutang (bayar nanti) dan pesanan selesai (barang sudah diterima pelanggan)
  dan pesanan tidak dibatalkan.

Piutang (accounts receivable) = pesanan payment_status = piutang yang belum dibatalkan (belum dibayar).
Pengeluaran = tabel expenses. Laba bersih = laba kotor - pengeluaran.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Expense, Order, OrderItem, Product

SOLD_FILTER = (
    (Order.payment_status == "paid")
    | ((Order.payment_method == "cod") & (Order.order_status == "selesai"))
    | ((Order.payment_method == "piutang") & (Order.order_status == "selesai"))
) & (Order.order_status != "dibatalkan")

RECEIVABLE_FILTER = (Order.payment_status == "piutang") & (Order.order_status != "dibatalkan")

# HPP per item: snapshot cost_price saat pesanan; fallback harga beli produk saat ini; fallback 0
COST_EXPR = func.coalesce(OrderItem.cost_price, Product.cost_price, 0)


@dataclass
class FinanceSnapshot:
    sales_revenue: float = 0.0
    sales_cost: float = 0.0
    gross_profit: float = 0.0
    margin_pct: float = 0.0
    sold_orders: int = 0
    items_sold: int = 0
    total_expenses: float = 0.0
    net_profit: float = 0.0
    receivables_total: float = 0.0
    receivables_count: int = 0
    stock_value: float = 0.0

    def dict(self) -> dict:
        return asdict(self)


def _range(stmt, start: Optional[datetime], end: Optional[datetime]):
    if start is not None:
        stmt = stmt.where(Order.created_at >= start)
    if end is not None:
        stmt = stmt.where(Order.created_at < end)
    return stmt


async def sales_totals(db: AsyncSession, start: Optional[datetime] = None, end: Optional[datetime] = None) -> tuple[float, float, int, int]:
    """(revenue, cost, sold_orders, items_sold) untuk pesanan terjual pada rentang waktu."""
    rev_stmt = _range(select(func.coalesce(func.sum(Order.total), 0), func.count(Order.id)).where(SOLD_FILTER), start, end)
    rev, n = (await db.execute(rev_stmt)).one()
    cost_stmt = _range(
        select(func.coalesce(func.sum(COST_EXPR * OrderItem.qty), 0), func.coalesce(func.sum(OrderItem.qty), 0))
        .select_from(OrderItem).join(Order, Order.id == OrderItem.order_id).outerjoin(Product, Product.id == OrderItem.product_id)
        .where(SOLD_FILTER), start, end,
    )
    cost, qty = (await db.execute(cost_stmt)).one()
    return float(rev or 0), float(cost or 0), int(n or 0), int(qty or 0)


WIB = timezone(timedelta(hours=7))


def _to_wib_date(dt: Optional[datetime]) -> Optional[date]:
    if dt is None:
        return None
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return dt
    return dt.astimezone(WIB).date()


async def expenses_total(db: AsyncSession, start: Optional[datetime] = None, end: Optional[datetime] = None) -> float:
    """Total pengeluaran. start inklusif, end eksklusif (tanggal WIB)."""
    stmt = select(func.coalesce(func.sum(Expense.amount), 0))
    s, e = _to_wib_date(start), _to_wib_date(end)
    if s is not None:
        stmt = stmt.where(Expense.expense_date >= s)
    if e is not None:
        stmt = stmt.where(Expense.expense_date < e)
    return float((await db.execute(stmt)).scalar() or 0)


async def receivables_totals(db: AsyncSession) -> tuple[float, int]:
    total, n = (await db.execute(select(func.coalesce(func.sum(Order.total), 0), func.count(Order.id)).where(RECEIVABLE_FILTER))).one()
    return float(total or 0), int(n or 0)


async def stock_value(db: AsyncSession) -> float:
    return float((await db.execute(select(func.coalesce(func.sum(Product.stock * Product.cost_price), 0)))).scalar() or 0)


async def snapshot(db: AsyncSession, start: Optional[datetime] = None, end: Optional[datetime] = None) -> FinanceSnapshot:
    rev, cost, n, qty = await sales_totals(db, start, end)
    exp = await expenses_total(db, start, end)
    recv, recv_n = await receivables_totals(db)
    sv = await stock_value(db)
    gross = rev - cost
    return FinanceSnapshot(
        sales_revenue=rev, sales_cost=cost, gross_profit=gross, margin_pct=round(gross / rev * 100, 1) if rev > 0 else 0.0,
        sold_orders=n, items_sold=qty, total_expenses=exp, net_profit=gross - exp, receivables_total=recv, receivables_count=recv_n, stock_value=sv,
    )
