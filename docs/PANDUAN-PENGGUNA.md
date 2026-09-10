# Panduan Pengguna Lengkap
## Semoyo Joyo — B2B E-Commerce + Mini ERP

> **Versi 1.0 · Juni 2026** · Disusun sesuai antarmuka aplikasi yang sedang berjalan.
> Kotak bertanda 📷 adalah **placeholder tangkapan layar** — ganti dengan screenshot asli sebelum dibagikan.

---

## Daftar Isi

**Bagian A — Umum**
1. Pengenalan Aplikasi & Peran Pengguna

**Bagian B — Sisi Pelanggan (Toko Online)**
2. Beranda & Katalog Produk
3. Keranjang Belanja
4. Checkout & Memilih Metode Pembayaran
5. Halaman Pembayaran (Transfer/VA, QRIS, E-Wallet, COD, Bayar Nanti)
6. Riwayat Pesanan, Detail Pesanan & Struk
7. Masuk sebagai Pelanggan

**Bagian C — Panel Admin / Owner (Mini ERP)**
8. Cara Login Staf (Admin / Owner)
9. Mengenal Tata Letak Panel Admin
10. Dashboard
11. Pesanan
12. Piutang (Bayar Nanti)
13. Pengeluaran
14. Produk
15. Stok Barang
16. Kategori
17. Laporan Penjualan 🔒
18. Audit Log 🔒
19. Pengaturan 🔒 (Akun Staf, Profil Toko, Database Pelanggan, Sinkronisasi Data)

**Bagian D — Lampiran**
20. Alur Kerja Harian yang Disarankan
21. Istilah & Status
22. Pertanyaan Umum (FAQ)

---

# BAGIAN A — UMUM

## 1. Pengenalan Aplikasi & Peran Pengguna

Semoyo Joyo adalah aplikasi web untuk supplier bahan baku dapur skala B2B. Aplikasi terdiri dari dua sisi:

| Sisi | Alamat | Pengguna |
|---|---|---|
| **Toko Online (Katalog)** | `/` | Pelanggan — memesan **tanpa registrasi**, cukup nama/nama usaha + nomor WA |
| **Panel Admin (Mini ERP)** | `/admin/...` | Staf toko: **Admin** dan **Owner** |

### Perbedaan Hak Akses Staf

| Fitur | Admin | Owner 🔒 |
|---|:---:|:---:|
| Dashboard, Pesanan, Piutang, Pengeluaran, Produk, Stok, Kategori | ✅ | ✅ |
| Melihat Modal (HPP), Laba, Pengeluaran, Nilai Stok di Dashboard | ❌ | ✅ |
| Menghapus pengeluaran / menghapus produk dari stok | ❌ | ✅ |
| Laporan Penjualan, Audit Log, Pengaturan | ❌ | ✅ |

> Simbol 🔒 pada dokumen ini berarti **hanya Owner** yang dapat mengakses.

📷 **[Tangkapan layar: Beranda toko & Dashboard admin berdampingan]**

---

# BAGIAN B — SISI PELANGGAN (TOKO ONLINE)

## 2. Beranda & Katalog Produk

Alamat: `https://<domain-toko>/`

### Bagian-bagian halaman
1. **Bilah atas (Navbar)**: logo Semoyo Joyo, kotak **"Cari bahan baku... (beras, ayam, sayur)"**, tombol **Pesanan**, **Masuk**, dan **Keranjang** (biru).
2. **Hero**: judul "Pasokan bahan baku segar, harga B2B transparan", tombol **Lihat Katalog →** dan **Cek Riwayat Pesanan**, serta 3 keunggulan (Kirim Terjadwal, Auto-verifikasi, Min. Order Jelas).
3. **Chip kategori** (baris bisa digeser): *Beras & Karbohidrat, Protein Hewani, Protein Nabati, Sayuran Segar, Buah-buahan, Minyak Bumbu & Rempah, Susu & Olahan* — angka di chip = jumlah produk.
4. **Bagian per kategori**: judul kategori, deskripsi, dan grid kartu produk.

📷 **[Tangkapan layar: Beranda — navbar, hero, chip kategori]**

### Langkah: Menelusuri katalog
1. Klik **Lihat Katalog →** atau gulir ke bawah.
2. Klik **chip kategori** untuk melompat ke bagian kategori tersebut.
3. Setiap **kartu produk** menampilkan: foto, nama, harga per satuan (mis. *Rp 12.500 / kg*), min. order, dan tombol tambah ke keranjang.

📷 **[Tangkapan layar: Grid kartu produk dalam satu kategori]**

### Langkah: Mencari produk
1. Ketik kata kunci di kotak pencarian navbar, mis. `ayam`.
2. Hasil tampil sebagai daftar produk yang cocok.
3. Klik **Hapus pencarian** untuk kembali ke katalog penuh.

