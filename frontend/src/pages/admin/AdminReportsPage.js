import { useCallback, useEffect, useMemo, useState } from "react";
import { Navigate } from "react-router-dom";
import { toast } from "sonner";
import {
  FileBarChart2, FileSpreadsheet, FileText, CalendarRange, Wallet, Coins, TrendingUp, TrendingDown, ReceiptText, ArrowUpDown, ArrowUp, ArrowDown,
  Loader2, RefreshCw, Percent, PackageCheck, Info,
} from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip as ChartTooltip, CartesianGrid, Legend } from "recharts";
import { api, errorMessage } from "@/lib/api";
import { useAdminGuard } from "@/hooks/useAdminGuard";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PaymentStatusBadge, OrderStatusBadge } from "@/components/StatusBadge";
import { rupiah, formatDate, PAYMENT_METHOD_LABEL, CHANNEL_LABEL } from "@/lib/format";
import { cn } from "@/lib/utils";

/* ---------------- date helpers (tanggal lokal, tanpa timezone shift) ---------------- */
const pad = (n) => String(n).padStart(2, "0");
const toISO = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const today = () => new Date();
const PRESETS = [
  { key: "today", label: "Hari Ini", range: () => { const t = today(); return [toISO(t), toISO(t)]; } },
  { key: "7d", label: "7 Hari Terakhir", range: () => { const t = today(); const s = new Date(t); s.setDate(t.getDate() - 6); return [toISO(s), toISO(t)]; } },
  { key: "30d", label: "30 Hari Terakhir", range: () => { const t = today(); const s = new Date(t); s.setDate(t.getDate() - 29); return [toISO(s), toISO(t)]; } },
  { key: "month", label: "Bulan Ini", range: () => { const t = today(); return [toISO(new Date(t.getFullYear(), t.getMonth(), 1)), toISO(t)]; } },
  { key: "lastMonth", label: "Bulan Lalu", range: () => { const t = today(); return [toISO(new Date(t.getFullYear(), t.getMonth() - 1, 1)), toISO(new Date(t.getFullYear(), t.getMonth(), 0))]; } },
  { key: "year", label: "Tahun Ini", range: () => { const t = today(); return [toISO(new Date(t.getFullYear(), 0, 1)), toISO(t)]; } },
];
const longDate = (iso) => (iso ? new Date(`${iso}T00:00:00`).toLocaleDateString("id-ID", { day: "numeric", month: "long", year: "numeric" }) : "-");
const shortDay = (iso) => new Date(`${iso}T00:00:00`).toLocaleDateString("id-ID", { day: "2-digit", month: "short" });
const compact = (n) => new Intl.NumberFormat("id-ID", { notation: "compact", maximumFractionDigits: 1 }).format(n);

const COLUMNS = [
  { key: "order_number", label: "No. Pesanan", sortable: true },
  { key: "created_at", label: "Tanggal", sortable: true },
  { key: "customer_name", label: "Nama Pembeli", sortable: true },
  { key: "payment_method", label: "Pembayaran", sortable: true },
  { key: "items_count", label: "Item", sortable: true, align: "right" },
  { key: "total", label: "Total Penjualan", sortable: true, align: "right" },
  { key: "cost", label: "Modal (HPP)", sortable: true, align: "right" },
  { key: "profit", label: "Laba", sortable: true, align: "right" },
  { key: "margin_pct", label: "Margin", sortable: true, align: "right" },
];

function parseFilename(headers, fallback) {
  const cd = headers?.["content-disposition"] || "";
  const m = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(cd);
  return m ? decodeURIComponent(m[1]) : fallback;
}

