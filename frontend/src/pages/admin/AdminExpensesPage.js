import { useCallback, useEffect, useState } from "react";
import { ReceiptText, Plus, Pencil, Trash2, Loader2, Search, CalendarRange, Truck, Wallet, Layers, Save } from "lucide-react";
import { toast } from "sonner";
import { api, errorMessage } from "@/lib/api";
import { useAdminGuard } from "@/hooks/useAdminGuard";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { rupiah, formatDateOnly, EXPENSE_CATEGORY_LABEL } from "@/lib/format";
import { cn } from "@/lib/utils";

const pad = (n) => String(n).padStart(2, "0");
const toISO = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const today = () => new Date();
const PRESETS = [
  { key: "today", label: "Hari Ini", range: () => { const t = today(); return [toISO(t), toISO(t)]; } },
  { key: "7d", label: "7 Hari", range: () => { const t = today(); const s = new Date(t); s.setDate(t.getDate() - 6); return [toISO(s), toISO(t)]; } },
  { key: "month", label: "Bulan Ini", range: () => { const t = today(); return [toISO(new Date(t.getFullYear(), t.getMonth(), 1)), toISO(t)]; } },
  { key: "lastMonth", label: "Bulan Lalu", range: () => { const t = today(); return [toISO(new Date(t.getFullYear(), t.getMonth() - 1, 1)), toISO(new Date(t.getFullYear(), t.getMonth(), 0))]; } },
  { key: "year", label: "Tahun Ini", range: () => { const t = today(); return [toISO(new Date(t.getFullYear(), 0, 1)), toISO(t)]; } },
];

const EMPTY = () => ({ expense_date: toISO(today()), category: "operasional", description: "", amount: "", payment_method: "cash", reference: "", note: "" });

