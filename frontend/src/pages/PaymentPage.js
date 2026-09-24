import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import { CheckCircle2, Copy, Loader2, RefreshCw, Landmark, AlertTriangle, ClipboardList, Receipt, HandCoins, Banknote, Clock, QrCode, ArrowLeftRight } from "lucide-react";
import { toast } from "sonner";
import { api, errorMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { PaymentStatusBadge, OrderStatusBadge } from "@/components/StatusBadge";
import { PaymentMethodPicker, usePaymentConfig } from "@/components/PaymentMethodPicker";
import { rupiah, formatDate, paymentLabel, PAYMENT_CHANNEL_LABEL } from "@/lib/format";
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
  sky: { box: "border-sky-200 bg-sky-50", icon: "bg-sky-600", title: "text-sky-900", desc: "text-sky-800" },
  rose: { box: "border-rose-200 bg-rose-50", icon: "bg-rose-600", title: "text-rose-900", desc: "text-rose-800" },
};

function StatusBanner({ order }) {
  const st = order.payment_status;
  const cancelled = order.order_status === "dibatalkan";
  let tone = "amber", Icon = Clock, title = "Menunggu pembayaran online", desc = `Selesaikan pembayaran ${rupiah(order.total)} agar pesanan dapat diproses.`;
  if (cancelled) {
    tone = "rose"; Icon = AlertTriangle; title = "Pesanan dibatalkan"; desc = "Pesanan ini telah dibatalkan. Hubungi kami bila ada pertanyaan.";
  } else if (st === "paid") {
    tone = "emerald"; Icon = CheckCircle2;
    title = order.order_status === "selesai" ? "Pembayaran diterima, pesanan selesai" : "Pembayaran diterima, pesanan sedang diproses";
    desc = `Lunas pada ${formatDate(order.paid_at)}. ${order.order_status === "selesai" ? "Terima kasih telah berbelanja." : `Tim kami akan menghubungi ${order.phone} untuk jadwal pengiriman.`}`;
  } else if (st === "proses") {
    tone = "sky"; Icon = Banknote; title = "Pesanan diproses, bayar tunai ke kasir";
    desc = `Siapkan uang tunai ${rupiah(order.total)}. Status berubah Lunas & Selesai setelah kasir menerima pembayaran.`;
  } else if (st === "piutang") {
    tone = "violet"; Icon = HandCoins; title = "Pesanan dicatat sebagai piutang (bayar nanti)";
    desc = `Tagihan ${rupiah(order.total)} masuk ke modul Piutang dan ditagihkan sesuai kesepakatan. Status berubah Lunas setelah admin mengonfirmasi pembayaran.`;
  } else if (st === "expired" || st === "failed") {
    tone = "rose"; Icon = AlertTriangle; title = st === "expired" ? "Tagihan online kedaluwarsa" : "Pembayaran online gagal";
    desc = "Silakan buat ulang tagihan dengan memilih kanal pembayaran lagi, atau ganti ke Cash / Bayar Nanti.";
  }
  const t = TONES[tone];
  return (
    <div className={cn("mt-6 flex items-start gap-3 rounded-2xl border p-5", t.box)} data-testid="payment-status-banner">
      <span className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-white", t.icon)}><Icon className="h-5 w-5" /></span>
      <div>
        <p className={cn("font-display text-lg font-semibold", t.title)}>{title}</p>
        <p className={cn("mt-0.5 text-sm", t.desc)}>{desc}</p>
      </div>
    </div>
  );
}

