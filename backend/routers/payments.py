"""Payment endpoints: konfigurasi metode, biaya layanan, instruksi bayar, ganti metode, cek status, dan integrasi BATPay
(B2B token inbound + webhook notifikasi).

Tiga metode pembayaran:
  cash    -> payment_status "proses", order_status "diproses"; lunas setelah kasir klik "Selesai / Terima Uang".
  piutang -> payment_status "piutang" (masuk modul Piutang); lunas via "Tandai Lunas".
  online  -> BATPay (QRIS / Virtual Account). Biaya layanan (gross-up) ditambahkan ke total; lunas otomatis via webhook.
"""
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import JWT_SECRET
from database import get_db
from events import broadcaster
from models import Order, PaymentTransaction
from payments.batpay import PROVIDER, BatpayError, batpay
from schemas import PaymentCreateIn, PaymentInstructionOut

router = APIRouter(prefix="/payments", tags=["payments"])
logger = logging.getLogger("mbg.payments")

METHOD_DEFS = [
    {"key": "cash", "name": "Cash (Tunai)", "description": "Bayar tunai ke kasir. Status Proses sampai kasir menerima uang"},
    {"key": "piutang", "name": "Bayar Nanti", "description": "Pelanggan tetap: ambil barang dulu, tagihan masuk modul Piutang"},
    {"key": "online", "name": "Bayar Online (BATPay)", "description": "QRIS / Virtual Account, verifikasi otomatis. Dikenakan biaya layanan"},
]

# Urutan monotonic agar notifikasi terlambat tidak menurunkan status
RANK = {"proses": 0, "pending": 0, "piutang": 0, "expired": 1, "failed": 1, "paid": 2}


def app_url() -> str:
    return (os.environ.get("APP_URL") or os.environ.get("REACT_APP_BACKEND_URL") or "").rstrip("/")


def methods_config() -> list[dict[str, Any]]:
    out = []
    for m in METHOD_DEFS:
        item = {**m, "available": True}
        if m["key"] == "online":
            item["available"] = batpay.enabled
            item["channels"] = batpay.channels()
        out.append(item)
    return out


async def _get_order(db: AsyncSession, order_number: str) -> Order:
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Pesanan tidak ditemukan")
    return order


def recompute_total(order: Order) -> None:
    order.total = Decimal(order.subtotal or 0) + Decimal(order.shipping_fee or 0) + Decimal(order.service_fee or 0)


def mark_paid(order: Order, *, complete: bool = False) -> None:
    order.payment_status = "paid"
    order.paid_at = order.paid_at or datetime.now(timezone.utc)
    if complete:
        order.order_status = "selesai"
    elif order.order_status == "baru":
        order.order_status = "diproses"
    broadcaster.publish("payment.paid", {"order_id": order.id, "order_number": order.order_number, "customer_name": order.customer_name,
                                         "total": float(order.total), "payment_method": order.payment_method})


def apply_status(order: Order, new_status: str) -> bool:
    """Monotonic status update; returns True if changed."""
    if RANK.get(new_status, 0) < RANK.get(order.payment_status, 0) or order.payment_status == new_status:
        return False
    if new_status == "paid":
        # Bayar Online lunas (webhook / cek status BATPay) -> pesanan langsung Selesai
        mark_paid(order, complete=True)
    else:
        order.payment_status = new_status
    return True


def add_transaction(db: AsyncSession, order: Order, *, provider: str, status: str, reference: Optional[str], raw: Any) -> PaymentTransaction:
    tx = PaymentTransaction(order_id=order.id, provider=provider, method=order.payment_method, channel=order.payment_channel, status=status,
                            amount=order.total, reference=reference, raw=raw)
    db.add(tx)
    return tx


