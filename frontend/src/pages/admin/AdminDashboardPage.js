import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ClipboardList, Clock3, Wallet, Package, Users, AlertTriangle, Tags, CalendarDays } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import { useAdminGuard } from "@/hooks/useAdminGuard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PaymentStatusBadge, OrderStatusBadge } from "@/components/StatusBadge";
import { rupiah, formatDate, ORDER_STATUS_LABEL } from "@/lib/format";

export default function AdminDashboardPage() {
  const guard = useAdminGuard();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/admin/dashboard").then((r) => setData(r.data)).catch((e) => { guard(e); setError(errorMessage(e)); });
  }, [guard]);

  const kpis = data
    ? [
        { label: "Total Pesanan", value: data.total_orders, icon: ClipboardList },
        { label: "Pesanan Hari Ini", value: data.orders_today, icon: CalendarDays },
        { label: "Menunggu Pembayaran", value: data.pending_payments, icon: Clock3 },
        { label: "Pendapatan Lunas", value: rupiah(data.revenue_paid), icon: Wallet },
        { label: "Produk", value: data.total_products, icon: Package },
        { label: "Kategori", value: data.total_categories, icon: Tags },
        { label: "Pelanggan", value: data.total_customers, icon: Users },
        { label: "Stok Menipis", value: data.low_stock_products, icon: AlertTriangle },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold">Dashboard</h1>
        <p className="text-sm text-muted-foreground">Ringkasan operasional toko dan pesanan.</p>
      </div>
      {error && <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error}</div>}

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {!data
          ? [...Array(8)].map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)
          : kpis.map(({ label, value, icon: I }) => (
              <Card key={label} data-testid="admin-kpi-card">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-medium text-muted-foreground">{label}</p>
                    <I className="h-4 w-4 text-primary" />
                  </div>
                  <p className="mt-2 font-display text-xl font-semibold sm:text-2xl">{value}</p>
                </CardContent>
              </Card>
            ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-12">
        <Card className="lg:col-span-8">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-base">Pesanan Terbaru</CardTitle>
            <Link to="/admin/pesanan" className="text-sm font-medium text-primary hover:underline">Lihat semua</Link>
          </CardHeader>
          <CardContent className="p-0">
            {!data ? (
              <div className="space-y-2 p-4">{[...Array(4)].map((_, i) => <Skeleton key={i} className="h-10" />)}</div>
            ) : data.recent_orders.length === 0 ? (
              <p className="p-6 text-center text-sm text-muted-foreground">Belum ada pesanan.</p>
            ) : (
              <Table data-testid="admin-recent-orders-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>No. Pesanan</TableHead>
                    <TableHead>Pelanggan</TableHead>
                    <TableHead>Total</TableHead>
                    <TableHead>Pembayaran</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.recent_orders.map((o) => (
                    <TableRow key={o.id}>
                      <TableCell>
                        <p className="font-medium">{o.order_number}</p>
                        <p className="text-xs text-muted-foreground">{formatDate(o.created_at)}</p>
                      </TableCell>
                      <TableCell>{o.customer_name}</TableCell>
                      <TableCell className="font-medium">{rupiah(o.total)}</TableCell>
                      <TableCell><PaymentStatusBadge status={o.payment_status} /></TableCell>
                      <TableCell><OrderStatusBadge status={o.order_status} /></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
        <Card className="lg:col-span-4">
          <CardHeader className="pb-3"><CardTitle className="text-base">Status Pesanan</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {!data ? [...Array(5)].map((_, i) => <Skeleton key={i} className="h-6" />) : Object.keys(ORDER_STATUS_LABEL).map((k) => {
              const v = data.status_breakdown[k] || 0;
              const pct = data.total_orders ? Math.round((v / data.total_orders) * 100) : 0;
              return (
                <div key={k}>
                  <div className="flex justify-between text-sm"><span>{ORDER_STATUS_LABEL[k]}</span><span className="font-semibold">{v}</span></div>
                  <div className="mt-1 h-2 rounded-full bg-muted"><div className="h-2 rounded-full bg-primary" style={{ width: `${pct}%` }} /></div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
