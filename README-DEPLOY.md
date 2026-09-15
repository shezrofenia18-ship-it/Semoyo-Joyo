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
   - `TRAVOY_API_KEY` / `TRAVOY_BASE_URL` / `TRAVOY_CALLBACK_TOKEN` (kosongkan dulu = Transfer VA mode placeholder)
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

## 5. Metode pembayaran & Travoy Pay (Transfer VA)
Metode pembayaran yang tersedia di checkout:
- **Cash (Tunai)** - pesanan langsung berstatus Lunas.
- **Bayar Nanti** - pesanan berstatus Piutang dan masuk modul Piutang (dilunasi admin via "Tandai Lunas").
- **Transfer VA (Travoy Pay)** - kerangka integrasi; aktif setelah dokumen API tersedia.

Mengaktifkan Travoy Pay nanti:
1. Lengkapi implementasi `backend/payments/travoy.py` (create_va, get_status, verify_callback, map_status) sesuai dokumen API.
2. Isi `TRAVOY_API_KEY`, `TRAVOY_BASE_URL`, `TRAVOY_CALLBACK_TOKEN` di env, redeploy backend.
3. Daftarkan URL callback di dashboard Travoy Pay: `https://APP_URL/api/payments/travoy/notification`.

## 6. Backup
Volume `pgdata` menyimpan database dan `uploads` menyimpan gambar produk yang diunggah admin. Backup rutin dengan `pg_dump` atau fitur backup Coolify.