async def build_charge(order: Order) -> dict[str, Any]:
    """Tentukan biaya layanan, status awal & instruksi pembayaran berdasarkan metode pesanan. Mengubah order.service_fee/total."""
    base = int(Decimal(order.subtotal or 0) + Decimal(order.shipping_fee or 0))
    if order.payment_method == "cash":
        order.payment_channel = None
        order.service_fee = Decimal("0")
        recompute_total(order)
        return {"provider": "cash", "payment_status": "proses", "order_status": "diproses", "reference": None,
                "instructions": {"type": "cash", "status": "proses", "message": "Bayar tunai ke kasir saat pesanan diterima. Kasir akan menekan 'Selesai / Terima Uang' untuk menandai lunas."},
                "raw": {"method": "cash"}}
    if order.payment_method == "piutang":
        order.payment_channel = None
        order.service_fee = Decimal("0")
        recompute_total(order)
        return {"provider": "manual", "payment_status": "piutang", "order_status": None, "reference": None,
                "instructions": {"type": "piutang", "status": "piutang", "message": "Dicatat sebagai piutang, dilunasi melalui admin"}, "raw": {"method": "piutang"}}

    # online (BATPay)
    channel = batpay.normalize_channel(order.payment_channel)
    order.payment_channel = channel
    fee = batpay.service_fee(base, channel)
    order.service_fee = Decimal(fee)
    recompute_total(order)
    amount = int(order.total)
    common = {"type": "online", "provider": PROVIDER, "channel": channel, "amount": amount, "base_amount": base, "service_fee": fee}
    if not batpay.enabled:
        return {"provider": PROVIDER, "payment_status": "pending", "order_status": None, "reference": None,
                "instructions": {**common, **batpay.placeholder_instructions(amount, channel)}, "raw": {"method": "online", "channel": channel, "status": "awaiting_integration"}}
    try:
        if channel.startswith("va_"):
            res = await batpay.create_va(reference=order.order_number, bank=channel[3:], amount=amount, customer_name=order.customer_name, phone=order.phone)
            ins = {**common, "status": "active", "channel_name": f"Virtual Account {res['bank_name']}", "va_number": res["va_number"], "bank_name": res["bank_name"],
                   "partner_service_id": res.get("partner_service_id"), "customer_no": res.get("customer_no"),
                   "expires_at": res["expires_at"], "message": f"Transfer tepat Rp {amount:,} ke nomor VA {res['bank_name']} di bawah. Status lunas otomatis setelah transfer diterima.".replace(",", ".")}
        else:
            res = await batpay.create_qris(reference=order.order_number, amount=amount, fee=fee)
            ins = {**common, "status": "active", "channel_name": "QRIS", "qr_content": res["qr_content"], "qr_url": res["qr_url"], "qr_image": res["qr_image"],
                   "merchant_name": res["merchant_name"], "expires_at": res["expires_at"], "message": "Scan QRIS dengan aplikasi e-wallet / mobile banking Anda."}
    except BatpayError as exc:
        logger.error("BATPay charge gagal untuk %s: %s", order.order_number, exc)
        raise HTTPException(502, f"Gagal membuat tagihan BATPay: {exc}")
    return {"provider": PROVIDER, "payment_status": "pending", "order_status": None, "reference": res.get("provider_ref") or order.order_number,
            "instructions": ins, "raw": res.get("raw")}


def apply_charge(order: Order, charge: dict[str, Any]) -> PaymentTransaction:
    order.payment_ref = charge.get("reference")
    order.payment_payload = {"provider": charge["provider"], "instructions": charge["instructions"], "created_at": datetime.now(timezone.utc).isoformat()}
    order.payment_status = charge["payment_status"]
    order.paid_at = None
    if charge.get("order_status") and order.order_status in ("baru", "diproses"):
        order.order_status = charge["order_status"]
    return PaymentTransaction(order_id=order.id, provider=charge["provider"], method=order.payment_method, channel=order.payment_channel,
                              status=order.payment_status, amount=order.total, reference=charge.get("reference"), raw=charge.get("raw"))


async def cancel_remote_charge(order: Order) -> None:
    """Batalkan tagihan BATPay yang masih aktif (best effort) saat metode/kanal diganti."""
    payload = order.payment_payload or {}
    ins = payload.get("instructions") or {}
    if payload.get("provider") != PROVIDER or ins.get("status") != "active" or not batpay.enabled:
        return
    try:
        if str(ins.get("channel", "")).startswith("va_"):
            await batpay.delete_va(reference=order.order_number, va_info=ins)
        else:
            await batpay.cancel_qris(reference=order.order_number, provider_ref=order.payment_ref, amount=int(order.total))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gagal membatalkan tagihan BATPay %s: %s", order.order_number, exc)


