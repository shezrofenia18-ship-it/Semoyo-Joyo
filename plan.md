# plan.md — MBG B2B E‑Commerce + Mini ERP (Tahap 1: Customer)

## 1) Objectives
- Membangun kerangka fullstack **FastAPI + React + Tailwind + PostgreSQL** yang siap deploy di **Coolify**.
- Menyediakan alur customer end-to-end: **Beranda (produk per kategori) → Keranjang → Checkout → Pembayaran → Riwayat Pesanan**.
- Menyediakan **struktur integrasi pembayaran** (Midtrans Snap) dalam mode **sandbox/simulasi**, lengkap dengan endpoint status + webhook.
- Menyediakan **seed data** kategori & produk + **Admin CRUD** sederhana.

---

## 2) Implementation Steps

### Phase 1 — Core POC (Isolation): PostgreSQL + Checkout→Order→Payment Simulation (wajib beres sebelum lanjut)
**Tujuan:** membuktikan koneksi DB, migrasi/tables, seed minimal, dan alur inti create order + payment “pending→paid” berjalan stabil.

**User stories (POC):**
1. Sebagai developer, saya ingin backend bisa konek ke PostgreSQL dan melakukan query sederhana agar fondasi stabil.
2. Sebagai customer, saya ingin checkout menghasilkan **order_number** agar pesanan bisa dilacak.
3. Sebagai customer, saya ingin memilih metode pembayaran dan mendapatkan instruksi pembayaran.
4. Sebagai sistem, saya ingin bisa mengubah status pembayaran dari pending ke paid (simulasi) agar alur pasca-bayar teruji.
5. Sebagai developer, saya ingin endpoint healthcheck memverifikasi koneksi DB agar mudah troubleshooting.

**Langkah:**
1. Tambah `DATABASE_URL` (Postgres) di `/app/backend/.env` + konfigurasi SQLAlchemy async (asyncpg).
2. Buat modul DB: `db.py` (engine, session, Base) + model awal: users, categories, products, orders, order_items, payment_transactions.
3. Tambah script self-healing lokal: `scripts/ensure_postgres.sh` (start pg jika DATABASE_URL localhost; gunakan `/app/pgdata`).
4. Buat endpoint minimal:
   - `GET /api/health` (cek koneksi DB)
   - `GET /api/home` (kategori + produk terkelompok)
   - `POST /api/checkout` (buat user+order+items)
   - `POST /api/payments/{order_number}/create` (return instruksi pembayaran; simulasi bila tanpa key)
   - `POST /api/payments/{order_number}/simulate` (ubah payment/order jadi paid)
5. Seed minimal (2 kategori + 4 produk) jika tabel kosong.
6. Buat `scripts/test_core_flow.py` untuk menguji: health → home → checkout → create payment → simulate → status OK.
7. Fix sampai POC 100% lulus (tidak lanjut ke Phase 2 sebelum ini stabil).

---

### Phase 2 — V1 App Development (Customer UI + Admin CRUD + Payment Pages)
**Tujuan:** membangun aplikasi MVP lengkap (tanpa kompleksitas berlebih), menggunakan komponen bersih (Tailwind) dan state cart persist.

**User stories (V1):**
1. Sebagai customer, saya ingin melihat produk dikelompokkan per kategori dengan gambar agar cepat memilih.
2. Sebagai customer, saya ingin menambah produk ke keranjang dengan qty yang menghormati **min. order**.
3. Sebagai customer, saya ingin checkout dengan Nama Lengkap, Alamat, No. Telp/WA agar pesanan diproses.
4. Sebagai customer, saya ingin melihat halaman pembayaran (COD/Transfer/QRIS/E‑Wallet) beserta instruksinya.
5. Sebagai admin, saya ingin CRUD kategori & produk agar katalog bisa dikelola.
6. Sebagai customer, saya ingin melihat riwayat pesanan setelah “login ringan” (Nama + Telp) agar bisa memantau order.

**Backend (FastAPI):**
1. Rapikan struktur folder: `routers/`, `models/`, `schemas/`, `services/`, `payments/`.
2. Implement API lengkap (MVP):
   - Katalog: `GET /api/categories`, `GET /api/products`, `GET /api/products/{id}`, `GET /api/home`
   - Auth customer ringan: `POST /api/auth/customer/login`, `GET /api/auth/me` (JWT)
   - Orders: `GET /api/orders/me`, `GET /api/orders/{order_number}`
   - Payments: `create/status/simulate` + webhook `POST /api/payments/midtrans/notification` (signature verify)
   - Admin: `POST /api/admin/login` + CRUD `admin/categories`, `admin/products`, list orders + update status
3. Pastikan normalisasi username dari Nama Lengkap (lowercase, trim, replace spaces) dan unique.
4. Seed data lengkap kategori & produk (Unsplash URLs) + endpoint seed (opsional) / auto-seed saat start bila kosong.

**Frontend (React):**
1. Setup Tailwind + UI kit sederhana (shadcn-like styling atau komponen custom) konsisten Bahasa Indonesia.
2. Implement pages:
   - `/` Beranda: list kategori + produk grouped, search sederhana, add-to-cart
   - `/keranjang`: edit qty, remove, subtotal
   - `/checkout`: form customer + ringkasan + pilih metode bayar
   - `/pembayaran/:orderNumber`: instruksi per metode + tombol simulasi (sandbox) + polling status
   - `/pesanan` + `/pesanan/:orderNumber`: riwayat + detail
   - `/admin` login + `/admin/kategori` `/admin/produk` `/admin/pesanan`
