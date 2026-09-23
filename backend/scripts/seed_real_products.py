"""Seeder 58 produk ASLI Semoyo Joyo ke PostgreSQL.

Jalankan:  cd /app/backend && python scripts/seed_real_products.py [--keep-old] [--no-verify-images]

Perilaku:
- Upsert berdasarkan slug nama produk (aman dijalankan ulang; tidak menduplikasi).
- Kategori dipetakan ke 7 kategori yang sudah ada (dibuat otomatis bila belum ada).
- Harga jual acak-masuk-akal di sekitar harga pasar (+-8%), harga beli (modal) = ~80% harga jual (margin +-20%).
- Stok awal 1000, min. order sesuai satuan (kg: 5/10, pack/pcs/liter: 5-12, sak/karton/dus: 1-2).
- Gambar: coba foto Unsplash relevan -> diverifikasi (HTTP) -> fallback LoremFlickr dengan kata kunci Inggris.
- Produk contoh lama (dari seed dummy) yang TIDAK ada di daftar ini akan DINONAKTIFKAN (is_active=false) agar
  katalog beranda hanya menampilkan produk asli. Gunakan --keep-old untuk membiarkannya tetap aktif.
"""
from __future__ import annotations

import asyncio
import random
import re
import sys
from decimal import Decimal
from pathlib import Path

import httpx
from dotenv import load_dotenv
from sqlalchemy import select

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from database import AsyncSessionLocal  # noqa: E402
from models import Category, Product, StockMovement  # noqa: E402
from seed import CATEGORIES as SEED_CATEGORIES  # noqa: E402

KEEP_OLD = "--keep-old" in sys.argv
VERIFY_IMAGES = "--no-verify-images" not in sys.argv
STOCK_AWAL = 1000
UNSPLASH = "https://images.unsplash.com/{pid}?auto=format&fit=crop&w=800&q=80"
FLICKR = "https://loremflickr.com/800/600/{kw}?lock={lock}"

BERAS, HEWANI, NABATI, SAYUR, BUAH, BUMBU, SUSU = (
    "Beras & Karbohidrat", "Protein Hewani", "Protein Nabati", "Sayuran Segar", "Buah-buahan", "Minyak, Bumbu & Rempah", "Susu & Olahan",
)

