import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Printer, Download, CheckCircle2, Clock3 } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { LOGO_FULL, BRAND_NAME, BRAND_TAGLINE } from "@/components/Brand";
import { rupiah, formatDate, PAYMENT_METHOD_LABEL, PAYMENT_STATUS_LABEL, ORDER_STATUS_LABEL, CHANNEL_LABEL } from "@/lib/format";

/**
 * Struk / Receipt pembelian berlogo Semoyo Joyo.
 * "Unduh PDF" memakai dialog cetak browser (Simpan sebagai PDF) — tanpa dependensi tambahan.
 */
export default function ReceiptPage() {
  const { orderNumber } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get(`/orders/${orderNumber}`).then((r) => setOrder(r.data)).catch((e) => setError(errorMessage(e, "Pesanan tidak ditemukan")));
  }, [orderNumber]);

  useEffect(() => {
    if (order) document.title = `Struk ${order.order_number} - ${BRAND_NAME}`;
    return () => { document.title = `${BRAND_NAME} - ${BRAND_TAGLINE}`; };
  }, [order]);

  const print = () => window.print();

  if (error) {
    return (
      <div className="mx-auto max-w-md px-4 py-16 text-center">
        <p className="text-sm text-muted-foreground">{error}</p>
        <Button className="mt-6" onClick={() => navigate("/pesanan")}>Ke Riwayat Pesanan</Button>
      </div>
    );
  }
  if (!order) {
    return <div className="mx-auto max-w-2xl space-y-3 px-4 py-10"><Skeleton className="h-10 w-1/2" /><Skeleton className="h-64" /></div>;
  }

  const isPaid = order.payment_status === "paid";
  const isCod = order.payment_method === "cod";

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
      <div className="no-print mb-4 flex flex-wrap items-center justify-between gap-2">
        <Button variant="ghost" className="gap-2 px-2" onClick={() => navigate(-1)}><ArrowLeft className="h-4 w-4" /> Kembali</Button>
        <div className="flex gap-2">
          <Button variant="outline" className="gap-2" onClick={print} data-testid="receipt-print-button"><Printer className="h-4 w-4" /> Cetak</Button>
          <Button className="gap-2" onClick={print} data-testid="receipt-download-button"><Download className="h-4 w-4" /> Unduh PDF</Button>
        </div>
      </div>

      <article id="receipt" className="receipt rounded-2xl border bg-white p-6 text-slate-900 shadow-sm sm:p-8" data-testid="receipt-card">
        {/* Header */}
        <header className="flex flex-wrap items-start justify-between gap-4 border-b-2 border-primary pb-5">
          <div>
            <img src={LOGO_FULL} alt={BRAND_NAME} className="h-14 w-auto object-contain" data-testid="receipt-logo" />
            <p className="mt-2 text-xs text-slate-500">Supplier bahan baku B2B &middot; Harga transparan &middot; Pengiriman terjadwal</p>
          </div>
          <div className="text-right">
            <p className="font-display text-2xl font-bold uppercase tracking-wide text-primary">Struk Pesanan</p>
            <p className="mt-1 font-mono text-sm font-semibold" data-testid="receipt-order-number">{order.order_number}</p>
            <p className="text-xs text-slate-500">{formatDate(order.created_at)}</p>
            <span className={`mt-2 inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-semibold ${isPaid ? "border-emerald-300 bg-emerald-50 text-emerald-800" : isCod ? "border-sky-300 bg-sky-50 text-sky-800" : "border-amber-300 bg-amber-50 text-amber-800"}`} data-testid="receipt-payment-status">
              {isPaid ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Clock3 className="h-3.5 w-3.5" />}
              {isPaid ? "LUNAS" : isCod ? "BAYAR DI TEMPAT (COD)" : order.payment_status === "piutang" ? "BELUM BAYAR / PIUTANG" : PAYMENT_STATUS_LABEL[order.payment_status]?.toUpperCase() || order.payment_status}
            </span>
          </div>
        </header>

        {/* Parties */}
        <section className="mt-5 grid gap-4 text-sm sm:grid-cols-2">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Pembeli</p>
            <p className="mt-1 font-semibold" data-testid="receipt-customer-name">{order.customer_name}</p>
            <p className="text-slate-600">{order.phone}</p>
            <p className="text-slate-600">{order.address}</p>
            {order.notes && <p className="mt-1 text-xs italic text-slate-500">Catatan: {order.notes}</p>}
          </div>
          <div className="sm:text-right">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Pembayaran</p>
            <p className="mt-1 font-semibold">{PAYMENT_METHOD_LABEL[order.payment_method] || order.payment_method}{order.payment_channel ? ` - ${CHANNEL_LABEL[order.payment_channel] || order.payment_channel}` : ""}</p>
            {order.payment_ref && <p className="break-all text-xs text-slate-500">Ref: {order.payment_ref}</p>}
            {order.paid_at && <p className="text-xs text-emerald-700">Dibayar {formatDate(order.paid_at)}</p>}
            <p className="mt-1 text-xs text-slate-500">Status pesanan: {ORDER_STATUS_LABEL[order.order_status] || order.order_status}</p>
          </div>
        </section>

        {/* Items */}
        <table className="mt-6 w-full text-sm" data-testid="receipt-items-table">
          <thead>
            <tr className="border-b bg-slate-50 text-left text-[11px] uppercase tracking-wider text-slate-500">
              <th className="py-2 pl-2 font-semibold">Produk</th>
              <th className="py-2 text-right font-semibold">Qty</th>
              <th className="py-2 text-right font-semibold">Harga</th>
              <th className="py-2 pr-2 text-right font-semibold">Subtotal</th>
            </tr>
          </thead>
          <tbody>
            {order.items.map((it, i) => (
              <tr key={it.id} className="border-b border-dashed">
                <td className="py-2.5 pl-2"><span className="text-slate-400">{i + 1}.</span> <span className="font-medium">{it.product_name}</span></td>
                <td className="py-2.5 text-right whitespace-nowrap">{it.qty} {it.unit}</td>
                <td className="py-2.5 text-right whitespace-nowrap">{rupiah(it.price)}</td>
                <td className="py-2.5 pr-2 text-right font-medium whitespace-nowrap">{rupiah(it.subtotal)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Totals */}
        <section className="mt-4 flex justify-end">
          <dl className="w-full max-w-xs space-y-1.5 text-sm">
            <div className="flex justify-between"><dt className="text-slate-500">Subtotal</dt><dd>{rupiah(order.subtotal)}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Ongkir</dt><dd>{Number(order.shipping_fee) > 0 ? rupiah(order.shipping_fee) : "Gratis"}</dd></div>
            <div className="flex justify-between border-t-2 border-primary pt-2 font-display text-lg font-bold"><dt>Total</dt><dd className="text-primary" data-testid="receipt-total">{rupiah(order.total)}</dd></div>
          </dl>
        </section>

        <footer className="mt-8 flex flex-wrap items-end justify-between gap-4 border-t pt-4 text-xs text-slate-500">
          <div>
            <p className="font-semibold text-slate-700">Terima kasih telah berbelanja di {BRAND_NAME}.</p>
            <p>{BRAND_TAGLINE}. Simpan struk ini sebagai bukti pemesanan.</p>
          </div>
          <div className="h-1.5 w-32 rounded-full bg-gradient-to-r from-primary to-brand-yellow" />
        </footer>
      </article>

      <p className="no-print mt-4 text-center text-xs text-muted-foreground">
        Tips: pada dialog cetak pilih tujuan <b>"Simpan sebagai PDF"</b> untuk mengunduh struk. <Link to={`/pesanan/${order.order_number}`} className="text-primary hover:underline">Lihat detail pesanan</Link>
      </p>
    </div>
  );
}
