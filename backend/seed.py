"""Seed data: kategori & produk bahan baku dapur MBG + akun admin."""
import logging
import os
import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import hash_password
from models import Category, Product, User

logger = logging.getLogger("mbg.seed")


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9\s-]", "", text.lower().strip())
    return re.sub(r"[\s-]+", "-", s).strip("-")


U = "https://images.unsplash.com/"
Q = "?auto=format&fit=crop&w=800&q=80"

CATEGORIES = [
    {"name": "Beras & Karbohidrat", "description": "Beras, jagung, ubi, mie, dan sumber karbohidrat lainnya", "image_url": U + "photo-1586201375761-83865001e31c" + Q},
    {"name": "Protein Hewani", "description": "Ayam, daging sapi, ikan, dan telur segar", "image_url": U + "photo-1604503468506-a8da13d82791" + Q},
    {"name": "Protein Nabati", "description": "Tahu, tempe, kacang-kacangan", "image_url": U + "photo-1626804475297-41608ea09aeb" + Q},
    {"name": "Sayuran Segar", "description": "Sayur mayur segar langsung dari petani", "image_url": U + "photo-1540420773420-3366772f4999" + Q},
    {"name": "Buah-buahan", "description": "Buah segar untuk pelengkap menu bergizi", "image_url": U + "photo-1610832958506-aa56368176cf" + Q},
    {"name": "Minyak, Bumbu & Rempah", "description": "Minyak goreng, gula, garam, kecap, dan bumbu dapur", "image_url": U + "photo-1596040033229-a9821ebd058d" + Q},
    {"name": "Susu & Olahan", "description": "Susu UHT, keju, dan produk olahan susu", "image_url": U + "photo-1563636619-e9143da7973b" + Q},
]

