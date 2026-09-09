import { useCallback, useEffect, useState } from "react";
import { HandCoins, Search, Loader2, CheckCircle2, AlertTriangle, Users, Wallet, History, Eye } from "lucide-react";
import { toast } from "sonner";
import { api, errorMessage } from "@/lib/api";
import { useAdminGuard } from "@/hooks/useAdminGuard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { PaymentStatusBadge, OrderStatusBadge } from "@/components/StatusBadge";
import { rupiah, formatDate, daysSince, SETTLE_METHOD_LABEL, PAYMENT_METHOD_LABEL } from "@/lib/format";
import { cn } from "@/lib/utils";

export default function AdminReceivablesPage() {
  const guard = useAdminGuard();
  const [data, setData] = useState(null);
  const [q, setQ] = useState("");
  const [settle, setSettle] = useState(null); // order
  const [detail, setDetail] = useState(null);
  const [form, setForm] = useState({ method: "cash", note: "" });
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    api.get("/admin/receivables", { params: q.trim() ? { q: q.trim() } : {} }).then((r) => setData(r.data)).catch((e) => { if (!guard(e)) toast.error(errorMessage(e)); });
  }, [guard, q]);

  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
  }, [load]);

  useEffect(() => {
    window.addEventListener("admin:event", load);
    return () => window.removeEventListener("admin:event", load);
  }, [load]);

  const openSettle = (o) => { setForm({ method: "cash", note: "" }); setSettle(o); };

  const submitSettle = async (e) => {
    e.preventDefault();
    if (!settle) return;
    setSaving(true);
    try {
      await api.post(`/admin/orders/${settle.id}/settle`, { method: form.method, note: form.note || null });
      toast.success(`Piutang ${settle.order_number} ditandai LUNAS`, { description: `${settle.customer_name} - ${rupiah(settle.total)}` });
      setSettle(null);
      setDetail(null);
      load();
    } catch (err) {
      if (!guard(err)) toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const kpis = data ? [
    { key: "total", label: "Total Piutang Berjalan", value: rupiah(data.total), icon: Wallet, cls: "border-violet-200 bg-violet-600 text-white", hint: `${data.count} pesanan belum dibayar`, hintCls: "text-white/80" },
    { key: "customers", label: "Pelanggan Berpiutang", value: data.by_customer.length, icon: Users, cls: "bg-card", hint: "Rekap per pelanggan di bawah" },
    { key: "overdue", label: "Lebih dari 14 Hari", value: data.overdue_count, icon: AlertTriangle, cls: data.overdue_count ? "border-rose-200 bg-rose-50" : "bg-card", valueCls: data.overdue_count ? "text-rose-800" : "", hint: "Perlu ditagih segera" },
    { key: "settled", label: "Piutang Sudah Dilunasi", value: rupiah(data.settled_total), icon: History, cls: "border-emerald-200 bg-emerald-50", valueCls: "text-emerald-800", hint: `${data.settled_count} pesanan (histori)` },
  ] : [];

  return (
    <div className="space-y-5" data-testid="receivables-page">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 font-display text-2xl font-semibold"><HandCoins className="h-6 w-6 text-primary" /> Piutang (Bayar Nanti)</h1>
          <p className="text-sm text-muted-foreground">Pesanan pelanggan yang mengambil barang dulu dan bayar belakangan (kasbon). Tandai lunas setelah pembayaran diterima.</p>
        </div>
      </div>

      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4" data-testid="receivables-summary">
        {!data
          ? [...Array(4)].map((_, i) => <Skeleton key={i} className="h-28 rounded-xl" />)
          : kpis.map(({ key, label, value, icon: I, cls, valueCls, hint, hintCls }) => (
              <Card key={key} className={cn("border", cls)} data-testid={`receivables-kpi-${key}`}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <p className={cn("text-xs font-medium", key === "total" ? "text-white/80" : "text-muted-foreground")}>{label}</p>
                    <I className={cn("h-4 w-4", key === "total" ? "text-brand-yellow" : "text-primary")} />
                  </div>
                  <p className={cn("mt-2 break-words font-display text-lg font-semibold sm:text-2xl", valueCls)} data-testid={`receivables-kpi-${key}-value`}>{value}</p>
                  <p className={cn("mt-1 text-[11px]", hintCls || "text-muted-foreground")}>{hint}</p>
                </CardContent>
              </Card>
            ))}
      </section>

      <div className="grid gap-4 lg:grid-cols-12">
        <Card className="lg:col-span-4" data-testid="receivables-by-customer">
          <CardHeader className="pb-3"><CardTitle className="text-base">Rekap per Pelanggan</CardTitle></CardHeader>
          <CardContent className="p-0">
            {!data ? (
              <div className="space-y-2 p-4">{[...Array(4)].map((_, i) => <Skeleton key={i} className="h-10" />)}</div>
            ) : data.by_customer.length === 0 ? (
              <p className="p-6 text-center text-sm text-muted-foreground">Tidak ada piutang berjalan.</p>
            ) : (
              <ul className="divide-y">
                {data.by_customer.map((c) => (
                  <li key={c.user_id || c.phone} className="flex items-center justify-between gap-3 px-4 py-3 text-sm" data-testid="receivable-customer-row">
                    <div className="min-w-0">
                      <p className="truncate font-medium">{c.customer_name}</p>
                      <p className="text-xs text-muted-foreground">{c.phone} &middot; {c.orders} pesanan &middot; terlama {daysSince(c.oldest_at)} hari</p>
                    </div>
                    <span className="shrink-0 font-semibold text-violet-800">{rupiah(c.total)}</span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card className="overflow-hidden lg:col-span-8" data-testid="receivables-table-card">
          <CardHeader className="flex flex-col gap-3 pb-3 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle className="text-base">Daftar Pesanan Piutang {data && <Badge variant="secondary" className="ml-2 rounded-md">{data.orders.length}</Badge>}</CardTitle>
            <div className="relative sm:w-72">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cari no. pesanan / nama / telp..." className="bg-card pl-9" data-testid="receivables-search" />
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {!data ? (
              <div className="space-y-2 p-4">{[...Array(5)].map((_, i) => <Skeleton key={i} className="h-12" />)}</div>
            ) : data.orders.length === 0 ? (
              <div className="flex flex-col items-center gap-2 p-10 text-center text-sm text-muted-foreground" data-testid="receivables-empty">
                <CheckCircle2 className="h-8 w-8 text-emerald-500" />
                <p className="font-medium text-foreground">Semua piutang sudah lunas</p>
                <p>Pesanan dengan metode "Bayar Nanti" atau status "Belum Bayar / Piutang" akan muncul di sini.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table data-testid="receivables-table">
                  <TableHeader>
                    <TableRow>
                      <TableHead>No. Pesanan</TableHead>
                      <TableHead>Pelanggan</TableHead>
                      <TableHead>Umur</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Tagihan</TableHead>
                      <TableHead className="text-right">Aksi</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.orders.map((o) => {
                      const age = daysSince(o.created_at);
                      return (
                        <TableRow key={o.id} data-testid="receivable-row" className="cursor-pointer" onClick={() => setDetail(o)}>
                          <TableCell>
                            <p className="font-medium">{o.order_number}</p>
                            <p className="text-xs text-muted-foreground">{formatDate(o.created_at)}</p>
                          </TableCell>
                          <TableCell>
                            <p className="font-medium">{o.customer_name}</p>
                            <p className="text-xs text-muted-foreground">{o.phone}</p>
                          </TableCell>
                          <TableCell>
                            <span className={cn("inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium", age > 14 ? "border-rose-200 bg-rose-50 text-rose-800" : age > 7 ? "border-amber-200 bg-amber-50 text-amber-800" : "border-border bg-muted text-muted-foreground")}>
                              {age} hari
                            </span>
                          </TableCell>
                          <TableCell><OrderStatusBadge status={o.order_status} /></TableCell>
                          <TableCell className="text-right font-semibold text-violet-800">{rupiah(o.total)}</TableCell>
                          <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                            <div className="flex justify-end gap-1">
                              <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Detail" onClick={() => setDetail(o)} data-testid="receivable-detail-button"><Eye className="h-4 w-4" /></Button>
                              <Button size="sm" className="gap-1.5 bg-emerald-600 text-white hover:bg-emerald-700" onClick={() => openSettle(o)} data-testid="receivable-settle-button">
                                <CheckCircle2 className="h-3.5 w-3.5" /> Tandai Lunas
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Detail sheet */}
      <Sheet open={!!detail} onOpenChange={(o) => !o && setDetail(null)}>
        <SheetContent className="w-full overflow-y-auto bg-background sm:max-w-lg" data-testid="receivable-detail-sheet">
          {detail && (
            <>
              <SheetHeader className="text-left">
                <SheetTitle className="font-display">{detail.order_number}</SheetTitle>
                <SheetDescription>{formatDate(detail.created_at)} &middot; {daysSince(detail.created_at)} hari lalu</SheetDescription>
              </SheetHeader>
              <div className="mt-5 space-y-4 text-sm">
                <div className="flex flex-wrap gap-2"><PaymentStatusBadge status={detail.payment_status} /><OrderStatusBadge status={detail.order_status} /></div>
                <div className="rounded-xl border bg-card p-4">
                  <p className="font-semibold">{detail.customer_name}</p>
                  <p className="text-muted-foreground">{detail.phone}</p>
                  <p className="text-muted-foreground">{detail.address}</p>
                  {detail.notes && <p className="mt-2 text-xs italic text-muted-foreground">Catatan: {detail.notes}</p>}
                  <p className="mt-2 text-xs text-muted-foreground">Metode awal: {PAYMENT_METHOD_LABEL[detail.payment_method] || detail.payment_method}</p>
                </div>
                <div className="rounded-xl border bg-card p-4">
                  <p className="mb-2 font-semibold">Item ({detail.items.length})</p>
                  <ul className="space-y-1.5">
                    {detail.items.map((it) => (
                      <li key={it.id} className="flex justify-between gap-2">
                        <span className="min-w-0 truncate">{it.product_name} <span className="text-muted-foreground">x{it.qty} {it.unit}</span></span>
                        <span className="shrink-0">{rupiah(it.subtotal)}</span>
                      </li>
                    ))}
                  </ul>
                  <Separator className="my-3" />
                  {Number(detail.shipping_fee) > 0 && <div className="flex justify-between text-muted-foreground"><span>Ongkir</span><span>{rupiah(detail.shipping_fee)}</span></div>}
                  <div className="flex justify-between font-semibold"><span>Total Tagihan</span><span className="font-display text-base text-violet-800">{rupiah(detail.total)}</span></div>
                </div>
                <Button className="w-full gap-2 bg-emerald-600 text-white hover:bg-emerald-700" onClick={() => openSettle(detail)} data-testid="receivable-sheet-settle-button">
                  <CheckCircle2 className="h-4 w-4" /> Tandai Lunas
                </Button>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>

      {/* Settle dialog */}
      <Dialog open={!!settle} onOpenChange={(o) => !o && setSettle(null)}>
        <DialogContent className="bg-card sm:max-w-md" data-testid="settle-dialog">
          {settle && (
            <form onSubmit={submitSettle} className="space-y-4">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2 font-display"><CheckCircle2 className="h-5 w-5 text-emerald-600" /> Konfirmasi Pelunasan</DialogTitle>
                <DialogDescription>
                  {settle.order_number} &middot; {settle.customer_name} &middot; <b className="text-foreground">{rupiah(settle.total)}</b>
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-1.5">
                <Label>Diterima melalui *</Label>
                <Select value={form.method} onValueChange={(v) => setForm({ ...form, method: v })}>
                  <SelectTrigger data-testid="settle-method-select"><SelectValue /></SelectTrigger>
                  <SelectContent>{Object.entries(SETTLE_METHOD_LABEL).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Catatan</Label>
                <Textarea rows={2} placeholder="mis. Transfer BCA 09/09, diterima oleh Budi" value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} data-testid="settle-note" />
              </div>
              <p className="text-xs text-muted-foreground">Pesanan akan berstatus <b>Lunas</b>, tercatat di transaksi pembayaran & audit log, dan masuk perhitungan penjualan/laporan.</p>
              <DialogFooter>
                <Button type="button" variant="ghost" onClick={() => setSettle(null)}>Batal</Button>
                <Button type="submit" disabled={saving} className="gap-2 bg-emerald-600 text-white hover:bg-emerald-700" data-testid="settle-submit">
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />} Tandai Lunas
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
