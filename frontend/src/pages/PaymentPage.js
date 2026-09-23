import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { CheckCircle2, Copy, Loader2, RefreshCw, Landmark, AlertTriangle, ClipboardList, Receipt, HandCoins, Banknote, Clock } from "lucide-react";
import { toast } from "sonner";
import { api, errorMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { PaymentStatusBadge, OrderStatusBadge } from "@/components/StatusBadge";
import { rupiah, formatDate, PAYMENT_METHOD_LABEL } from "@/lib/format";
import { cn } from "@/lib/utils";

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

const TONES = {
  emerald: { box: "border-emerald-200 bg-emerald-50", icon: "bg-emerald-600", title: "text-emerald-900", desc: "text-emerald-800" },
  violet: { box: "border-violet-200 bg-violet-50", icon: "bg-violet-600", title: "text-violet-900", desc: "text-violet-800" },
  amber: { box: "border-amber-200 bg-amber-50", icon: "bg-amber-600", title: "text-amber-900", desc: "text-amber-800" },
};

function StatusBanner({ order }) {
  const isPaid = order.payment_status === "paid";
  const isPiutang = order.payment_status === "piutang";
  const t = TONES[isPaid ? "emerald" : isPiutang ? "violet" : "amber"];
  const Icon = isPaid ? CheckCircle2 : isPiutang ? HandCoins : Clock;
  const title = isPaid
    ? order.payment_method === "cash" ? "Pembayaran tunai diterima, pesanan sedang diproses" : "Pembayaran diterima, pesanan sedang diproses"
    : isPiutang ? "Pesanan dicatat sebagai piutang (bayar nanti)" : "Menunggu pembayaran Transfer VA";
  const desc = isPaid
    ? `Lunas pada ${formatDate(order.paid_at)}. Tim kami akan menghubungi ${order.phone} untuk jadwal pengiriman.`
    : isPiutang
    ? `Tagihan ${rupiah(order.total)} masuk ke modul Piutang dan ditagihkan sesuai kesepakatan. Status berubah Lunas setelah admin mengonfirmasi pembayaran.`
    : `Selesaikan transfer ${rupiah(order.total)} agar pesanan dapat diproses.`;
  return (
    <div className={cn("mt-6 flex items-start gap-3 rounded-2xl border p-5", t.box)} data-testid="payment-success-banner">
      <span className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-white", t.icon)}><Icon className="h-5 w-5" /></span>
      <div>
        <p className={cn("font-display text-lg font-semibold", t.title)}>{title}</p>
        <p className={cn("mt-0.5 text-sm", t.desc)}>{desc}</p>
      </div>
    </div>
  );
}

export default function PaymentPage() {
  const { orderNumber } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [payment, setPayment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
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
        if (!silent && data.payment_status === "pending") toast.info("Pembayaran belum diterima", { description: "Status akan diperbarui otomatis setelah transfer terverifikasi." });
        if (!silent && data.payment_status === "paid") toast.success("Pembayaran diterima");
      } catch (e) {
        if (!silent) toast.error(errorMessage(e));
      } finally {
        if (!silent) setChecking(false);
      }
    },
    [orderNumber]
  );

  useEffect(() => {
    if (!order || order.payment_status !== "pending") return undefined;
    timer.current = setInterval(() => checkStatus(true), 8000);
    return () => clearInterval(timer.current);
  }, [order, checkStatus]);

  const switchMethod = async (method) => {
    setSwitching(true);
    try {
      await api.post(`/payments/${orderNumber}/create`, { payment_method: method });
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
  const awaitingVa = order.payment_method === "transfer_va" && order.payment_status === "pending";
  const vaActive = awaitingVa && ins.status === "active" && ins.va_number;

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 sm:py-10">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm text-muted-foreground">No. Pesanan</p>
          <h1 className="font-display text-2xl font-semibold sm:text-3xl" data-testid="payment-order-number">{order.order_number}</h1>
          <p className="mt-1 text-sm text-muted-foreground">Dibuat {formatDate(order.created_at)} · {PAYMENT_METHOD_LABEL[order.payment_method] || order.payment_method}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <PaymentStatusBadge status={order.payment_status} data-testid="payment-status-badge" className="px-3 py-1 text-sm" />
          <OrderStatusBadge status={order.order_status} data-testid="order-status-badge" className="px-3 py-1 text-sm" />
          <Button variant="outline" size="sm" className="gap-2 border-primary/40 text-primary" onClick={() => navigate(`/struk/${order.order_number}`)} data-testid="payment-receipt-button">
            <Receipt className="h-4 w-4" /> Struk / PDF
          </Button>
        </div>
      </div>

      <StatusBanner order={order} />

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_340px]">
        <div className="space-y-6">
          {awaitingVa && (
            <Card data-testid="transfer-va-card">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-accent-foreground"><Landmark className="h-5 w-5" /></span>
                  <div>
                    <CardTitle className="font-display text-lg">Transfer Virtual Account · Travoy Pay</CardTitle>
                    <CardDescription>{vaActive && ins.expires_at ? `Selesaikan sebelum ${formatDate(ins.expires_at)}` : "Selesaikan pembayaran untuk memproses pesanan"}</CardDescription>
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

                {vaActive ? (
                  <div className="rounded-xl border bg-card p-4">
                    <p className="text-xs text-muted-foreground">Nomor Virtual Account {ins.bank_name || ""}</p>
                    <div className="mt-1 flex items-center justify-between gap-3">
                      <p className="font-display text-xl font-semibold tracking-wider sm:text-2xl" data-testid="payment-va-number">{ins.va_number}</p>
                      <CopyButton value={ins.va_number} testId="copy-va-button" />
                    </div>
                  </div>
                ) : (
                  <div className="flex items-start gap-3 rounded-xl border-2 border-dashed border-sky-300 bg-sky-50 p-4 text-sm text-sky-900" data-testid="transfer-va-placeholder">
                    <Clock className="mt-0.5 h-4 w-4 shrink-0" />
                    <div>
                      <p className="font-semibold">Integrasi Travoy Pay sedang disiapkan</p>
                      <p className="mt-0.5 text-sky-800">{ins.message || "Nomor Virtual Account akan tampil di sini setelah integrasi aktif."} Sementara itu Anda dapat mengganti metode ke Tunai atau Bayar Nanti di bawah.</p>
                    </div>
                  </div>
                )}

                <Separator />
                <div className="flex flex-wrap items-center gap-2">
                  <Button variant="secondary" className="gap-2" onClick={() => checkStatus(false)} disabled={checking} data-testid="payment-check-status-button">
                    {checking ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />} Cek Status
                  </Button>
                  <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-amber-500" /> Memantau pembayaran otomatis
                  </span>
                </div>
              </CardContent>
            </Card>
          )}

          {!isPaid && order.order_status !== "dibatalkan" && (
            <Card data-testid="switch-method-card">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Ganti metode pembayaran</CardTitle>
                <CardDescription>Pesanan belum lunas, metode masih bisa diubah.</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                {[["cash", "Cash (Tunai)", Banknote], ["piutang", "Bayar Nanti", HandCoins], ["transfer_va", "Transfer VA", Landmark]].map(([m, label, I]) => {
                  const active = order.payment_method === m;
                  return (
                    <Button key={m} type="button" size="sm" variant={active ? "default" : "outline"} className="gap-1.5" disabled={switching || active} onClick={() => switchMethod(m)} data-testid={`switch-method-${m}`}>
                      <I className="h-3.5 w-3.5" /> {label}
                    </Button>
                  );
                })}
              </CardContent>
            </Card>
          )}
        </div>

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
              <Button variant="secondary" className="w-full gap-2" data-testid="go-to-orders-button"><ClipboardList className="h-4 w-4" /> Riwayat</Button>
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
