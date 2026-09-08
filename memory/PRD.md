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

## Backlog
- Pembelian ke supplier (PO), laporan penjualan periode, ongkir, notifikasi WA, invoice PDF, Midtrans production