📷 **[Tangkapan layar: Hasil pencarian "ayam"]**

### Langkah: Menambahkan ke keranjang
1. Pada kartu produk, klik tombol tambah (ikon keranjang / **+**).
2. Jumlah otomatis mengikuti **min. order** produk (mis. 10 kg). Gunakan **+ / −** untuk mengubah jumlah.
3. Ikon keranjang di navbar dan tombol keranjang melayang di kanan bawah menampilkan jumlah item.

📷 **[Tangkapan layar: Kartu produk setelah ditambahkan, dengan pengatur jumlah]**

---

## 3. Keranjang Belanja

Alamat: `/keranjang` — dibuka dari tombol **Keranjang** di navbar atau tombol melayang kanan bawah.

### Isi halaman
- Daftar item: foto, nama, harga satuan, pengatur **jumlah (+/−)**, subtotal per item, ikon **hapus (🗑)**.
- Ringkasan: **Subtotal**, catatan ongkir (ditentukan admin), dan tombol biru **Lanjut ke Checkout**.
- Tombol kembali **Belanja Lagi / ke Beranda**.

### Langkah
1. Periksa jumlah tiap item; pastikan tidak di bawah min. order (sistem akan menolak jika kurang).
2. Hapus item yang tidak diperlukan dengan ikon 🗑.
3. Klik **Lanjut ke Checkout**.

📷 **[Tangkapan layar: Halaman Keranjang dengan 2–3 item]**

---

## 4. Checkout & Memilih Metode Pembayaran

Alamat: `/checkout`

### Formulir data pemesan
| Kolom | Wajib | Keterangan |
|---|:---:|---|
| **Nama / Nama usaha** | ✔ | Nama pribadi atau nama dapur/usaha |
| **No. Telp / WA** | ✔ | Format `08xxxxxxxxxx`; dipakai untuk melihat riwayat pesanan |
| **Alamat Pengiriman** | ✔ | Nama jalan, kecamatan, kota/kabupaten, patokan |
| **Catatan** | – | Contoh: *"Kirim pagi sebelum jam 09.00"* |

📷 **[Tangkapan layar: Formulir checkout terisi]**

### Metode pembayaran yang tersedia
| Metode | Keterangan di layar | Kapan dipakai |
|---|---|---|
| **COD** | Bayar saat barang diterima | Pembayaran tunai ke kurir |
| **Transfer Bank** | Virtual Account, verifikasi otomatis | Transfer ke nomor VA (BCA/BNI/BRI/Mandiri/Permata) |
| **QRIS** | Scan QR dari e-wallet / m-banking | Bayar scan QR |
| **E-Wallet** | GoPay / OVO / DANA / ShopeePay | Bayar via aplikasi e-wallet |
| **Bayar Nanti (Piutang)** | Pelanggan tetap: ambil barang dulu, bayar belakangan | Kasbon — hanya untuk pelanggan tetap sesuai kesepakatan |

> Saat memilih **Bayar Nanti**, muncul kotak ungu pemberitahuan bahwa pesanan dicatat sebagai **piutang (kasbon)** dan status akan berubah *Lunas* setelah admin mengonfirmasi pembayaran.

📷 **[Tangkapan layar: Pilihan metode pembayaran + kotak pemberitahuan piutang]**

### Langkah
1. Lengkapi formulir data pemesan.
2. Pilih salah satu **metode pembayaran**.
3. Periksa **ringkasan pesanan** di sisi kanan (item, subtotal, total).
4. Klik **Buat Pesanan & Bayar** (atau **Buat Pesanan (Bayar Nanti)** untuk piutang).
5. Notifikasi *"Pesanan berhasil dibuat"* muncul; nomor pesanan berawalan **SJ-**.
6. Anda diarahkan ke **Halaman Pembayaran**.

📷 **[Tangkapan layar: Notifikasi pesanan berhasil dibuat]**

---

## 5. Halaman Pembayaran

Alamat: `/pembayaran/SJ-XXXXXXXX`

### Isi halaman
- **Nomor pesanan**, total tagihan, status pembayaran, dan metode yang dipilih.
- **Instruksi pembayaran** sesuai metode:
  - *Transfer Bank*: nama bank, **nomor Virtual Account** dengan tombol **Salin**, batas waktu.
  - *QRIS*: gambar kode QR untuk di-scan.
  - *E-Wallet*: nama kanal dan tombol **Bayar dengan …** (aktif bila gateway terhubung).
  - *COD*: keterangan bayar saat barang diterima.
  - *Bayar Nanti*: keterangan piutang, menunggu konfirmasi admin.
