# Panduan Pengguna — Semoyo Joyo (B2B E-Commerce + Mini ERP)

> Draf v1.0 · Disesuaikan dengan antarmuka aplikasi saat ini.
> Berlaku untuk **Admin** dan **Owner**. Bagian yang hanya bisa diakses Owner ditandai 🔒.

---

## Daftar Isi
1. [Pengenalan & Peran Pengguna](#1-pengenalan--peran-pengguna)
2. [Cara Login Staf (Admin / Owner)](#2-cara-login-staf-admin--owner)
3. [Mengenal Menu Panel Admin](#3-mengenal-menu-panel-admin)
4. [Modul Piutang (Bayar Nanti)](#4-modul-piutang-bayar-nanti)
5. [Modul Pengeluaran](#5-modul-pengeluaran)
6. [Ringkas: Alur Harian yang Disarankan](#6-ringkas-alur-harian-yang-disarankan)
7. [Pertanyaan Umum (FAQ)](#7-pertanyaan-umum-faq)

---

## 1. Pengenalan & Peran Pengguna

Aplikasi ini memiliki dua sisi:

| Sisi | Alamat | Siapa yang memakai |
|---|---|---|
| **Toko (Katalog)** | `/` (beranda) | Pelanggan — pesan tanpa registrasi, cukup nama/nama usaha + nomor WA |
| **Panel Admin (Mini ERP)** | `/admin/...` | Staf toko (Admin & Owner) |

Perbedaan hak akses:

| Fitur | Admin | Owner 🔒 |
|---|:---:|:---:|
| Dashboard, Pesanan, Piutang, Pengeluaran, Produk, Stok, Kategori | ✅ | ✅ |
| Melihat modal (HPP), laba, dan total pengeluaran di Dashboard | ❌ | ✅ |
| Menghapus pengeluaran | ❌ | ✅ |
| Laporan Penjualan, Audit Log, Pengaturan | ❌ | ✅ |

---

## 2. Cara Login Staf (Admin / Owner)

Halaman login staf **sengaja disembunyikan** dari pelanggan (tidak ada tombol "Admin" di menu toko).

### Langkah-langkah
1. Buka halaman login dengan **salah satu** cara:
   - Ketik alamat langsung: `https://<domain-toko>/rahasia-admin`, **atau**
   - Gulir ke paling bawah beranda toko, lalu klik **ikon gembok kecil (transparan) di pojok kanan bawah footer**.
2. Akan muncul kartu **"Masuk Admin / Owner"** dengan logo Semoyo Joyo.
3. Isi kolom **Username** dan **Password**.
   - Akun bawaan: `admin / admin123` (Admin) dan `owner / owner123` (Owner).
   - *Segera ganti password bawaan setelah login pertama (lihat Tips).*
4. Klik tombol biru **Masuk**.
5. Setelah berhasil, Anda diarahkan ke **Dashboard** (`/admin/dashboard`).

### Keluar (logout)
Klik nama pengguna / tombol **Keluar** di bagian atas panel admin (pojok kanan atas pada desktop, atau menu ☰ pada ponsel).

### Tips & Catatan
- Jika Anda membuka `/admin` saja tanpa login, sistem otomatis mengarahkan ke beranda toko — ini normal.
- Admin yang mencoba membuka menu khusus Owner (Laporan, Audit Log, Pengaturan) akan dikembalikan ke Dashboard.
- 🔒 **Ganti password:** Owner → menu **Pengaturan** → tab **Akun Staf** → ubah username/password Admin atau Owner (wajib konfirmasi password Owner).
- Sesi login tersimpan di browser. Bila muncul pesan "sesi berakhir", cukup login ulang.

---

## 3. Mengenal Menu Panel Admin

Menu berada di **sisi kiri** (desktop) atau di **tombol ☰** (ponsel):

| Menu | Fungsi singkat |
|---|---|
| **Dashboard** | KPI: pesanan hari ini, omzet, stok menipis; (Owner) HPP, laba kotor/bersih, pengeluaran |
| **Pesanan** | Daftar pesanan pelanggan, ubah status, edit, tandai lunas |
| **Piutang** | Rekap pesanan "Bayar Nanti"/kasbon yang belum dibayar |
| **Pengeluaran** | Catat biaya operasional (angkut, listrik, gaji, dll.) |
| **Produk** | Tambah/edit produk, harga jual, harga beli (modal), gambar |
| **Stok Barang** | Tambah/kurangi/set stok, riwayat pergerakan stok |
| **Kategori** | Kelola kategori katalog |
| **Laporan** 🔒 | Laporan penjualan per periode + unduh Excel/PDF |
| **Audit Log** 🔒 | Jejak semua aksi staf |
| **Pengaturan** 🔒 | Akun staf, profil toko, database pelanggan, sinkronisasi data |

Titik merah kecil di samping menu menandakan ada data baru yang belum dilihat (misal pesanan baru).

---

## 4. Modul Piutang (Bayar Nanti)

### 4.1 Apa itu Piutang di aplikasi ini?
Piutang = pesanan di mana pelanggan **mengambil barang dulu dan membayar belakangan** (kasbon). Pesanan seperti ini muncul jika:
- Pelanggan memilih metode **"Bayar Nanti (Piutang)"** saat checkout di toko, **atau**
- Admin mengubah status pembayaran sebuah pesanan menjadi **Piutang** melalui menu Pesanan → Edit.

Piutang **belum dihitung sebagai penjualan** sampai ditandai **Lunas**. Nilai piutang terlihat terpisah di Dashboard dan Laporan.

### 4.2 Membuka Halaman Piutang
1. Login sebagai Admin/Owner.
2. Klik menu **Piutang** (ikon tangan memegang koin). Alamat: `/admin/piutang`.

### 4.3 Membaca Halaman Piutang
Bagian atas menampilkan **4 kartu ringkasan**:

| Kartu | Arti |
|---|---|
| **Total Piutang Berjalan** (biru-ungu) | Jumlah rupiah semua pesanan yang belum dibayar + jumlah pesanannya |
| **Pelanggan Berpiutang** | Berapa pelanggan yang masih punya tagihan |
| **Lebih dari 14 Hari** | Jumlah pesanan yang sudah menunggak > 14 hari — *perlu ditagih segera* (kartu memerah bila ada) |
| **Piutang Sudah Dilunasi** (hijau) | Total histori piutang yang sudah dibayar |

Di bawahnya ada dua panel:
- **Rekap per Pelanggan** (kiri): nama, nomor telepon, jumlah pesanan, umur tagihan terlama, dan total tagihan per pelanggan. Berguna untuk menagih sekaligus.
- **Daftar Pesanan Piutang** (kanan): tabel per pesanan dengan kolom **No. Pesanan, Pelanggan, Umur, Status, Tagihan, Aksi**.
  - Kolom **Umur** berwarna: abu-abu (≤ 7 hari), kuning (8–14 hari), **merah (> 14 hari)**.

### 4.4 Mencari Piutang Tertentu
Ketik di kotak **"Cari no. pesanan / nama / telp..."** di kanan atas tabel. Hasil tersaring otomatis (tanpa menekan Enter).

### 4.5 Melihat Detail Piutang
1. Klik **baris pesanan** atau ikon **mata (👁 Detail)** di kolom Aksi.
2. Panel geser di kanan menampilkan: status pembayaran & pesanan, data pelanggan (nama, telepon, alamat, catatan), **metode awal**, daftar item beserta jumlah/satuan, ongkir (jika ada), dan **Total Tagihan**.
3. Dari panel ini Anda juga bisa langsung menekan **Tandai Lunas**.

### 4.6 Menandai Piutang Lunas (Pembayaran Diterima) — Langkah Utama
Lakukan ini **setelah uang benar-benar diterima** dari pelanggan.

1. Di tabel, klik tombol hijau **✔ Tandai Lunas** pada baris pesanan (atau dari panel detail).
2. Muncul dialog **"Konfirmasi Pelunasan"** yang menampilkan No. Pesanan, nama pelanggan, dan nominal tagihan — **cek kembali angkanya**.
3. Pilih **Diterima melalui \*** (wajib): `Tunai`, `Transfer Bank`, `QRIS`, `E-Wallet`, atau `Lainnya`.
4. Isi **Catatan** (opsional, tapi disarankan), contoh: *"Transfer BCA 09/09, diterima oleh Budi"*.
5. Klik **Tandai Lunas**.
6. Notifikasi hijau muncul: *"Piutang SJ-XXXX ditandai LUNAS"*. Pesanan hilang dari daftar berjalan dan masuk ke **Piutang Sudah Dilunasi**.

**Yang terjadi otomatis setelah lunas:**
- Status pembayaran pesanan berubah menjadi **Lunas**.
- Tercatat sebagai transaksi pembayaran manual dan masuk **Audit Log** (aksi `settle`).
- Pesanan mulai dihitung dalam omzet/laba di **Dashboard** dan **Laporan** (bila status pesanan sudah *Selesai*).

> ⚠️ Pelunasan **tidak bisa dibatalkan** dari halaman Piutang. Pastikan pembayaran sudah benar-benar diterima sebelum menekan Tandai Lunas.

### 4.7 Cara Lain: Tandai Lunas dari Menu Pesanan
Buka **Pesanan** → klik pesanan → di kotak **Pembayaran** akan tampak tanda *"Piutang / kasbon - belum dibayar"* dan tombol **Tandai Lunas (pembayaran diterima)**. Prosesnya sama seperti langkah 4.6.

### 4.8 Praktik Baik Pengelolaan Piutang
- Cek kartu **Lebih dari 14 Hari** setiap pagi; hubungi pelanggan dari panel **Rekap per Pelanggan** (nomor WA tertera).
- Selalu isi **Catatan** saat pelunasan (bank, tanggal, penerima) agar mudah dicocokkan dengan mutasi rekening.
- 🔒 Owner dapat melihat total piutang per pelanggan dan segmen pelanggan di **Pengaturan → Database Pelanggan**.

---

## 5. Modul Pengeluaran

### 5.1 Fungsi
Mencatat **biaya operasional** toko (ongkos angkut, listrik, gaji, sewa, dll.). Semua pengeluaran **mengurangi laba bersih** di Dashboard (Owner) dan Laporan Penjualan:

> **Laba Bersih = Laba Kotor (Omzet − HPP) − Total Pengeluaran**

### 5.2 Membuka Halaman
Klik menu **Pengeluaran** (ikon struk). Alamat: `/admin/pengeluaran`.

### 5.3 Membaca Halaman
- **Filter Periode** (kartu atas):
  - Tombol cepat: **Hari Ini · 7 Hari · Bulan Ini · Bulan Lalu · Tahun Ini** (default: *Bulan Ini*).
  - Atau isi **tanggal mulai** dan **tanggal akhir** manual (muncul peringatan merah bila tanggal mulai > akhir).
  - Dropdown **kategori** (Semua kategori / salah satu kategori).
  - Kotak **"Cari keterangan..."**.
- **Kartu ringkasan**:
  - **Total Pengeluaran** (biru) beserta jumlah transaksi pada periode.
  - **Ongkos Angkut / Kirim** — total khusus kategori angkut.
  - **Per Kategori** — 4 kategori terbesar dengan persentase dan bar.
- **Daftar Pengeluaran**: tabel **Tanggal, Keterangan, Kategori, Bayar (Tunai/Transfer), Nominal (merah, tanda minus), Aksi** dan baris **TOTAL** di bawah.

### 5.4 Mencatat Pengeluaran Baru — Langkah Utama
1. Klik tombol biru **+ Catat Pengeluaran** di kanan atas (atau *"Catat pengeluaran pertama"* jika daftar masih kosong).
2. Isi formulir **"Catat Pengeluaran"**:

   | Kolom | Wajib | Keterangan |
   |---|:---:|---|
   | **Tanggal** | ✔ | Default hari ini; bisa dimundurkan untuk pencatatan susulan |
   | **Kategori** | ✔ | Pilih: `Ongkos Angkut / Kirim`, `Operasional`, `Gaji / Upah`, `Sewa`, `Listrik & Air`, `Perlengkapan`, `Pembelian Barang`, `Lainnya` |
   | **Keterangan** | ✔ | Minimal 2 karakter. Contoh: *"Ongkos angkut beras 25 sak dari gudang"* |
   | **Nominal (Rp)** | ✔ | Angka bulat > 0. Di bawah kolom tampil format rupiah untuk pengecekan |
   | **Dibayar via** | – | `Tunai` (default) atau `Transfer` |
   | **Referensi** | – | No. nota / nama produk / supplier |
   | **Catatan** | – | Keterangan tambahan |

3. Klik **Simpan**.
4. Notifikasi *"Pengeluaran dicatat"* muncul; data langsung tampil di tabel dan ringkasan diperbarui.

> Jika kolom wajib kosong, sistem menampilkan pesan merah seperti *"Keterangan wajib diisi"* atau *"Nominal harus lebih dari 0"* — lengkapi lalu simpan kembali.

### 5.5 Mengubah (Edit) Pengeluaran
1. Klik ikon **pensil (✎)** di kolom Aksi pada baris yang dimaksud.
2. Formulir **"Edit Pengeluaran"** terbuka dengan data terisi. Ubah yang perlu.
3. Klik **Simpan** → notifikasi *"Pengeluaran diperbarui"*.

### 5.6 Menghapus Pengeluaran 🔒 (Owner saja)
1. Login sebagai **Owner** (Admin tidak melihat ikon hapus).
2. Klik ikon **tempat sampah (🗑)** pada baris.
3. Baca dialog *"Hapus pengeluaran ini?"* yang menampilkan keterangan & nominal.
4. Klik **Hapus** untuk konfirmasi (permanen) atau **Batal**.
5. Laba bersih otomatis dihitung ulang.

### 5.7 Pengeluaran Otomatis dari Stok Masuk
Saat menambah stok di menu **Stok Barang → Tambah**, ada kolom opsional **"Biaya angkut / ongkos"** (nominal + keterangan). Jika diisi:
- Biaya tersebut **otomatis tercatat** di Pengeluaran dengan kategori *Ongkos Angkut / Kirim*.
- Di tabel Pengeluaran baris ini ditandai *"otomatis dari stok masuk"*.
- Tidak perlu mencatat ulang secara manual (hindari dobel).

### 5.8 Melihat Dampaknya
- 🔒 **Dashboard (Owner)**: kartu Pengeluaran & Laba Bersih.
- 🔒 **Laporan** → pilih periode → ringkasan menampilkan pendapatan, HPP, **pengeluaran**, laba bersih; ikut terbawa pada unduhan **Excel** dan **PDF**.

---

## 6. Ringkas: Alur Harian yang Disarankan

| Waktu | Aktivitas | Menu |
|---|---|---|
| Pagi | Cek pesanan baru & ubah status (Diproses → Dikirim → Selesai) | Pesanan |
| Pagi | Cek piutang > 14 hari, hubungi pelanggan | Piutang → kartu *Lebih dari 14 Hari* |
| Saat barang datang | Tambah stok + isi biaya angkut | Stok Barang → Tambah |
| Saat ada biaya | Catat pengeluaran (listrik, gaji, dll.) | Pengeluaran → + Catat Pengeluaran |
| Saat pelanggan bayar kasbon | Tandai Lunas + isi catatan | Piutang → Tandai Lunas |
| Akhir hari / bulan 🔒 | Lihat laporan & unduh Excel/PDF | Laporan |

---

## 7. Pertanyaan Umum (FAQ)

**Pesanan piutang tidak muncul di omzet Dashboard/Laporan?**
Piutang baru dihitung sebagai penjualan setelah **Tandai Lunas** *dan* status pesanan **Selesai**. Pastikan keduanya terpenuhi.

**Saya tidak menemukan tombol Hapus di Pengeluaran.**
Hapus hanya untuk **Owner**. Admin hanya bisa menambah dan mengedit.

**Salah menekan Tandai Lunas, bagaimana?**
Tidak ada tombol "batalkan pelunasan". Hubungi Owner; perbaikan dilakukan lewat **Pesanan → Edit** (ubah status pembayaran) dan akan tercatat di Audit Log.

**Login gagal padahal password benar?**
Pastikan mengetik di halaman `/rahasia-admin` (bukan `/masuk` yang khusus pelanggan). Bila Owner pernah mengganti kredensial di Pengaturan, gunakan kredensial baru tersebut.

**Angka di Dashboard terasa tidak sinkron?**
🔒 Owner → **Pengaturan → Sinkronisasi Data** → jalankan sinkronisasi untuk menghitung ulang subtotal, total, dan snapshot HPP. Hasilnya tercatat di Audit Log.

---

*Dokumen ini adalah draf. Tangkapan layar dapat ditambahkan pada setiap langkah sebelum dibagikan ke staf.*