def instruction_out(order: Order) -> PaymentInstructionOut:
    payload = order.payment_payload or {}
    return PaymentInstructionOut(
        order_number=order.order_number, payment_method=order.payment_method, payment_channel=order.payment_channel, payment_status=order.payment_status,
        amount=float(order.total), service_fee=float(order.service_fee or 0), provider=payload.get("provider", "manual"), instructions=payload.get("instructions", {}),
    )


async def sync_remote_status(db: AsyncSession, order: Order) -> None:
    """Tarik status terbaru dari BATPay untuk pesanan online yang masih pending (fallback bila webhook terlambat)."""
    if not (batpay.enabled and order.payment_method == "online" and order.payment_status == "pending"):
        return
    ins = (order.payment_payload or {}).get("instructions") or {}
    if ins.get("status") != "active":
        return
    try:
        if str(order.payment_channel or "").startswith("va_"):
            remote = await batpay.query_va(reference=order.order_number, va_info=ins)
        else:
            remote = await batpay.query_qris(reference=order.order_number, provider_ref=order.payment_ref)
        if apply_status(order, remote["status"]):
            add_transaction(db, order, provider=PROVIDER, status=order.payment_status, reference=order.payment_ref, raw=remote.get("raw"))
            await db.commit()
    except Exception as exc:  # noqa: BLE001 - jaringan / BATPay down -> tampilkan status terakhir yang diketahui
        logger.warning("BATPay status check gagal %s: %s", order.order_number, exc)


# ====================================================================================
# Public endpoints
# ====================================================================================
@router.get("/config")
async def payment_config():
    """Metode pembayaran + kanal Bayar Online (biaya layanan per kanal)."""
    return {"mode": batpay.mode, "provider": PROVIDER, "online_enabled": batpay.enabled, "methods": methods_config()}


@router.get("/fee")
async def payment_fee(amount: float = Query(ge=0), channel: Optional[str] = Query(default="qris")):
    """Pratinjau biaya layanan Bayar Online untuk nominal & kanal tertentu (dipakai halaman checkout)."""
    ch = batpay.normalize_channel(channel)
    fee = batpay.service_fee(amount, ch)
    return {"channel": ch, "base_amount": amount, "service_fee": fee, "total": amount + fee,
            "channels": [{**c, "service_fee": batpay.service_fee(amount, c["key"]), "total": amount + batpay.service_fee(amount, c["key"])} for c in batpay.channels()]}


@router.get("/{order_number}", response_model=PaymentInstructionOut)
async def get_payment(order_number: str, db: AsyncSession = Depends(get_db)):
    return instruction_out(await _get_order(db, order_number))


@router.post("/{order_number}/create", response_model=PaymentInstructionOut)
async def create_payment(order_number: str, body: PaymentCreateIn, db: AsyncSession = Depends(get_db)):
    """Pelanggan mengganti metode / kanal pembayaran selama pesanan belum lunas & belum dibatalkan."""
    order = await _get_order(db, order_number)
    if order.payment_status == "paid":
        raise HTTPException(400, "Pesanan sudah dibayar")
    if order.order_status == "dibatalkan":
        raise HTTPException(400, "Pesanan sudah dibatalkan")
    await cancel_remote_charge(order)
    order.payment_method = body.payment_method or order.payment_method
    if body.payment_channel is not None or order.payment_method != "online":
        order.payment_channel = body.payment_channel if order.payment_method == "online" else None
    charge = await build_charge(order)
    db.add(apply_charge(order, charge))
    await db.commit()
    await db.refresh(order)
    return instruction_out(order)


@router.get("/{order_number}/status")
async def payment_status(order_number: str, db: AsyncSession = Depends(get_db)):
    order = await _get_order(db, order_number)
    await sync_remote_status(db, order)
    return {
        "order_number": order.order_number, "payment_status": order.payment_status, "order_status": order.order_status, "paid_at": order.paid_at,
        "payment_method": order.payment_method, "payment_channel": order.payment_channel, "amount": float(order.total), "service_fee": float(order.service_fee or 0),
    }


