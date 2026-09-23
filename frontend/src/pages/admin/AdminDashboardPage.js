import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ClipboardList, Clock3, Wallet, Package, Users, AlertTriangle, Tags, CalendarDays, TrendingUp, TrendingDown, Coins, Boxes, Percent, Pencil, HandCoins, ReceiptText, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { api, errorMessage } from "@/lib/api";
import { useAdminGuard } from "@/hooks/useAdminGuard";
import { useAuth } from "@/context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PaymentStatusBadge, OrderStatusBadge } from "@/components/StatusBadge";
import { rupiah, formatDate, ORDER_STATUS_LABEL } from "@/lib/format";

export default function AdminDashboardPage() {
  const guard = useAdminGuard();
  const { isOwner } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = () => api.get("/admin/dashboard").then((r) => setData(r.data)).catch((e) => { guard(e); setError(errorMessage(e)); });
    load();
    window.addEventListener("admin:event", load);
    return () => window.removeEventListener("admin:event", load);
  }, [guard]);

  const kpis = data
    ? [
        { label: "Total Pesanan", value: data.total_orders, icon: ClipboardList },
        { label: "Pesanan Hari Ini", value: data.orders_today, icon: CalendarDays },
        { label: "Menunggu Pembayaran", value: data.pending_payments, icon: Clock3 },
        { label: "Produk", value: data.total_products, icon: Package },
        { label: "Kategori", value: data.total_categories, icon: Tags },
        { label: "Pelanggan", value: data.total_customers, icon: Users },
        { label: "Stok Menipis", value: data.low_stock_products, icon: AlertTriangle },
        isOwner ? { label: "Nilai Stok (Modal)", value: rupiah(data.stock_value), icon: Boxes } : { label: "Pendapatan (Omzet)", value: rupiah(data.revenue_paid), icon: Wallet },
      ]
    : [];

  const isLoss = data ? data.gross_profit < 0 : false;
  const isNetLoss = data ? data.net_profit < 0 : false;
  const finance = data
    ? [
        { key: "revenue", label: "Pendapatan (Omzet)", value: rupiah(data.revenue_paid), icon: Wallet, cls: "border-primary/30 bg-primary text-primary-foreground", iconCls: "text-brand-yellow", hint: "Lunas, COD & piutang selesai" },
        { key: "cost", label: "Total Modal (HPP)", value: rupiah(data.cost_paid), icon: Coins, cls: "bg-card", iconCls: "text-amber-600", hint: "Harga beli x jumlah terjual" },
        { key: "profit", label: isLoss ? "Rugi Kotor" : "Laba Kotor", value: `${isLoss ? "-" : ""}${rupiah(Math.abs(data.gross_profit))}`, icon: isLoss ? TrendingDown : TrendingUp, cls: isLoss ? "border-rose-200 bg-rose-50" : "border-emerald-200 bg-emerald-50", iconCls: isLoss ? "text-rose-700" : "text-emerald-700", valueCls: isLoss ? "text-rose-800" : "text-emerald-800", hint: `Margin ${data.margin_pct}%` },
        { key: "expenses", label: "Pengeluaran", value: rupiah(data.total_expenses), icon: ReceiptText, cls: "bg-card", iconCls: "text-rose-600", hint: `Bulan ini ${rupiah(data.expenses_month)}`, to: "/admin/pengeluaran" },
        { key: "net", label: isNetLoss ? "Rugi Bersih" : "Laba Bersih", value: `${isNetLoss ? "-" : ""}${rupiah(Math.abs(data.net_profit))}`, icon: isNetLoss ? TrendingDown : TrendingUp, cls: isNetLoss ? "border-rose-300 bg-rose-100" : "border-brand-yellow/60 bg-accent", iconCls: isNetLoss ? "text-rose-700" : "text-amber-700", valueCls: isNetLoss ? "text-rose-900" : "", hint: "Laba kotor - pengeluaran" },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold">Dashboard</h1>
        <p className="text-sm text-muted-foreground">Ringkasan operasional toko dan pesanan.</p>
      </div>
      {error && <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error}</div>}

      {/* Keuangan: Laba / Rugi otomatis (khusus Owner) */}
      {isOwner && (
      <section className="space-y-3" data-testid="finance-section">
        <div className="flex items-center gap-2">
          <h2 className="font-display text-base font-semibold">Keuangan &middot; Laba / Rugi</h2>
          <span className="rounded-full bg-secondary px-2 py-0.5 text-[11px] font-medium text-muted-foreground">dihitung dari pesanan lunas / COD & piutang selesai, dikurangi pengeluaran</span>
        </div>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
          {!data
            ? [...Array(5)].map((_, i) => <Skeleton key={i} className="h-28 rounded-xl" />)
            : finance.map(({ key, label, value, icon: I, cls, iconCls, valueCls, hint }) => (
                <Card key={key} className={cn("border", cls)} data-testid={`finance-kpi-${key}`}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <p className={cn("text-xs font-medium", key === "revenue" ? "text-primary-foreground/80" : "text-muted-foreground")}>{label}</p>
                      <I className={cn("h-4 w-4", iconCls)} />
                    </div>
                    <p className={cn("mt-2 break-words font-display text-lg font-semibold sm:text-2xl", valueCls)}>{value}</p>
                    <p className={cn("mt-1 text-[11px]", key === "revenue" ? "text-primary-foreground/70" : "text-muted-foreground")}>{hint}</p>
                  </CardContent>
                </Card>
              ))}
        </div>
      </section>
      )}

      {data && data.receivables_count > 0 && (
        <Link to="/admin/piutang" className="block" data-testid="dashboard-receivables-banner">
          <div className="flex flex-col gap-3 rounded-2xl border border-violet-200 bg-violet-50 px-5 py-4 text-violet-900 transition-colors hover:bg-violet-100 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-violet-600 text-white"><HandCoins className="h-5 w-5" /></span>
              <div>
                <p className="font-display text-base font-semibold">Piutang berjalan {rupiah(data.receivables_total)}</p>
                <p className="text-sm text-violet-800">{data.receivables_count} pesanan belum dibayar (bayar nanti / kasbon). Tandai lunas setelah pembayaran diterima.</p>
              </div>
            </div>
            <span className="inline-flex items-center gap-1 text-sm font-semibold">Kelola piutang <ArrowRight className="h-4 w-4" /></span>
          </div>
        </Link>
      )}

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
                  <p className="mt-2 break-words font-display text-lg font-semibold sm:text-2xl">{value}</p>
                </CardContent>
              </Card>
            ))}
      </div>

      {isOwner && (
      <Card data-testid="profit-by-product-card">
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="text-base">Laba per Produk (Top 10)</CardTitle>
          <Link to="/admin/produk" className="text-sm font-medium text-primary hover:underline">Atur harga beli</Link>
        </CardHeader>
        <CardContent className="p-0">
          {!data ? (
            <div className="space-y-2 p-4">{[...Array(4)].map((_, i) => <Skeleton key={i} className="h-10" />)}</div>
          ) : data.profit_by_product.length === 0 ? (
            <p className="p-6 text-center text-sm text-muted-foreground">Belum ada penjualan lunas. Laba akan muncul otomatis setelah pesanan dibayar / COD selesai.</p>
          ) : (
            <div className="overflow-x-auto">
              <Table data-testid="admin-profit-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Produk</TableHead>
                    <TableHead className="text-right">Terjual</TableHead>
                    <TableHead className="text-right">Omzet</TableHead>
                    <TableHead className="text-right">Modal</TableHead>
                    <TableHead className="text-right">Laba</TableHead>
                    <TableHead className="text-right">Margin</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.profit_by_product.map((r) => (
                    <TableRow key={r.product_id || r.product_name} data-testid="admin-profit-row">
                      <TableCell className="font-medium">{r.product_name}</TableCell>
                      <TableCell className="text-right">{r.qty_sold}</TableCell>
                      <TableCell className="text-right">{rupiah(r.revenue)}</TableCell>
                      <TableCell className="text-right text-muted-foreground">{rupiah(r.cost)}</TableCell>
                      <TableCell className={cn("text-right font-semibold", r.profit < 0 ? "text-rose-700" : "text-emerald-700")}>{r.profit < 0 ? "-" : ""}{rupiah(Math.abs(r.profit))}</TableCell>
                      <TableCell className="text-right">{r.margin_pct}%</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
      )}

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
              <div className="overflow-x-auto">
              <Table data-testid="admin-recent-orders-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>No. Pesanan</TableHead>
                    <TableHead>Pelanggan</TableHead>
                    <TableHead>Total</TableHead>
                    <TableHead>Pembayaran</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Aksi</TableHead>
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
                      <TableCell className="text-right">
                        <Link to={`/admin/pesanan?q=${encodeURIComponent(o.order_number)}`}>
                          <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Kelola pesanan"><Pencil className="h-4 w-4" /></Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              </div>
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
                  <div className="mt-1 h-2 rounded-full bg-muted"><div className={cn("h-2 rounded-full", k === "selesai" ? "bg-brand-yellow" : k === "dibatalkan" ? "bg-rose-400" : "bg-primary")} style={{ width: `${pct}%` }} /></div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
