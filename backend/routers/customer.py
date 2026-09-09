"""Customer auth (Nama Lengkap sebagai ID login) + checkout + orders."""
import random
import string
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import create_token, get_current_user, normalize_phone, normalize_username
from database import get_db
from models import Order, OrderItem, PaymentTransaction, Product, StockMovement, User
from events import broadcaster
from payments.midtrans import midtrans
from schemas import CheckoutIn, CheckoutOut, CustomerLoginIn, OrderOut, TokenOut, UserOut

router = APIRouter(tags=["customer"])


async def generate_order_number(db: AsyncSession) -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    for _ in range(10):
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        num = f"SJ-{today}-{suffix}"
        exists = (await db.execute(select(Order.id).where(Order.order_number == num))).first()
        if not exists:
            return num
    raise HTTPException(500, "Gagal membuat nomor pesanan, coba lagi")


async def find_or_create_customer(db: AsyncSession, full_name: str, phone: str, address: str) -> User:
    username = normalize_username(full_name)
    user = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
    if user:
        if user.role in ("admin", "owner"):
            raise HTTPException(400, "Nama ini tidak dapat digunakan, silakan gunakan nama lain")
        user.phone = phone
        user.address = address
        user.full_name = full_name
    else:
        user = User(full_name=full_name, username=username, phone=phone, address=address, role="customer")
        db.add(user)
    await db.flush()
    return user


# ---------- Auth ----------
@router.post("/auth/customer/login", response_model=TokenOut)
async def customer_login(body: CustomerLoginIn, db: AsyncSession = Depends(get_db)):
    username = normalize_username(body.full_name)
    user = (await db.execute(select(User).where(User.username == username, User.role == "customer"))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "Akun tidak ditemukan. Pastikan Nama Lengkap sama seperti saat checkout.")
    if normalize_phone(user.phone or "") != normalize_phone(body.phone):
        raise HTTPException(401, "No. Telp/WA tidak cocok dengan data pesanan Anda")
    return TokenOut(access_token=create_token(user), user=UserOut.model_validate(user))


@router.get("/auth/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


# ---------- Checkout ----------
@router.post("/checkout", response_model=CheckoutOut)
async def checkout(body: CheckoutIn, db: AsyncSession = Depends(get_db)):
    phone = body.phone.strip()
    if len(normalize_phone(phone)) < 9:
        raise HTTPException(400, "No. Telp/WA tidak valid")

    # validate items
    ids = [i.product_id for i in body.items]
    prods = (await db.execute(select(Product).where(Product.id.in_(ids)))).scalars().all()
    pmap = {p.id: p for p in prods}
    order_items: list[OrderItem] = []
    movements: list[StockMovement] = []
    subtotal = Decimal("0")
    for it in body.items:
        p = pmap.get(it.product_id)
        if not p or not p.is_active:
            raise HTTPException(400, f"Produk tidak tersedia: {it.product_id}")
        if it.qty < p.min_order:
            raise HTTPException(400, f"Minimal pemesanan {p.name} adalah {p.min_order} {p.unit}")
        if p.stock < it.qty:
            raise HTTPException(400, f"Stok {p.name} tidak mencukupi (tersisa {p.stock} {p.unit})")
        line = Decimal(p.price) * it.qty
        subtotal += line
        order_items.append(OrderItem(product_id=p.id, product_name=p.name, image_url=p.image_url, unit=p.unit, price=p.price,
                                     cost_price=p.cost_price, qty=it.qty, subtotal=line))
        stock_before = p.stock
        p.stock -= it.qty
        movements.append(StockMovement(product_id=p.id, product_name=p.name, movement_type="out", qty=-it.qty, stock_before=stock_before,
                                       stock_after=p.stock, source="order", note="Pesanan pelanggan"))

    user = await find_or_create_customer(db, body.full_name, phone, body.address)
    order_number = await generate_order_number(db)
    shipping = Decimal("0")
    total = subtotal + shipping

    order = Order(
        order_number=order_number, user_id=user.id, customer_name=user.full_name, phone=phone, address=body.address,
        notes=body.notes, subtotal=subtotal, shipping_fee=shipping, total=total,
        payment_method=body.payment_method, payment_channel=body.payment_channel,
        payment_status={"cod": "cod", "piutang": "piutang"}.get(body.payment_method, "pending"), order_status="baru",
    )
    order.items = order_items
    db.add(order)
    for mv in movements:
        mv.reference = order_number
        db.add(mv)
    await db.flush()

    # create payment instructions right away
    try:
        charge = await midtrans.create_charge(
            order_number=order_number, amount=int(total), method=body.payment_method, channel=body.payment_channel,
            customer_name=user.full_name, phone=phone,
            items=[{"id": oi.product_id or oi.id, "price": float(oi.price), "qty": oi.qty, "name": oi.product_name} for oi in order_items],
        )
    except Exception as exc:  # gateway error -> keep order, mark pending, expose message
        charge = {"provider": "midtrans", "simulation": False, "reference": None, "payment_status": "pending",
                  "instructions": {"type": body.payment_method, "error": str(exc)}, "raw": {"error": str(exc)}}

    order.payment_ref = charge.get("reference")
    order.payment_status = charge.get("payment_status", order.payment_status)
    order.payment_payload = {"provider": charge["provider"], "simulation": charge["simulation"], "instructions": charge["instructions"]}
    db.add(PaymentTransaction(order_id=order.id, provider=charge["provider"], method=body.payment_method, channel=body.payment_channel,
                              status=order.payment_status, amount=total, reference=charge.get("reference"), raw=charge.get("raw")))
    await db.commit()

    order = (await db.execute(select(Order).where(Order.id == order.id))).scalar_one()
    broadcaster.publish("order.new", {
        "order_id": order.id, "order_number": order_number, "customer_name": user.full_name, "total": float(total),
        "payment_method": body.payment_method, "payment_status": order.payment_status, "items": len(order_items),
    })
    return CheckoutOut(
        order=OrderOut.model_validate(order),
        access_token=create_token(user),
        user=UserOut.model_validate(user),
        payment={
            "order_number": order_number, "payment_method": body.payment_method, "payment_channel": body.payment_channel,
            "payment_status": order.payment_status, "amount": float(total), "provider": charge["provider"],
            "simulation": charge["simulation"], "instructions": charge["instructions"],
        },
    )


# ---------- Orders ----------
@router.get("/orders/me", response_model=list[OrderOut])
async def my_orders(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc()))).scalars().all()
    return [OrderOut.model_validate(o) for o in rows]


@router.get("/orders/{order_number}", response_model=OrderOut)
async def get_order(order_number: str, db: AsyncSession = Depends(get_db)):
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Pesanan tidak ditemukan")
    return OrderOut.model_validate(order)
