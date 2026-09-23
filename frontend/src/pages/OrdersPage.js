import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ClipboardList, ChevronRight, LogIn } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/EmptyState";
import { PaymentStatusBadge, OrderStatusBadge } from "@/components/StatusBadge";
import { rupiah, formatDate, PAYMENT_METHOD_LABEL } from "@/lib/format";

export default function OrdersPage() {
  const { user, checking } = useAuth();
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (checking) return;
    if (!user) {
      setLoading(false);
      return;
    }
    setLoading(true);
    api
      .get("/orders/me")
      .then((r) => setOrders(r.data))
      .catch((e) => setError(errorMessage(e, "Gagal memuat riwayat pesanan")))
      .finally(() => setLoading(false));
  }, [user, checking]);

  if (!checking && !user) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
        <EmptyState
          icon={LogIn}
          title="Masuk untuk melihat riwayat pesanan"
          description="Gunakan Nama / Nama usaha dan No. Telp/WA yang sama seperti saat checkout."
          actionLabel="Masuk"
          onAction={() => navigate("/masuk")}
          testId="orders-login-prompt"
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 sm:py-10">
      <div className="mb-6">
        <h1 className="font-display text-2xl font-semibold sm:text-3xl">Riwayat Pesanan</h1>
        {user && <p className="mt-1 text-sm text-muted-foreground">{user.full_name} &middot; ID: {user.username}</p>}
      </div>

      {error && <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error}</div>}

      {loading || checking ? (
        <div className="space-y-3">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-24 w-full rounded-xl" />)}</div>
      ) : orders.length === 0 ? (
        <EmptyState icon={ClipboardList} title="Belum ada pesanan" description="Pesanan yang Anda buat akan muncul di sini." actionLabel="Mulai Belanja" onAction={() => navigate("/")} testId="orders-empty-state" />
      ) : (
        <ul className="space-y-3" data-testid="order-history-list">
          {orders.map((o) => (
            <li key={o.id}>
              <Link to={`/pesanan/${o.order_number}`} data-testid="order-history-item">
                <Card className="flex items-center gap-4 p-4 transition-shadow hover:shadow-md sm:p-5">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-display font-semibold">{o.order_number}</p>
                      <PaymentStatusBadge status={o.payment_status} />
                      <OrderStatusBadge status={o.order_status} />
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {formatDate(o.created_at)} &middot; {o.items.length} produk &middot; {PAYMENT_METHOD_LABEL[o.payment_method]}
                    </p>
                    <p className="mt-1 truncate text-sm text-muted-foreground">{o.items.map((i) => `${i.product_name} x${i.qty}`).join(", ")}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-display text-lg font-semibold">{rupiah(o.total)}</p>
                    {o.payment_status === "pending" && (
                      <Button size="sm" variant="secondary" className="mt-1" onClick={(e) => { e.preventDefault(); navigate(`/pembayaran/${o.order_number}`); }} data-testid="order-pay-now-button">
                        Bayar Sekarang
                      </Button>
                    )}
                  </div>
                  <ChevronRight className="hidden h-5 w-5 text-muted-foreground sm:block" />
                </Card>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