# (nama, kategori, deskripsi B2B, harga jual acuan, satuan, min_order, kata kunci gambar (EN), [unsplash photo id kandidat])
PRODUCTS: list[tuple] = [
    # ---- Beras & Karbohidrat ----
    ("Beras Cap Kelelawar", BERAS, "Beras premium Cap Kelelawar, pulen dan wangi. Kemasan 25 kg, konsisten untuk porsi besar Dapur MBG.", 340000, "sak", 1, "rice,sack", ["photo-1586201375761-83865001e31c"]),
    ("Tepung Terigu", BERAS, "Tepung terigu protein sedang serbaguna, cocok untuk gorengan, adonan, dan bakery skala dapur besar.", 12500, "kg", 10, "wheat,flour", ["photo-1574323347407-f5e1ad6d020b"]),
    ("Tepung Tapioka", BERAS, "Tepung tapioka (kanji) halus dan putih bersih, untuk pengental, cilok, dan adonan bakso.", 11000, "kg", 10, "tapioca,starch,flour", ["photo-1574323347407-f5e1ad6d020b"]),
    ("Tepung Beras", BERAS, "Tepung beras halus untuk kue tradisional, pelapis gorengan renyah, dan bubur.", 13000, "kg", 10, "rice,flour", ["photo-1536304993881-ff6e9eefa2a6", "photo-1586201375761-83865001e31c"]),
    ("Tepung Panir", BERAS, "Tepung panir (bread crumb) kasar berwarna oranye, pelapis renyah untuk nugget, katsu, dan risoles.", 18000, "kg", 5, "bread,crumbs", ["photo-1585325701956-60dd9c8553bc", "photo-1509440159596-0249088772ff"]),
    ("La Fonte Fetuccini", BERAS, "Pasta La Fonte Fettuccine 500 g, tekstur al dente stabil untuk menu pasta porsi besar.", 19500, "pack", 12, "fettuccine,pasta", ["photo-1551183053-bf91a1d81141"]),
    ("Kentang Goreng", BERAS, "Kentang goreng beku (french fries) shoestring 1 kg, hasil renyah, praktis tinggal goreng.", 32000, "kg", 5, "french,fries", ["photo-1573080496219-bb080dd4f877"]),
    # ---- Protein Hewani: ayam & telur ----
    ("Ayam Fillet", HEWANI, "Fillet dada ayam tanpa tulang & kulit, segar dan higienis. Ideal untuk nugget, katsu, dan tumisan.", 52000, "kg", 5, "chicken,breast,fillet", ["photo-1604503468506-a8da13d82791"]),
    ("Ayam Potong", HEWANI, "Ayam broiler potong 8-12 bagian, bersih dan siap masak. Ukuran seragam untuk porsi MBG.", 38000, "kg", 10, "raw,chicken,meat", ["photo-1604503468506-a8da13d82791"]),
    ("Ayam Utuh", HEWANI, "Ayam broiler utuh karkas 0,9-1,1 kg/ekor, sudah dibersihkan, rantai dingin terjaga.", 36000, "kg", 10, "whole,chicken", ["photo-1587593810167-a84920ea0781", "photo-1604503468506-a8da13d82791"]),
    ("Telur Ayam", HEWANI, "Telur ayam negeri segar grade A, 1 peti ±15 kg (±240 butir). Sumber protein harian andalan.", 28500, "kg", 15, "eggs,tray", ["photo-1582722872445-44dc5f7e3c8f"]),
    ("Telur Bebek", HEWANI, "Telur bebek segar ukuran besar, kuning telur pekat. Cocok untuk martabak dan kue.", 3200, "butir", 30, "duck,eggs", ["photo-1506976785307-8732e854ad03", "photo-1582722872445-44dc5f7e3c8f"]),
    ("Telur Asin", HEWANI, "Telur asin bebek matang, rasa gurih pas, masir. Siap saji sebagai lauk pendamping.", 4500, "butir", 30, "salted,egg", ["photo-1498654077810-12c21d4d6dc3", "photo-1582722872445-44dc5f7e3c8f"]),
    # ---- Protein Hewani: ikan & seafood ----
    ("Lele Frozen", HEWANI, "Ikan lele beku ukuran konsumsi (8-10 ekor/kg), sudah dibersihkan, siap goreng.", 27000, "kg", 10, "catfish,fish", ["photo-1510130387422-82bed34b37e9", "photo-1535140728325-a4d3707eee61"]),
    ("Lele Segar", HEWANI, "Ikan lele segar hidup/panen hari yang sama, ukuran konsumsi seragam.", 25000, "kg", 10, "catfish,fresh", ["photo-1510130387422-82bed34b37e9", "photo-1535140728325-a4d3707eee61"]),
    ("Lele Fillet Frozen", HEWANI, "Fillet lele beku tanpa tulang, praktis untuk menu anak, bebas duri.", 48000, "kg", 5, "fish,fillet,raw", ["photo-1519708227418-c8fd9a32b7a2"]),
    ("Ikan Dori", HEWANI, "Fillet ikan dori beku premium tanpa tulang, daging putih lembut, favorit menu MBG.", 56000, "kg", 5, "dory,fish,fillet", ["photo-1519708227418-c8fd9a32b7a2"]),
    ("Patin Frozen", HEWANI, "Ikan patin beku utuh, sudah dibersihkan, cocok untuk pindang dan gulai.", 30000, "kg", 10, "pangasius,fish", ["photo-1510130387422-82bed34b37e9", "photo-1535140728325-a4d3707eee61"]),
    ("Patin Fillet Frozen", HEWANI, "Fillet ikan patin beku tanpa tulang & kulit, rendah duri, siap olah.", 49000, "kg", 5, "white,fish,fillet", ["photo-1519708227418-c8fd9a32b7a2"]),
    ("Nila Frozen", HEWANI, "Ikan nila beku ukuran 3-4 ekor/kg, sudah disisik dan dibersihkan.", 32000, "kg", 10, "tilapia,fish", ["photo-1510130387422-82bed34b37e9", "photo-1535140728325-a4d3707eee61"]),
    ("Gurame Frozen", HEWANI, "Ikan gurame beku ukuran 2-3 ekor/kg, daging tebal, cocok untuk goreng dan bakar.", 55000, "kg", 5, "gourami,fish", ["photo-1510130387422-82bed34b37e9", "photo-1535140728325-a4d3707eee61"]),
    ("Udang Frozen", HEWANI, "Udang vannamei beku kupas (PD) size 41-50, higienis, siap masak.", 95000, "kg", 5, "frozen,shrimp", ["photo-1565680018434-b513d5e5fd47"]),
    ("Udang Segar", HEWANI, "Udang vannamei segar ukuran sedang (size 50-60), dikirim dengan es untuk kesegaran maksimal.", 88000, "kg", 5, "fresh,shrimp,prawn", ["photo-1559737558-2f5a35f4523b", "photo-1565680018434-b513d5e5fd47"]),
    # ---- Protein Nabati ----
    ("Edamame", NABATI, "Edamame beku premium berkulit, tinggi protein nabati. Cocok untuk camilan sehat dan pelengkap menu.", 28000, "kg", 5, "edamame,soybeans", ["photo-1515543904379-3d757afe72e4"]),
    # ---- Sayuran Segar ----
    ("Wortel", SAYUR, "Wortel segar ukuran sedang, manis dan renyah. Panen lokal, disortir seragam.", 12000, "kg", 10, "carrots,vegetable", ["photo-1598170845058-32b9d6a5da37"]),
    ("Kenot", SAYUR, "Kenot (wortel impor/baby carrot) segar, tekstur renyah dan warna cerah untuk sup dan salad.", 16000, "kg", 5, "baby,carrots", ["photo-1598170845058-32b9d6a5da37"]),
    ("Tomat", SAYUR, "Tomat merah segar grade A, padat dan tidak lembek. Untuk sup, sambal, dan tumisan.", 10000, "kg", 10, "tomatoes,fresh", ["photo-1592924357228-91a4daadcfea"]),
    ("Kol", SAYUR, "Kol/kubis putih segar ukuran besar, krop padat. Cocok untuk sup, capcay, dan lalapan.", 7000, "kg", 10, "cabbage,vegetable", ["photo-1594282486552-05b4d80fbb9f"]),
    ("Selada", SAYUR, "Selada keriting segar petik pagi, daun renyah untuk salad dan pelengkap burger.", 18000, "kg", 5, "lettuce,fresh", ["photo-1622206151226-18ca2c9ab4a1", "photo-1622206151226-18ca2c9ab4a1"]),
    ("Pakcoy", SAYUR, "Sawi pakcoy segar, batang renyah dan daun hijau tua. Ideal untuk tumisan dan mie.", 12000, "kg", 5, "bok,choy", ["photo-1626139576127-f02f74c10298", "photo-1622206151226-18ca2c9ab4a1"]),
    ("Bawang Merah", SAYUR, "Bawang merah Brebes kering askip, aroma tajam, kualitas super.", 38000, "kg", 5, "shallots,onion", ["photo-1618512496248-a07fe83aa8cb"]),
    ("Bawang Putih", SAYUR, "Bawang putih kating, kering dan padat, siap pakai untuk bumbu dasar.", 34000, "kg", 5, "garlic,bulbs", ["photo-1540148426945-6cf22a6b2383"]),
    ("Bawang Merah Kupas", SAYUR, "Bawang merah kupas siap pakai, hemat waktu persiapan dapur. Dikupas higienis hari yang sama.", 46000, "kg", 5, "peeled,shallots", ["photo-1618512496248-a07fe83aa8cb"]),
    ("Bawang Putih Kupas", SAYUR, "Bawang putih kupas siap pakai, bersih tanpa kulit, efisien untuk produksi massal.", 42000, "kg", 5, "peeled,garlic", ["photo-1540148426945-6cf22a6b2383"]),
    ("Bawang Bombay", SAYUR, "Bawang bombay ukuran besar, manis saat ditumis. Untuk saus, sup, dan menu western.", 24000, "kg", 5, "onions,yellow", ["photo-1518977956812-cd3dbadaaf31"]),
    ("Cabai Merah Besar", SAYUR, "Cabai merah besar segar, warna merah merata, untuk sambal dan bumbu halus.", 42000, "kg", 5, "red,chili,peppers", ["photo-1583119022894-919a68a3d0e3"]),
    ("Parsli", SAYUR, "Parsley (peterseli) segar, aroma harum untuk garnish dan bumbu menu western.", 45000, "kg", 1, "parsley,herb", ["photo-1708798534031-3711ec8cc16e", "photo-1622206151226-18ca2c9ab4a1"]),
    ("Frozen Mix Vegetable", SAYUR, "Sayuran campur beku (wortel, jagung, buncis, kacang polong) 1 kg. Praktis, bergizi, tanpa limbah kupas.", 26000, "kg", 5, "frozen,mixed,vegetables", ["photo-1540420773420-3366772f4999"]),
    ("Bunga Kol Frozen", SAYUR, "Bunga kol (cauliflower) beku potong, siap masak, kualitas ekspor.", 24000, "kg", 5, "cauliflower,florets", ["photo-1568584711075-3d021a7c3ca3"]),
    # ---- Buah-buahan ----
    ("Jambu Citra", BUAH, "Jambu air Citra merah, manis dan renyah, ukuran besar. Buah segar untuk menu MBG.", 22000, "kg", 5, "rose,apple,fruit", ["photo-1536511132770-e5058c7e8c46", "photo-1610832958506-aa56368176cf"]),
    ("Melon", BUAH, "Melon hijau/madu manis, berat 1,5-2 kg per buah, tingkat kematangan optimal.", 15000, "kg", 10, "melon,fruit", ["photo-1571575173700-afb9492e6a50"]),
    ("Semangka", BUAH, "Semangka merah non-biji, berat 3-5 kg per buah, manis dan segar.", 8000, "kg", 20, "watermelon,fruit", ["photo-1587049352846-4a222e784d38"]),
    # ---- Minyak, Bumbu & Rempah ----
    ("Minyak Goreng", BUMBU, "Minyak goreng sawit kemasan jerigen 18 liter, jernih dan tidak cepat tengik.", 285000, "jerigen", 1, "cooking,oil", ["photo-1474979266404-7eaacbcd87c5"]),
    ("Saos Tiram", BUMBU, "Saus tiram kemasan besar untuk tumisan dan marinasi, rasa gurih konsisten.", 32000, "botol", 6, "oyster,sauce", ["photo-1654245137394-1de7e1e16f6f", "photo-1598514983318-2f64f8f4796c"]),
    ("Kecap Inggris", BUMBU, "Kecap inggris (worcestershire) untuk marinasi steak, saus, dan tumisan ala western.", 28000, "botol", 6, "worcestershire,sauce", ["photo-1591496534942-8ea0cb46182b", "photo-1598514983318-2f64f8f4796c"]),
    ("Kecap Manis", BUMBU, "Kecap manis refill 5,7 kg, kental dan legit, untuk kebutuhan dapur besar.", 98000, "pouch", 2, "soy,sauce", ["photo-1711915528610-8699564923e8", "photo-1598514983318-2f64f8f4796c"]),
    ("Cury Powder", BUMBU, "Bubuk kari (curry powder) impor, aroma rempah kuat untuk kari, marinasi, dan saus.", 65000, "kg", 1, "curry,powder,spice", ["photo-1509358271058-acd22cc93898", "photo-1596040033229-a9821ebd058d"]),
    ("Garam Dolphin", BUMBU, "Garam beryodium Cap Dolphin halus 250 g, dus isi 40. Standar rasa dapur profesional.", 120000, "dus", 1, "salt,seasoning", ["photo-1518110925495-5fe2fda0442c"]),
    ("Gula Pasir", BUMBU, "Gula pasir putih kristal, kemasan 50 kg, larut cepat untuk minuman dan masakan.", 16500, "kg", 10, "white,sugar", ["photo-1673791031202-ebc0eea03bf2", "photo-1581441363689-1f3c3c414635"]),
    ("Gula Merah", BUMBU, "Gula merah/aren asli cetak, aroma karamel alami untuk bumbu dan kue tradisional.", 24000, "kg", 5, "palm,sugar", ["photo-1641679103706-fc8542e2a97a", "photo-1581441363689-1f3c3c414635"]),
    ("Kemiri", BUMBU, "Kemiri kupas kering kualitas super, bumbu dasar untuk opor, soto, dan rendang.", 48000, "kg", 2, "candlenut,spice", ["photo-1509358271058-acd22cc93898", "photo-1596040033229-a9821ebd058d"]),
    ("Ketumbar", BUMBU, "Ketumbar butir kering, aroma harum khas untuk bumbu ayam goreng dan empal.", 42000, "kg", 2, "coriander,seeds", ["photo-1596040033229-a9821ebd058d", "photo-1596040033229-a9821ebd058d"]),
    ("Oregano", BUMBU, "Oregano kering premium untuk pizza, pasta, dan saus, aroma stabil.", 28000, "pack", 6, "oregano,dried,herb", ["photo-1596040033229-a9821ebd058d", "photo-1596040033229-a9821ebd058d"]),
    ("Mayonaise", BUMBU, "Mayones kemasan 1 kg, tekstur lembut dan creamy untuk salad, burger, dan sandwich.", 36000, "kg", 5, "mayonnaise,sauce", ["photo-1573812461383-e5f8b759d12e", "photo-1598514983318-2f64f8f4796c"]),
    ("Mustard", BUMBU, "Saus mustard kemasan besar, rasa tajam khas untuk hot dog, burger, dan dressing.", 42000, "botol", 6, "mustard,sauce", ["photo-1697026993856-261121bb5025", "photo-1598514983318-2f64f8f4796c"]),
    # ---- Susu & Olahan ----
    ("Susu UHT", SUSU, "Susu UHT full cream 1 liter, karton isi 12. Sumber kalsium harian untuk menu MBG.", 210000, "karton", 1, "milk,carton", ["photo-1550583724-b2692b85b150", "photo-1563636619-e9143da7973b"]),
    ("Cooking Cream", SUSU, "Cooking cream 1 liter, tahan panas dan tidak pecah, untuk saus krim dan sup western.", 58000, "liter", 6, "cooking,cream", ["photo-1528750997573-59b89d56f4f7", "photo-1563636619-e9143da7973b"]),
    ("Mentega", SUSU, "Mentega (butter) blok 1 kg, aroma gurih untuk bakery, saus, dan tumisan.", 68000, "kg", 5, "butter,block", ["photo-1589985270826-4b7bb135bc9d", "photo-1486297678162-eb2a19b0a32d"]),
]