function OnlineInstructions({ order, ins, checking, onCheck }) {
  const isVa = String(order.payment_channel || "").startsWith("va_");
  const active = ins.status === "active";
  const qrSrc = ins.qr_url || ins.qr_image;
  return (
    <Card data-testid="online-payment-card">
      <CardHeader>
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">{isVa ? <Landmark className="h-5 w-5" /> : <QrCode className="h-5 w-5" />}</span>
          <div>
            <CardTitle className="font-display text-lg">{PAYMENT_CHANNEL_LABEL[order.payment_channel] || "Bayar Online"} · BATPay</CardTitle>
            <CardDescription>{active && ins.expires_at ? `Selesaikan sebelum ${formatDate(ins.expires_at)}` : "Selesaikan pembayaran untuk memproses pesanan"}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="rounded-xl border bg-muted/40 p-4">
          <p className="text-xs text-muted-foreground">Total yang harus dibayar (termasuk biaya layanan {rupiah(order.service_fee)})</p>
          <div className="mt-1 flex items-center justify-between gap-3">
            <p className="font-display text-2xl font-semibold" data-testid="payment-amount">{rupiah(order.total)}</p>
            <CopyButton value={Math.round(order.total)} testId="copy-amount-button" />
          </div>
        </div>

        {active && isVa && (
          <div className="rounded-xl border bg-card p-4" data-testid="va-instructions">
            <p className="text-xs text-muted-foreground">Nomor Virtual Account {ins.bank_name || ""}</p>
            <div className="mt-1 flex items-center justify-between gap-3">
              <p className="font-display text-xl font-semibold tracking-wider sm:text-2xl" data-testid="payment-va-number">{ins.va_number}</p>
              <CopyButton value={ins.va_number} testId="copy-va-button" />
            </div>
            <p className="mt-2 text-xs text-muted-foreground">{ins.message}</p>
          </div>
        )}
        {active && !isVa && (
          <div className="flex flex-col items-center gap-3 rounded-xl border bg-white p-4" data-testid="qris-instructions">
            {qrSrc ? (
              <img src={qrSrc} alt="QRIS" className="h-56 w-56 object-contain" data-testid="qris-image" />
            ) : ins.qr_content ? (
              <QRCodeSVG value={ins.qr_content} size={224} level="M" includeMargin data-testid="qris-svg" />
            ) : null}
            <p className="text-center text-xs text-muted-foreground">{ins.merchant_name ? `Merchant: ${ins.merchant_name}. ` : ""}{ins.message}</p>
            {ins.qr_content && <CopyButton value={ins.qr_content} testId="copy-qr-button" />}
          </div>
        )}
        {!active && (
          <div className="flex items-start gap-3 rounded-xl border-2 border-dashed border-amber-300 bg-amber-50 p-4 text-sm text-amber-900" data-testid="online-placeholder">
            <Clock className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <p className="font-semibold">Bayar Online belum aktif</p>
              <p className="mt-0.5 text-amber-800">{ins.message || "Instruksi pembayaran akan tampil di sini setelah integrasi BATPay aktif."} Anda dapat mengganti metode di bawah.</p>
            </div>
          </div>
        )}

        <Separator />
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="secondary" className="gap-2" onClick={onCheck} disabled={checking} data-testid="payment-check-status-button">
            {checking ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />} Cek Status
          </Button>
          <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="h-2 w-2 animate-pulse rounded-full bg-amber-500" /> Memantau pembayaran otomatis
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

export default function PaymentPage() {
  const { orderNumber } = useParams();
  const navigate = useNavigate();
  const config = usePaymentConfig();
  const [order, setOrder] = useState(null);
  const [payment, setPayment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [checking, setChecking] = useState(false);
  const [switching, setSwitching] = useState(false);
  const [showSwitch, setShowSwitch] = useState(false);
  const [newMethod, setNewMethod] = useState("cash");
  const [newChannel, setNewChannel] = useState("qris");
  const timer = useRef(null);

  const load = useCallback(async () => {
    try {
      const [o, p] = await Promise.all([api.get(`/orders/${orderNumber}`), api.get(`/payments/${orderNumber}`)]);
      setOrder(o.data);
      setPayment(p.data);
      setNewMethod(o.data.payment_method);
      setNewChannel(o.data.payment_channel || "qris");
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
        if (!silent && data.payment_status === "pending") toast.info("Pembayaran belum diterima", { description: "Status akan diperbarui otomatis setelah pembayaran terverifikasi." });
        if (data.payment_status === "paid" && !silent) toast.success("Pembayaran diterima");
      } catch (e) {
        if (!silent) toast.error(errorMessage(e));
      } finally {
        if (!silent) setChecking(false);
      }
    },
    [orderNumber]
  );

  useEffect(() => {
    if (!order || !(order.payment_status === "pending" || order.payment_status === "proses")) return undefined;
    timer.current = setInterval(() => checkStatus(true), 8000);
    return () => clearInterval(timer.current);
  }, [order, checkStatus]);

  const applySwitch = async () => {
    if (newMethod === "online" && !config?.online_enabled) return toast.error("Bayar Online belum aktif");
    setSwitching(true);
    try {
      await api.post(`/payments/${orderNumber}/create`, { payment_method: newMethod, payment_channel: newMethod === "online" ? newChannel : null });
      toast.success("Metode pembayaran diperbarui");
      setShowSwitch(false);
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
  const cancelled = order.order_status === "dibatalkan";
  const showOnline = order.payment_method === "online" && !isPaid && !cancelled;
  const canSwitch = !isPaid && !cancelled;
  const baseAmount = Number(order.subtotal) + Number(order.shipping_fee || 0);
  const changed = newMethod !== order.payment_method || (newMethod === "online" && newChannel !== order.payment_channel);

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 sm:py-10">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm text-muted-foreground">No. Pesanan</p>
          <h1 className="font-display text-2xl font-semibold sm:text-3xl" data-testid="payment-order-number">{order.order_number}</h1>
          <p className="mt-1 text-sm text-muted-foreground" data-testid="payment-method-label">Dibuat {formatDate(order.created_at)} · {paymentLabel(order)}</p>
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
          {showOnline && <OnlineInstructions order={order} ins={ins} checking={checking} onCheck={() => checkStatus(false)} />}

          {order.payment_status === "proses" && (
            <Card data-testid="cash-instructions-card">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base"><Banknote className="h-4 w-4 text-sky-700" /> Pembayaran Tunai di Kasir</CardTitle>
                <CardDescription>Tunjukkan nomor pesanan <b>{order.order_number}</b> kepada kasir dan bayar tunai <b>{rupiah(order.total)}</b>. Kasir akan menandai pesanan Selesai setelah uang diterima.</CardDescription>
              </CardHeader>
            </Card>
          )}

          {canSwitch && (
            <Card data-testid="switch-method-card">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <CardTitle className="text-base">Ganti metode pembayaran</CardTitle>
                    <CardDescription>Pesanan belum lunas, metode masih bisa diubah.</CardDescription>
                  </div>
                  {!showSwitch && (
                    <Button type="button" variant="outline" size="sm" className="gap-1.5" onClick={() => setShowSwitch(true)} data-testid="switch-method-open">
                      <ArrowLeftRight className="h-3.5 w-3.5" /> Ubah
                    </Button>
                  )}
                </div>
              </CardHeader>
              {showSwitch && (
                <CardContent className="space-y-3">
                  <PaymentMethodPicker method={newMethod} onMethodChange={setNewMethod} channel={newChannel} onChannelChange={setNewChannel} amount={baseAmount} config={config} compact idPrefix="switch" disabled={switching} />
                  <div className="flex justify-end gap-2">
                    <Button type="button" variant="ghost" size="sm" onClick={() => setShowSwitch(false)} disabled={switching}>Batal</Button>
                    <Button type="button" size="sm" className="gap-2" onClick={applySwitch} disabled={switching || !changed} data-testid="switch-method-apply">
                      {switching ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />} Simpan Metode
                    </Button>
                  </div>
                </CardContent>
              )}
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
              {Number(order.service_fee) > 0 && (
                <div className="flex justify-between" data-testid="payment-service-fee"><span className="text-muted-foreground">Biaya Layanan</span><span>{rupiah(order.service_fee)}</span></div>
              )}
              <div className="flex items-center justify-between pt-1">
                <span className="font-semibold">Total</span>
                <span className="font-display text-xl font-semibold" data-testid="payment-total">{rupiah(order.total)}</span>
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
