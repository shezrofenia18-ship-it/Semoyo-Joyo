"""Payment endpoints: create/re-create instructions, status, simulation (sandbox), Midtrans webhook."""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from events import broadcaster
from models import Order, PaymentTransaction
from payments.midtrans import BANKS, EWALLETS, midtrans
from schemas import PaymentCreateIn, PaymentInstructionOut

router = APIRouter(prefix="/payments", tags=["payments"])
logger = logging.getLogger("mbg.payments")

RANK = {"pending": 0, "cod": 0, "piutang": 0, "expired": 1, "failed": 1, "paid": 2}


async def _get_order(db: AsyncSession, order_number: str) -> Order:
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Pesanan tidak ditemukan")
    return order


def _instruction_out(order: Order) -> PaymentInstructionOut:
    payload = order.payment_payload or {}
    return PaymentInstructionOut(
        order_number=order.order_number, payment_method=order.payment_method, payment_channel=order.payment_channel,
        payment_status=order.payment_status, amount=float(order.total), provider=payload.get("provider", "simulation"),
        simulation=bool(payload.get("simulation", True)), instructions=payload.get("instructions", {}),
    )


def _apply_status(order: Order, new_status: str) -> bool:
    """Monotonic status update; returns True if changed."""
    if RANK.get(new_status, 0) < RANK.get(order.payment_status, 0):
        return False
    if order.payment_status == new_status:
        return False
    order.payment_status = new_status
    if new_status == "paid":
        order.paid_at = datetime.now(timezone.utc)
        if order.order_status == "baru":
            order.order_status = "diproses"
        broadcaster.publish("payment.paid", {"order_id": order.id, "order_number": order.order_number, "customer_name": order.customer_name,
                                             "total": float(order.total), "payment_method": order.payment_method})
    return True


@router.get("/config")
async def payment_config():
    return {
        "mode": midtrans.mode,
        "simulation": not midtrans.enabled,
        "client_key": midtrans.client_key or None,
        "methods": [
            {"key": "cod", "name": "COD (Bayar di Tempat)", "channels": []},
            {"key": "bank_transfer", "name": "Transfer Bank (Virtual Account)", "channels": [{"key": k, "name": v} for k, v in BANKS.items()]},
            {"key": "qris", "name": "QRIS", "channels": []},
            {"key": "ewallet", "name": "E-Wallet", "channels": [{"key": k, "name": v} for k, v in EWALLETS.items()]},
            {"key": "piutang", "name": "Bayar Nanti (Piutang)", "channels": []},
        ],
    }


@router.get("/{order_number}", response_model=PaymentInstructionOut)
async def get_payment(order_number: str, db: AsyncSession = Depends(get_db)):
    order = await _get_order(db, order_number)
    return _instruction_out(order)


@router.post("/{order_number}/create", response_model=PaymentInstructionOut)
async def create_payment(order_number: str, body: PaymentCreateIn, db: AsyncSession = Depends(get_db)):
    """(Re)create payment instructions, optionally switching method/channel while still unpaid."""
    order = await _get_order(db, order_number)
    if order.payment_status == "paid":
        raise HTTPException(400, "Pesanan sudah dibayar")
    if order.order_status == "dibatalkan":
        raise HTTPException(400, "Pesanan sudah dibatalkan")
    method = body.payment_method or order.payment_method
    channel = body.payment_channel if body.payment_method else (body.payment_channel or order.payment_channel)
    try:
        charge = await midtrans.create_charge(
            order_number=order.order_number, amount=int(order.total), method=method, channel=channel,
            customer_name=order.customer_name, phone=order.phone,
            items=[{"id": oi.product_id or oi.id, "price": float(oi.price), "qty": oi.qty, "name": oi.product_name} for oi in order.items],
        )
    except Exception as exc:
        raise HTTPException(502, f"Gagal membuat transaksi pembayaran: {exc}")
    order.payment_method = method
    order.payment_channel = channel
    order.payment_ref = charge.get("reference")
    order.payment_status = charge.get("payment_status", "pending")
    order.payment_payload = {"provider": charge["provider"], "simulation": charge["simulation"], "instructions": charge["instructions"]}
    db.add(PaymentTransaction(order_id=order.id, provider=charge["provider"], method=method, channel=channel, status=order.payment_status,
                              amount=order.total, reference=charge.get("reference"), raw=charge.get("raw")))
    await db.commit()
    await db.refresh(order)
    return _instruction_out(order)