- Tombol **Cek Status** untuk memeriksa apakah pembayaran sudah masuk.
- Kartu **Ganti metode pembayaran** — untuk berpindah metode sebelum dibayar (notifikasi *"Metode pembayaran diperbarui"*).
- Tombol **Struk / PDF**, **Belanja Lagi**, **Kembali ke Beranda**.

> **Mode Simulasi:** Bila gateway pembayaran (Midtrans) belum diaktifkan, tampil tombol **Simulasi Bayar (Sandbox)** untuk menandai pembayaran sebagai lunas — dipakai untuk uji coba. Tombol ini hilang otomatis saat gateway aktif.

📷 **[Tangkapan layar: Halaman pembayaran Transfer Bank dengan nomor VA & tombol Salin]**
📷 **[Tangkapan layar: Kartu "Ganti metode pembayaran"]**

### Langkah membayar (Transfer Bank / VA)
1. Klik **Salin** pada nomor VA.
2. Lakukan transfer melalui m-banking/ATM ke nomor VA tersebut sebesar total tagihan.
3. Kembali ke halaman dan klik **Cek Status** → jika berhasil muncul *"Pembayaran diterima"* dan status berubah **Lunas**.
4. Klik **Struk / PDF** untuk menyimpan bukti.

---

## 6. Riwayat Pesanan, Detail Pesanan & Struk

### Riwayat Pesanan — `/pesanan`
1. Klik **Pesanan** di navbar (atau **Cek Riwayat Pesanan** di beranda).
2. Jika belum "masuk", isi nama & nomor WA yang dipakai saat checkout (lihat Bab 7).
3. Daftar pesanan tampil: nomor **SJ-**, tanggal, total, **status pesanan** dan **status pembayaran**.
4. Pesanan yang belum dibayar memiliki tombol **Bayar Sekarang**.

📷 **[Tangkapan layar: Riwayat Pesanan dengan beberapa pesanan]**

### Detail Pesanan — `/pesanan/SJ-XXXXXXXX`
Klik salah satu pesanan untuk melihat: data pengiriman, daftar item, ongkir, total, status, dan tombol **Bayar** (bila belum lunas) serta **Struk**.

📷 **[Tangkapan layar: Detail pesanan]**

### Struk — `/struk/SJ-XXXXXXXX`
Struk berlogo Semoyo Joyo berisi nama pelanggan, tabel item, total, dan status pembayaran. Tersedia tombol **Cetak** dan **Unduh** (PDF), serta **Ke Riwayat Pesanan**.

📷 **[Tangkapan layar: Struk pesanan]**

---

## 7. Masuk sebagai Pelanggan

Alamat: `/masuk` — melalui tombol **Masuk** di navbar.

1. Isi **Nama / Nama usaha** dan **No. Telp / WA** (`08xxxxxxxxxx`) yang sama seperti saat checkout.
2. Klik **Masuk**.
3. Riwayat pesanan atas nomor WA tersebut akan tampil di menu **Pesanan**.

> Tidak ada password untuk pelanggan; identitas berdasarkan nomor WA.

📷 **[Tangkapan layar: Halaman Masuk pelanggan]**

---

# BAGIAN C — PANEL ADMIN / OWNER (MINI ERP)

## 8. Cara Login Staf (Admin / Owner)

Halaman login staf **disembunyikan** dari pelanggan — tidak ada tombol "Admin" di toko.

### Langkah
1. Buka halaman login dengan **salah satu** cara:
   - Ketik alamat `https://<domain-toko>/rahasia-admin`, **atau**
   - Gulir ke bawah beranda, klik **ikon gembok kecil transparan di pojok kanan bawah footer**.
2. Tampil kartu **"Masuk Admin / Owner"** berlogo Semoyo Joyo.
3. Isi **Username** dan **Password**.
   - Akun bawaan: `admin / admin123` (Admin), `owner / owner123` (Owner).
4. Klik tombol biru **Masuk**.
5. Anda diarahkan ke **Dashboard** (`/admin/dashboard`).

📷 **[Tangkapan layar: Ikon gembok di footer]**
📷 **[Tangkapan layar: Form "Masuk Admin / Owner"]**

### Keluar
Klik **Keluar** di bagian bawah menu samping (desktop) atau di menu ☰ (ponsel).

### Catatan penting
- Membuka `/admin` tanpa login → otomatis diarahkan ke beranda toko (normal).
- Admin yang membuka menu khusus Owner akan dikembalikan ke Dashboard.
- **Segera ganti password bawaan**: Owner → **Pengaturan → Akun Staf** (Bab 19.1).

---

## 9. Mengenal Tata Letak Panel Admin

- **Menu samping (kiri)** pada desktop; pada ponsel gunakan tombol **☰**.
- **Titik merah** di samping nama menu = ada data baru yang belum dilihat (mis. pesanan baru).
- Bagian bawah menu: nama akun & peran (Admin/Owner), tombol **Keluar**.

