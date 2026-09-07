"""Phase 1 POC: prove PostgreSQL + SQLAlchemy async works end-to-end in isolation.

Run: cd /app/backend && python test_core.py
"""
import asyncio
import subprocess
from decimal import Decimal

from sqlalchemy import select, text

from database import AsyncSessionLocal, Base, engine, ensure_local_postgres
from models import Category, Order, OrderItem, PaymentTransaction, Product, User


async def main():
    print("1) ensure_local_postgres...")
    ensure_local_postgres()

    print("2) raw connection + version...")
    async with engine.connect() as conn:
        v = (await conn.execute(text("select version()"))).scalar()
        print("   OK:", v.split(",")[0])

    print("3) create tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with engine.connect() as conn:
        tables = (await conn.execute(text(
            "select table_name from information_schema.tables where table_schema='public' order by 1"))).scalars().all()
        print("   tables:", tables)
        for t in ["users", "categories", "products", "orders", "order_items", "payment_transactions"]:
            assert t in tables, f"missing table {t}"

    print("4) insert/select roundtrip (category -> product -> user -> order -> item -> payment)...")
    async with AsyncSessionLocal() as s:
        cat = Category(name="POC Kategori", slug="poc-kategori-" + str(id(s)))
        s.add(cat)
        await s.flush()
        prod = Product(category_id=cat.id, name="POC Beras", slug="poc-beras-" + str(id(s)),
                       price=Decimal("12500.00"), unit="kg", min_order=25, stock=1000)
        s.add(prod)
        user = User(full_name="Budi POC", username="budi-poc-" + str(id(s)), phone="0812", address="Jl. Test")
        s.add(user)
        await s.flush()
        order = Order(order_number="MBG-POC-" + str(id(s))[-6:], user_id=user.id, customer_name=user.full_name,
                      phone="0812", address="Jl. Test", subtotal=Decimal("312500"), total=Decimal("312500"),
                      payment_method="bank_transfer", payment_payload={"mode": "simulation"})
        s.add(order)
        await s.flush()
        s.add(OrderItem(order_id=order.id, product_id=prod.id, product_name=prod.name, unit="kg",
                        price=prod.price, qty=25, subtotal=Decimal("312500")))
        s.add(PaymentTransaction(order_id=order.id, provider="simulation", method="bank_transfer",
                                 status="pending", amount=Decimal("312500"), raw={"va": "123"}))
        await s.commit()

        res = await s.execute(select(Order).where(Order.id == order.id))
        o = res.scalar_one()
        assert o.items and o.items[0].qty == 25
        assert o.payment_payload["mode"] == "simulation"
        print("   OK order", o.order_number, "items:", len(o.items), "total:", o.total)

        # cleanup POC rows
        await s.delete(o)
        await s.delete(user)
        await s.delete(prod)
        await s.delete(cat)
        await s.commit()
        print("   cleanup OK")

    print("5) self-healing script idempotency...")
    r = subprocess.run(["bash", "scripts/ensure_postgres.sh"], capture_output=True, text=True)
    print("   ", r.stdout.strip(), "| rc=", r.returncode)
    assert r.returncode == 0

    await engine.dispose()
    print("\nPOC SUCCESS: PostgreSQL + SQLAlchemy async fully working")


if __name__ == "__main__":
    asyncio.run(main())
