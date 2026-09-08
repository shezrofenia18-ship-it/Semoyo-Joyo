import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Plus, Pencil, Trash2, Search, Loader2, Upload, Package } from "lucide-react";
import { toast } from "sonner";
import { api, errorMessage } from "@/lib/api";
import { useAdminGuard } from "@/hooks/useAdminGuard";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ProductImage } from "@/components/ProductImage";
import { rupiah } from "@/lib/format";

const UNITS = ["kg", "gram", "liter", "ml", "pack", "karton", "sak", "ikat", "butir", "papan", "pouch", "jerigen", "blok", "buah", "ekor", "lusin"];
const EMPTY = { category_id: "", name: "", description: "", price: "", cost_price: "", unit: "kg", min_order: 1, stock: 0, image_url: "", is_active: true };

export default function AdminProductsPage() {
  const guard = useAdminGuard();
  const { isOwner } = useAuth();
  const [products, setProducts] = useState(null);
  const [categories, setCategories] = useState([]);
  const [q, setQ] = useState("");
  const [filterCat, setFilterCat] = useState("all");
  const [dialog, setDialog] = useState(null); // {mode:'create'|'edit', data}
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const fileRef = useRef(null);

  const load = useCallback(async () => {
    try {
      const [p, c] = await Promise.all([api.get("/admin/products"), api.get("/admin/categories")]);
      setProducts(p.data);
      setCategories(c.data);
    } catch (e) {
      if (!guard(e)) toast.error(errorMessage(e));
    }
  }, [guard]);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = useMemo(() => {
    if (!products) return [];
    return products.filter((p) => (filterCat === "all" || p.category_id === filterCat) && (!q || p.name.toLowerCase().includes(q.toLowerCase())));
  }, [products, q, filterCat]);

  const openCreate = () => {
    setForm({ ...EMPTY, category_id: categories[0]?.id || "" });
    setDialog({ mode: "create" });
  };
  const openEdit = (p) => {
    setForm({ category_id: p.category_id, name: p.name, description: p.description || "", price: p.price, cost_price: p.cost_price ?? "", unit: p.unit, min_order: p.min_order, stock: p.stock, image_url: p.image_url || "", is_active: p.is_active });
    setDialog({ mode: "edit", data: p });
  };

  const save = async (e) => {
    e.preventDefault();
    if (!form.category_id) return toast.error("Pilih kategori");
    if (!form.name.trim()) return toast.error("Nama produk wajib diisi");
    setSaving(true);
    const payload = { ...form, price: Number(form.price) || 0, cost_price: Number(form.cost_price) || 0, min_order: Number(form.min_order) || 1, stock: Number(form.stock) || 0, image_url: form.image_url || null, description: form.description || null };
    try {
      if (dialog.mode === "create") {
        await api.post("/admin/products", payload);
        toast.success("Produk ditambahkan");
      } else {
        await api.put(`/admin/products/${dialog.data.id}`, payload);
        toast.success("Produk diperbarui");
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
      await api.delete(`/admin/products/${deleteTarget.id}`);
      toast.success("Produk dihapus");
      setDeleteTarget(null);
      load();
    } catch (err) {
      if (!guard(err)) toast.error(errorMessage(err));
    }
  };

  const upload = async (file) => {
    if (!file) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const { data } = await api.post("/admin/upload", fd, { headers: { "Content-Type": "multipart/form-data" } });
      setForm((f) => ({ ...f, image_url: data.url }));
      toast.success("Gambar diunggah");
    } catch (err) {
      if (!guard(err)) toast.error(errorMessage(err, "Gagal mengunggah gambar"));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold">Produk</h1>
          <p className="text-sm text-muted-foreground">{products ? `${products.length} produk terdaftar` : "Memuat..."}</p>
        </div>
        <Button onClick={openCreate} className="gap-2" data-testid="admin-add-product-button"><Plus className="h-4 w-4" /> Tambah Produk</Button>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cari produk..." className="bg-card pl-9" data-testid="admin-product-search" />
        </div>
        <Select value={filterCat} onValueChange={setFilterCat}>
          <SelectTrigger className="w-full bg-card sm:w-60" data-testid="admin-product-filter-category"><SelectValue placeholder="Semua kategori" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Semua kategori</SelectItem>
            {categories.map((c) => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      <Card className="overflow-hidden">
        {!products ? (
          <div className="space-y-2 p-4">{[...Array(6)].map((_, i) => <Skeleton key={i} className="h-12" />)}</div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center gap-2 p-10 text-center text-sm text-muted-foreground">
            <Package className="h-8 w-8" /> Tidak ada produk yang cocok.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table data-testid="admin-products-table">
              <TableHeader>
                <TableRow>
                  <TableHead>Produk</TableHead>
                  <TableHead>Kategori</TableHead>
                  <TableHead className="text-right">Harga Jual</TableHead>
                  {isOwner && <TableHead className="text-right">Harga Beli</TableHead>}
                  {isOwner && <TableHead className="text-right">Laba / Unit</TableHead>}
                  <TableHead className="text-right">Min. Order</TableHead>
                  <TableHead className="text-right">Stok</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Aksi</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((p) => (
                  <TableRow key={p.id} data-testid="admin-product-row">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 shrink-0 overflow-hidden rounded-md bg-muted"><ProductImage src={p.image_url} alt={p.name} iconClassName="h-4 w-4" /></div>
                        <div className="min-w-0">
                          <p className="truncate font-medium">{p.name}</p>
                          <p className="truncate text-xs text-muted-foreground">{p.slug}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">{p.category_name}</TableCell>
                    <TableCell className="text-right font-medium">{rupiah(p.price)}<span className="text-xs text-muted-foreground">/{p.unit}</span></TableCell>
                    {isOwner && <TableCell className="text-right text-muted-foreground" data-testid="admin-product-cost">{rupiah(p.cost_price)}</TableCell>}
                    {isOwner && (
                      <TableCell className="text-right" data-testid="admin-product-profit">
                        <span className={p.profit_per_unit < 0 ? "font-semibold text-rose-700" : "font-semibold text-emerald-700"}>{p.profit_per_unit < 0 ? "-" : ""}{rupiah(Math.abs(p.profit_per_unit))}</span>
                        <span className="ml-1 text-xs text-muted-foreground">({p.margin_pct}%)</span>
                      </TableCell>
                    )}
                    <TableCell className="text-right">{p.min_order} {p.unit}</TableCell>
                    <TableCell className="text-right">
                      <span className={p.stock <= p.min_order * 2 ? "font-semibold text-amber-700" : ""}>{p.stock}</span>
                    </TableCell>
                    <TableCell>{p.is_active ? <Badge className="bg-emerald-50 text-emerald-800 hover:bg-emerald-50">Aktif</Badge> : <Badge variant="secondary">Nonaktif</Badge>}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Edit" onClick={() => openEdit(p)} data-testid="admin-edit-product-button"><Pencil className="h-4 w-4" /></Button>
                        {isOwner && <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" aria-label="Hapus" onClick={() => setDeleteTarget(p)} data-testid="admin-delete-product-button"><Trash2 className="h-4 w-4" /></Button>}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>

      {/* Create / Edit dialog */}
      <Dialog open={!!dialog} onOpenChange={(o) => !o && setDialog(null)}>
        <DialogContent className="max-h-[90vh] overflow-y-auto bg-card sm:max-w-2xl" data-testid="admin-crud-dialog">
          <DialogHeader>
            <DialogTitle className="font-display">{dialog?.mode === "create" ? "Tambah Produk" : "Edit Produk"}</DialogTitle>
            <DialogDescription>Lengkapi informasi produk. Harga dalam Rupiah per satuan. Harga beli dipakai untuk menghitung laba/rugi otomatis.</DialogDescription>
          </DialogHeader>
          <form onSubmit={save} className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5 sm:col-span-2">
              <Label>Nama Produk *</Label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="product-form-name" required />
            </div>
            <div className="space-y-1.5">
              <Label>Kategori *</Label>
              <Select value={form.category_id} onValueChange={(v) => setForm({ ...form, category_id: v })}>
                <SelectTrigger data-testid="product-form-category"><SelectValue placeholder="Pilih kategori" /></SelectTrigger>
                <SelectContent>{categories.map((c) => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Satuan *</Label>
              <Select value={form.unit} onValueChange={(v) => setForm({ ...form, unit: v })}>
                <SelectTrigger data-testid="product-form-unit"><SelectValue /></SelectTrigger>
                <SelectContent>{UNITS.map((u) => <SelectItem key={u} value={u}>{u}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Harga Jual (Rp) *</Label>
              <Input type="number" min="0" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} data-testid="product-form-price" required />
            </div>
            {isOwner && (
            <div className="space-y-1.5">
              <Label>Harga Beli / Modal (Rp)</Label>
              <Input type="number" min="0" value={form.cost_price} onChange={(e) => setForm({ ...form, cost_price: e.target.value })} placeholder="0" data-testid="product-form-cost-price" />
              <p className="text-xs text-muted-foreground">
                {Number(form.price) > 0 ? (
                  <>Laba/unit: <span className={Number(form.price) - Number(form.cost_price || 0) < 0 ? "font-semibold text-rose-700" : "font-semibold text-emerald-700"}>{rupiah(Number(form.price) - Number(form.cost_price || 0))}</span> ({Math.round(((Number(form.price) - Number(form.cost_price || 0)) / Number(form.price)) * 1000) / 10}%)</>
                ) : "Isi harga jual untuk melihat estimasi laba."}
              </p>
            </div>
            )}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Min. Order</Label>
                <Input type="number" min="1" value={form.min_order} onChange={(e) => setForm({ ...form, min_order: e.target.value })} data-testid="product-form-min-order" />
              </div>
              <div className="space-y-1.5">
                <Label>Stok</Label>
                <Input type="number" min="0" value={form.stock} onChange={(e) => setForm({ ...form, stock: e.target.value })} data-testid="product-form-stock" />
              </div>
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <Label>Deskripsi Produk</Label>
              <Textarea rows={3} placeholder="Deskripsi singkat yang dibaca pembeli di beranda: kualitas, asal, kemasan, cara simpan..." value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} data-testid="product-form-description" />
              <p className="text-xs text-muted-foreground">Tampil di kartu produk (ringkas) dan pop-up detail produk (lengkap).</p>
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <Label>Gambar Produk</Label>
              <div className="flex gap-3">
                <div className="h-20 w-20 shrink-0 overflow-hidden rounded-lg border bg-muted"><ProductImage src={form.image_url} alt="preview" /></div>
                <div className="flex-1 space-y-2">
                  <Input placeholder="https://... (URL gambar)" value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })} data-testid="product-form-image-url" />
                  <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={(e) => upload(e.target.files?.[0])} />
                  <Button type="button" variant="secondary" size="sm" className="gap-2" disabled={uploading} onClick={() => fileRef.current?.click()} data-testid="product-form-upload-button">
                    {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />} Unggah dari perangkat
                  </Button>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between rounded-lg border p-3 sm:col-span-2">
              <div>
                <p className="text-sm font-medium">Tampilkan di katalog</p>
                <p className="text-xs text-muted-foreground">Produk nonaktif tidak muncul di beranda pelanggan.</p>
              </div>
              <Switch checked={form.is_active} onCheckedChange={(v) => setForm({ ...form, is_active: v })} data-testid="product-form-active" />
            </div>
            <DialogFooter className="sm:col-span-2">
              <Button type="button" variant="ghost" onClick={() => setDialog(null)}>Batal</Button>
              <Button type="submit" disabled={saving} className="gap-2" data-testid="product-form-submit">
                {saving && <Loader2 className="h-4 w-4 animate-spin" />} Simpan
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!deleteTarget} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <AlertDialogContent className="bg-card">
          <AlertDialogHeader>
            <AlertDialogTitle>Hapus produk?</AlertDialogTitle>
            <AlertDialogDescription>"{deleteTarget?.name}" akan dihapus dari katalog. Riwayat pesanan yang sudah ada tetap tersimpan.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Batal</AlertDialogCancel>
            <AlertDialogAction onClick={remove} className="bg-destructive text-destructive-foreground hover:bg-destructive/90" data-testid="confirm-delete-product">Hapus</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