# ====================================================================================
# BATPay inbound (SNAP): B2B access token untuk BATPay + webhook notifikasi
# ====================================================================================
def _snap(code: str, message: str, status: int = 200, **extra: Any) -> JSONResponse:
    return JSONResponse({"responseCode": code, "responseMessage": message, **extra}, status_code=status)


@router.post("/batpay/access-token/b2b")
async def batpay_inbound_token(request: Request):
    """BATPay meminta access token ke partner sebelum mengirim notifikasi (SNAP B2B, service code 73)."""
    if not batpay.enabled:
        return _snap("5037300", "Service Unavailable. BATPay belum dikonfigurasi", 503)
    ok, reason = batpay.verify_inbound_token_request(dict(request.headers))
    if not ok:
        code = "4017300" if "Unauthorized" in reason else "4007302"
        return _snap(code, reason, 401 if code.startswith("401") else 400)
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    if body.get("grantType") != "client_credentials":
        return _snap("4007301", "Invalid Field Format grantType", 400)
    token, expires_in = batpay.issue_inbound_token(JWT_SECRET)
    return _snap("2007300", "Successful", accessToken=token, tokenType="Bearer", expiresIn=str(expires_in), additionalInfo={})


@router.post("/batpay/webhook")
async def batpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Webhook/callback notifikasi pembayaran BATPay (QRIS `qr-mpm-notify` & VA `transfer-va/payment`).

    Verifikasi: signature SNAP (Bearer token yang kita terbitkan + X-SIGNATURE HMAC_SHA512) atau token internal X-CALLBACK-TOKEN.
    Sukses -> pesanan Lunas (paid) + status pesanan Diproses.
    """
    raw = await request.body()
    if not batpay.webhook_ready:
        return _snap("5035200", "Service Unavailable. BATPay belum dikonfigurasi", 503)
    ok, how = batpay.verify_webhook(dict(request.headers), raw, JWT_SECRET)
    if not ok:
        logger.warning("Webhook BATPay ditolak: %s", how)
        return _snap("4015200", f"Unauthorized. {how}", 401)
    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        return _snap("4005200", "Bad Request. Body bukan JSON", 400)
    note = batpay.parse_notification(payload if isinstance(payload, dict) else {})
    ref = str(note.get("reference") or "")
    order = None
    if ref:
        order = (await db.execute(select(Order).where((Order.order_number == ref) | (Order.payment_ref == ref)))).scalar_one_or_none()
    if not order and note.get("provider_ref"):
        order = (await db.execute(select(Order).where(Order.payment_ref == str(note["provider_ref"])))).scalar_one_or_none()
    if not order:
        logger.warning("Webhook BATPay: pesanan tidak ditemukan (ref=%s)", ref)
        return _snap("4045200", "Transaction Not Found", 404)
    if order.payment_method != "online":
        return _snap("4035200", "Transaction Not Permitted. Pesanan bukan Bayar Online", 403)
    new_status = note["status"]
    if new_status == "paid" and note.get("paid_amount") and float(note["paid_amount"]) + 0.5 < float(order.total):
        logger.warning("Webhook BATPay: nominal %s < total %s untuk %s", note["paid_amount"], order.total, order.order_number)
        add_transaction(db, order, provider=PROVIDER, status="mismatch", reference=order.payment_ref, raw={"via": how, "payload": payload})
        await db.commit()
        return _snap("4045213", "Invalid Amount", 404)
    changed = apply_status(order, new_status)
    if changed:
        add_transaction(db, order, provider=PROVIDER, status=order.payment_status, reference=note.get("provider_ref") or order.payment_ref, raw={"via": how, "payload": payload})
        if order.payment_status == "paid":
            order.payment_payload = {**(order.payment_payload or {}), "paid_via": {"kind": note.get("kind"), "at": order.paid_at.isoformat(), "verified": how}}
        await db.commit()
        broadcaster.publish("order.updated", {"order_number": order.order_number, "order_status": order.order_status, "payment_status": order.payment_status, "by": "batpay"})
    code = "2002500" if note.get("kind") == "va" else "2005200"
    return _snap(code, "Successful", order_number=order.order_number, payment_status=order.payment_status, changed=changed)
