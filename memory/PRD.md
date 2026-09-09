# PRD - Semoyo Joyo B2B E-Commerce + Mini ERP

## Ringkasan
Web app B2B supplier bahan baku (ex "Supplier MBG", rebrand ke **Semoyo Joyo - Solusi Belanja Terpercaya**). Stack: FastAPI + SQLAlchemy async + PostgreSQL 15, React + Tailwind + shadcn/ui. Bahasa Indonesia. Deploy via Coolify (docker-compose).
Brand: Biru #0B4EA2 (primary), Kuning #F5C400 (aksen), Putih. Logo: frontend/public/logo.png, logo-icon.png, favicon.png.

## Tahap 1 (SELESAI)
- Skema: users, categories, products, orders, order_items, payment_transactions
- Beranda katalog per kategori, search, keranjang, checkout tanpa registrasi (nama + WA)
- Pembayaran: COD, VA Midtrans (SIMULASI jika key kosong), QRIS placeholder, E-Wallet; webhook Midtrans
- Riwayat & detail pesanan; login ringan pelanggan
- Admin: login, dashboard KPI, CRUD kategori & produk (+upload), pesanan + ubah status

## Tahap 2 (SELESAI - backend teruji 100%)
- Rebranding Semoyo Joyo + tema biru/kuning/putih; tombol "Portal Admin" -> "Dashboard Admin" (langsung ke /admin/dashboard) jika owner sudah login (Navbar, Footer, dropdown)
- Produk: `cost_price` (harga beli/modal) + laba/unit + margin; migrasi ringan otomatis (backfill 80% harga sekali)
- Dashboard keuangan: omzet, HPP, laba kotor, margin, nilai stok, laba per produk (hanya pesanan paid ATAU COD selesai, bukan dibatalkan)
- Stok Barang (/admin/stok): ringkasan, tabel status habis/menipis/aman, Tambah/Kurangi/Edit(set)/Riwayat/Hapus; tabel `stock_movements` (auto-log dari checkout, batal, hapus pesanan, form produk)
- Pesanan admin: Edit (nama/telp/alamat/catatan/ongkir/status) + Hapus (stok dikembalikan)
- Nomor pesanan prefix `SJ-`

## API baru
- GET/POST/PUT /api/admin/products (cost_price), GET /api/admin/stock, POST /api/admin/stock/{id}/adjust, GET /api/admin/stock/movements, PUT/DELETE /api/admin/orders/{id}, GET /api/admin/dashboard (+finance)

## Konfigurasi
- backend/.env: DATABASE_URL, AUTO_START_LOCAL_PG, JWT_SECRET, ADMIN_USERNAME/PASSWORD (admin/admin123), MIDTRANS_*
- Dev PostgreSQL: bundle /root/pg15 + data /app/pgdata via backend/scripts/ensure_postgres.sh (self-healing saat pod restart)

## Setup ulang workspace (git clone, Sep 2026)
- Repo di-import ke /app; PostgreSQL 15 diinstal via apt lalu dibundel ke /root/pg15 oleh ensure_postgres.sh; data baru di /app/pgdata (auto-seed 7 kategori, 38 produk, user admin & owner).
- backend/.env dibuat ulang (gitignored): DATABASE_URL localhost, AUTO_START_LOCAL_PG=true, admin/admin123, owner/owner123, Midtrans kosong (simulasi).
- Health OK, frontend compiled, home + /admin tampil normal.

## Tahap 3a (SELESAI - teruji 100%): Laporan Penjualan (Owner-only)
- Halaman /admin/laporan (nav "Laporan", hanya Owner; admin diredirect ke dashboard)
- Filter periode: preset (Hari Ini, 7/30 Hari, Bulan Ini, Bulan Lalu, Tahun Ini) + input tanggal mulai/akhir (WIB), validasi start<=end
- Ringkasan: pendapatan kotor, modal (HPP), laba bersih (+margin), jumlah pesanan lunas; grafik harian pendapatan vs laba; produk terjual
- Tabel detail sortable (klik header): No. Pesanan, Tanggal, Pembeli, Pembayaran, Item, Total, Modal, Laba, Margin + baris TOTAL
- Download Excel (openpyxl: sheet Ringkasan+logo, Detail Pesanan, Produk Terjual; format Rupiah, freeze panes, autofilter, rumus total) & PDF (reportlab A4 landscape, kop logo Semoyo Joyo, footer halaman, tanda tangan owner)
- API: GET /api/admin/reports/sales, /sales/export.xlsx, /sales/export.pdf (?start=YYYY-MM-DD&end=YYYY-MM-DD); export tercatat di audit log (action=export)
- Definisi terjual = paid ATAU (COD & selesai), tidak dibatalkan, berdasarkan tanggal pesanan (konsisten dengan dashboard)
- Script contoh data: backend/scripts/seed_sample_orders.py (10 pesanan via API asli, sebagian backdated)

## Katalog Produk Asli (SELESAI)
- 58 produk asli pemilik di-seed via `backend/scripts/seed_real_products.py` (idempotent upsert by slug; `--keep-old` untuk tidak menonaktifkan dummy; `--no-verify-images` skip cek URL).
- Pemetaan ke 7 kategori existing; deskripsi B2B; harga jual acak +-8% dari acuan pasar, modal 78-82% (margin ~20%); stok 1000; min order per satuan.
- Gambar: Unsplash direct URL, tiap URL diverifikasi HTTP saat seeding; relevansi dicek visual (45 foto unik). 33 produk dummy lama dinonaktifkan (is_active=false, bisa diaktifkan lagi via Admin > Produk).
- Catatan: "Kenot" dipetakan ke Sayuran Segar (asumsi wortel impor/baby carrot) - konfirmasi pemilik.

## Backlog
- Pembelian ke supplier (PO), laporan penjualan periode, ongkir, notifikasi WA, invoice PDF, Midtrans production

## Perbaikan Build Docker Production (Sep 2026) - SELESAI
- Penyebab: `backend/requirements.txt` adalah hasil `pip freeze` environment dev (135 paket) yang memuat
  `litellm @ https://customer-assets.emergentagent.com/...` (URL internal, tidak bisa diakses saat build),
  `emergentintegrations` (index privat), `s5cmd`, `librt`, `hf-xet`, `psycopg2-binary`, pandas/numpy, dll.
  -> `pip install -r requirements.txt` exit code 1 di `python:3.11-slim`.
- Solusi: requirements.txt ditulis ulang hanya 16 pustaka runtime nyata (fastapi, starlette, uvicorn[standard],
  python-multipart, pydantic, python-dotenv, SQLAlchemy, asyncpg, greenlet, PyJWT, bcrypt, httpx, openpyxl,
  reportlab, pillow) - semua wheel siap pakai, pinned, tanpa duplikat/konflik (`pip check` bersih).
  Diverifikasi install di venv kosong Python 3.11 dengan `--no-cache-dir` -> sukses; semua modul backend ter-import.
- `requirements-dev.txt` baru (pytest, pytest-xdist) untuk dev saja.
- `backend/Dockerfile`: hapus build-essential/libpq-dev (tidak perlu), `pip install --upgrade pip`, 1 worker
  (hindari race seeding), `--proxy-headers`. `backend/.dockerignore` baru (pgdata, uploads, .env, cache, tes).
- `.env.example` di root dibuat (sebelumnya tidak ada karena ter-gitignore; `.gitignore` ditambah `!.env.example`).
- docker-compose.yml: tambah OWNER_USERNAME/OWNER_PASSWORD.
- Workspace: repo di-import ulang, PG15 di-bundle ke /root/pg15, data /app/pgdata, 58 produk asli di-seed.