| Menu | Fungsi | Akses |
|---|---|:---:|
| Dashboard | Ringkasan KPI & keuangan | Semua |
| Pesanan | Kelola pesanan pelanggan | Semua |
| Piutang | Kasbon/bayar nanti yang belum lunas | Semua |
| Pengeluaran | Biaya operasional | Semua |
| Produk | Katalog & harga | Semua |
| Stok Barang | Stok masuk/keluar & riwayat | Semua |
| Kategori | Kelola kategori | Semua |
| Laporan | Laporan penjualan + Excel/PDF | 🔒 Owner |
| Audit Log | Jejak aktivitas staf | 🔒 Owner |
| Pengaturan | Akun, profil toko, pelanggan, sinkronisasi | 🔒 Owner |

📷 **[Tangkapan layar: Menu samping panel admin (versi Owner)]**

---

## 10. Dashboard

Alamat: `/admin/dashboard`

### Kartu KPI (semua peran)
**Pesanan Hari Ini · Total Pesanan · Menunggu Pembayaran · Pelanggan · Produk · Kategori · Stok Menipis**

### Kartu Keuangan · Laba/Rugi 🔒 (Owner)
**Pendapatan (Omzet) · Total Modal (HPP) · Laba · Margin · Pengeluaran · Nilai Stok (Modal)**

> Definisi "terjual": pesanan **Lunas**, atau **COD/Piutang yang statusnya Selesai**, dan tidak dibatalkan.
> **Laba Bersih = Omzet − HPP − Pengeluaran.**

### Panel lain
- **Status Pesanan**: jumlah per status (Baru, Diproses, Dikirim, Selesai, Dibatalkan).
- **Pesanan Terbaru**: tabel No. Pesanan, Pelanggan, Pembayaran, Status, Total, Aksi (klik untuk membuka detail di menu Pesanan).
- **Laba per Produk (Top 10)** 🔒: Produk, Terjual, Omzet, Modal, Laba, Margin.

📷 **[Tangkapan layar: Dashboard Owner lengkap]**
📷 **[Tangkapan layar: Dashboard Admin (tanpa kartu keuangan)]**

---

## 11. Pesanan

Alamat: `/admin/pesanan`

### Tampilan
- Filter **status pesanan** dan **status pembayaran**, kotak **"Cari no. pesanan / nama / telp..."**.
- Tabel: **No. Pesanan · Pelanggan · Metode · Pembayaran · Status · Total · Aksi**.

📷 **[Tangkapan layar: Daftar pesanan]**

### 11.1 Melihat detail pesanan
Klik baris pesanan → panel geser kanan menampilkan: data pelanggan (nama, telepon, alamat, catatan), kotak **Pembayaran** (metode, referensi, waktu lunas), daftar **Item**, ongkir & total, serta pilihan **Status Pesanan**.

📷 **[Tangkapan layar: Panel detail pesanan]**

### 11.2 Mengubah status pesanan
1. Di panel detail, pada bagian **Status Pesanan**, pilih: **Baru → Diproses → Dikirim → Selesai** (atau **Dibatalkan**).
2. Notifikasi *"Status diperbarui"*.
3. Catatan otomatis:
   - **Dibatalkan** → stok item dikembalikan otomatis.
   - **Selesai** pada pesanan COD/Piutang → mulai dihitung sebagai penjualan.

### 11.3 Mengedit data pesanan
1. Klik tombol **Edit** di panel detail.
2. Ubah: **Nama Pelanggan**, **No. Telp/WA**, **Alamat**, **Catatan**, **Ongkir (Rp)**, **Status Pembayaran**, **Status Pesanan**.
3. Klik **Simpan** → *"Data pesanan diperbarui"*.
   - Validasi: nama minimal 2 karakter, alamat minimal 5 karakter.

📷 **[Tangkapan layar: Form edit pesanan]**

### 11.4 Menandai pesanan lunas (pembayaran diterima manual)
1. Di kotak **Pembayaran** klik **Tandai Lunas (pembayaran diterima)** — tampil untuk pesanan yang belum lunas & tidak dibatalkan.
2. Pilih **Diterima melalui** (Tunai / Transfer Bank / QRIS / E-Wallet / Lainnya), isi catatan (mis. *"Tunai diterima di gudang"*).
3. Klik **Tandai Lunas**.

### 11.5 Menghapus pesanan
1. Klik ikon **hapus (🗑)** → dialog *"Hapus pesanan …?"*.
2. Konfirmasi **Hapus**. Stok item dikembalikan otomatis, aksi tercatat di Audit Log.

---

## 12. Piutang (Bayar Nanti)

Alamat: `/admin/piutang`