@router.get("/{order_number}/status")
async def payment_status(order_number: str, db: AsyncSession = Depends(get_db)):
    """Poll status. In real mode this also queries Midtrans GET /v2/{order_id}/status."""
    order = await _get_order(db, order_number)
    if midtrans.enabled and order.payment_status == "pending" and order.payment_method not in ("cod", "piutang"):
        try:
            remote = await midtrans.get_status(order.order_number)
            if remote and _apply_status(order, remote["status"]):
                db.add(PaymentTransaction(order_id=order.id, provider="midtrans", method=order.payment_method, channel=order.payment_channel,
                                          status=order.payment_status, amount=order.total, reference=order.payment_ref, raw=remote["raw"]))
                await db.commit()
        except Exception as exc:  # network issue -> return current known status
            logger.warning("midtrans status check failed: %s", exc)
    return {
        "order_number": order.order_number, "payment_status": order.payment_status, "order_status": order.order_status,
        "paid_at": order.paid_at, "payment_method": order.payment_method, "payment_channel": order.payment_channel, "amount": float(order.total),
    }


@router.post("/{order_number}/simulate")
async def simulate_payment(order_number: str, db: AsyncSession = Depends(get_db)):
    """SANDBOX ONLY: mark payment as paid. Disabled automatically when Midtrans keys are configured."""
    if midtrans.enabled:
        raise HTTPException(403, "Simulasi dinonaktifkan karena gateway pembayaran aktif")
    order = await _get_order(db, order_number)
    if order.payment_method == "cod":
        raise HTTPException(400, "Pesanan COD dibayar saat barang diterima")
    if order.payment_method == "piutang":
        raise HTTPException(400, "Pesanan piutang dilunasi melalui admin (Tandai Lunas)")
    if order.payment_status == "paid":
        return {"ok": True, "payment_status": "paid", "message": "Pesanan sudah dibayar"}
    _apply_status(order, "paid")
    db.add(PaymentTransaction(order_id=order.id, provider="simulation", method=order.payment_method, channel=order.payment_channel,
                              status="paid", amount=order.total, reference=order.payment_ref, raw={"mode": "simulation", "transaction_status": "settlement"}))
    await db.commit()
    return {"ok": True, "payment_status": "paid", "order_status": order.order_status, "message": "Pembayaran simulasi berhasil"}


@router.post("/midtrans/notification")
async def midtrans_notification(request: Request, db: AsyncSession = Depends(get_db)):
    """Midtrans HTTP(S) notification webhook. Verifies SHA512 signature, idempotent + monotonic."""
    payload = await request.json()
    if not midtrans.enabled:
        raise HTTPException(503, "Midtrans belum dikonfigurasi")
    if not midtrans.verify_signature(payload):
        raise HTTPException(403, "Signature tidak valid")
    order_number = payload.get("order_id", "")
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one_or_none()
    if not order:
        return {"ok": True, "ignored": True}
    new_status = midtrans.map_status(payload.get("transaction_status"), payload.get("fraud_status"))
    changed = _apply_status(order, new_status)
    if changed:
        order.payment_ref = payload.get("transaction_id") or order.payment_ref
        db.add(PaymentTransaction(order_id=order.id, provider="midtrans", method=order.payment_method, channel=order.payment_channel,
                                  status=new_status, amount=order.total, reference=payload.get("transaction_id"), raw=payload))
        await db.commit()
    return {"ok": True, "payment_status": order.payment_status}