PRODUCTS = [
    # Beras & Karbohidrat
    ("Beras & Karbohidrat", "Beras Medium Premium", "Beras putih medium kualitas premium, pulen, cocok untuk porsi besar dapur MBG.", 12500, "kg", 25, 5000, "photo-1586201375761-83865001e31c"),
    ("Beras & Karbohidrat", "Beras Merah Organik", "Beras merah organik tinggi serat untuk menu sehat.", 18000, "kg", 10, 800, "photo-1536304993881-ff6e9eefa2a6"),
    ("Beras & Karbohidrat", "Jagung Manis Pipil", "Jagung manis pipil segar, siap olah untuk sup dan tumisan.", 11000, "kg", 10, 600, "photo-1551754655-cd27e38d2076"),
    ("Beras & Karbohidrat", "Kentang Granola", "Kentang granola ukuran sedang, cocok untuk perkedel dan sup.", 14000, "kg", 10, 900, "photo-1518977676601-b53f82aba655"),
    ("Beras & Karbohidrat", "Mie Telur Kering", "Mie telur kering kemasan 1 kg, praktis untuk menu mie goreng/rebus.", 22000, "pack", 5, 400, "photo-1612929633738-8fe44f7ec841"),
    ("Beras & Karbohidrat", "Tepung Terigu Protein Sedang", "Tepung terigu serbaguna kemasan 25 kg.", 265000, "sak", 1, 120, "photo-1574323347407-f5e1ad6d020b"),
    # Protein Hewani
    ("Protein Hewani", "Ayam Broiler Karkas", "Ayam broiler karkas segar 0,9-1,1 kg/ekor, sudah dibersihkan.", 36000, "kg", 10, 1500, "photo-1604503468506-a8da13d82791"),
    ("Protein Hewani", "Daging Sapi Giling", "Daging sapi giling segar, rendah lemak, untuk bakso dan perkedel daging.", 125000, "kg", 5, 300, "photo-1603048297172-c92544798d5a"),
    ("Protein Hewani", "Ikan Kembung Segar", "Ikan kembung segar hasil tangkapan nelayan lokal.", 38000, "kg", 10, 500, "photo-1535140728325-a4d3707eee61"),
    ("Protein Hewani", "Fillet Ikan Dori", "Fillet ikan dori beku tanpa tulang, praktis untuk anak-anak.", 58000, "kg", 5, 350, "photo-1519708227418-c8fd9a32b7a2"),
    ("Protein Hewani", "Telur Ayam Negeri", "Telur ayam negeri segar grade A, 1 peti = 15 kg (~240 butir).", 27500, "kg", 15, 2000, "photo-1582722872445-44dc5f7e3c8f"),
    # Protein Nabati
    ("Protein Nabati", "Tempe Kedelai", "Tempe kedelai murni papan 500 g, fermentasi sempurna.", 8000, "papan", 20, 1000, "photo-1626804475297-41608ea09aeb"),
    ("Protein Nabati", "Tahu Putih", "Tahu putih ukuran besar, 10 potong per pack.", 9000, "pack", 20, 800, "photo-1546069901-ba9599a7e63c"),
    ("Protein Nabati", "Kacang Hijau", "Kacang hijau kualitas super untuk bubur dan sup.", 24000, "kg", 5, 400, "photo-1515543904379-3d757afe72e4"),
    ("Protein Nabati", "Kacang Tanah Kupas", "Kacang tanah kupas kering untuk bumbu pecel dan sambal kacang.", 32000, "kg", 5, 300, "photo-1567892737950-30c4db37cd89"),
    # Sayuran Segar
    ("Sayuran Segar", "Wortel Lokal", "Wortel segar ukuran sedang, manis dan renyah.", 12000, "kg", 10, 700, "photo-1598170845058-32b9d6a5da37"),
    ("Sayuran Segar", "Bayam Hijau", "Bayam hijau segar petik pagi, ikat 250 g.", 4000, "ikat", 30, 900, "photo-1576045057995-568f588f82fb"),
    ("Sayuran Segar", "Kangkung", "Kangkung segar, ikat 250 g.", 3500, "ikat", 30, 900, "photo-1622206151226-18ca2c9ab4a1"),
    ("Sayuran Segar", "Tomat Merah", "Tomat merah segar grade A untuk sup, sambal, dan tumisan.", 10000, "kg", 10, 600, "photo-1592924357228-91a4daadcfea"),
    ("Sayuran Segar", "Buncis", "Buncis muda segar, renyah.", 13000, "kg", 5, 400, "photo-1567375698348-5d9d5ae99de0"),
    ("Sayuran Segar", "Kol / Kubis", "Kol putih segar ukuran besar.", 7000, "kg", 10, 500, "photo-1594282486552-05b4d80fbb9f"),
    ("Sayuran Segar", "Bawang Merah", "Bawang merah Brebes kering askip.", 38000, "kg", 5, 400, "photo-1618512496248-a07fe83aa8cb"),
    ("Sayuran Segar", "Bawang Putih", "Bawang putih kating, kering dan padat.", 34000, "kg", 5, 400, "photo-1540148426945-6cf22a6b2383"),
    ("Sayuran Segar", "Cabai Merah Besar", "Cabai merah besar segar untuk sambal dan bumbu.", 42000, "kg", 3, 200, "photo-1583119022894-919a68a3d0e3"),
    # Buah-buahan
    ("Buah-buahan", "Pisang Cavendish", "Pisang cavendish matang optimal, 1 sisir ± 1,2 kg.", 16000, "kg", 10, 600, "photo-1571771894821-ce9b6c11b08e"),
    ("Buah-buahan", "Jeruk Medan", "Jeruk medan manis, ukuran sedang.", 22000, "kg", 10, 500, "photo-1547514701-42782101795e"),
    ("Buah-buahan", "Semangka Merah", "Semangka merah non-biji, berat 3-5 kg/buah.", 8000, "kg", 20, 800, "photo-1587049352846-4a222e784d38"),
    ("Buah-buahan", "Pepaya California", "Pepaya california matang, manis, 1-1,5 kg/buah.", 9000, "kg", 15, 500, "photo-1526318472351-c75fcf070305"),
    ("Buah-buahan", "Melon Hijau", "Melon hijau manis, 1,5-2 kg/buah.", 15000, "kg", 10, 300, "photo-1571575173700-afb9492e6a50"),
    # Minyak, Bumbu & Rempah
    ("Minyak, Bumbu & Rempah", "Minyak Goreng Sawit", "Minyak goreng sawit kemasan jerigen 18 liter.", 285000, "jerigen", 1, 200, "photo-1474979266404-7eaacbcd87c5"),
    ("Minyak, Bumbu & Rempah", "Gula Pasir", "Gula pasir putih kemasan 1 kg.", 17500, "kg", 10, 800, "photo-1581441363689-1f3c3c414635"),
    ("Minyak, Bumbu & Rempah", "Garam Beryodium", "Garam halus beryodium kemasan 500 g.", 4500, "pack", 20, 1000, "photo-1518110925495-5fe2fda0442c"),
    ("Minyak, Bumbu & Rempah", "Kecap Manis", "Kecap manis refill 5,7 kg untuk kebutuhan dapur besar.", 98000, "pouch", 1, 150, "photo-1598514983318-2f64f8f4796c"),
    ("Minyak, Bumbu & Rempah", "Santan Kelapa Cair", "Santan kelapa cair UHT kemasan 1 liter.", 28000, "liter", 6, 300, "photo-1622597467836-f3285f2131b8"),
    ("Minyak, Bumbu & Rempah", "Bumbu Dasar Kuning", "Bumbu dasar kuning siap pakai kemasan 1 kg.", 45000, "kg", 2, 150, "photo-1596040033229-a9821ebd058d"),
    # Susu & Olahan
    ("Susu & Olahan", "Susu UHT Full Cream 1L", "Susu UHT full cream kemasan 1 liter, karton isi 12.", 210000, "karton", 1, 300, "photo-1563636619-e9143da7973b"),
    ("Susu & Olahan", "Susu UHT Kotak 125ml", "Susu UHT rasa cokelat/stroberi 125 ml, karton isi 40.", 148000, "karton", 2, 500, "photo-1550583724-b2692b85b150"),
    ("Susu & Olahan", "Keju Cheddar Blok", "Keju cheddar olahan blok 2 kg.", 135000, "blok", 1, 100, "photo-1486297678162-eb2a19b0a32d"),
]