### 12.1 Pengertian
Piutang = pesanan yang barangnya diambil dulu, dibayar belakangan (kasbon). Muncul bila pelanggan memilih **Bayar Nanti** saat checkout, atau admin mengubah status pembayaran pesanan menjadi **Piutang**. Piutang **belum dihitung sebagai penjualan** sampai **Lunas**.

### 12.2 Kartu ringkasan
| Kartu | Arti |
|---|---|
| **Total Piutang Berjalan** (ungu) | Total rupiah & jumlah pesanan belum dibayar |
| **Pelanggan Berpiutang** | Jumlah pelanggan yang masih menunggak |
| **Lebih dari 14 Hari** | Pesanan menunggak > 14 hari — perlu ditagih segera (kartu memerah bila ada) |
| **Piutang Sudah Dilunasi** (hijau) | Histori total yang sudah dibayar |

📷 **[Tangkapan layar: Halaman Piutang — 4 kartu ringkasan]**

### 12.3 Panel Rekap per Pelanggan & Daftar Pesanan Piutang
- **Rekap per Pelanggan** (kiri): nama, telepon, jumlah pesanan, umur tagihan terlama, total.
- **Daftar Pesanan Piutang** (kanan): **No. Pesanan · Pelanggan · Umur · Status · Tagihan · Aksi**.
  - Warna **Umur**: abu-abu (≤7 hari), kuning (8–14 hari), **merah (>14 hari)**.
- Kotak **"Cari no. pesanan / nama / telp..."** menyaring otomatis.

📷 **[Tangkapan layar: Rekap per pelanggan & tabel piutang dengan badge umur merah]**

### 12.4 Melihat detail
Klik baris atau ikon **mata (Detail)** → panel kanan: status, data pelanggan, **metode awal**, item, ongkir, **Total Tagihan**, tombol **Tandai Lunas**.

📷 **[Tangkapan layar: Panel detail piutang]**

### 12.5 Menandai Lunas — langkah utama
1. Klik tombol hijau **✔ Tandai Lunas** di baris pesanan (atau di panel detail).
2. Dialog **"Konfirmasi Pelunasan"** menampilkan No. Pesanan, nama, dan nominal — **periksa kembali**.
3. Pilih **Diterima melalui \***: Tunai / Transfer Bank / QRIS / E-Wallet / Lainnya.
4. Isi **Catatan** (disarankan), mis. *"Transfer BCA 09/09, diterima oleh Budi"*.
5. Klik **Tandai Lunas** → notifikasi *"Piutang SJ-… ditandai LUNAS"*.

**Efek otomatis:** status pembayaran → **Lunas**; tercatat sebagai transaksi pembayaran manual + **Audit Log** (`settle`); masuk perhitungan penjualan di Dashboard & Laporan (bila status pesanan Selesai).

> ⚠️ Pelunasan tidak bisa dibatalkan dari halaman Piutang. Pastikan uang sudah benar-benar diterima.

📷 **[Tangkapan layar: Dialog Konfirmasi Pelunasan]**
📷 **[Tangkapan layar: Notifikasi "ditandai LUNAS" & tabel setelah pelunasan]**

### 12.6 Praktik baik
- Cek kartu **Lebih dari 14 Hari** setiap pagi; hubungi pelanggan dari **Rekap per Pelanggan**.
- Selalu isi catatan pelunasan (bank, tanggal, penerima).
- 🔒 Owner: lihat piutang per pelanggan & segmen di **Pengaturan → Database Pelanggan**.

---

## 13. Pengeluaran

Alamat: `/admin/pengeluaran`

### 13.1 Fungsi
Mencatat biaya operasional. Semua pengeluaran **mengurangi laba bersih** di Dashboard (Owner) dan Laporan.

### 13.2 Filter & ringkasan
- **Periode**: tombol cepat **Hari Ini · 7 Hari · Bulan Ini · Bulan Lalu · Tahun Ini** (default Bulan Ini) atau tanggal mulai/akhir manual; dropdown **kategori**; kotak **"Cari keterangan..."**.
- Kartu: **Total Pengeluaran** (biru, + jumlah transaksi), **Ongkos Angkut / Kirim**, **Per Kategori** (4 terbesar dengan persentase).
- Tabel **Daftar Pengeluaran**: **Tanggal · Keterangan · Kategori · Bayar · Nominal · Aksi** + baris **TOTAL**.

📷 **[Tangkapan layar: Halaman Pengeluaran — filter, kartu, tabel]**

### 13.3 Mencatat pengeluaran baru
1. Klik **+ Catat Pengeluaran** (kanan atas).
2. Isi formulir:

