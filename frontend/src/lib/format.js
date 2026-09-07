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

export const PAYMENT_METHOD_LABEL = {
  cod: "COD (Bayar di Tempat)",
  bank_transfer: "Transfer Bank",
  qris: "QRIS",
  ewallet: "E-Wallet",
};

export const PAYMENT_STATUS_LABEL = {
  pending: "Menunggu Pembayaran",
  paid: "Lunas",
  failed: "Gagal",
  expired: "Kedaluwarsa",
  cod: "Bayar di Tempat",
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