export default function AdminReportsPage() {
  const guard = useAdminGuard();
  const { isOwner, admin } = useAuth();
  const [preset, setPreset] = useState("month");
  const [[start, end], setRange] = useState(() => PRESETS[3].range());
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sort, setSort] = useState({ key: "created_at", dir: "desc" });
  const [downloading, setDownloading] = useState(null); // "xlsx" | "pdf" | null

  const rangeInvalid = !start || !end || start > end;

  const load = useCallback(() => {
    if (rangeInvalid) return;
    setLoading(true);
    setError("");
    api.get("/admin/reports/sales", { params: { start, end } })
      .then((r) => setReport(r.data))
      .catch((e) => { if (!guard(e)) { setError(errorMessage(e)); toast.error(errorMessage(e)); } })
      .finally(() => setLoading(false));
  }, [start, end, rangeInvalid, guard]);

  useEffect(() => {
    if (!isOwner) return undefined;
    const t = setTimeout(load, 200);
    return () => clearTimeout(t);
  }, [load, isOwner]);

  const applyPreset = (p) => { setPreset(p.key); setRange(p.range()); };
  const setStart = (v) => { setPreset(""); setRange([v, end]); };
  const setEnd = (v) => { setPreset(""); setRange([start, v]); };

  const toggleSort = (key) => setSort((s) => (s.key === key ? { key, dir: s.dir === "asc" ? "desc" : "asc" } : { key, dir: key === "customer_name" || key === "order_number" || key === "payment_method" ? "asc" : "desc" }));

  const sortedRows = useMemo(() => {
    if (!report) return [];
    const rows = [...report.rows];
    const { key, dir } = sort;
    rows.sort((a, b) => {
      let va = a[key], vb = b[key];
      if (key === "created_at") { va = new Date(va).getTime(); vb = new Date(vb).getTime(); }
      if (typeof va === "string") return dir === "asc" ? va.localeCompare(vb, "id") : vb.localeCompare(va, "id");
      return dir === "asc" ? va - vb : vb - va;
    });
    return rows;
  }, [report, sort]);

  const download = async (fmt) => {
    if (rangeInvalid) return toast.error("Rentang tanggal tidak valid");
    setDownloading(fmt);
    try {
      const res = await api.get(`/admin/reports/sales/export.${fmt}`, { params: { start, end }, responseType: "blob", timeout: 120000 });
      const name = parseFilename(res.headers, `Laporan-Penjualan-Semoyo-Joyo_${start}_${end}.${fmt}`);
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 4000);
      toast.success(`${fmt === "xlsx" ? "Excel" : "PDF"} berhasil diunduh`, { description: name });
    } catch (e) {
      if (!guard(e)) {
        let msg = errorMessage(e, "Gagal mengunduh laporan");
        try { if (e?.response?.data instanceof Blob) { const j = JSON.parse(await e.response.data.text()); if (j?.detail) msg = j.detail; } } catch { /* ignore */ }
        toast.error(msg);
      }
    } finally {
      setDownloading(null);
    }
  };

  if (!isOwner) return <Navigate to="/admin/dashboard" replace />;

  const sm = report?.summary;
  const isLoss = sm ? sm.net_profit < 0 : false;
  const kpis = sm
    ? [
        { key: "revenue", label: "Total Pendapatan Kotor", value: rupiah(sm.gross_revenue), icon: Wallet, cls: "border-primary/30 bg-primary text-primary-foreground", iconCls: "text-brand-yellow", hint: `${sm.items_sold} item terjual` },
        { key: "cost", label: "Total Modal (HPP)", value: rupiah(sm.total_cost), icon: Coins, cls: "bg-card", iconCls: "text-amber-600", hint: "Harga beli x jumlah terjual" },
        { key: "profit", label: isLoss ? "Total Rugi Bersih" : "Total Laba Bersih", value: `${isLoss ? "-" : ""}${rupiah(Math.abs(sm.net_profit))}`, icon: isLoss ? TrendingDown : TrendingUp, cls: isLoss ? "border-rose-200 bg-rose-50" : "border-emerald-200 bg-emerald-50", iconCls: isLoss ? "text-rose-700" : "text-emerald-700", valueCls: isLoss ? "text-rose-800" : "text-emerald-800", hint: `Margin ${sm.margin_pct}%` },
        { key: "orders", label: "Jumlah Pesanan Lunas", value: sm.paid_orders, icon: ReceiptText, cls: "border-brand-yellow/60 bg-accent", iconCls: "text-amber-700", hint: sm.paid_orders ? `Rata-rata ${rupiah(sm.avg_order_value)} / pesanan` : "Belum ada pesanan lunas" },
      ]
    : [];

  const SortIcon = ({ col }) => {
    if (sort.key !== col) return <ArrowUpDown className="h-3.5 w-3.5 opacity-40" />;
    return sort.dir === "asc" ? <ArrowUp className="h-3.5 w-3.5 text-primary" /> : <ArrowDown className="h-3.5 w-3.5 text-primary" />;
  };

  return (
    <div className="space-y-5" data-testid="reports-page">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 font-display text-2xl font-semibold"><FileBarChart2 className="h-6 w-6 text-primary" /> Laporan Penjualan</h1>
          <p className="text-sm text-muted-foreground">Rekap pendapatan, modal (HPP), dan laba bersih dari pesanan lunas / COD selesai. Khusus Owner.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" className="gap-2" onClick={load} disabled={loading || rangeInvalid} data-testid="reports-refresh">
            <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} /> Muat ulang
          </Button>
          <Button variant="outline" size="sm" className="gap-2 border-emerald-300 bg-emerald-50 text-emerald-800 hover:bg-emerald-100 hover:text-emerald-900" onClick={() => download("xlsx")} disabled={!!downloading || rangeInvalid || !report} data-testid="reports-download-excel">
            {downloading === "xlsx" ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileSpreadsheet className="h-4 w-4" />} Download Excel
          </Button>
          <Button size="sm" className="gap-2" onClick={() => download("pdf")} disabled={!!downloading || rangeInvalid || !report} data-testid="reports-download-pdf">
            {downloading === "pdf" ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />} Download PDF
          </Button>
        </div>
      </div>

      {/* Filter periode */}
      <Card data-testid="reports-filter">
        <CardContent className="space-y-4 p-4 sm:p-5">
          <div className="flex items-center gap-2 text-sm font-semibold"><CalendarRange className="h-4 w-4 text-primary" /> Filter Periode</div>
          <div className="flex flex-wrap gap-2">
            {PRESETS.map((p) => (
              <button key={p.key} type="button" onClick={() => applyPreset(p)} data-testid={`reports-preset-${p.key}`}
                className={cn("rounded-full border px-3 py-1.5 text-xs font-medium transition-colors", preset === p.key ? "border-primary bg-primary text-primary-foreground shadow-sm" : "bg-card text-muted-foreground hover:border-primary/40 hover:text-foreground")}>
                {p.label}
              </button>
            ))}
          </div>
          <div className="grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
            <div className="space-y-1.5">
              <Label htmlFor="report-start">Tanggal Mulai</Label>
              <Input id="report-start" type="date" value={start} max={end || undefined} onChange={(e) => setStart(e.target.value)} className="bg-card" data-testid="reports-start-date" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="report-end">Tanggal Akhir</Label>
              <Input id="report-end" type="date" value={end} min={start || undefined} onChange={(e) => setEnd(e.target.value)} className="bg-card" data-testid="reports-end-date" />
            </div>
            <div className="rounded-lg border bg-muted/50 px-3 py-2 text-xs text-muted-foreground sm:min-w-[220px]" data-testid="reports-period-label">
              <p className="font-medium text-foreground">Periode laporan</p>
              <p>{rangeInvalid ? <span className="text-rose-600">Tanggal mulai harus sebelum tanggal akhir</span> : `${longDate(start)} - ${longDate(end)}`}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {error && <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800" data-testid="reports-error">{error}</div>}

      {/* Ringkasan */}
      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4" data-testid="reports-summary">
        {!report || loading
          ? [...Array(4)].map((_, i) => <Skeleton key={i} className="h-28 rounded-xl" />)
          : kpis.map(({ key, label, value, icon: I, cls, iconCls, valueCls, hint }) => (
              <Card key={key} className={cn("border", cls)} data-testid={`reports-kpi-${key}`}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <p className={cn("text-xs font-medium", key === "revenue" ? "text-primary-foreground/80" : "text-muted-foreground")}>{label}</p>
                    <I className={cn("h-4 w-4", iconCls)} />
                  </div>
                  <p className={cn("mt-2 break-words font-display text-lg font-semibold sm:text-2xl", valueCls)} data-testid={`reports-kpi-${key}-value`}>{value}</p>
                  <p className={cn("mt-1 text-[11px]", key === "revenue" ? "text-primary-foreground/70" : "text-muted-foreground")}>{hint}</p>
                </CardContent>
              </Card>
            ))}
      </section>

      {/* Grafik harian */}
      {report && !loading && report.daily.length > 0 && (
        <Card data-testid="reports-chart-card">
          <CardHeader className="pb-2"><CardTitle className="text-base">Tren Harian &middot; Pendapatan vs Laba</CardTitle></CardHeader>
          <CardContent className="h-64 px-2 pb-3">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={report.daily.map((d) => ({ ...d, label: shortDay(d.date) }))} margin={{ top: 8, right: 12, left: 0, bottom: 0 }} barGap={2}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E9F0" />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                <YAxis tickFormatter={compact} tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={52} />
                <ChartTooltip formatter={(v, n) => [rupiah(v), n]} labelFormatter={(l, p) => (p?.[0]?.payload ? `${longDate(p[0].payload.date)} - ${p[0].payload.orders} pesanan` : l)} contentStyle={{ borderRadius: 10, fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="revenue" name="Pendapatan" fill="#0B4EA2" radius={[4, 4, 0, 0]} />
                <Bar dataKey="profit" name="Laba" fill="#F5C400" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Tabel detail */}
      <Card className="overflow-hidden" data-testid="reports-table-card">
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2 pb-3">
          <CardTitle className="text-base">Detail Pesanan {report && !loading && <Badge variant="secondary" className="ml-2 rounded-md" data-testid="reports-row-count">{report.rows.length} pesanan</Badge>}</CardTitle>
          <p className="flex items-center gap-1 text-xs text-muted-foreground"><Info className="h-3.5 w-3.5" /> Klik judul kolom untuk mengurutkan</p>
        </CardHeader>
        <CardContent className="p-0">
          {!report || loading ? (
            <div className="space-y-2 p-4">{[...Array(6)].map((_, i) => <Skeleton key={i} className="h-10" />)}</div>
          ) : report.rows.length === 0 ? (
            <div className="flex flex-col items-center gap-2 p-10 text-center text-sm text-muted-foreground" data-testid="reports-empty">
              <PackageCheck className="h-8 w-8" />
              <p className="font-medium text-foreground">Belum ada pesanan lunas pada periode ini</p>
              <p>Coba ubah rentang tanggal, atau tunggu hingga ada pesanan yang dibayar / COD selesai.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table data-testid="reports-table">
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-10 text-center">No</TableHead>
                    {COLUMNS.map((c) => (
                      <TableHead key={c.key} className={cn(c.align === "right" && "text-right")}>
                        <button type="button" onClick={() => toggleSort(c.key)} data-testid={`reports-sort-${c.key}`} aria-sort={sort.key === c.key ? (sort.dir === "asc" ? "ascending" : "descending") : "none"}
                          className={cn("inline-flex items-center gap-1 whitespace-nowrap font-medium hover:text-foreground", c.align === "right" && "flex-row-reverse", sort.key === c.key && "text-foreground")}>
                          {c.label} <SortIcon col={c.key} />
                        </button>
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedRows.map((r, i) => (
                    <TableRow key={r.order_id} data-testid="reports-row">
                      <TableCell className="text-center text-xs text-muted-foreground">{i + 1}</TableCell>
                      <TableCell>
                        <p className="font-medium">{r.order_number}</p>
                        <div className="mt-0.5 flex gap-1"><OrderStatusBadge status={r.order_status} /></div>
                      </TableCell>
                      <TableCell className="whitespace-nowrap text-sm">
                        {formatDate(r.created_at)}
                        {r.paid_at && <p className="text-[11px] text-muted-foreground">Lunas {formatDate(r.paid_at)}</p>}
                      </TableCell>
                      <TableCell>
                        <p className="font-medium">{r.customer_name}</p>
                        <p className="text-xs text-muted-foreground">{r.phone}</p>
                      </TableCell>
                      <TableCell>
                        <p className="text-sm">{PAYMENT_METHOD_LABEL[r.payment_method] || r.payment_method}{r.payment_channel ? ` · ${CHANNEL_LABEL[r.payment_channel] || r.payment_channel.toUpperCase()}` : ""}</p>
                        <PaymentStatusBadge status={r.payment_status} />
                      </TableCell>
                      <TableCell className="text-right">{r.items_count}</TableCell>
                      <TableCell className="text-right font-medium">{rupiah(r.total)}{r.shipping_fee > 0 && <p className="text-[11px] font-normal text-muted-foreground">incl. ongkir {rupiah(r.shipping_fee)}</p>}</TableCell>
                      <TableCell className="text-right text-muted-foreground">{rupiah(r.cost)}</TableCell>
                      <TableCell className={cn("text-right font-semibold", r.profit < 0 ? "text-rose-700" : "text-emerald-700")}>{r.profit < 0 ? "-" : ""}{rupiah(Math.abs(r.profit))}</TableCell>
                      <TableCell className="text-right"><span className="inline-flex items-center gap-0.5">{r.margin_pct}<Percent className="h-3 w-3" /></span></TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="bg-accent/60 font-semibold hover:bg-accent/60" data-testid="reports-total-row">
                    <TableCell />
                    <TableCell colSpan={4}>TOTAL ({sm.paid_orders} pesanan)</TableCell>
                    <TableCell className="text-right">{sm.items_sold}</TableCell>
                    <TableCell className="text-right">{rupiah(sm.gross_revenue)}</TableCell>
                    <TableCell className="text-right">{rupiah(sm.total_cost)}</TableCell>
                    <TableCell className={cn("text-right", isLoss ? "text-rose-700" : "text-emerald-700")}>{isLoss ? "-" : ""}{rupiah(Math.abs(sm.net_profit))}</TableCell>
                    <TableCell className="text-right">{sm.margin_pct}%</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Produk terjual */}
      {report && !loading && report.top_products.length > 0 && (
        <Card data-testid="reports-products-card">
          <CardHeader className="pb-3"><CardTitle className="text-base">Produk Terjual pada Periode Ini</CardTitle></CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Produk</TableHead>
                    <TableHead className="text-right">Qty</TableHead>
                    <TableHead className="text-right">Omzet</TableHead>
                    <TableHead className="text-right">Modal</TableHead>
                    <TableHead className="text-right">Laba</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {report.top_products.map((p) => (
                    <TableRow key={p.product_name} data-testid="reports-product-row">
                      <TableCell className="font-medium">{p.product_name}</TableCell>
                      <TableCell className="text-right">{p.qty}</TableCell>
                      <TableCell className="text-right">{rupiah(p.revenue)}</TableCell>
                      <TableCell className="text-right text-muted-foreground">{rupiah(p.cost)}</TableCell>
                      <TableCell className={cn("text-right font-semibold", p.profit < 0 ? "text-rose-700" : "text-emerald-700")}>{p.profit < 0 ? "-" : ""}{rupiah(Math.abs(p.profit))}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      <p className="text-xs text-muted-foreground">Laporan dibuat oleh {admin?.full_name || "Owner"} &middot; Zona waktu WIB &middot; File unduhan diberi nama otomatis sesuai periode.</p>
    </div>
  );
}