| Kolom | Wajib | Keterangan |
|---|:---:|---|
| **Tanggal** | ✔ | Default hari ini; bisa dimundurkan |
| **Kategori** | ✔ | Ongkos Angkut / Kirim · Operasional · Gaji / Upah · Sewa · Listrik & Air · Perlengkapan · Pembelian Barang · Lainnya |
| **Keterangan** | ✔ | Min. 2 karakter, mis. *"Ongkos angkut beras 25 sak dari gudang"* |
| **Nominal (Rp)** | ✔ | Angka bulat > 0; pratinjau format rupiah tampil di bawah kolom |
| **Dibayar via** | – | Tunai (default) / Transfer |
| **Referensi** | – | No. nota / nama produk / supplier |
| **Catatan** | – | Keterangan tambahan |

3. Klik **Simpan** → *"Pengeluaran dicatat"*.

📷 **[Tangkapan layar: Form Catat Pengeluaran]**

### 13.4 Mengedit
Klik ikon **pensil** → ubah → **Simpan** → *"Pengeluaran diperbarui"*.

### 13.5 Menghapus 🔒 (Owner)
Klik ikon **tempat sampah** → dialog *"Hapus pengeluaran ini?"* → **Hapus**. Laba bersih dihitung ulang.

📷 **[Tangkapan layar: Dialog konfirmasi hapus pengeluaran]**

### 13.6 Pengeluaran otomatis dari Stok Masuk
Saat **Stok Barang → Tambah**, isi kolom opsional **"Biaya angkut / ongkos"** → otomatis tercatat di Pengeluaran (kategori Ongkos Angkut / Kirim) dengan tanda *"otomatis dari stok masuk"*. Jangan dicatat dua kali.

---

## 14. Produk

Alamat: `/admin/produk`

### Tampilan
- Kotak **"Cari produk..."**, filter **Semua kategori**, tombol **+ Tambah Produk**.
- Tabel: **Produk · Kategori · Harga Beli · Harga Jual · Laba / Unit · Min. Order · Stok · Status (Aktif/Nonaktif) · Aksi**.

📷 **[Tangkapan layar: Daftar produk]**

### 14.1 Menambah produk
1. Klik **+ Tambah Produk**.
2. Isi formulir:

| Kolom | Wajib | Keterangan |
|---|:---:|---|
| **Nama Produk** | ✔ | |
| **Kategori** | ✔ | Pilih dari dropdown |
| **Deskripsi Produk** | – | Dibaca pembeli di beranda: kualitas, asal, kemasan, cara simpan |
| **Harga Jual (Rp)** | ✔ | Harga ke pelanggan |
| **Harga Beli / Modal (Rp)** | – | Untuk hitung laba & HPP (default 80% harga jual bila kosong) |
| **Satuan** | ✔ | kg, pack, sak, karton, liter, ikat, dll. |
| **Min. Order** | – | Jumlah minimal per pesanan |
| **Stok** | – | Stok awal |
| **Gambar Produk** | – | Unggah file (→ *"Gambar diunggah"*) atau tempel **URL gambar** |
| **Aktif** (switch) | – | Nonaktif = disembunyikan dari katalog |

3. Klik **Simpan** → *"Produk ditambahkan"*.

📷 **[Tangkapan layar: Form Tambah Produk]**

### 14.2 Mengedit / menonaktifkan
Klik ikon **pensil** → ubah data (mis. matikan switch **Aktif** untuk menyembunyikan dari katalog) → **Simpan** → *"Produk diperbarui"*. Perubahan stok dari form ini otomatis tercatat di riwayat stok.

### 14.3 Menghapus
Ikon **tempat sampah** → *"Hapus produk?"* → **Hapus** → *"Produk dihapus"*.

---

## 15. Stok Barang

Alamat: `/admin/stok`

### Ringkasan
Kartu: **Total Produk · Total Unit Tersedia · Menipis / Habis · Nilai Stok (Modal)** 🔒.
Filter status: **Aman · Menipis · Habis**; kotak **"Cari barang..."**.

### Tabel
**Barang · Kategori · Sisa Stok · Min. Order · Status · Nilai Stok · Mutasi Terakhir · Aksi**

📷 **[Tangkapan layar: Halaman Stok Barang]**

### 15.1 Tambah stok (barang masuk)
1. Klik **+ Tambah** (hijau) pada baris barang.
2. Isi **Jumlah**, **Catatan** (opsional).
3. Opsional: **Biaya angkut / ongkos** — Nominal (Rp) + keterangan → otomatis masuk Pengeluaran.
4. **Simpan**. Riwayat stok bertambah dengan sumber *manual/stock_in*.

📷 **[Tangkapan layar: Dialog Tambah Stok dengan kolom biaya angkut]**

### 15.2 Kurangi stok (rusak/hilang/dipakai)
Klik **− Kurangi** (kuning) → isi jumlah & catatan → **Simpan**.

### 15.3 Edit / set stok manual
Klik ikon **pensil** → masukkan angka stok akhir → **Simpan** (sistem mencatat selisihnya).

