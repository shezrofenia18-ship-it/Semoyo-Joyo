"""Buat contoh pesanan (via API asli) agar Dashboard, Piutang & Laporan Penjualan punya data untuk diuji.

Jalankan: cd /app/backend && python scripts/seed_sample_orders.py
- 4 pesanan Cash  -> kasir klik "Selesai / Terima Uang" (lunas, selesai -> dihitung terjual)
- 1 pesanan Cash  -> masih Proses (belum diterima uangnya -> TIDAK masuk laporan)
- 2 pesanan Bayar Nanti -> satu dilunasi (Tandai Lunas), satu masih piutang
- 1 pesanan Bayar Nanti -> status selesai (dihitung terjual walau belum bayar)
- 2 pesanan Bayar Online (QRIS / VA) -> pending (menunggu webhook BATPay; TIDAK masuk laporan)
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

# (metode, kanal, aksi akhir, hari lalu)
PLAN = [
    ("cash", None, "complete", 0), ("cash", None, "complete", 2), ("cash", None, "complete", 5), ("cash", None, "complete", 40),
    ("cash", None, "proses", 0),
    ("piutang", None, "settle", 12), ("piutang", None, "piutang", 1), ("piutang", None, "selesai", 3),
    ("online", "qris", "pending", 0), ("online", "va_bca", "pending", 0),
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
        for i, (method, channel, final, days_ago) in enumerate(PLAN):
            name, phone, addr = CUSTOMERS[i % len(CUSTOMERS)]
            body = {"full_name": name, "phone": phone, "address": addr, "payment_method": method, "payment_channel": channel,
                    "items": pick_items(products, random.randint(1, 3)), "notes": "Contoh pesanan untuk laporan"}
            r = await c.post("/checkout", json=body)
            r.raise_for_status()
            on = r.json()["order"]["order_number"]
            if final == "complete":
                (await c.post(f"/admin/orders/{on}/complete-cash", headers=H)).raise_for_status()
            elif final == "settle":
                (await c.post(f"/admin/orders/{on}/settle", json={"method": "transfer", "note": "Contoh pelunasan piutang"}, headers=H)).raise_for_status()
            elif final == "selesai":
                (await c.patch(f"/admin/orders/{on}/status", json={"order_status": "selesai"}, headers=H)).raise_for_status()
            created.append((on, days_ago))
            print(f"[{i+1:02d}] {on} {method:<8} {channel or '-':<8} -> {final:<9} ({days_ago} hari lalu)")

        # Backdate langsung di DB (created_at & paid_at) agar filter tanggal teruji
        from sqlalchemy import update
        from database import AsyncSessionLocal
        from models import Order

        async with AsyncSessionLocal() as s:
            for on, d in created:
                if d:
                    ts = datetime.now(timezone.utc) - timedelta(days=d, hours=random.randint(0, 6))
                    await s.execute(update(Order).where(Order.order_number == on, Order.paid_at.isnot(None)).values(created_at=ts, paid_at=ts + timedelta(minutes=15)))
                    await s.execute(update(Order).where(Order.order_number == on, Order.paid_at.is_(None)).values(created_at=ts))
            await s.commit()
        print("Selesai. Total pesanan dibuat:", len(created))


if __name__ == "__main__":
    asyncio.run(main())
