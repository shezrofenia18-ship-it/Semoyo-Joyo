# Rencana: Tarik Repo Semoyo-Joyo ke Workspace

## Tujuan
Mengimpor repo `shezrofenia18-ship-it/Semoyo-Joyo` (branch `main`, commit terbaru "Update docker-compose.yml") ke workspace ini sehingga aplikasi **Semoyo Joyo B2B E-Commerce + Mini ERP** berjalan kembali di preview tanpa perubahan fungsi.

## Yang Akan Dilakukan
1. Mengganti isi workspace saat ini (template kosong) dengan seluruh isi repo: backend, frontend, memory, tests, dokumen deploy.
2. Menyiapkan PostgreSQL 15 lokal di dalam pod (repo memakai PostgreSQL, bukan MongoDB), data disimpan di `/app/pgdata` dan otomatis hidup saat backend start (skrip `ensure_postgres.sh` yang sudah ada di repo).
3. Membuat ulang `backend/.env` (file ini tidak ikut di repo karena gitignored) dengan nilai:
   - Koneksi database lokal, `AUTO_START_LOCAL_PG=true`
   - Akun staf: **admin / admin123** dan **owner / owner123**
   - Midtrans dikosongkan → pembayaran berjalan **MODE SIMULASI**
4. Menginstal dependensi backend (Python) dan frontend (yarn), lalu menjalankan ulang layanan.
5. Menjalankan seed: 7 kategori, akun admin & owner, dan **58 produk asli** (`seed_real_products.py`), sehingga katalog langsung terisi seperti kondisi terakhir.
6. Verifikasi: beranda katalog, checkout, login `/rahasia-admin`, dashboard, stok, piutang, pengeluaran, laporan owner.

## Yang TIDAK Dilakukan
- Tidak ada perubahan kode, fitur, atau desain — murni impor dan menjalankan.
- Tidak mengisi kunci Midtrans production.
- Data pesanan/transaksi lama dari deployment sebelumnya **tidak** ikut (repo hanya berisi kode; database dibuat baru).

## Asumsi (bisa dikoreksi)
- Tetap memakai **PostgreSQL** sesuai kode repo, tidak dimigrasi ke MongoDB.
- Kredensial staf default admin/admin123 & owner/owner123 (bisa diubah Owner dari menu Pengaturan setelah login).
- Riwayat git repo dipertahankan agar bisa push kembali ke GitHub yang sama.
- Contoh pesanan dummy (`seed_sample_orders.py`) **tidak** dijalankan, agar laporan keuangan bersih.