### 15.4 Riwayat mutasi
Klik ikon **jam (Riwayat)** → daftar pergerakan: tanggal, jenis (masuk/keluar), jumlah, stok sebelum/sesudah, sumber (checkout, batal, hapus pesanan, manual), catatan, petugas.

📷 **[Tangkapan layar: Riwayat mutasi stok satu produk]**

### 15.5 Hapus produk dari stok 🔒 (Owner)
Ikon **tempat sampah** → *"Hapus produk dari stok?"* → **Hapus** → *"Produk dihapus dari stok & katalog"*.

> Stok berkurang **otomatis** saat pelanggan checkout dan **kembali otomatis** saat pesanan dibatalkan/dihapus.

---

## 16. Kategori

Alamat: `/admin/kategori`

- Tabel: **Kategori · Deskripsi · Produk (jumlah) · Urutan · Status · Aksi**.
- **+ Tambah Kategori**: **Nama Kategori\***, **Deskripsi**, **URL Gambar** (`https://...`), **Urutan** (posisi di beranda), status aktif → **Simpan** → *"Kategori ditambahkan"*.
- **Edit** (pensil) → *"Kategori diperbarui"*; **Hapus** (tempat sampah) → *"Hapus kategori?"* → *"Kategori dihapus"* (pastikan tidak ada produk di dalamnya).

📷 **[Tangkapan layar: Daftar kategori & form tambah kategori]**

---

## 17. Laporan Penjualan 🔒

Alamat: `/admin/laporan` — hanya Owner.

### 17.1 Memilih periode
- Tombol cepat: **Hari Ini · 7 Hari Terakhir · 30 Hari Terakhir · Bulan Ini · Bulan Lalu · Tahun Ini**.
- Atau isi **Tanggal Mulai** & **Tanggal Akhir** (WIB). Jika terbalik muncul *"Rentang tanggal tidak valid"*.

📷 **[Tangkapan layar: Filter periode laporan]**

### 17.2 Ringkasan
**Total Pendapatan Kotor · Total Modal (HPP) · Pengeluaran Periode · Total Penjualan/Laba (+margin) · Pesanan Terjual**

### 17.3 Grafik & tabel
- **Tren Harian · Pendapatan vs Laba** (grafik).
- **Produk Terjual pada Periode Ini**: No, Produk, Qty, Omzet, Modal, Laba.
- **Detail Pesanan**: **No. Pesanan · Tanggal · Nama Pembeli · Pembayaran · Item · Total · Modal (HPP) · Laba · Margin** + baris TOTAL. Klik judul kolom untuk **mengurutkan**.

📷 **[Tangkapan layar: Ringkasan, grafik, tabel detail laporan]**

### 17.4 Mengunduh laporan
1. Klik **Download Excel** (sheet Ringkasan berlogo, Detail Pesanan, Produk Terjual; format Rupiah, filter otomatis, rumus total) atau **Download PDF** (A4 landscape, kop logo, tanda tangan owner).
2. Notifikasi *"Excel/PDF berhasil diunduh"*. Setiap unduhan tercatat di Audit Log (*Unduh Laporan*).

📷 **[Tangkapan layar: Tombol Download Excel/PDF & contoh file PDF]**

---

## 18. Audit Log 🔒

Alamat: `/admin/audit-log` — hanya Owner.

- Tabel: **Waktu · Akun · Aksi · Objek · Keterangan**.
- Filter jenis aksi: **Masuk · Tambah · Ubah · Hapus · Status · Stok · Unduh Laporan** (juga *settle* & *sync*).
- Kotak **"Cari aktivitas / nama produk / no. pesanan..."**, tombol **Muat ulang**.

Gunakan untuk menelusuri siapa mengubah apa dan kapan (mis. siapa menandai piutang lunas, siapa menghapus produk).

📷 **[Tangkapan layar: Halaman Audit Log]**

---

## 19. Pengaturan 🔒

Alamat: `/admin/pengaturan` — hanya Owner. Terdiri dari 4 tab.

### 19.1 Tab **Akun Staf**
- Kartu **Akun Admin & Owner**: tabel **Akun · Username (ID Login) · Role · Aksi**.
- **Ubah ID / Password**: isi **Nama tampilan**, **Username (ID login)**, **Password baru**, lalu **Konfirmasi password Owner** (wajib) → **Simpan**.
- **+ Tambah Admin**: **Nama\***, **Username\***, **Password\***, **Konfirmasi\*** (password Owner) → **Simpan**.
- **Hapus akun admin**: ikon tempat sampah → konfirmasi.

> Ini tempat mengganti password bawaan `admin123` / `owner123`.

📷 **[Tangkapan layar: Tab Akun Staf & dialog Ubah Kredensial]**

