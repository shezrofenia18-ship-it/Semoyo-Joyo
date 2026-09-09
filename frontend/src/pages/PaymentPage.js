import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { CheckCircle2, Copy, Loader2, RefreshCw, Truck, Landmark, QrCode, Wallet, AlertTriangle, ExternalLink, FlaskConical, ClipboardList, Receipt, HandCoins } from "lucide-react";
import { toast } from "sonner";
import { api, errorMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { PaymentStatusBadge, OrderStatusBadge } from "@/components/StatusBadge";
import { rupiah, formatDate, PAYMENT_METHOD_LABEL, CHANNEL_LABEL } from "@/lib/format";
import { cn } from "@/lib/utils";

const ICONS = { cod: Truck, bank_transfer: Landmark, qris: QrCode, ewallet: Wallet, piutang: HandCoins };

function CopyButton({ value, testId }) {
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(String(value));
      toast.success("Disalin ke clipboard");
    } catch {
      toast.error("Gagal menyalin");
    }
  };
  return (
    <Button type="button" variant="secondary" size="sm" className="gap-1.5" onClick={copy} data-testid={testId}>
      <Copy className="h-3.5 w-3.5" /> Salin
    </Button>
  );
}

export default function PaymentPage() {
  const { orderNumber } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [payment, setPayment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [simulating, setSimulating] = useState(false);
  const [checking, setChecking] = useState(false);
  const [switching, setSwitching] = useState(false);
  const timer = useRef(null);

  const load = useCallback(async () => {
    try {
      const [o, p] = await Promise.all([api.get(`/orders/${orderNumber}`), api.get(`/payments/${orderNumber}`)]);
      setOrder(o.data);
      setPayment(p.data);
      setError("");
    } catch (e) {
      setError(errorMessage(e, "Pesanan tidak ditemukan"));
    } finally {
      setLoading(false);
    }
  }, [orderNumber]);

  useEffect(() => {
    load();
  }, [load]);

  const checkStatus = useCallback(
    async (silent = false) => {
      if (!silent) setChecking(true);
      try {
        const { data } = await api.get(`/payments/${orderNumber}/status`);
        setOrder((prev) => (prev ? { ...prev, payment_status: data.payment_status, order_status: data.order_status, paid_at: data.paid_at } : prev));
        setPayment((prev) => (prev ? { ...prev, payment_status: data.payment_status } : prev));
        if (!silent && data.payment_status === "pending") toast.info("Pembayaran belum diterima", { description: "Status akan diperbarui otomatis setelah pembayaran masuk." });
        if (!silent && data.payment_status === "paid") toast.success("Pembayaran diterima");
      } catch (e) {
        if (!silent) toast.error(errorMessage(e));
      } finally {
        if (!silent) setChecking(false);
      }
    },
    [orderNumber]
  );

  // polling while pending
  useEffect(() => {
    if (!order || order.payment_status !== "pending") return undefined;
    timer.current = setInterval(() => checkStatus(true), 8000);
    return () => clearInterval(timer.current);
  }, [order, checkStatus]);

  const simulate = async () => {
    setSimulating(true);
    try {
      const { data } = await api.post(`/payments/${orderNumber}/simulate`);
      toast.success(data.message || "Pembayaran berhasil");
      await load();
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setSimulating(false);
    }
  };

  const switchMethod = async (method, channel) => {
    setSwitching(true);
    try {
      await api.post(`/payments/${orderNumber}/create`, { payment_method: method, payment_channel: channel });
      toast.success("Metode pembayaran diperbarui");
      await load();
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setSwitching(false);
    }
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl space-y-4 px-4 py-10 sm:px-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-60 w-full" />
      </div>
    );
  }
  if (error || !order) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 text-center sm:px-6">
        <AlertTriangle className="mx-auto h-10 w-10 text-amber-500" />
        <h1 className="mt-3 font-display text-xl font-semibold">{error || "Pesanan tidak ditemukan"}</h1>
        <Button className="mt-6" onClick={() => navigate("/")}>Kembali ke Beranda</Button>
      </div>
    );
  }

  const ins = payment?.instructions || {};
  const isPaid = order.payment_status === "paid";
  const isCod = order.payment_method === "cod";
  const isPiutang = order.payment_status === "piutang" || (order.payment_method === "piutang" && !isPaid);
  const Icon = ICONS[order.payment_method] || Wallet;
  const simulation = payment?.simulation;

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 sm:py-10">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm text-muted-foreground">No. Pesanan</p>
          <h1 className="font-display text-2xl font-semibold sm:text-3xl" data-testid="payment-order-number">{order.order_number}</h1>
          <p className="mt-1 text-sm text-muted-foreground">Dibuat {formatDate(order.created_at)}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <PaymentStatusBadge status={order.payment_status} data-testid="payment-status-badge" className="px-3 py-1 text-sm" />
          <OrderStatusBadge status={order.order_status} data-testid="order-status-badge" className="px-3 py-1 text-sm" />
          <Button variant="outline" size="sm" className="gap-2 border-primary/40 text-primary" onClick={() => navigate(`/struk/${order.order_number}`)} data-testid="payment-receipt-button">
            <Receipt className="h-4 w-4" /> Struk / PDF
          </Button>
        </div>
      </div>

      {/* Success / COD banner */}
      {(isPaid || isCod || isPiutang) && (
        <div className={cn("mt-6 flex items-start gap-3 rounded-2xl border p-5", isPaid ? "border-emerald-200 bg-emerald-50" : isPiutang ? "border-violet-200 bg-violet-50" : "border-sky-200 bg-sky-50")} data-testid="payment-success-banner">
          <span className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-white", isPaid ? "bg-emerald-600" : isPiutang ? "bg-violet-600" : "bg-sky-600")}>
            {isPaid ? <CheckCircle2 className="h-5 w-5" /> : isPiutang ? <HandCoins className="h-5 w-5" /> : <Truck className="h-5 w-5" />}
          </span>
          <div>
            <p className={cn("font-display text-lg font-semibold", isPaid ? "text-emerald-900" : isPiutang ? "text-violet-900" : "text-sky-900")}>
              {isPaid ? "Pembayaran diterima, pesanan sedang diproses" : isPiutang ? "Pesanan dicatat sebagai piutang (bayar nanti)" : "Pesanan diterima, bayar saat barang tiba"}
            </p>
            <p className={cn("mt-0.5 text-sm", isPaid ? "text-emerald-800" : isPiutang ? "text-violet-800" : "text-sky-800")}>
              {isPaid
                ? `Lunas pada ${formatDate(order.paid_at)}. Tim kami akan menghubungi ${order.phone} untuk jadwal pengiriman.`
                : isPiutang
                ? `Tagihan ${rupiah(order.total)} akan ditagihkan sesuai kesepakatan. Status berubah Lunas setelah admin mengonfirmasi pembayaran Anda.`
                : `Kurir akan menghubungi ${order.phone} sebelum pengiriman. Siapkan pembayaran ${rupiah(order.total)}.`}
            </p>
          </div>
        </div>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_340px]">
        {/* Instructions */}
        <div className="space-y-6">
          {!isPaid && !isCod && !isPiutang && (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                    <Icon className="h-5 w-5" />
                  </span>
                  <div>
                    <CardTitle className="font-display text-lg">
                      {PAYMENT_METHOD_LABEL[order.payment_method]}
                      {order.payment_channel ? ` - ${CHANNEL_LABEL[order.payment_channel] || order.payment_channel}` : ""}
                    </CardTitle>
                    <CardDescription>
                      {ins.expires_at ? `Selesaikan sebelum ${formatDate(ins.expires_at)}` : "Selesaikan pembayaran untuk memproses pesanan"}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="rounded-xl border bg-muted/40 p-4">
                  <p className="text-xs text-muted-foreground">Total yang harus dibayar</p>
                  <div className="mt-1 flex items-center justify-between gap-3">
                    <p className="font-display text-2xl font-semibold" data-testid="payment-amount">{rupiah(order.total)}</p>
                    <CopyButton value={Math.round(order.total)} testId="copy-amount-button" />
                  </div>
                </div>

                {ins.error && (
                  <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
                    Gagal membuat transaksi di gateway: {ins.error}. Coba pilih metode lain di bawah.
                  </div>
                )}

                {order.payment_method === "bank_transfer" && (ins.va_number || ins.bill_key) && (
                  <div className="rounded-xl border bg-card p-4">
                    <p className="text-xs text-muted-foreground">{ins.bill_key ? "Kode Perusahaan / Kode Bayar" : `Nomor Virtual Account ${ins.bank_name || ""}`}</p>
                    {ins.bill_key ? (
                      <div className="mt-1 space-y-1">
                        <p className="font-display text-lg font-semibold tracking-wide">Biller: {ins.biller_code}</p>
                        <div className="flex items-center justify-between gap-3">
                          <p className="font-display text-xl font-semibold tracking-wider" data-testid="payment-va-number">{ins.bill_key}</p>
                          <CopyButton value={ins.bill_key} testId="copy-va-button" />
                        </div>
                      </div>
                    ) : (
                      <div className="mt-1 flex items-center justify-between gap-3">
                        <p className="font-display text-xl font-semibold tracking-wider sm:text-2xl" data-testid="payment-va-number">{ins.va_number}</p>
                        <CopyButton value={ins.va_number} testId="copy-va-button" />
                      </div>
                    )}
                  </div>
                )}

                {order.payment_method === "qris" && (
                  <div className="flex flex-col items-center rounded-xl border bg-card p-5 text-center">
                    <img
                      src={ins.qr_url || "/qris-placeholder.svg"}
                      alt="Kode QRIS"
                      data-testid="payment-qris-image"
                      className="h-56 w-56 rounded-lg border bg-white p-2"
                    />
                    <p className="mt-3 text-sm font-semibold">Scan untuk membayar {rupiah(order.total)}</p>
                    {ins.static && (
                      <p className="mt-1 text-xs text-muted-foreground" data-testid="qris-placeholder-note">
                        Gambar QRIS statis sementara. QR dinamis aktif setelah gateway terhubung.
                      </p>
                    )}
                  </div>
                )}

                {order.payment_method === "ewallet" && (
                  <div className="rounded-xl border bg-card p-4">
                    <p className="text-sm font-semibold">{ins.channel_name || "E-Wallet"}</p>
                    {ins.deeplink || ins.redirect_url ? (
                      <a href={ins.deeplink || ins.redirect_url} target="_blank" rel="noreferrer">
                        <Button className="mt-3 gap-2" data-testid="ewallet-pay-button">
                          Bayar dengan {ins.channel_name} <ExternalLink className="h-4 w-4" />
                        </Button>
                      </a>
                    ) : (
                      <p className="mt-1 text-xs text-muted-foreground">Mode simulasi: tombol pembayaran e-wallet akan aktif setelah gateway terhubung. Gunakan tombol Simulasi Bayar di bawah.</p>
                    )}
                    {ins.qr_url && <img src={ins.qr_url} alt="QR e-wallet" className="mt-3 h-48 w-48 rounded-lg border bg-white p-2" />}
                  </div>
                )}

                {Array.isArray(ins.steps) && ins.steps.length > 0 && (
                  <ol className="space-y-2 text-sm">
                    {ins.steps.map((s, i) => (
                      <li key={i} className="flex gap-3">
                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-secondary text-xs font-semibold">{i + 1}</span>
                        <span className="text-muted-foreground">{s}</span>
                      </li>
                    ))}
                  </ol>
                )}

                <Separator />

                <div className="flex flex-wrap items-center gap-2">
                  <Button variant="secondary" className="gap-2" onClick={() => checkStatus(false)} disabled={checking} data-testid="payment-check-status-button">
                    {checking ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                    Cek Status
                  </Button>
                  {simulation && (
                    <Button className="gap-2 bg-amber-600 text-white hover:bg-amber-700" onClick={simulate} disabled={simulating} data-testid="payment-simulate-button">
                      {simulating ? <Loader2 className="h-4 w-4 animate-spin" /> : <FlaskConical className="h-4 w-4" />}
                      Simulasi Bayar (Sandbox)
                    </Button>
                  )}
                  <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-amber-500" /> Memantau pembayaran otomatis
                  </span>
                </div>
              </CardContent>
            </Card>
          )}

          {!isPaid && !isCod && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Ganti metode pembayaran</CardTitle>
                <CardDescription>Masih belum bayar? Anda bisa mengganti metode.</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                {[
                  ["bank_transfer", "bca", "BCA VA"], ["bank_transfer", "bni", "BNI VA"], ["bank_transfer", "bri", "BRI VA"], ["bank_transfer", "mandiri", "Mandiri"],
                  ["qris", null, "QRIS"], ["ewallet", "gopay", "GoPay"], ["ewallet", "ovo", "OVO"], ["ewallet", "dana", "DANA"], ["ewallet", "shopeepay", "ShopeePay"], ["cod", null, "COD"], ["piutang", null, "Bayar Nanti"],
                ].map(([m, c, label]) => {
                  const active = order.payment_method === m && (order.payment_channel || null) === c;
                  return (
                    <Button key={label} type="button" size="sm" variant={active ? "default" : "outline"} disabled={switching || active} onClick={() => switchMethod(m, c)} data-testid={`switch-method-${m}${c ? "-" + c : ""}`}>
                      {label}
                    </Button>
                  );
                })}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Order summary */}
        <div className="space-y-4 lg:sticky lg:top-24 lg:self-start">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="font-display text-lg">Rincian Pesanan</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <ul className="space-y-2" data-testid="payment-order-items">
                {order.items.map((it) => (
                  <li key={it.id} className="flex justify-between gap-2">
                    <span className="min-w-0 truncate">{it.product_name} <span className="text-muted-foreground">x{it.qty} {it.unit}</span></span>
                    <span className="shrink-0">{rupiah(it.subtotal)}</span>
                  </li>
                ))}
              </ul>
              <Separator />
              <div className="flex justify-between"><span className="text-muted-foreground">Subtotal</span><span>{rupiah(order.subtotal)}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Ongkir</span><span>{order.shipping_fee > 0 ? rupiah(order.shipping_fee) : "Dikonfirmasi admin"}</span></div>
              <div className="flex items-center justify-between pt-1">
                <span className="font-semibold">Total</span>
                <span className="font-display text-xl font-semibold">{rupiah(order.total)}</span>
              </div>
              <Separator />
              <div className="space-y-1 text-xs text-muted-foreground">
                <p className="font-semibold text-foreground">{order.customer_name}</p>
                <p>{order.phone}</p>
                <p>{order.address}</p>
                {order.notes && <p className="italic">Catatan: {order.notes}</p>}
              </div>
            </CardContent>
          </Card>
          <div className="grid grid-cols-2 gap-2">
            <Link to="/pesanan">
              <Button variant="secondary" className="w-full gap-2" data-testid="go-to-orders-button">
                <ClipboardList className="h-4 w-4" /> Riwayat
              </Button>
            </Link>
            <Link to="/">
              <Button variant="outline" className="w-full">Belanja Lagi</Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
