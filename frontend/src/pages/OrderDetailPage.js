import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, CreditCard, AlertTriangle } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { ProductImage } from "@/components/ProductImage";
import { PaymentStatusBadge, OrderStatusBadge } from "@/components/StatusBadge";
import { rupiah, formatDate, PAYMENT_METHOD_LABEL, CHANNEL_LABEL, ORDER_STATUS_LABEL } from "@/lib/format";
import { cn } from "@/lib/utils";

const STEPS = ["baru", "diproses", "dikirim", "selesai"];

export default function OrderDetailPage() {
  const { orderNumber } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get(`/orders/${orderNumber}`).then((r) => setOrder(r.data)).catch((e) => setError(errorMessage(e, "Pesanan tidak ditemukan")));
  }, [orderNumber]);

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 text-center">
        <AlertTriangle className="mx-auto h-10 w-10 text-amber-500" />
        <p className="mt-3 font-display text-xl font-semibold">{error}</p>
        <Button className="mt-6" onClick={() => navigate("/pesanan")}>Ke Riwayat Pesanan</Button>
      </div>
    );
  }
  if (!order) {
    return (
      <div className="mx-auto max-w-4xl space-y-4 px-4 py-10 sm:px-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  const stepIdx = order.order_status === "dibatalkan" ? -1 : STEPS.indexOf(order.order_status);

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 sm:py-10">
      <Button variant="ghost" className="mb-4 gap-2 px-2" onClick={() => navigate("/pesanan")}>
        <ArrowLeft className="h-4 w-4" /> Riwayat Pesanan
      </Button>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-semibold sm:text-3xl" data-testid="order-detail-number">{order.order_number}</h1>
          <p className="mt-1 text-sm text-muted-foreground">Dibuat {formatDate(order.created_at)}</p>
        </div>
        <div className="flex gap-2">
          <PaymentStatusBadge status={order.payment_status} className="px-3 py-1 text-sm" data-testid="order-detail-payment-status" />
          <OrderStatusBadge status={order.order_status} className="px-3 py-1 text-sm" data-testid="order-detail-order-status" />
        </div>
      </div>

      {/* Progress */}
      <Card className="mt-6">
        <CardContent className="p-5">
          {order.order_status === "dibatalkan" ? (
            <p className="text-sm font-medium text-rose-700">Pesanan ini telah dibatalkan.</p>
          ) : (
            <ol className="grid grid-cols-4 gap-2">
              {STEPS.map((s, i) => (
                <li key={s} className="flex flex-col items-center gap-2 text-center">
                  <span className={cn("h-2 w-full rounded-full", i <= stepIdx ? "bg-primary" : "bg-muted")} />
                  <span className={cn("text-xs", i <= stepIdx ? "font-semibold text-foreground" : "text-muted-foreground")}>{ORDER_STATUS_LABEL[s]}</span>
                </li>
              ))}
            </ol>
          )}
        </CardContent>
      </Card>

      {order.payment_status === "pending" && (
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
          <p className="text-sm text-amber-900">Pesanan menunggu pembayaran. Selesaikan pembayaran agar segera diproses.</p>
          <Link to={`/pembayaran/${order.order_number}`}>
            <Button size="sm" className="gap-2" data-testid="order-detail-pay-button"><CreditCard className="h-4 w-4" /> Lanjutkan Pembayaran</Button>
          </Link>
        </div>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_320px]">
        <Card>
          <CardHeader className="pb-3"><CardTitle className="font-display text-lg">Produk Dipesan</CardTitle></CardHeader>
          <CardContent>
            <ul className="divide-y">
              {order.items.map((it) => (
                <li key={it.id} className="flex items-center gap-3 py-3">
                  <div className="h-14 w-14 shrink-0 overflow-hidden rounded-lg bg-muted"><ProductImage src={it.image_url} alt={it.product_name} iconClassName="h-5 w-5" /></div>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium">{it.product_name}</p>
                    <p className="text-xs text-muted-foreground">{it.qty} {it.unit} x {rupiah(it.price)}</p>
                  </div>
                  <p className="font-semibold">{rupiah(it.subtotal)}</p>
                </li>
              ))}
            </ul>
            <Separator className="my-3" />
            <div className="space-y-1.5 text-sm">
              <div className="flex justify-between"><span className="text-muted-foreground">Subtotal</span><span>{rupiah(order.subtotal)}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Ongkir</span><span>{order.shipping_fee > 0 ? rupiah(order.shipping_fee) : "-"}</span></div>
              <div className="flex justify-between pt-1"><span className="font-semibold">Total</span><span className="font-display text-lg font-semibold">{rupiah(order.total)}</span></div>
            </div>
          </CardContent>
        </Card>
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3"><CardTitle className="text-base">Pembayaran</CardTitle></CardHeader>
            <CardContent className="space-y-1 text-sm">
              <p className="font-medium">{PAYMENT_METHOD_LABEL[order.payment_method]}{order.payment_channel ? ` - ${CHANNEL_LABEL[order.payment_channel] || order.payment_channel}` : ""}</p>
              {order.paid_at && <p className="text-muted-foreground">Lunas {formatDate(order.paid_at)}</p>}
              {order.payment_ref && <p className="break-all text-xs text-muted-foreground">Ref: {order.payment_ref}</p>}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3"><CardTitle className="text-base">Pengiriman</CardTitle></CardHeader>
            <CardContent className="space-y-1 text-sm">
              <p className="font-medium">{order.customer_name}</p>
              <p className="text-muted-foreground">{order.phone}</p>
              <p className="text-muted-foreground">{order.address}</p>
              {order.notes && <p className="pt-1 text-xs italic text-muted-foreground">Catatan: {order.notes}</p>}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