3. State management: Cart Context + localStorage; token customer di localStorage.

**Testing (end-to-end 1x setelah V1):**
- Jalankan alur: beranda → tambah cart → checkout → pembayaran (simulasi) → order paid → riwayat pesanan.
- Jalankan admin CRUD: tambah kategori/produk → muncul di beranda.

---

### Phase 3 — Hardening + Deploy (Coolify) + Quality Pass
**Tujuan:** memastikan stabil, reproducible, dan siap VPS.

**User stories (hardening):**
1. Sebagai operator, saya ingin deploy via docker-compose (postgres+backend+frontend) agar mudah di Coolify.
2. Sebagai user, saya ingin UI tetap responsif di mobile agar mudah order dari lapangan.
3. Sebagai admin, saya ingin status order bisa diubah dan terlihat customer agar proses transparan.
4. Sebagai operator, saya ingin env var terpisah (dev vs prod) agar aman.
5. Sebagai sistem, saya ingin data konsisten (harga/stock/min_order) agar tidak ada order invalid.

**Langkah:**
1. Dockerization:
   - `backend/Dockerfile` (uvicorn) + `frontend/Dockerfile` (build + nginx)
   - `docker-compose.yml` dengan service `postgres` (volume), `backend`, `frontend`.
2. Dokumentasi: `README-DEPLOY.md` (Coolify steps, env vars, webhook URL).
3. Validasi & guardrails:
   - Validasi qty >= min_order, stock check (MVP: prevent negative)
   - Error states jelas di UI (empty states, loading, failure).
4. Testing komprehensif 1 putaran (core flows + admin flows + refresh page persistence).

---

## 3) Next Actions
1. Implement **Phase 1 POC**: SQLAlchemy async + models + endpoints minimal + `test_core_flow.py`.
2. Pastikan Postgres startup strategy:
   - Dev container: `ensure_postgres.sh` (localhost)
   - Coolify: gunakan service postgres di compose + env `DATABASE_URL`.
3. Setelah POC lulus, lanjut Phase 2 (backend routers + UI pages) dalam batch besar agar cepat selesai.

---

## 4) Success Criteria
- POC lulus: script `test_core_flow.py` menghasilkan order + payment simulate sukses, dan `GET /api/health` OK.
- Beranda menampilkan produk **terkelompok kategori** dengan gambar dan harga/satuan/min order.
- Cart & checkout bekerja end-to-end, menghasilkan halaman pembayaran sesuai metode.
- Mode simulasi pembayaran mengubah status order menjadi **paid** dan tampil di riwayat pesanan.
- Admin dapat CRUD kategori & produk; perubahan tampil di beranda.
- Tersedia docker-compose + instruksi deploy Coolify; app jalan setelah restart (data persist via volume/pgdata).

---
## STATUS (diperbarui setelah Phase 2)
- [x] Phase 1 POC SELESAI: PostgreSQL 15 lokal (data /app/pgdata), SQLAlchemy async + asyncpg, test_core.py lulus, scripts/ensure_postgres.sh self-healing (auto start saat backend boot).
- [x] Phase 2 SELESAI & TERUJI (testing agent 100% backend+frontend):
  - Backend: catalog, checkout (nama->username login ID), customer login Nama+Telp, orders, payments (Midtrans Core API struktur + SIMULASI saat key kosong, webhook SHA512, status polling), admin (login, dashboard, CRUD kategori/produk, upload gambar, orders + status).
  - Frontend: Beranda (grouped by kategori, search, chips), Keranjang (sheet + halaman), Checkout, Pembayaran (COD/Transfer VA/QRIS placeholder/E-Wallet + Simulasi Bayar + ganti metode), Riwayat & Detail Pesanan, Masuk, Admin (dashboard/produk/kategori/pesanan).
  - Deploy: backend/Dockerfile, frontend/Dockerfile + nginx.conf, docker-compose.yml, .env.example, README-DEPLOY.md.
- Kredensial dev: admin/admin123 (backend/.env). Mode pembayaran: simulation.
- [ ] Phase 3 (berikutnya, sesuai permintaan user): ERP mini lanjutan (stok masuk/keluar, pembelian ke supplier, laporan), ongkir, notifikasi WA, aktivasi Midtrans dengan key asli, invoice PDF.

- [x] BUGFIX (pod restart): binary PostgreSQL dibundel di /root/pg15 (persisten), ensure_postgres.sh pakai bundle tanpa apt, lifespan retry DB init. Verified via testing agent (iteration_2, 100%).
- [x] WORKSPACE BARU (git clone): PG15 diinstal ulang + bundle /root/pg15, backend/.env dibuat ulang, seed otomatis 7 kategori/38 produk.
- [x] Phase 3a SELESAI: Laporan Penjualan (Owner-only) /admin/laporan — filter periode, ringkasan (omzet/HPP/laba/pesanan lunas), tabel sortable, export Excel (.xlsx) & PDF berkop logo. routers/reports.py. Testing agent iteration_4: backend 100%, frontend lulus.
- [ ] Phase 3 sisa: PO ke supplier, ongkir, notifikasi WA, invoice PDF per pesanan, aktivasi Midtrans key asli.

- [x] BUGFIX DEPLOY (Sep 2026): requirements.txt dibersihkan (16 pustaka runtime, pinned, tanpa URL internal), Dockerfile backend dirapikan, .dockerignore + .env.example ditambahkan. Verified: install di venv kosong Python 3.11 sukses, backend + frontend berjalan normal di workspace.
