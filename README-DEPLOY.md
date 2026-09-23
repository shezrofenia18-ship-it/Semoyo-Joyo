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
   - `BATPAY_*` (kosongkan dulu = Bayar Online mode placeholder; lihat bagian 5)
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

## 5. Metode pembayaran & BATPay (Bayar Online)
Metode pembayaran di checkout (dropdown, tepat 3 opsi):
- **Cash (Tunai)** - pesanan berstatus **Proses** (bayar & pesanan). Admin/Owner menekan **"Selesai / Terima Uang"** di detail pesanan -> pembayaran **Lunas**, pesanan **Selesai**.
- **Bayar Nanti** - pesanan berstatus **Piutang** dan masuk modul Piutang (dilunasi admin via "Tandai Lunas").
- **Bayar Online (BATPay)** - QRIS dinamis atau Virtual Account (BCA/Mandiri/CIMB/Danamon). Pembeli memilih kanal saat checkout dan melihat
  **Biaya Layanan** per kanal (gross-up otomatis dari MDR agar dana yang cair ke toko utuh). Default global `BATPAY_FEE_PERCENT=0.7` (%) dan
  `BATPAY_FEE_FIXED=0` (Rp); bisa di-override per kanal lewat `BATPAY_QRIS_FEE_PERCENT/FIXED` dan `BATPAY_VA_FEE_PERCENT/FIXED` (kosong = pakai default).
  Rumus: `total = ceil((dasar + biaya_tetap) / (1 - persen/100))`, `biaya_layanan = total - dasar`.
  Status **Lunas** & pesanan **Selesai** otomatis saat webhook BATPay masuk.

Admin dapat mengubah metode pembayaran pesanan yang belum lunas lewat **"Ubah Metode Pembayaran"** di panel detail pesanan (biaya layanan dihitung ulang otomatis).

### Mengaktifkan BATPay
1. Buat pasangan kunci RSA-2048 (PKCS8): `bash backend/scripts/generate_batpay_keys.sh` -> unggah `public_key.pem` ke dashboard BATPay (Upload Public Key).
2. Isi env backend: `BATPAY_ENV` (`sandbox`/`production`), `BATPAY_BASE_URL` (staging: `https://sg-openapi.batbiz.id`; kosong = otomatis), `BATPAY_PARTNER_ID`, `BATPAY_CLIENT_ID`, `BATPAY_SECRET_KEY`, `BATPAY_PRIVATE_KEY` (isi PEM satu baris dengan `\n`, path file, atau base64), `BATPAY_MERCHANT_ID`, `BATPAY_CHANNEL_ID`. Redeploy backend.
   Owner dapat menekan **Uji Koneksi** di **Pengaturan -> Bayar Online** untuk memastikan token B2B berhasil diambil dari BATPay.
3. Daftarkan URL berikut di dashboard BATPay (Owner dapat melihatnya di **Pengaturan -> Bayar Online**):
   - B2B Access Token (BATPay -> partner): `https://APP_URL/api/payments/batpay/access-token/b2b`
   - Webhook / Payment Notification (QRIS `qr-mpm-notify` & VA `transfer-va/payment`): `https://APP_URL/api/payments/batpay/webhook`
4. Cek `GET /api/health` -> `payment_mode` = `batpay_sandbox` / `batpay_production`.

Referensi protokol SNAP yang dipakai (`backend/payments/batpay.py`): token B2B `POST /api/v1.0/access-token/b2b` (signature SHA256withRSA `clientKey|timestamp`),
transaksi dengan `X-SIGNATURE` HMAC_SHA512 atas `METHOD:PATH:token:sha256(body):timestamp`, QRIS `qr-mpm-generate/query/cancel`, VA `transfer-va/create-va/status/delete-va`.
Webhook memverifikasi Bearer token yang kita terbitkan + `X-SIGNATURE`; untuk uji manual gunakan `BATPAY_WEBHOOK_TOKEN` (header `X-CALLBACK-TOKEN`).

## 6. Backup
Volume `pgdata` menyimpan database dan `uploads` menyimpan gambar produk yang diunggah admin. Backup rutin dengan `pg_dump` atau fitur backup Coolify.