assert len(PRODUCTS) == 58, f"Jumlah produk {len(PRODUCTS)} != 58"


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9\s-]", "", text.lower().strip())
    return re.sub(r"[\s-]+", "-", s).strip("-")


def round_price(n: float) -> int:
    step = 100 if n < 20000 else 500
    return int(round(n / step) * step)


def make_prices(base: int) -> tuple[Decimal, Decimal]:
    """Harga jual acak +-8% dari acuan; modal = 78-82% harga jual (margin ~20%)."""
    price = round_price(base * random.uniform(0.92, 1.08))
    cost = round_price(price * random.uniform(0.78, 0.82))
    return Decimal(price), Decimal(cost)


async def pick_image(client: httpx.AsyncClient, candidates: list[str], keywords: str, lock: int) -> str:
    fallback = FLICKR.format(kw=keywords, lock=lock)
    if not VERIFY_IMAGES:
        return UNSPLASH.format(pid=candidates[0]) if candidates else fallback
    for pid in candidates:
        url = UNSPLASH.format(pid=pid)
        try:
            r = await client.head(url, follow_redirects=True, timeout=8)
            if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
                return url
        except Exception:
            pass
    return fallback


async def main() -> None:
    random.seed(2026)
    async with AsyncSessionLocal() as db, httpx.AsyncClient() as client:
        # -- kategori --
        cats = {c.name: c for c in (await db.execute(select(Category))).scalars().all()}
        for sc in SEED_CATEGORIES:
            if sc["name"] not in cats:
                c = Category(name=sc["name"], slug=slugify(sc["name"]), description=sc["description"], image_url=sc["image_url"], sort_order=len(cats))
                db.add(c)
                await db.flush()
                cats[c.name] = c
                print(f"+ kategori baru: {c.name}")

        existing = {p.slug: p for p in (await db.execute(select(Product))).scalars().all()}
        new_slugs: set[str] = set()
        created = updated = 0

        print(f"Memproses {len(PRODUCTS)} produk (verifikasi gambar: {'ya' if VERIFY_IMAGES else 'tidak'})...")
        for i, (name, cat_name, desc, base, unit, min_order, kw, pids) in enumerate(PRODUCTS, start=1):
            slug = slugify(name)
            new_slugs.add(slug)
            price, cost = make_prices(base)
            image = await pick_image(client, pids, kw, lock=100 + i)
            cat = cats[cat_name]
            p = existing.get(slug)
            if p:
                p.category_id, p.name, p.description, p.price, p.cost_price, p.unit, p.min_order, p.image_url, p.is_active = (
                    cat.id, name, desc, price, cost, unit, min_order, image, True)
                if p.stock < STOCK_AWAL:
                    db.add(StockMovement(product_id=p.id, product_name=p.name, movement_type="in", qty=STOCK_AWAL - p.stock, stock_before=p.stock,
                                         stock_after=STOCK_AWAL, source="manual", note="Penyesuaian stok awal (seed produk asli)", created_by="seeder"))
                    p.stock = STOCK_AWAL
                updated += 1
                tag = "~ update"
            else:
                p = Product(category_id=cat.id, name=name, slug=slug, description=desc, price=price, cost_price=cost, unit=unit, min_order=min_order,
                            stock=STOCK_AWAL, image_url=image, is_active=True)
                db.add(p)
                await db.flush()
                db.add(StockMovement(product_id=p.id, product_name=p.name, movement_type="in", qty=STOCK_AWAL, stock_before=0, stock_after=STOCK_AWAL,
                                     source="manual", note="Stok awal produk asli (seeder)", created_by="seeder"))
                created += 1
                tag = "+ baru  "
            margin = float((price - cost) / price * 100)
            src = "unsplash" if "unsplash" in image else "flickr"
            print(f"[{i:02d}] {tag} {name:<24} {cat_name:<24} jual Rp{int(price):>9,} modal Rp{int(cost):>9,} margin {margin:4.1f}%  {unit:<7} min {min_order:<3} img:{src}")

        # -- nonaktifkan produk dummy lama yang tidak ada di daftar --
        deactivated = 0
        if not KEEP_OLD:
            for slug, p in existing.items():
                if slug not in new_slugs and p.is_active:
                    p.is_active = False
                    deactivated += 1

        await db.commit()
        active = (await db.execute(select(Product).where(Product.is_active.is_(True)))).scalars().all()
        print("\n=== SELESAI ===")
        print(f"Produk baru dibuat : {created}")
        print(f"Produk diperbarui  : {updated}")
        print(f"Produk lama dinonaktifkan: {deactivated}{' (dilewati, --keep-old)' if KEEP_OLD else ''}")
        print(f"Total produk aktif di katalog: {len(active)}")


if __name__ == "__main__":
    asyncio.run(main())
