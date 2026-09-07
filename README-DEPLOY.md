# Panduan Deploy ke Coolify (VPS Ubuntu)

Aplikasi terdiri dari 3 service: **PostgreSQL 15**, **Backend FastAPI** (port 8001), **Frontend React + nginx** (port 80, proxy `/api` ke backend).

## 1. Siapkan repository
Push seluruh folder proyek (`backend/`, `frontend/`, `docker-compose.yml`, `.env.example`) ke GitHub/GitLab.

## 2. Buat resource di Coolify
1. **Project → New Resource → Docker Compose** (pilih repo & branch).
2. Coolify akan membaca `docker-compose.yml` di root.
3. Pada tab **Environment Variables**, isi variabel dari `.env.example`:
   - `POSTGRES_PASSWORD`, `JWT_SECRET`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`
   - `APP_URL` = domain publik frontend, mis. `https://toko.domain.com`
   - `CORS_ORIGINS` = domain yang sama
   - `MIDTRANS_SERVER_KEY` / `MIDTRANS_CLIENT_KEY` (kosongkan dulu = mode simulasi)
4. Set domain pada service **frontend** (port 80). Backend tidak perlu domain publik karena diakses via proxy `/api`.
5. Deploy.

## 3. Alternatif: deploy terpisah (tanpa compose)
- **PostgreSQL**: Coolify → New Resource → Database → PostgreSQL 15. Catat internal URL.
- **Backend**: New Resource → Dockerfile (`backend/Dockerfile`), port 8001, env `DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db`, `AUTO_START_LOCAL_PG=false`.
- **Frontend**: New Resource → Dockerfile (`frontend/Dockerfile`), build arg `REACT_APP_BACKEND_URL=https://api.domain.com`, dan ubah `frontend/nginx.conf` `proxy_pass` ke URL backend (atau hapus blok `/api/` jika frontend memanggil backend langsung via domain).

## 4. Setelah deploy
- Cek `https://APP_URL/api/health` → `{"status":"ok","db_connected":true}`.
- Login admin di `https://APP_URL/admin` dengan `ADMIN_USERNAME` / `ADMIN_PASSWORD`.
- Seed data (7 kategori, 38 produk) otomatis dimasukkan saat database masih kosong.

## 5. Mengaktifkan Midtrans (auto-cek pembayaran)
1. Daftar di https://dashboard.midtrans.com → Settings → Access Keys.
2. Isi `MIDTRANS_SERVER_KEY` dan `MIDTRANS_CLIENT_KEY` di env, redeploy backend.
3. Di dashboard Midtrans → Settings → Configuration → **Payment Notification URL**:
   `https://APP_URL/api/payments/midtrans/notification`
4. Set `MIDTRANS_IS_PRODUCTION=true` saat siap produksi.

Saat key kosong, sistem berjalan dalam **mode simulasi**: nomor VA/e-wallet dibuat lokal dan tersedia tombol *Simulasi Bayar* di halaman pembayaran (otomatis nonaktif saat key diisi).

## 6. Backup
Volume `pgdata` menyimpan database dan `uploads` menyimpan gambar produk yang diunggah admin. Backup rutin dengan `pg_dump` atau fitur backup Coolify.