### 19.2 Tab **Profil Toko**
- **Identitas & Kontak Toko**: nama, **Deskripsi Singkat**, telepon/WA, email, **Alamat Lengkap** — tampil di footer toko & struk.
- **Rekening Pembayaran (internal)**: **Bank**, **No. Rekening**, **Atas Nama** — catatan internal untuk staf.
- Klik **Simpan**.

📷 **[Tangkapan layar: Tab Profil Toko]**

### 19.3 Tab **Database Pelanggan**
- Kartu: **Total Pelanggan · Pelanggan Tetap (≥3 pesanan) · Baru Bulan Ini · Rata-rata belanja**.
- **Daftar Pelanggan**: **Pelanggan · Pesanan · Total Belanja · Piutang · Transaksi Terakhir · Segmen** (*Pelanggan Tetap / Aktif / Baru / Pasif*).
- Berguna untuk menentukan siapa yang boleh memakai **Bayar Nanti**.

📷 **[Tangkapan layar: Tab Database Pelanggan]**

### 19.4 Tab **Sinkronisasi Data**
- Kartu **Angka Tersinkron (sumber tunggal)**: Omzet, Modal (HPP), Laba Kotor, Laba Bersih, Nilai Stok — angka final yang dipakai Dashboard & Laporan.
- Tombol **Jalankan Sinkronisasi** → dialog *"Jalankan sinkronisasi data?"* → **Ya**.
- **Hasil Pemeriksaan**: daftar perbaikan otomatis (subtotal item, total pesanan, waktu lunas, snapshot HPP, status COD/piutang) dan **anomali stok** (hanya dilaporkan, tidak diubah).
- Hasil terakhir tersimpan di Audit Log (`sync`).

Jalankan bila angka Dashboard/Laporan terasa tidak konsisten.

📷 **[Tangkapan layar: Tab Sinkronisasi Data & hasil pemeriksaan]**

---

# BAGIAN D — LAMPIRAN

## 20. Alur Kerja Harian yang Disarankan

| Waktu | Aktivitas | Menu |
|---|---|---|
| Pagi | Cek pesanan baru, ubah status **Diproses → Dikirim → Selesai** | Pesanan |
| Pagi | Cek piutang **> 14 hari**, hubungi pelanggan | Piutang |
| Barang datang | **Tambah** stok + isi biaya angkut | Stok Barang |
| Ada biaya | **Catat Pengeluaran** (listrik, gaji, dll.) | Pengeluaran |
| Pelanggan bayar kasbon | **Tandai Lunas** + catatan | Piutang |
| Harga berubah | Ubah **Harga Jual / Harga Beli** | Produk |
| Akhir hari / bulan 🔒 | Lihat laporan, **Download Excel/PDF** | Laporan |
| Berkala 🔒 | Cek **Audit Log**, jalankan **Sinkronisasi Data** | Audit Log, Pengaturan |

## 21. Istilah & Status

**Status Pesanan:** Baru → Diproses → Dikirim → Selesai · Dibatalkan
**Status Pembayaran:** Menunggu Pembayaran · Lunas · Gagal · Kedaluwarsa · Piutang
**Metode Pembayaran:** COD (Bayar di Tempat) · Transfer Bank · QRIS · E-Wallet · Bayar Nanti (Piutang)
**HPP / Modal:** harga beli × jumlah terjual. **Laba Kotor:** Omzet − HPP. **Laba Bersih:** Laba Kotor − Pengeluaran.
**Terjual:** pesanan Lunas, atau COD/Piutang yang **Selesai**, dan tidak dibatalkan.
**Nomor pesanan:** berawalan **SJ-**.

## 22. Pertanyaan Umum (FAQ)

**Pesanan piutang tidak masuk omzet?** — Harus **Tandai Lunas** *dan* status pesanan **Selesai**.

**Tidak ada tombol Hapus di Pengeluaran/Stok?** — Hanya **Owner** yang bisa menghapus.

**Salah menekan Tandai Lunas?** — Owner memperbaiki via **Pesanan → Edit → Status Pembayaran**; tercatat di Audit Log.

**Login staf gagal?** — Pastikan di `/rahasia-admin` (bukan `/masuk`). Bila Owner sudah mengganti kredensial, gunakan yang baru.

**Produk tidak tampil di beranda?** — Cek switch **Aktif** di Produk dan pastikan kategorinya aktif.

**Tombol "Simulasi Bayar" muncul di halaman pembayaran?** — Gateway Midtrans belum diisi; aplikasi berjalan **mode simulasi**. Isi kunci Midtrans di server untuk pembayaran nyata.

**Angka Dashboard terasa tidak sinkron?** — Owner → **Pengaturan → Sinkronisasi Data → Jalankan Sinkronisasi**.

---

*© Semoyo Joyo — Solusi Belanja Terpercaya. Dokumen internal untuk staf.*
