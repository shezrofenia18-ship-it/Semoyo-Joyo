"""Payment endpoints: instruksi pembayaran, ganti metode, cek status, callback Travoy Pay (kerangka)."""
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from events import broadcaster
from models import Order, PaymentTransaction
from payments.travoy import PROVIDER, travoy
from schemas import PaymentCreateIn, PaymentInstructionOut

router = APIRouter(prefix="/payments", tags=["payments"])
logger = logging.getLogger("mbg.payments")

METHODS = [
    {"key": "cash", "name": "Cash (Tunai)", "description": "Dibayar langsung di kasir, pesanan berstatus Lunas", "available": True},
    {"key": "piutang", "name": "Bayar Nanti", "description": "Pelanggan tetap: ambil barang dulu, masuk modul Piutang", "available": True},
    {"key": "transfer_va", "name": "Transfer VA (Travoy Pay)", "description": "Virtual Account, verifikasi otomatis", "available": travoy.enabled},
]

RANK = {"pending": 0, "piutang": 0, "expired": 1, "failed": 1, "paid": 2}


async def _get_order(db: AsyncSession, order_number: str) -> Order:
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Pesanan tidak ditemukan")
    return order


def mark_paid(order: Order) -> None:
    order.payment_status = "paid"
    order.paid_at = datetime.now(timezone.utc)
    if order.order_status == "baru":
        order.order_status = "diproses"
    broadcaster.publish("payment.paid", {"order_id": order.id, "order_number": order.order_number, "customer_name": order.customer_name,
                                         "total": float(order.total), "payment_method": order.payment_method})


def _apply_status(order: Order, new_status: str) -> bool:
    """Monotonic status update; returns True if changed."""
    if RANK.get(new_status, 0) < RANK.get(order.payment_status, 0) or order.payment_status == new_status:
        return False
    if new_status == "paid":
        mark_paid(order)
    else:
        order.payment_status = new_status
    return True


async def build_charge(order: Order) -> dict[str, Any]:
    """Tentukan status & instruksi pembayaran awal berdasarkan metode pesanan."""
    amount = int(order.total)
    if order.payment_method == "cash":
        return {"provider": "cash", "payment_status": "paid", "reference": None,
                "instructions": {"type": "cash", "message": "Dibayar tunai di kasir"}, "raw": {"method": "cash"}}
    if order.payment_method == "piutang":
        return {"provider": "manual", "payment_status": "piutang", "reference": None,
                "instructions": {"type": "piutang", "message": "Dicatat sebagai piutang, dilunasi melalui admin"}, "raw": {"method": "piutang"}}
    # transfer_va
    if travoy.enabled:
        va = await travoy.create_va(order_number=order.order_number, amount=amount, customer_name=order.customer_name, phone=order.phone)
        return {"provider": PROVIDER, "payment_status": "pending", "reference": va.get("reference"),
                "instructions": {"type": "transfer_va", "provider": PROVIDER, "status": "active", **{k: va.get(k) for k in ("va_number", "bank_name", "expires_at")}},
                "raw": va.get("raw")}
    return {"provider": PROVIDER, "payment_status": "pending", "reference": None, "instructions": travoy.placeholder_instructions(amount),
            "raw": {"method": "transfer_va", "status": "awaiting_integration"}}


def apply_charge(order: Order, charge: dict[str, Any]) -> PaymentTransaction:
    order.payment_ref = charge.get("reference")
    order.payment_payload = {"provider": charge["provider"], "instructions": charge["instructions"]}
    if charge["payment_status"] == "paid":
        mark_paid(order)
    else:
        order.payment_status = charge["payment_status"]
        order.paid_at = None
    return PaymentTransaction(order_id=order.id, provider=charge["provider"], method=order.payment_method, channel=None,
                              status=order.payment_status, amount=order.total, reference=charge.get("reference"), raw=charge.get("raw"))


def _instruction_out(order: Order) -> PaymentInstructionOut:
    payload = order.payment_payload or {}
    return PaymentInstructionOut(
        order_number=order.order_number, payment_method=order.payment_method, payment_status=order.payment_status,
        amount=float(order.total), provider=payload.get("provider", "manual"), instructions=payload.get("instructions", {}),
    )


@router.get("/config")
async def payment_config():
    return {"mode": travoy.mode, "methods": METHODS}


@router.get("/{order_number}", response_model=PaymentInstructionOut)
async def get_payment(order_number: str, db: AsyncSession = Depends(get_db)):
    return _instruction_out(await _get_order(db, order_number))


@router.post("/{order_number}/create", response_model=PaymentInstructionOut)
async def create_payment(order_number: str, body: PaymentCreateIn, db: AsyncSession = Depends(get_db)):
    """Ganti metode pembayaran selama pesanan belum lunas / belum dibatalkan."""
    order = await _get_order(db, order_number)
    if order.payment_status == "paid":
        raise HTTPException(400, "Pesanan sudah dibayar")
    if order.order_status == "dibatalkan":
        raise HTTPException(400, "Pesanan sudah dibatalkan")
    order.payment_method = body.payment_method or order.payment_method
    order.payment_channel = None
    try:
        charge = await build_charge(order)
    except NotImplementedError as exc:
        raise HTTPException(501, str(exc))
    db.add(apply_charge(order, charge))
    await db.commit()
    await db.refresh(order)
    return _instruction_out(order)


@router.get("/{order_number}/status")
async def payment_status(order_number: str, db: AsyncSession = Depends(get_db)):
    order = await _get_order(db, order_number)
    if travoy.enabled and order.payment_method == "transfer_va" and order.payment_status == "pending":
        try:
            remote = await travoy.get_status(order.order_number)
            if _apply_status(order, remote["status"]):
                db.add(PaymentTransaction(order_id=order.id, provider=PROVIDER, method=order.payment_method, channel=None,
                                          status=order.payment_status, amount=order.total, reference=order.payment_ref, raw=remote.get("raw")))
                await db.commit()
        except NotImplementedError:
            pass
        except Exception as exc:  # network issue -> return current known status
            logger.warning("travoy status check failed: %s", exc)
    return {
        "order_number": order.order_number, "payment_status": order.payment_status, "order_status": order.order_status,
        "paid_at": order.paid_at, "payment_method": order.payment_method, "amount": float(order.total),
    }


@router.post("/travoy/notification")
async def travoy_notification(request: Request, db: AsyncSession = Depends(get_db)):
    """Callback/webhook Travoy Pay (KERANGKA). Aktif setelah dokumen API tersedia & env TRAVOY_* diisi."""
    if not travoy.enabled:
        raise HTTPException(503, "Travoy Pay belum dikonfigurasi")
    payload = await request.json()
    try:
        if not travoy.verify_callback(dict(request.headers), payload):
            raise HTTPException(403, "Signature tidak valid")
        new_status = travoy.map_status(payload)
    except NotImplementedError as exc:
        raise HTTPException(501, str(exc))
    order = (await db.execute(select(Order).where(Order.order_number == payload.get("order_number", "")))).scalar_one_or_none()
    if not order:
        return {"ok": True, "ignored": True}
    if _apply_status(order, new_status):
        db.add(PaymentTransaction(order_id=order.id, provider=PROVIDER, method=order.payment_method, channel=None,
                                  status=new_status, amount=order.total, reference=payload.get("reference") or order.payment_ref, raw=payload))
        await db.commit()
    return {"ok": True, "payment_status": order.payment_status}
