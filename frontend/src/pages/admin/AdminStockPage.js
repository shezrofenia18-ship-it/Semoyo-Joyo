import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Boxes, Loader2, Plus, Minus, Pencil, Trash2, History, AlertTriangle, PackageX, Wallet, ArrowDownToLine, ArrowUpFromLine, SlidersHorizontal } from "lucide-react";
import { toast } from "sonner";
import { api, errorMessage } from "@/lib/api";
import { useAdminGuard } from "@/hooks/useAdminGuard";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { ProductImage } from "@/components/ProductImage";
import { rupiah, formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";

const STATUS = {
  habis: { label: "Habis", cls: "bg-rose-50 text-rose-800 border-rose-200" },
  menipis: { label: "Menipis", cls: "bg-amber-50 text-amber-800 border-amber-200" },
  aman: { label: "Aman", cls: "bg-emerald-50 text-emerald-800 border-emerald-200" },
};
const MOVE_LABEL = { in: "Masuk", out: "Keluar", adjust: "Penyesuaian" };
const SOURCE_LABEL = { manual: "Manual", order: "Pesanan", cancel: "Pembatalan" };

const StockStatusBadge = ({ status }) => (
  <Badge variant="outline" className={cn("rounded-md font-medium", STATUS[status]?.cls || STATUS.aman.cls)} data-testid="stock-status-badge">
    {STATUS[status]?.label || status}
  </Badge>
);

export default function AdminStockPage() {
  const guard = useAdminGuard();
  const { isOwner } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState("all");
  const [dialog, setDialog] = useState(null); // { type: 'in'|'out'|'adjust', item }
  const [form, setForm] = useState({ qty: "", note: "" });
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [history, setHistory] = useState(null); // { item, rows }
  const [historyLoading, setHistoryLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      const { data } = await api.get("/admin/stock");
      setData(data);
    } catch (e) {
      if (!guard(e)) toast.error(errorMessage(e));
    }
  }, [guard]);

  useEffect(() => {
    load();
  }, [load]);

  const items = useMemo(() => {
    if (!data) return [];
    return data.items.filter((it) => (filter === "all" || it.status === filter) && (!q || it.name.toLowerCase().includes(q.toLowerCase())));
  }, [data, q, filter]);

  const openDialog = (type, item) => {
    setForm({ qty: type === "adjust" ? String(item.stock) : "", note: "" });
    setDialog({ type, item });
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!dialog) return;
    const qty = Number(form.qty);
    if (Number.isNaN(qty) || qty < 0 || (dialog.type !== "adjust" && qty <= 0)) return toast.error("Jumlah tidak valid");
    setSaving(true);
    try {
      const { data: updated } = await api.post(`/admin/stock/${dialog.item.id}/adjust`, { movement_type: dialog.type, qty, note: form.note || null });
      setData((prev) => {
        if (!prev) return prev;
        const nextItems = prev.items.map((it) => (it.id === updated.id ? updated : it));
        return { ...prev, items: nextItems };
      });
      toast.success(dialog.type === "in" ? `Stok ${updated.name} bertambah menjadi ${updated.stock} ${updated.unit}` : dialog.type === "out" ? `Stok ${updated.name} berkurang menjadi ${updated.stock} ${updated.unit}` : `Stok ${updated.name} diset ke ${updated.stock} ${updated.unit}`);
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
      await api.delete(`/admin/products/${deleteTarget.id}`);
      toast.success("Produk dihapus dari stok & katalog");
      setDeleteTarget(null);
      load();
    } catch (err) {
      if (!guard(err)) toast.error(errorMessage(err));
    }
  };

  const openHistory = async (item) => {
    setHistory({ item, rows: null });
    setHistoryLoading(true);
    try {
      const { data: rows } = await api.get("/admin/stock/movements", { params: { product_id: item.id, limit: 50 } });
      setHistory({ item, rows });
    } catch (err) {
      if (!guard(err)) toast.error(errorMessage(err));
      setHistory(null);
    } finally {
      setHistoryLoading(false);
    }
  };

  const summary = data
    ? [
        { label: "Total Produk", value: data.total_products, icon: Boxes, tone: "text-primary" },
        { label: "Total Unit Tersedia", value: new Intl.NumberFormat("id-ID").format(data.total_units), icon: ArrowDownToLine, tone: "text-primary" },
        ...(isOwner ? [{ label: "Nilai Stok (Modal)", value: rupiah(data.total_stock_value), icon: Wallet, tone: "text-emerald-700" }] : []),
        { label: "Menipis / Habis", value: `${data.low_stock} / ${data.out_of_stock}`, icon: AlertTriangle, tone: "text-amber-600" },
      ]
    : [];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold">Stok Barang</h1>
          <p className="text-sm text-muted-foreground">Pantau sisa stok semua barang dan sesuaikan secara manual (tambah / kurangi / set).</p>
        </div>
        <Button variant="outline" className="gap-2" onClick={() => navigate("/admin/produk")} data-testid="stock-goto-products">
          <Plus className="h-4 w-4" /> Tambah Produk Baru
        </Button>
      </div>

      <div className={cn("grid grid-cols-2 gap-3", isOwner ? "lg:grid-cols-4" : "lg:grid-cols-3")}>
        {!data
          ? [...Array(4)].map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)
          : summary.map(({ label, value, icon: I, tone }) => (
              <Card key={label} data-testid="stock-kpi-card">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-medium text-muted-foreground">{label}</p>
                    <I className={cn("h-4 w-4", tone)} />
                  </div>
                  <p className="mt-2 font-display text-lg font-semibold sm:text-2xl">{value}</p>
                </CardContent>
              </Card>
            ))}
      </div>

      <div className="flex flex-col gap-2 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cari barang..." className="bg-card pl-9" data-testid="stock-search" />
        </div>
        <Select value={filter} onValueChange={setFilter}>
          <SelectTrigger className="w-full bg-card sm:w-52" data-testid="stock-filter-status"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Semua status stok</SelectItem>
            <SelectItem value="aman">Aman</SelectItem>
            <SelectItem value="menipis">Menipis</SelectItem>
            <SelectItem value="habis">Habis</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card className="overflow-hidden">
        {!data ? (
          <div className="space-y-2 p-4">{[...Array(6)].map((_, i) => <Skeleton key={i} className="h-12" />)}</div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center gap-2 p-10 text-center text-sm text-muted-foreground"><PackageX className="h-8 w-8" /> Tidak ada barang yang cocok.</div>
        ) : (
          <div className="overflow-x-auto">
            <Table data-testid="admin-stock-table">
              <TableHeader>
                <TableRow>
                  <TableHead>Barang</TableHead>
                  <TableHead>Kategori</TableHead>
                  <TableHead className="text-right">Sisa Stok</TableHead>
                  <TableHead className="text-right">Min. Order</TableHead>
                  <TableHead>Status</TableHead>
                  {isOwner && <TableHead className="text-right">Nilai Stok</TableHead>}
                  <TableHead>Mutasi Terakhir</TableHead>
                  <TableHead className="text-right">Aksi</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((it) => (
                  <TableRow key={it.id} data-testid="admin-stock-row" className={it.status === "habis" ? "bg-rose-50/40" : it.status === "menipis" ? "bg-amber-50/40" : ""}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 shrink-0 overflow-hidden rounded-md bg-muted"><ProductImage src={it.image_url} alt={it.name} iconClassName="h-4 w-4" /></div>
                        <div className="min-w-0">
                          <p className="truncate font-medium">{it.name}</p>
                          <p className="truncate text-xs text-muted-foreground">{isOwner ? `Modal ${rupiah(it.cost_price)}/${it.unit}` : `Jual ${rupiah(it.price)}/${it.unit}`}{!it.is_active && " · Nonaktif"}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">{it.category_name}</TableCell>
                    <TableCell className="text-right">
                      <span className={cn("font-display text-base font-semibold", it.status === "habis" ? "text-rose-700" : it.status === "menipis" ? "text-amber-700" : "")} data-testid="stock-qty">{it.stock}</span>
                      <span className="ml-1 text-xs text-muted-foreground">{it.unit}</span>
                    </TableCell>
                    <TableCell className="text-right text-sm">{it.min_order} {it.unit}</TableCell>
                    <TableCell><StockStatusBadge status={it.status} /></TableCell>
                    {isOwner && <TableCell className="text-right text-sm">{rupiah(it.stock_value)}</TableCell>}
                    <TableCell className="text-xs text-muted-foreground">{it.last_movement_at ? formatDate(it.last_movement_at) : "-"}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button variant="outline" size="sm" className="h-8 gap-1 border-emerald-300 px-2 text-emerald-700 hover:bg-emerald-50" onClick={() => openDialog("in", it)} data-testid="stock-add-button" aria-label="Tambah stok"><Plus className="h-3.5 w-3.5" /> Tambah</Button>
                        <Button variant="outline" size="sm" className="h-8 gap-1 border-amber-300 px-2 text-amber-700 hover:bg-amber-50" onClick={() => openDialog("out", it)} data-testid="stock-reduce-button" aria-label="Kurangi stok"><Minus className="h-3.5 w-3.5" /> Kurangi</Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Edit / set stok" title="Edit (set stok manual)" onClick={() => openDialog("adjust", it)} data-testid="stock-edit-button"><Pencil className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Riwayat" title="Riwayat mutasi" onClick={() => openHistory(it)} data-testid="stock-history-button"><History className="h-4 w-4" /></Button>
                        {isOwner && <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" aria-label="Hapus" title="Hapus produk" onClick={() => setDeleteTarget(it)} data-testid="stock-delete-button"><Trash2 className="h-4 w-4" /></Button>}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>

      {/* Adjust dialog */}
      <Dialog open={!!dialog} onOpenChange={(o) => !o && setDialog(null)}>
        <DialogContent className="bg-card sm:max-w-md" data-testid="stock-adjust-dialog">
          {dialog && (
            <form onSubmit={submit} className="space-y-4">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2 font-display">
                  {dialog.type === "in" && <><ArrowDownToLine className="h-5 w-5 text-emerald-600" /> Tambah Stok</>}
                  {dialog.type === "out" && <><ArrowUpFromLine className="h-5 w-5 text-amber-600" /> Kurangi Stok</>}
                  {dialog.type === "adjust" && <><SlidersHorizontal className="h-5 w-5 text-primary" /> Edit / Set Stok</>}
                </DialogTitle>
                <DialogDescription>
                  {dialog.item.name} &middot; stok saat ini <b>{dialog.item.stock} {dialog.item.unit}</b>
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-1.5">
                <Label>{dialog.type === "adjust" ? `Stok baru (${dialog.item.unit})` : `Jumlah (${dialog.item.unit})`} *</Label>
                <Input type="number" min="0" autoFocus value={form.qty} onChange={(e) => setForm({ ...form, qty: e.target.value })} data-testid="stock-adjust-qty" required />
                {form.qty !== "" && (
                  <p className="text-xs text-muted-foreground" data-testid="stock-adjust-preview">
                    Stok setelah perubahan:{" "}
                    <b>
                      {dialog.type === "in" ? dialog.item.stock + Number(form.qty) : dialog.type === "out" ? dialog.item.stock - Number(form.qty) : Number(form.qty)} {dialog.item.unit}
                    </b>
                  </p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label>Catatan</Label>
                <Textarea rows={2} placeholder={dialog.type === "in" ? "mis. Pembelian dari supplier / restock" : dialog.type === "out" ? "mis. Rusak, kedaluwarsa, pemakaian internal" : "mis. Hasil stock opname"} value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} data-testid="stock-adjust-note" />
              </div>
              <DialogFooter>
                <Button type="button" variant="ghost" onClick={() => setDialog(null)}>Batal</Button>
                <Button type="submit" disabled={saving} className="gap-2" data-testid="stock-adjust-submit">
                  {saving && <Loader2 className="h-4 w-4 animate-spin" />} Simpan
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* History sheet */}
      <Sheet open={!!history} onOpenChange={(o) => !o && setHistory(null)}>
        <SheetContent className="w-full overflow-y-auto bg-background sm:max-w-lg" data-testid="stock-history-sheet">
          {history && (
            <>
              <SheetHeader className="text-left">
                <SheetTitle className="font-display">Riwayat Mutasi Stok</SheetTitle>
                <SheetDescription>{history.item.name} &middot; stok saat ini {history.item.stock} {history.item.unit}</SheetDescription>
              </SheetHeader>
              <div className="mt-5">
                {historyLoading || !history.rows ? (
                  <div className="space-y-2">{[...Array(5)].map((_, i) => <Skeleton key={i} className="h-12" />)}</div>
                ) : history.rows.length === 0 ? (
                  <p className="rounded-xl border bg-card p-6 text-center text-sm text-muted-foreground">Belum ada mutasi stok untuk barang ini.</p>
                ) : (
                  <ul className="space-y-2">
                    {history.rows.map((m) => (
                      <li key={m.id} className="rounded-xl border bg-card p-3 text-sm" data-testid="stock-history-row">
                        <div className="flex items-center justify-between gap-2">
                          <span className="flex items-center gap-2 font-medium">
                            <Badge variant="outline" className={cn("rounded-md", m.qty > 0 ? "border-emerald-200 bg-emerald-50 text-emerald-800" : m.qty < 0 ? "border-amber-200 bg-amber-50 text-amber-800" : "")}>{MOVE_LABEL[m.movement_type] || m.movement_type}</Badge>
                            <span className={m.qty > 0 ? "text-emerald-700" : m.qty < 0 ? "text-amber-700" : ""}>{m.qty > 0 ? "+" : ""}{m.qty} {history.item.unit}</span>
                          </span>
                          <span className="text-xs text-muted-foreground">{formatDate(m.created_at)}</span>
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {m.stock_before} &rarr; {m.stock_after} {history.item.unit} &middot; {SOURCE_LABEL[m.source] || m.source}
                          {m.reference && <> &middot; {m.reference}</>}
                          {m.created_by && <> &middot; oleh {m.created_by}</>}
                        </p>
                        {m.note && <p className="mt-1 text-xs italic text-muted-foreground">"{m.note}"</p>}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>

      <AlertDialog open={!!deleteTarget} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <AlertDialogContent className="bg-card">
          <AlertDialogHeader>
            <AlertDialogTitle>Hapus produk dari stok?</AlertDialogTitle>
            <AlertDialogDescription>"{deleteTarget?.name}" beserta riwayat mutasinya akan dihapus dari katalog. Riwayat pesanan yang sudah ada tetap tersimpan.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Batal</AlertDialogCancel>
            <AlertDialogAction onClick={remove} className="bg-destructive text-destructive-foreground hover:bg-destructive/90" data-testid="confirm-delete-stock">Hapus</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
