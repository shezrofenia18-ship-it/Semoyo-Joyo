# PRD - Supplier MBG B2B E-Commerce + Mini ERP (Tahap 1)

## Ringkasan
Web app B2B untuk supplier bahan baku Dapur MBG. Stack: FastAPI + SQLAlchemy async + PostgreSQL 15, React + Tailwind + shadcn/ui. Bahasa Indonesia. Deploy via Coolify (docker-compose).

## Fitur Tahap 1 (SELESAI)
- Skema PostgreSQL: users, categories, products, orders, order_items, payment_transactions
- Beranda: produk (gambar, harga/satuan, min order) dikelompokkan per kategori; search; chip kategori
- Keranjang (sheet + halaman, localStorage, hormati min order) & Checkout (Nama Lengkap -> ID login, Telp/WA, Alamat, Catatan)
- Pembayaran: COD, Transfer Bank VA (Midtrans Core API struktur, mode SIMULASI jika key kosong), QRIS (placeholder statis), E-Wallet; polling status; Simulasi Bayar (sandbox); ganti metode; webhook Midtrans (SHA512)
- Riwayat & detail pesanan; login ringan Nama + Telp
- Admin (Mini ERP): login, dashboard KPI, CRUD kategori & produk (+upload gambar), daftar pesanan + ubah status
- Seed: 7 kategori, 38 produk

## Konfigurasi
- backend/.env: DATABASE_URL, AUTO_START_LOCAL_PG, JWT_SECRET, ADMIN_USERNAME/PASSWORD, MIDTRANS_*
- Dev PostgreSQL: /app/pgdata, dijalankan otomatis oleh scripts/ensure_postgres.sh saat backend start
- Deploy: docker-compose.yml (postgres+backend+frontend), README-DEPLOY.md

## Backlog (Tahap berikutnya)
- Stok masuk/keluar & pembelian ke supplier, laporan penjualan, ongkir, notifikasi WA, invoice PDF, aktivasi Midtrans production