async def seed_if_empty(db: AsyncSession) -> None:
    # ---- admin user ----
    admin_username = os.environ.get("ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    res = await db.execute(select(User).where(User.username == admin_username))
    admin = res.scalar_one_or_none()
    if not admin:
        db.add(User(full_name="Administrator", username=admin_username, role="admin", password_hash=hash_password(admin_password)))
        logger.info("seed: admin user created (%s)", admin_username)
    else:
        admin.role = "admin"
        admin.password_hash = hash_password(admin_password)

    count = (await db.execute(select(func.count(Category.id)))).scalar() or 0
    if count == 0:
        cat_map: dict[str, Category] = {}
        for i, c in enumerate(CATEGORIES):
            cat = Category(name=c["name"], slug=slugify(c["name"]), description=c["description"], image_url=c["image_url"], sort_order=i)
            db.add(cat)
            cat_map[c["name"]] = cat
        await db.flush()
        for cat_name, name, desc, price, unit, min_order, stock, photo in PRODUCTS:
            db.add(Product(
                category_id=cat_map[cat_name].id, name=name, slug=slugify(name), description=desc,
                price=price, unit=unit, min_order=min_order, stock=stock, image_url=U + photo + Q, is_active=True,
            ))
        logger.info("seed: %d categories, %d products inserted", len(CATEGORIES), len(PRODUCTS))
    await db.commit()