export default function AdminExpensesPage() {
  const guard = useAdminGuard();
  const { isOwner } = useAuth();
  const [preset, setPreset] = useState("month");
  const [[start, end], setRange] = useState(() => PRESETS[2].range());
  const [category, setCategory] = useState("all");
  const [q, setQ] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dialog, setDialog] = useState(null); // { mode: 'create'|'edit', item }
  const [form, setForm] = useState(EMPTY());
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const rangeInvalid = !start || !end || start > end;

  const load = useCallback(() => {
    if (rangeInvalid) return;
    setLoading(true);
    const params = { start, end };
    if (category !== "all") params.category = category;
    if (q.trim()) params.q = q.trim();
    api.get("/admin/expenses", { params }).then((r) => setData(r.data)).catch((e) => { if (!guard(e)) toast.error(errorMessage(e)); }).finally(() => setLoading(false));
  }, [start, end, category, q, rangeInvalid, guard]);

  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
  }, [load]);

  const applyPreset = (p) => { setPreset(p.key); setRange(p.range()); };

  const openCreate = () => { setForm(EMPTY()); setDialog({ mode: "create" }); };
  const openEdit = (item) => {
    setForm({ expense_date: item.expense_date, category: item.category, description: item.description, amount: String(Math.round(item.amount)), payment_method: item.payment_method, reference: item.reference || "", note: item.note || "" });
    setDialog({ mode: "edit", item });
  };

  const submit = async (e) => {
    e.preventDefault();
    const amount = Number(form.amount);
    if (!form.description.trim() || form.description.trim().length < 2) return toast.error("Keterangan wajib diisi");
    if (!amount || amount <= 0) return toast.error("Nominal harus lebih dari 0");
    if (!form.expense_date) return toast.error("Tanggal wajib diisi");
    setSaving(true);
    try {
      const payload = { ...form, amount, description: form.description.trim(), reference: form.reference || null, note: form.note || null };
      if (dialog.mode === "edit") {
        await api.put(`/admin/expenses/${dialog.item.id}`, payload);
        toast.success("Pengeluaran diperbarui");
      } else {
        await api.post("/admin/expenses", payload);
        toast.success("Pengeluaran dicatat", { description: `${payload.description} - ${rupiah(amount)}` });
      }
      setDialog(null);
      load();
    } catch (err) {
      if (!guard(err)) toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (!deleteTarget) return;
    try {
      await api.delete(`/admin/expenses/${deleteTarget.id}`);
      toast.success("Pengeluaran dihapus");
      setDeleteTarget(null);
      load();
    } catch (err) {
      if (!guard(err)) toast.error(errorMessage(err));
    }
  };

  const angkut = data?.by_category.find((c) => c.category === "angkut");

  return (
    <div className="space-y-5" data-testid="expenses-page">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 font-display text-2xl font-semibold"><ReceiptText className="h-6 w-6 text-primary" /> Pengeluaran</h1>
          <p className="text-sm text-muted-foreground">Catat biaya operasional (ongkos angkut, listrik, gaji, dll). Pengeluaran mengurangi laba bersih di Dashboard & Laporan.</p>
        </div>
        <Button className="gap-2" onClick={openCreate} data-testid="expense-add-button"><Plus className="h-4 w-4" /> Catat Pengeluaran</Button>
      </div>

      <Card data-testid="expenses-filter">
        <CardContent className="space-y-3 p-4">
          <div className="flex items-center gap-2 text-sm font-semibold"><CalendarRange className="h-4 w-4 text-primary" /> Periode</div>
          <div className="flex flex-wrap gap-2">
            {PRESETS.map((p) => (
              <button key={p.key} type="button" onClick={() => applyPreset(p)} data-testid={`expenses-preset-${p.key}`}
                className={cn("rounded-full border px-3 py-1.5 text-xs font-medium transition-colors", preset === p.key ? "border-primary bg-primary text-primary-foreground shadow-sm" : "bg-card text-muted-foreground hover:border-primary/40 hover:text-foreground")}>
                {p.label}
              </button>
            ))}
          </div>
          <div className="grid gap-3 sm:grid-cols-4">
            <Input type="date" value={start} max={end || undefined} onChange={(e) => { setPreset(""); setRange([e.target.value, end]); }} className="bg-card" data-testid="expenses-start" />
            <Input type="date" value={end} min={start || undefined} onChange={(e) => { setPreset(""); setRange([start, e.target.value]); }} className="bg-card" data-testid="expenses-end" />
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger className="bg-card" data-testid="expenses-category-filter"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Semua kategori</SelectItem>
                {Object.entries(EXPENSE_CATEGORY_LABEL).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}
              </SelectContent>
            </Select>
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cari keterangan..." className="bg-card pl-9" data-testid="expenses-search" />
            </div>
          </div>
          {rangeInvalid && <p className="text-xs text-rose-600">Tanggal mulai harus sebelum tanggal akhir</p>}
        </CardContent>
      </Card>

      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4" data-testid="expenses-summary">
        {!data || loading ? [...Array(4)].map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />) : (
          <>
            <Card className="border-primary/30 bg-primary text-primary-foreground" data-testid="expenses-kpi-total">
              <CardContent className="p-4">
                <div className="flex items-center justify-between"><p className="text-xs font-medium text-primary-foreground/80">Total Pengeluaran</p><Wallet className="h-4 w-4 text-brand-yellow" /></div>
                <p className="mt-2 break-words font-display text-lg font-semibold sm:text-2xl" data-testid="expenses-kpi-total-value">{rupiah(data.total)}</p>
                <p className="mt-1 text-[11px] text-primary-foreground/70">{data.count} transaksi pada periode</p>
              </CardContent>
            </Card>
            <Card data-testid="expenses-kpi-angkut">
              <CardContent className="p-4">
                <div className="flex items-center justify-between"><p className="text-xs font-medium text-muted-foreground">Ongkos Angkut / Kirim</p><Truck className="h-4 w-4 text-primary" /></div>
                <p className="mt-2 break-words font-display text-lg font-semibold sm:text-2xl">{rupiah(angkut?.total || 0)}</p>
                <p className="mt-1 text-[11px] text-muted-foreground">{angkut?.count || 0} transaksi</p>
              </CardContent>
            </Card>
            <Card className="col-span-2" data-testid="expenses-kpi-categories">
              <CardContent className="p-4">
                <div className="flex items-center justify-between"><p className="text-xs font-medium text-muted-foreground">Per Kategori</p><Layers className="h-4 w-4 text-primary" /></div>
                {data.by_category.length === 0 ? <p className="mt-2 text-sm text-muted-foreground">Belum ada pengeluaran.</p> : (
                  <ul className="mt-2 space-y-1.5">
                    {data.by_category.slice(0, 4).map((c) => {
                      const pct = data.total ? Math.round((c.total / data.total) * 100) : 0;
                      return (
                        <li key={c.category} className="text-xs">
                          <div className="flex justify-between"><span>{EXPENSE_CATEGORY_LABEL[c.category] || c.category}</span><span className="font-semibold">{rupiah(c.total)} <span className="text-muted-foreground">({pct}%)</span></span></div>
                          <div className="mt-0.5 h-1.5 rounded-full bg-muted"><div className="h-1.5 rounded-full bg-primary" style={{ width: `${pct}%` }} /></div>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </section>

      <Card className="overflow-hidden" data-testid="expenses-table-card">
        <CardHeader className="pb-3"><CardTitle className="text-base">Daftar Pengeluaran {data && !loading && <Badge variant="secondary" className="ml-2 rounded-md">{data.items.length}</Badge>}</CardTitle></CardHeader>
        <CardContent className="p-0">
          {!data || loading ? (
            <div className="space-y-2 p-4">{[...Array(5)].map((_, i) => <Skeleton key={i} className="h-12" />)}</div>
          ) : data.items.length === 0 ? (
            <div className="flex flex-col items-center gap-2 p-10 text-center text-sm text-muted-foreground" data-testid="expenses-empty">
              <ReceiptText className="h-8 w-8" />
              <p className="font-medium text-foreground">Belum ada pengeluaran pada periode ini</p>
              <Button size="sm" variant="outline" className="mt-1 gap-2" onClick={openCreate}><Plus className="h-4 w-4" /> Catat pengeluaran pertama</Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table data-testid="expenses-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Tanggal</TableHead>
                    <TableHead>Keterangan</TableHead>
                    <TableHead>Kategori</TableHead>
                    <TableHead>Bayar</TableHead>
                    <TableHead className="text-right">Nominal</TableHead>
                    <TableHead className="text-right">Aksi</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.items.map((it) => (
                    <TableRow key={it.id} data-testid="expense-row">
                      <TableCell className="whitespace-nowrap text-sm">{formatDateOnly(it.expense_date)}</TableCell>
                      <TableCell>
                        <p className="font-medium">{it.description}</p>
                        <p className="text-xs text-muted-foreground">{[it.reference, it.note, it.source === "stock_in" ? "otomatis dari stok masuk" : null, it.created_by && `oleh ${it.created_by}`].filter(Boolean).join(" · ")}</p>
                      </TableCell>
                      <TableCell><Badge variant="outline" className="rounded-md">{EXPENSE_CATEGORY_LABEL[it.category] || it.category}</Badge></TableCell>
                      <TableCell className="text-sm capitalize">{it.payment_method === "cash" ? "Tunai" : "Transfer"}</TableCell>
                      <TableCell className="text-right font-semibold text-rose-700">-{rupiah(it.amount)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Edit" onClick={() => openEdit(it)} data-testid="expense-edit-button"><Pencil className="h-4 w-4" /></Button>
                          {isOwner && <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" aria-label="Hapus" onClick={() => setDeleteTarget(it)} data-testid="expense-delete-button"><Trash2 className="h-4 w-4" /></Button>}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="bg-accent/60 font-semibold hover:bg-accent/60" data-testid="expenses-total-row">
                    <TableCell colSpan={4}>TOTAL ({data.count} transaksi)</TableCell>
                    <TableCell className="text-right text-rose-700">-{rupiah(data.total)}</TableCell>
                    <TableCell />
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={!!dialog} onOpenChange={(o) => !o && setDialog(null)}>
        <DialogContent className="bg-card sm:max-w-lg" data-testid="expense-dialog">
          {dialog && (
            <form onSubmit={submit} className="space-y-4">
              <DialogHeader>
                <DialogTitle className="font-display">{dialog.mode === "edit" ? "Edit Pengeluaran" : "Catat Pengeluaran"}</DialogTitle>
                <DialogDescription>Biaya operasional akan dikurangkan dari laba kotor untuk menghitung laba bersih.</DialogDescription>
              </DialogHeader>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label>Tanggal *</Label>
                  <Input type="date" value={form.expense_date} onChange={(e) => setForm({ ...form, expense_date: e.target.value })} required data-testid="expense-date" />
                </div>
                <div className="space-y-1.5">
                  <Label>Kategori *</Label>
                  <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
                    <SelectTrigger data-testid="expense-category"><SelectValue /></SelectTrigger>
                    <SelectContent>{Object.entries(EXPENSE_CATEGORY_LABEL).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5 sm:col-span-2">
                  <Label>Keterangan *</Label>
                  <Input placeholder="mis. Ongkos angkut beras 25 sak dari gudang" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} required data-testid="expense-description" />
                </div>
                <div className="space-y-1.5">
                  <Label>Nominal (Rp) *</Label>
                  <Input type="number" min="1" step="1" inputMode="numeric" placeholder="150000" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required data-testid="expense-amount" />
                  {form.amount && <p className="text-xs text-muted-foreground">{rupiah(form.amount)}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label>Dibayar via</Label>
                  <Select value={form.payment_method} onValueChange={(v) => setForm({ ...form, payment_method: v })}>
                    <SelectTrigger data-testid="expense-payment-method"><SelectValue /></SelectTrigger>
                    <SelectContent><SelectItem value="cash">Tunai</SelectItem><SelectItem value="transfer">Transfer</SelectItem></SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5 sm:col-span-2">
                  <Label>Referensi (opsional)</Label>
                  <Input placeholder="No. nota / nama produk / supplier" value={form.reference} onChange={(e) => setForm({ ...form, reference: e.target.value })} data-testid="expense-reference" />
                </div>
                <div className="space-y-1.5 sm:col-span-2">
                  <Label>Catatan (opsional)</Label>
                  <Textarea rows={2} value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} data-testid="expense-note" />
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="ghost" onClick={() => setDialog(null)}>Batal</Button>
                <Button type="submit" disabled={saving} className="gap-2" data-testid="expense-submit">
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Simpan
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!deleteTarget} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <AlertDialogContent className="bg-card">
          <AlertDialogHeader>
            <AlertDialogTitle>Hapus pengeluaran ini?</AlertDialogTitle>
            <AlertDialogDescription>"{deleteTarget?.description}" sebesar {rupiah(deleteTarget?.amount)} akan dihapus permanen dan laba bersih dihitung ulang.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Batal</AlertDialogCancel>
            <AlertDialogAction onClick={remove} className="bg-destructive text-destructive-foreground hover:bg-destructive/90" data-testid="confirm-delete-expense">Hapus</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
