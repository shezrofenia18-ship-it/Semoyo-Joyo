import { useCallback, useEffect, useState } from "react";
import { Plus, Pencil, Trash2, Loader2, Tags } from "lucide-react";
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
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { ProductImage } from "@/components/ProductImage";

const EMPTY = { name: "", description: "", image_url: "", sort_order: 0, is_active: true };

export default function AdminCategoriesPage() {
  const guard = useAdminGuard();
  const { isOwner } = useAuth();
  const [cats, setCats] = useState(null);
  const [dialog, setDialog] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const load = useCallback(() => {
    api.get("/admin/categories").then((r) => setCats(r.data)).catch((e) => { if (!guard(e)) toast.error(errorMessage(e)); });
  }, [guard]);

  useEffect(() => {
    load();
  }, [load]);

  const openCreate = () => {
    setForm({ ...EMPTY, sort_order: (cats?.length || 0) });
    setDialog({ mode: "create" });
  };
  const openEdit = (c) => {
    setForm({ name: c.name, description: c.description || "", image_url: c.image_url || "", sort_order: c.sort_order, is_active: c.is_active });
    setDialog({ mode: "edit", data: c });
  };

  const save = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return toast.error("Nama kategori wajib diisi");
    setSaving(true);
    const payload = { ...form, sort_order: Number(form.sort_order) || 0, image_url: form.image_url || null, description: form.description || null };
    try {
      if (dialog.mode === "create") {
        await api.post("/admin/categories", payload);
        toast.success("Kategori ditambahkan");
      } else {
        await api.put(`/admin/categories/${dialog.data.id}`, payload);
        toast.success("Kategori diperbarui");
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
    try {
      await api.delete(`/admin/categories/${deleteTarget.id}`);
      toast.success("Kategori dihapus");
      setDeleteTarget(null);
      load();
    } catch (err) {
      if (!guard(err)) toast.error(errorMessage(err));
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold">Kategori</h1>
          <p className="text-sm text-muted-foreground">Kelompok barang yang tampil di beranda pelanggan.</p>
        </div>
        <Button onClick={openCreate} className="gap-2" data-testid="admin-add-category-button"><Plus className="h-4 w-4" /> Tambah Kategori</Button>
      </div>

      <Card className="overflow-hidden">
        {!cats ? (
          <div className="space-y-2 p-4">{[...Array(5)].map((_, i) => <Skeleton key={i} className="h-12" />)}</div>
        ) : cats.length === 0 ? (
          <div className="flex flex-col items-center gap-2 p-10 text-center text-sm text-muted-foreground"><Tags className="h-8 w-8" /> Belum ada kategori.</div>
        ) : (
          <Table data-testid="admin-categories-table">
            <TableHeader>
              <TableRow>
                <TableHead className="w-16">Urutan</TableHead>
                <TableHead>Kategori</TableHead>
                <TableHead className="text-right">Produk</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Aksi</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {cats.map((c) => (
                <TableRow key={c.id} data-testid="admin-category-row">
                  <TableCell className="text-muted-foreground">{c.sort_order}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 shrink-0 overflow-hidden rounded-md bg-muted"><ProductImage src={c.image_url} alt={c.name} iconClassName="h-4 w-4" /></div>
                      <div className="min-w-0">
                        <p className="font-medium">{c.name}</p>
                        <p className="truncate text-xs text-muted-foreground">{c.description || c.slug}</p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">{c.product_count}</TableCell>
                  <TableCell>{c.is_active ? <Badge className="bg-emerald-50 text-emerald-800 hover:bg-emerald-50">Aktif</Badge> : <Badge variant="secondary">Nonaktif</Badge>}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Edit" onClick={() => openEdit(c)} data-testid="admin-edit-category-button"><Pencil className="h-4 w-4" /></Button>
                      {isOwner && <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" aria-label="Hapus" onClick={() => setDeleteTarget(c)} data-testid="admin-delete-category-button"><Trash2 className="h-4 w-4" /></Button>}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      <Dialog open={!!dialog} onOpenChange={(o) => !o && setDialog(null)}>
        <DialogContent className="bg-card" data-testid="admin-crud-dialog">
          <DialogHeader>
            <DialogTitle className="font-display">{dialog?.mode === "create" ? "Tambah Kategori" : "Edit Kategori"}</DialogTitle>
            <DialogDescription>Kategori digunakan untuk mengelompokkan produk di beranda.</DialogDescription>
          </DialogHeader>
          <form onSubmit={save} className="space-y-4">
            <div className="space-y-1.5">
              <Label>Nama Kategori *</Label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="category-form-name" required />
            </div>
            <div className="space-y-1.5">
              <Label>Deskripsi</Label>
              <Textarea rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} data-testid="category-form-description" />
            </div>
            <div className="grid grid-cols-[1fr_120px] gap-3">
              <div className="space-y-1.5">
                <Label>URL Gambar</Label>
                <Input placeholder="https://..." value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })} data-testid="category-form-image-url" />
              </div>
              <div className="space-y-1.5">
                <Label>Urutan</Label>
                <Input type="number" value={form.sort_order} onChange={(e) => setForm({ ...form, sort_order: e.target.value })} data-testid="category-form-sort-order" />
              </div>
            </div>
            <div className="flex items-center justify-between rounded-lg border p-3">
              <p className="text-sm font-medium">Aktif</p>
              <Switch checked={form.is_active} onCheckedChange={(v) => setForm({ ...form, is_active: v })} data-testid="category-form-active" />
            </div>
            <DialogFooter>
              <Button type="button" variant="ghost" onClick={() => setDialog(null)}>Batal</Button>
              <Button type="submit" disabled={saving} className="gap-2" data-testid="category-form-submit">{saving && <Loader2 className="h-4 w-4 animate-spin" />} Simpan</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!deleteTarget} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <AlertDialogContent className="bg-card">
          <AlertDialogHeader>
            <AlertDialogTitle>Hapus kategori?</AlertDialogTitle>
            <AlertDialogDescription>"{deleteTarget?.name}" akan dihapus. Kategori yang masih memiliki produk tidak dapat dihapus.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Batal</AlertDialogCancel>
            <AlertDialogAction onClick={remove} className="bg-destructive text-destructive-foreground hover:bg-destructive/90" data-testid="confirm-delete-category">Hapus</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
