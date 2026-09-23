"""Buat contoh pesanan (via API asli) agar Laporan Penjualan punya data untuk diuji.

Jalankan: cd /app/backend && python scripts/seed_sample_orders.py
- 6 pesanan transfer -> disimulasikan lunas
- 2 pesanan COD -> status selesai (dihitung terjual)
- 1 pesanan COD baru (belum selesai -> TIDAK masuk laporan)
- 1 pesanan transfer pending (TIDAK masuk laporan)
Beberapa pesanan lunas di-backdate (2, 5, 12, 40 hari lalu) langsung di DB agar filter periode teruji.
"""
import asyncio
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

BASE = os.environ.get("SEED_API_BASE", "http://localhost:8001/api")
ADMIN = (os.environ.get("ADMIN_USERNAME", "admin"), os.environ.get("ADMIN_PASSWORD", "admin123"))

CUSTOMERS = [
    ("SPPG Dapur Melati", "081234567001", "Jl. Melati No. 10, Semarang"),
    ("Katering Berkah Jaya", "081234567002", "Jl. Pandanaran 45, Semarang"),
    ("Warung Makan Bu Sri", "081234567003", "Jl. Gajah Mada 12, Semarang"),
    ("Dapur MBG Sejahtera", "081234567004", "Jl. Pemuda 88, Semarang"),
    ("Rumah Makan Padang Raya", "081234567005", "Jl. Ahmad Yani 3, Semarang"),
]


def pick_items(products, n):
    chosen = random.sample(products, n)
    return [{"product_id": p["id"], "qty": p["min_order"] * random.randint(1, 3)} for p in chosen]


async def main():
    random.seed(42)
    async with httpx.AsyncClient(base_url=BASE, timeout=30) as c:
        home = (await c.get("/home")).json()
        products = [p for cat in home.get("categories", []) for p in cat.get("products", []) if p.get("stock", 0) > 20]
        if not products:
            prods = (await c.get("/products")).json()
            products = [p for p in prods if p.get("stock", 0) > 20]
        assert products, "Tidak ada produk"
        tok = (await c.post("/admin/login", json={"username": ADMIN[0], "password": ADMIN[1]})).json()["access_token"]
        H = {"Authorization": f"Bearer {tok}"}

        created = []  # (order_number, days_ago)
        plan = [("bank_transfer", "bca", "paid", 0), ("bank_transfer", "bni", "paid", 0), ("ewallet", "gopay", "paid", 2), ("bank_transfer", "mandiri", "paid", 5),
                ("qris", None, "paid", 12), ("bank_transfer", "bri", "paid", 40), ("cod", None, "selesai", 1), ("cod", None, "selesai", 3),
                ("cod", None, "baru", 0), ("bank_transfer", "bca", "pending", 0)]
        for i, (method, channel, final, days_ago) in enumerate(plan):
            name, phone, addr = CUSTOMERS[i % len(CUSTOMERS)]
            body = {"full_name": name, "phone": phone, "address": addr, "payment_method": method, "payment_channel": channel, "items": pick_items(products, random.randint(1, 3)),
                    "notes": "Contoh pesanan untuk laporan"}
            r = await c.post("/checkout", json=body)
            r.raise_for_status()
            on = r.json().get("order_number") or r.json().get("order", {}).get("order_number")
            if method != "cod":
                await c.post(f"/payments/{on}/create", json={"payment_method": method, "payment_channel": channel})
            if final == "paid":
                (await c.post(f"/payments/{on}/simulate")).raise_for_status()
            elif final == "selesai":
                (await c.patch(f"/admin/orders/{on}/status", json={"order_status": "selesai"}, headers=H)).raise_for_status()
            created.append((on, days_ago))
            print(f"[{i+1:02d}] {on} {method:<13} -> {final:<8} ({days_ago} hari lalu)")

        # Backdate langsung di DB (created_at & paid_at) agar filter tanggal teruji
        from sqlalchemy import update
        from database import AsyncSessionLocal
        from models import Order

        async with AsyncSessionLocal() as s:
            for on, d in created:
                if d:
                    ts = datetime.now(timezone.utc) - timedelta(days=d, hours=random.randint(0, 6))
                    await s.execute(update(Order).where(Order.order_number == on).values(created_at=ts, paid_at=ts + timedelta(minutes=15)))
            await s.commit()
        print("Selesai. Total pesanan dibuat:", len(created))


if __name__ == "__main__":
    asyncio.run(main())
