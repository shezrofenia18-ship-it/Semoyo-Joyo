export const rupiah = (n) =>
  "Rp " + new Intl.NumberFormat("id-ID", { maximumFractionDigits: 0 }).format(Number(n || 0));

export const formatDate = (iso, withTime = true) => {
  if (!iso) return "-";
  const d = new Date(iso);
  return d.toLocaleString("id-ID", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    ...(withTime ? { hour: "2-digit", minute: "2-digit" } : {}),
  });
};

export const formatDateOnly = (iso) => {
  if (!iso) return "-";
  return new Date(`${String(iso).slice(0, 10)}T00:00:00`).toLocaleDateString("id-ID", { day: "2-digit", month: "short", year: "numeric" });
};

export const daysSince = (iso) => (iso ? Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 86400000)) : 0);

export const PAYMENT_METHOD_LABEL = {
  cod: "COD (Bayar di Tempat)",
  bank_transfer: "Transfer Bank",
  qris: "QRIS",
  ewallet: "E-Wallet",
  piutang: "Bayar Nanti (Piutang)",
};

export const PAYMENT_STATUS_LABEL = {
  pending: "Menunggu Pembayaran",
  paid: "Lunas",
  failed: "Gagal",
  expired: "Kedaluwarsa",
  cod: "Bayar di Tempat",
  piutang: "Belum Bayar / Piutang",
};

export const ORDER_STATUS_LABEL = {
  baru: "Baru",
  diproses: "Diproses",
  dikirim: "Dikirim",
  selesai: "Selesai",
  dibatalkan: "Dibatalkan",
};

export const CHANNEL_LABEL = {
  bca: "BCA",
  bni: "BNI",
  bri: "BRI",
  mandiri: "Mandiri",
  permata: "Permata",
  gopay: "GoPay",
  shopeepay: "ShopeePay",
  ovo: "OVO",
  dana: "DANA",
};

export const EXPENSE_CATEGORY_LABEL = {
  angkut: "Ongkos Angkut / Kirim",
  operasional: "Operasional",
  gaji: "Gaji / Upah",
  sewa: "Sewa",
  listrik_air: "Listrik & Air",
  perlengkapan: "Perlengkapan",
  pembelian: "Pembelian Barang",
  lainnya: "Lainnya",
};

export const SETTLE_METHOD_LABEL = {
  cash: "Tunai",
  transfer: "Transfer Bank",
  qris: "QRIS",
  ewallet: "E-Wallet",
  lainnya: "Lainnya",
};

export const CUSTOMER_SEGMENT_LABEL = {
  tetap: "Pelanggan Tetap",
  aktif: "Aktif",
  baru: "Baru",
  pasif: "Pasif",
};
