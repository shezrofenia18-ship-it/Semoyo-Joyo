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

/** Tiga metode pembayaran resmi: Cash, Bayar Nanti (piutang), Bayar Online (BATPay). */
export const PAYMENT_METHOD_LABEL = {
  cash: "Cash (Tunai)",
  piutang: "Bayar Nanti (Piutang)",
  online: "Bayar Online (BATPay)",
};

/** Kanal Bayar Online BATPay. */
export const PAYMENT_CHANNEL_LABEL = {
  qris: "QRIS",
  va_bca: "Virtual Account BCA",
  va_mandiri: "Virtual Account Mandiri",
  va_cimb: "Virtual Account CIMB Niaga",
  va_danamon: "Virtual Account Danamon",
};

export const paymentLabel = (order) => {
  if (!order) return "-";
  const base = PAYMENT_METHOD_LABEL[order.payment_method] || order.payment_method;
  if (order.payment_method === "online" && order.payment_channel) return `${base} · ${PAYMENT_CHANNEL_LABEL[order.payment_channel] || order.payment_channel}`;
  return base;
};

export const PAYMENT_STATUS_LABEL = {
  proses: "Proses (Bayar di Kasir)",
  pending: "Menunggu Pembayaran",
  paid: "Lunas",
  failed: "Gagal",
  expired: "Kedaluwarsa",
  piutang: "Belum Bayar / Piutang",
};

export const ORDER_STATUS_LABEL = {
  baru: "Baru",
  diproses: "Diproses",
  dikirim: "Dikirim",
  selesai: "Selesai",
  dibatalkan: "Dibatalkan",
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
