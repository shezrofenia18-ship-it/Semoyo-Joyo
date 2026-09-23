import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Settings, UserCog, Store, Users, RefreshCw, ShieldCheck, KeyRound, Loader2, Save, Plus, Trash2, Search, CheckCircle2, AlertTriangle, Info,
  Pencil, Wallet, HandCoins, Coins, TrendingUp, ReceiptText, Boxes, ShoppingBag, Sparkles,
} from "lucide-react";
import { toast } from "sonner";
import { api, errorMessage } from "@/lib/api";
import { useAdminGuard } from "@/hooks/useAdminGuard";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { SegmentBadge } from "@/components/StatusBadge";
import { rupiah, formatDate, CUSTOMER_SEGMENT_LABEL } from "@/lib/format";
import { cn } from "@/lib/utils";

const TABS = [
  { key: "akun", label: "Akun Staf", icon: UserCog },
  { key: "toko", label: "Profil Toko", icon: Store },
  { key: "pelanggan", label: "Database Pelanggan", icon: Users },
  { key: "sinkronisasi", label: "Sinkronisasi Data", icon: RefreshCw },
];

export default function AdminSettingsPage() {
  const [params, setParams] = useSearchParams();
  const tab = TABS.some((t) => t.key === params.get("tab")) ? params.get("tab") : "akun";

  return (
    <div className="space-y-5" data-testid="settings-page">
      <div>
        <h1 className="flex items-center gap-2 font-display text-2xl font-semibold"><Settings className="h-6 w-6 text-primary" /> Pengaturan</h1>
        <p className="text-sm text-muted-foreground">Khusus Owner: kelola akun staf, identitas toko, database pelanggan, dan integritas data.</p>
      </div>

      <Tabs value={tab} onValueChange={(v) => setParams({ tab: v })}>
        <TabsList className="h-auto w-full flex-wrap justify-start gap-1 bg-card p-1" data-testid="settings-tabs">
          {TABS.map(({ key, label, icon: I }) => (
            <TabsTrigger key={key} value={key} className="gap-2 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground" data-testid={`settings-tab-${key}`}>
              <I className="h-4 w-4" /> {label}
            </TabsTrigger>
          ))}
        </TabsList>
        <TabsContent value="akun" className="mt-5"><StaffTab /></TabsContent>
        <TabsContent value="toko" className="mt-5"><StoreTab /></TabsContent>
        <TabsContent value="pelanggan" className="mt-5"><CustomersTab /></TabsContent>
        <TabsContent value="sinkronisasi" className="mt-5"><SyncTab /></TabsContent>
      </Tabs>
    </div>
  );
}

/* ============================== Akun Staf ============================== */
function StaffTab() {
  const guard = useAdminGuard();
  const { admin, refreshAdmin, logoutAdmin } = useAuth();
  const [staff, setStaff] = useState(null);
  const [edit, setEdit] = useState(null); // user
  const [create, setCreate] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [form, setForm] = useState({ username: "", full_name: "", password: "", confirm: "", owner_password: "" });
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    api.get("/admin/settings/staff").then((r) => setStaff(r.data)).catch((e) => { if (!guard(e)) toast.error(errorMessage(e)); });
  }, [guard]);
  useEffect(() => { load(); }, [load]);

  const openEdit = (u) => { setForm({ username: u.username, full_name: u.full_name, password: "", confirm: "", owner_password: "" }); setEdit(u); };
  const openCreate = () => { setForm({ username: "", full_name: "", password: "", confirm: "", owner_password: "" }); setCreate(true); };

  const submitEdit = async (e) => {
    e.preventDefault();
    if (form.password && form.password.length < 6) return toast.error("Password baru minimal 6 karakter");
    if (form.password && form.password !== form.confirm) return toast.error("Konfirmasi password tidak sama");
    if (!form.owner_password) return toast.error("Masukkan password Owner Anda untuk konfirmasi");
    const payload = { owner_password: form.owner_password };
    if (form.username.trim().toLowerCase() !== edit.username) payload.username = form.username.trim().toLowerCase();
    if (form.password) payload.password = form.password;
    if (form.full_name.trim() !== edit.full_name) payload.full_name = form.full_name.trim();
    if (Object.keys(payload).length === 1) return toast.error("Tidak ada perubahan");
    setSaving(true);
    try {
      const { data } = await api.put(`/admin/settings/staff/${edit.id}/credentials`, payload);
      toast.success(`Kredensial akun ${data.role} "${data.username}" diperbarui`);
      const isSelf = admin?.id === edit.id;
      setEdit(null);
      load();
      if (isSelf && (payload.username || payload.password)) {
        toast.info("Kredensial akun Anda berubah. Silakan masuk kembali dengan ID/password baru.");
        setTimeout(() => { logoutAdmin(); window.location.href = "/rahasia-admin"; }, 1800);
      } else {
        refreshAdmin();
      }
    } catch (err) {
      if (!guard(err)) toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const submitCreate = async (e) => {
    e.preventDefault();
    if (form.password.length < 6) return toast.error("Password minimal 6 karakter");
    if (form.password !== form.confirm) return toast.error("Konfirmasi password tidak sama");
    if (!form.owner_password) return toast.error("Masukkan password Owner Anda untuk konfirmasi");
    setSaving(true);
    try {
      await api.post("/admin/settings/staff", { owner_password: form.owner_password, username: form.username.trim().toLowerCase(), password: form.password, full_name: form.full_name.trim() });
      toast.success("Akun admin baru dibuat");
      setCreate(false);
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
      await api.delete(`/admin/settings/staff/${deleteTarget.id}`);
      toast.success(`Akun ${deleteTarget.username} dihapus`);
      setDeleteTarget(null);
      load();
    } catch (err) {
      if (!guard(err)) toast.error(errorMessage(err));
    }
  };

  return (
    <div className="space-y-4" data-testid="staff-tab">
      <Card>
        <CardHeader className="flex flex-row flex-wrap items-start justify-between gap-3 pb-3">
          <div>
            <CardTitle className="text-base">Akun Admin & Owner</CardTitle>
            <CardDescription>Ubah ID login (username) dan password. Setiap perubahan wajib dikonfirmasi dengan password Owner dan tercatat di Audit Log.</CardDescription>
          </div>
          <Button size="sm" className="gap-2" onClick={openCreate} data-testid="staff-add-button"><Plus className="h-4 w-4" /> Tambah Admin</Button>
        </CardHeader>
        <CardContent className="p-0">
          {!staff ? <div className="space-y-2 p-4">{[...Array(2)].map((_, i) => <Skeleton key={i} className="h-12" />)}</div> : (
            <Table data-testid="staff-table">
              <TableHeader>
                <TableRow><TableHead>Akun</TableHead><TableHead>Username (ID Login)</TableHead><TableHead>Role</TableHead><TableHead className="text-right">Aksi</TableHead></TableRow>
              </TableHeader>
              <TableBody>
                {staff.map((u) => (
                  <TableRow key={u.id} data-testid="staff-row">
                    <TableCell className="font-medium">{u.full_name}{admin?.id === u.id && <span className="ml-2 text-xs text-muted-foreground">(Anda)</span>}</TableCell>
                    <TableCell><code className="rounded bg-muted px-1.5 py-0.5 text-sm">{u.username}</code></TableCell>
                    <TableCell>
                      <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold", u.role === "owner" ? "bg-brand-yellow text-brand-yellow-foreground" : "bg-secondary text-secondary-foreground")}>
                        {u.role === "owner" ? <ShieldCheck className="h-3 w-3" /> : <UserCog className="h-3 w-3" />} {u.role === "owner" ? "Owner" : "Admin"}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button variant="outline" size="sm" className="gap-1.5" onClick={() => openEdit(u)} data-testid="staff-edit-button"><KeyRound className="h-3.5 w-3.5" /> Ubah ID / Password</Button>
                        {u.role !== "owner" && <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" aria-label="Hapus" onClick={() => setDeleteTarget(u)} data-testid="staff-delete-button"><Trash2 className="h-4 w-4" /></Button>}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
      <p className="flex items-start gap-2 text-xs text-muted-foreground"><Info className="mt-0.5 h-3.5 w-3.5 shrink-0" /> Halaman login staf tidak ditampilkan di toko. Akses melalui URL <code className="rounded bg-muted px-1">/rahasia-admin</code> atau ikon gembok kecil di pojok kanan bawah footer.</p>

      {/* Edit dialog */}
      <Dialog open={!!edit} onOpenChange={(o) => !o && setEdit(null)}>
        <DialogContent className="bg-card sm:max-w-md" data-testid="staff-edit-dialog">
          {edit && (
            <form onSubmit={submitEdit} className="space-y-4">
              <DialogHeader>
                <DialogTitle className="font-display">Ubah Kredensial {edit.role === "owner" ? "Owner" : "Admin"}</DialogTitle>
                <DialogDescription>Kosongkan password jika hanya ingin mengubah username / nama.</DialogDescription>
              </DialogHeader>
              <div className="space-y-1.5">
                <Label>Nama tampilan</Label>
                <Input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} data-testid="staff-full-name" />
              </div>
              <div className="space-y-1.5">
                <Label>Username (ID login) *</Label>
                <Input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} autoComplete="off" required data-testid="staff-username" />
                <p className="text-[11px] text-muted-foreground">Huruf kecil, angka, titik, strip, garis bawah. 3-50 karakter.</p>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label>Password baru</Label>
                  <Input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} autoComplete="new-password" placeholder="min. 6 karakter" data-testid="staff-password" />
                </div>
                <div className="space-y-1.5">
                  <Label>Konfirmasi password</Label>
                  <Input type="password" value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} autoComplete="new-password" data-testid="staff-password-confirm" />
                </div>
              </div>
              <div className="space-y-1.5 rounded-xl border border-brand-yellow/60 bg-accent p-3">
                <Label className="flex items-center gap-1.5"><ShieldCheck className="h-3.5 w-3.5 text-primary" /> Password Owner Anda saat ini *</Label>
                <Input type="password" value={form.owner_password} onChange={(e) => setForm({ ...form, owner_password: e.target.value })} autoComplete="current-password" required data-testid="staff-owner-password" />
              </div>
              <DialogFooter>
                <Button type="button" variant="ghost" onClick={() => setEdit(null)}>Batal</Button>
                <Button type="submit" disabled={saving} className="gap-2" data-testid="staff-save">{saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Simpan</Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Create dialog */}
      <Dialog open={create} onOpenChange={(o) => !o && setCreate(false)}>
        <DialogContent className="bg-card sm:max-w-md" data-testid="staff-create-dialog">
          <form onSubmit={submitCreate} className="space-y-4">
            <DialogHeader>
              <DialogTitle className="font-display">Tambah Akun Admin</DialogTitle>
              <DialogDescription>Admin dapat mengelola pesanan, produk, stok, piutang, dan pengeluaran. Tidak bisa melihat modal/laba, laporan, dan pengaturan.</DialogDescription>
            </DialogHeader>
            <div className="space-y-1.5"><Label>Nama *</Label><Input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required data-testid="staff-create-name" /></div>
            <div className="space-y-1.5"><Label>Username *</Label><Input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} autoComplete="off" required data-testid="staff-create-username" /></div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5"><Label>Password *</Label><Input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} autoComplete="new-password" required data-testid="staff-create-password" /></div>
              <div className="space-y-1.5"><Label>Konfirmasi *</Label><Input type="password" value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} autoComplete="new-password" required data-testid="staff-create-confirm" /></div>
            </div>
            <div className="space-y-1.5 rounded-xl border border-brand-yellow/60 bg-accent p-3">
              <Label className="flex items-center gap-1.5"><ShieldCheck className="h-3.5 w-3.5 text-primary" /> Password Owner Anda saat ini *</Label>
              <Input type="password" value={form.owner_password} onChange={(e) => setForm({ ...form, owner_password: e.target.value })} autoComplete="current-password" required data-testid="staff-create-owner-password" />
            </div>
            <DialogFooter>
              <Button type="button" variant="ghost" onClick={() => setCreate(false)}>Batal</Button>
              <Button type="submit" disabled={saving} className="gap-2" data-testid="staff-create-save">{saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />} Buat Akun</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!deleteTarget} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <AlertDialogContent className="bg-card">
          <AlertDialogHeader>
            <AlertDialogTitle>Hapus akun admin "{deleteTarget?.username}"?</AlertDialogTitle>
            <AlertDialogDescription>Akun tidak bisa lagi masuk ke panel admin. Riwayat aktivitasnya tetap tersimpan di Audit Log.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Batal</AlertDialogCancel>
            <AlertDialogAction onClick={remove} className="bg-destructive text-destructive-foreground hover:bg-destructive/90" data-testid="confirm-delete-staff">Hapus</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

/* ============================== Profil Toko ============================== */
const STORE_FIELDS = [
  ["store_name", "Nama Toko *", "text"], ["tagline", "Tagline", "text"], ["owner_name", "Nama Pemilik", "text"], ["operating_hours", "Jam Operasional", "text"],
  ["phone", "No. Telepon", "text"], ["whatsapp", "WhatsApp", "text"], ["email", "Email", "email"], ["city", "Kota / Kabupaten", "text"],
];

function StoreTab() {
  const guard = useAdminGuard();
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);
  const [meta, setMeta] = useState(null);

  useEffect(() => {
    api.get("/admin/settings/store").then((r) => { const { updated_at, updated_by, ...rest } = r.data; setForm(rest); setMeta({ updated_at, updated_by }); }).catch((e) => { if (!guard(e)) toast.error(errorMessage(e)); });
  }, [guard]);

  const submit = async (e) => {
    e.preventDefault();
    if (!form.store_name || form.store_name.trim().length < 2) return toast.error("Nama toko wajib diisi");
    setSaving(true);
    try {
      const { data } = await api.put("/admin/settings/store", form);
      const { updated_at, updated_by, ...rest } = data;
      setForm(rest); setMeta({ updated_at, updated_by });
      toast.success("Profil toko disimpan", { description: "Identitas & kontak tampil di footer toko." });
    } catch (err) {
      if (!guard(err)) toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  if (!form) return <div className="space-y-3"><Skeleton className="h-10 w-full" /><Skeleton className="h-64 w-full" /></div>;
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <form onSubmit={submit} className="space-y-4" data-testid="store-tab">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Identitas & Kontak Toko</CardTitle>
          <CardDescription>Ditampilkan di footer toko dan dokumen. Rekening bank hanya untuk internal.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          {STORE_FIELDS.map(([k, label, type]) => (
            <div key={k} className="space-y-1.5">
              <Label htmlFor={`store-${k}`}>{label}</Label>
              <Input id={`store-${k}`} type={type} value={form[k] || ""} onChange={set(k)} className="bg-card" required={k === "store_name"} data-testid={`store-${k}`} />
            </div>
          ))}
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="store-address">Alamat Lengkap</Label>
            <Textarea id="store-address" rows={2} value={form.address || ""} onChange={set("address")} className="bg-card" data-testid="store-address" />
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="store-description">Deskripsi Singkat</Label>
            <Textarea id="store-description" rows={3} value={form.description || ""} onChange={set("description")} className="bg-card" placeholder="Mitra pasokan bahan baku segar untuk dapur & UMKM..." data-testid="store-description" />
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Rekening Pembayaran (internal)</CardTitle>
          <CardDescription>Referensi untuk pelunasan piutang / transfer manual. Tidak dipublikasikan.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-3">
          <div className="space-y-1.5"><Label>Bank</Label><Input value={form.bank_name || ""} onChange={set("bank_name")} className="bg-card" data-testid="store-bank_name" /></div>
          <div className="space-y-1.5"><Label>No. Rekening</Label><Input value={form.bank_account || ""} onChange={set("bank_account")} className="bg-card" data-testid="store-bank_account" /></div>
          <div className="space-y-1.5"><Label>Atas Nama</Label><Input value={form.bank_holder || ""} onChange={set("bank_holder")} className="bg-card" data-testid="store-bank_holder" /></div>
        </CardContent>
      </Card>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">{meta?.updated_by ? `Terakhir diubah ${formatDate(meta.updated_at)} oleh ${meta.updated_by}` : "Belum pernah diubah"}</p>
        <Button type="submit" disabled={saving} className="gap-2" data-testid="store-save">{saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Simpan Profil Toko</Button>
      </div>
    </form>
  );
}

/* ============================== Database Pelanggan ============================== */
function CustomersTab() {
  const guard = useAdminGuard();
  const [data, setData] = useState(null);
  const [q, setQ] = useState("");
  const [segment, setSegment] = useState("all");
  const [sort, setSort] = useState("order_count");

  useEffect(() => {
    api.get("/admin/settings/customers").then((r) => setData(r.data)).catch((e) => { if (!guard(e)) toast.error(errorMessage(e)); });
  }, [guard]);

  const rows = useMemo(() => {
    if (!data) return [];
    const term = q.trim().toLowerCase();
    let list = data.customers.filter((c) => (segment === "all" || c.segment === segment) && (!term || c.full_name.toLowerCase().includes(term) || (c.phone || "").includes(term) || c.username.includes(term)));
    list = [...list].sort((a, b) => {
      if (sort === "last_order_at") return new Date(b.last_order_at || 0) - new Date(a.last_order_at || 0);
      if (sort === "created_at") return new Date(b.created_at) - new Date(a.created_at);
      return (b[sort] || 0) - (a[sort] || 0);
    });
    return list;
  }, [data, q, segment, sort]);

  const kpis = data ? [
    { key: "total", label: "Total Pelanggan", value: data.total_customers, icon: Users, cls: "border-primary/30 bg-primary text-primary-foreground", hint: "Akun terdaftar via checkout" },
    { key: "regular", label: "Pelanggan Tetap", value: data.regular_customers, icon: Sparkles, cls: "border-brand-yellow/60 bg-accent", hint: ">= 3 pesanan" },
    { key: "new", label: "Baru Bulan Ini", value: data.new_this_month, icon: Plus, cls: "bg-card", hint: "Mendaftar bulan berjalan" },
    { key: "recv", label: "Punya Piutang", value: data.with_receivables, icon: HandCoins, cls: data.with_receivables ? "border-violet-200 bg-violet-50" : "bg-card", hint: "Perlu ditagih" },
  ] : [];

  return (
    <div className="space-y-4" data-testid="customers-tab">
      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4" data-testid="customers-summary">
        {!data ? [...Array(4)].map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />) : kpis.map(({ key, label, value, icon: I, cls, hint }) => (
          <Card key={key} className={cn("border", cls)} data-testid={`customers-kpi-${key}`}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between"><p className={cn("text-xs font-medium", key === "total" ? "text-primary-foreground/80" : "text-muted-foreground")}>{label}</p><I className={cn("h-4 w-4", key === "total" ? "text-brand-yellow" : "text-primary")} /></div>
              <p className="mt-2 font-display text-lg font-semibold sm:text-2xl">{value}</p>
              <p className={cn("mt-1 text-[11px]", key === "total" ? "text-primary-foreground/70" : "text-muted-foreground")}>{hint}</p>
            </CardContent>
          </Card>
        ))}
      </section>

      <Card className="overflow-hidden">
        <CardHeader className="flex flex-col gap-3 pb-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <CardTitle className="text-base">Daftar Pelanggan {data && <Badge variant="secondary" className="ml-2 rounded-md">{rows.length}</Badge>}</CardTitle>
            <CardDescription>Analisis frekuensi transaksi untuk mengenali pelanggan tetap (kandidat fasilitas piutang).</CardDescription>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <div className="relative sm:w-56">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cari nama / telp..." className="bg-card pl-9" data-testid="customers-search" />
            </div>
            <Select value={segment} onValueChange={setSegment}>
              <SelectTrigger className="bg-card sm:w-44" data-testid="customers-segment-filter"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Semua segmen</SelectItem>
                {Object.entries(CUSTOMER_SEGMENT_LABEL).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}
              </SelectContent>
            </Select>
            <Select value={sort} onValueChange={setSort}>
              <SelectTrigger className="bg-card sm:w-48" data-testid="customers-sort"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="order_count">Paling sering pesan</SelectItem>
                <SelectItem value="total_all_orders">Nilai belanja terbesar</SelectItem>
                <SelectItem value="receivable_total">Piutang terbesar</SelectItem>
                <SelectItem value="last_order_at">Transaksi terakhir</SelectItem>
                <SelectItem value="created_at">Terbaru mendaftar</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {!data ? <div className="space-y-2 p-4">{[...Array(5)].map((_, i) => <Skeleton key={i} className="h-12" />)}</div> : rows.length === 0 ? (
            <div className="flex flex-col items-center gap-2 p-10 text-center text-sm text-muted-foreground" data-testid="customers-empty"><Users className="h-8 w-8" /> Tidak ada pelanggan yang cocok.</div>
          ) : (
            <div className="overflow-x-auto">
              <Table data-testid="customers-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Pelanggan</TableHead>
                    <TableHead>Segmen</TableHead>
                    <TableHead className="text-right">Pesanan</TableHead>
                    <TableHead className="text-right">Total Belanja</TableHead>
                    <TableHead className="text-right">Rata-rata</TableHead>
                    <TableHead className="text-right">Piutang</TableHead>
                    <TableHead>Transaksi Terakhir</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((c) => (
                    <TableRow key={c.id} data-testid="customer-row">
                      <TableCell>
                        <p className="font-medium">{c.full_name}</p>
                        <p className="text-xs text-muted-foreground">{c.phone || "-"} &middot; ID {c.username}</p>
                        {c.address && <p className="max-w-[260px] truncate text-[11px] text-muted-foreground">{c.address}</p>}
                      </TableCell>
                      <TableCell><SegmentBadge segment={c.segment} /></TableCell>
                      <TableCell className="text-right"><span className="font-semibold">{c.order_count}</span><span className="text-xs text-muted-foreground"> ({c.paid_orders} lunas)</span></TableCell>
                      <TableCell className="text-right font-medium">{rupiah(c.total_all_orders)}</TableCell>
                      <TableCell className="text-right text-muted-foreground">{rupiah(c.avg_order_value)}</TableCell>
                      <TableCell className={cn("text-right", c.receivable_total > 0 ? "font-semibold text-violet-800" : "text-muted-foreground")}>{c.receivable_total > 0 ? rupiah(c.receivable_total) : "-"}</TableCell>
                      <TableCell className="whitespace-nowrap text-sm">{c.last_order_at ? formatDate(c.last_order_at) : <span className="text-muted-foreground">Belum pernah</span>}<p className="text-[11px] text-muted-foreground">Daftar {formatDate(c.created_at, false)}</p></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

/* ============================== Sinkronisasi Data ============================== */
const CHECK_ICON = { order_items: ShoppingBag, orders: ReceiptText, products: Boxes, expenses: Wallet, customers: Users, receivables: HandCoins };

function SyncTab() {
  const guard = useAdminGuard();
  const [last, setLast] = useState(undefined);
  const [running, setRunning] = useState(false);
  const [confirm, setConfirm] = useState(false);

  useEffect(() => {
    api.get("/admin/settings/sync/last").then((r) => setLast(r.data || null)).catch((e) => { if (!guard(e)) setLast(null); });
  }, [guard]);

  const run = async () => {
    setConfirm(false);
    setRunning(true);
    try {
      const { data } = await api.post("/admin/settings/sync", {}, { timeout: 120000 });
      setLast(data);
      if (data.total_fixed > 0) toast.success(`Sinkronisasi selesai: ${data.total_fixed} nilai turunan diperbaiki`, { description: `${data.total_checked} record diperiksa dalam ${data.duration_ms} ms` });
      else toast.success("Sinkronisasi selesai: semua data sudah konsisten", { description: `${data.total_checked} record diperiksa dalam ${data.duration_ms} ms` });
      window.dispatchEvent(new Event("admin:event"));
    } catch (err) {
      if (!guard(err)) toast.error(errorMessage(err, "Sinkronisasi gagal"));
    } finally {
      setRunning(false);
    }
  };

  const snap = last?.snapshot;
  const snapItems = snap ? [
    { label: "Penjualan (Omzet)", value: rupiah(snap.sales_revenue), icon: Wallet, hint: `${snap.sold_orders} pesanan terjual` },
    { label: "Modal (HPP)", value: rupiah(snap.sales_cost), icon: Coins, hint: `${snap.items_sold} item` },
    { label: "Laba Kotor", value: rupiah(snap.gross_profit), icon: TrendingUp, hint: `Margin ${snap.margin_pct}%`, cls: snap.gross_profit < 0 ? "text-rose-700" : "text-emerald-700" },
    { label: "Pengeluaran", value: rupiah(snap.total_expenses), icon: ReceiptText, hint: "Seluruh periode" },
    { label: "Laba Bersih", value: rupiah(snap.net_profit), icon: TrendingUp, hint: "Laba kotor - pengeluaran", cls: snap.net_profit < 0 ? "text-rose-700" : "text-emerald-700" },
    { label: "Piutang Berjalan", value: rupiah(snap.receivables_total), icon: HandCoins, hint: `${snap.receivables_count} pesanan`, cls: "text-violet-800" },
    { label: "Nilai Stok", value: rupiah(snap.stock_value), icon: Boxes, hint: "Stok x harga beli" },
  ] : [];

  return (
    <div className="space-y-4" data-testid="sync-tab">
      <Card className="border-primary/30">
        <CardContent className="flex flex-col gap-4 p-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-start gap-3">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground"><RefreshCw className={cn("h-5 w-5", running && "animate-spin")} /></span>
            <div>
              <p className="font-display text-base font-semibold">Sinkronisasi Data</p>
              <p className="text-sm text-muted-foreground">Memvalidasi & menghitung ulang angka Penjualan, Pembelian (HPP), Pengeluaran, Keuangan, Laporan, dan Riwayat dari sumber tunggal agar tidak ada selisih. Aman dijalankan kapan saja: hanya nilai turunan yang diperbaiki, data utama tidak diubah/dihapus.</p>
            </div>
          </div>
          <Button size="lg" className="gap-2 lg:shrink-0" onClick={() => setConfirm(true)} disabled={running} data-testid="sync-run-button">
            {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />} {running ? "Memproses..." : "Sinkronisasi Data Sekarang"}
          </Button>
        </CardContent>
      </Card>

      {last === undefined ? <Skeleton className="h-40 w-full" /> : last === null ? (
        <Card><CardContent className="flex flex-col items-center gap-2 p-10 text-center text-sm text-muted-foreground" data-testid="sync-empty"><Info className="h-8 w-8" /> Belum pernah disinkronkan. Klik tombol di atas untuk menjalankan pemeriksaan pertama.</CardContent></Card>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-3" data-testid="sync-summary">
            <Card className={cn(last.total_warnings ? "border-amber-200 bg-amber-50" : "border-emerald-200 bg-emerald-50")}>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">{last.total_warnings ? <AlertTriangle className="h-4 w-4 text-amber-700" /> : <CheckCircle2 className="h-4 w-4 text-emerald-700" />}<p className="text-xs font-medium text-muted-foreground">Status</p></div>
                <p className={cn("mt-2 font-display text-lg font-semibold", last.total_warnings ? "text-amber-900" : "text-emerald-900")} data-testid="sync-status">{last.total_warnings ? `${last.total_warnings} peringatan` : "Semua konsisten"}</p>
                <p className="mt-1 text-[11px] text-muted-foreground">Terakhir: {formatDate(last.ran_at)} &middot; {last.duration_ms} ms</p>
              </CardContent>
            </Card>
            <Card><CardContent className="p-4"><p className="text-xs font-medium text-muted-foreground">Record Diperiksa</p><p className="mt-2 font-display text-lg font-semibold" data-testid="sync-checked">{last.total_checked}</p><p className="mt-1 text-[11px] text-muted-foreground">Item, pesanan, produk, pengeluaran, pelanggan, piutang</p></CardContent></Card>
            <Card><CardContent className="p-4"><p className="text-xs font-medium text-muted-foreground">Nilai Diperbaiki</p><p className="mt-2 font-display text-lg font-semibold" data-testid="sync-fixed">{last.total_fixed}</p><p className="mt-1 text-[11px] text-muted-foreground">Subtotal, total, tanggal lunas, snapshot HPP</p></CardContent></Card>
          </div>

          <Card data-testid="sync-checks">
            <CardHeader className="pb-3"><CardTitle className="text-base">Hasil Pemeriksaan</CardTitle></CardHeader>
            <CardContent className="p-0">
              <ul className="divide-y">
                {last.checks.map((c) => {
                  const I = CHECK_ICON[c.key] || CheckCircle2;
                  return (
                    <li key={c.key} className="px-4 py-3" data-testid={`sync-check-${c.key}`}>
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2 text-sm"><I className="h-4 w-4 text-primary" /> <span className="font-medium">{c.label}</span></div>
                        <div className="flex items-center gap-2 text-xs">
                          <span className="text-muted-foreground">{c.checked} diperiksa</span>
                          {c.fixed > 0 && <Badge variant="outline" className="rounded-md border-sky-200 bg-sky-50 text-sky-800">{c.fixed} diperbaiki</Badge>}
                          <Badge variant="outline" className={cn("rounded-md", c.status === "warning" ? "border-amber-200 bg-amber-50 text-amber-800" : "border-emerald-200 bg-emerald-50 text-emerald-800")}>{c.status === "warning" ? "Perlu perhatian" : c.status === "fixed" ? "Disinkronkan" : "OK"}</Badge>
                        </div>
                      </div>
                      {c.warnings.length > 0 && (
                        <ul className="mt-2 space-y-1 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
                          {c.warnings.map((w, i) => <li key={i} className="flex gap-2"><AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" /> {w}</li>)}
                        </ul>
                      )}
                    </li>
                  );
                })}
              </ul>
            </CardContent>
          </Card>

          <Card data-testid="sync-snapshot">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Angka Tersinkron (sumber tunggal)</CardTitle>
              <CardDescription>Nilai ini sama persis dengan yang ditampilkan di Dashboard, Piutang, Pengeluaran, dan Laporan.</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {snapItems.map(({ label, value, icon: I, hint, cls }) => (
                <div key={label} className="rounded-xl border bg-card p-3">
                  <div className="flex items-center justify-between"><p className="text-xs text-muted-foreground">{label}</p><I className="h-3.5 w-3.5 text-primary" /></div>
                  <p className={cn("mt-1 break-words font-display text-base font-semibold", cls)}>{value}</p>
                  <p className="text-[11px] text-muted-foreground">{hint}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </>
      )}

      <AlertDialog open={confirm} onOpenChange={setConfirm}>
        <AlertDialogContent className="bg-card">
          <AlertDialogHeader>
            <AlertDialogTitle>Jalankan sinkronisasi data?</AlertDialogTitle>
            <AlertDialogDescription>Sistem akan memeriksa seluruh item pesanan, pesanan, produk, pengeluaran, pelanggan, dan piutang, lalu memperbaiki nilai turunan yang tidak sinkron. Data utama tidak akan dihapus atau diubah. Proses biasanya selesai dalam beberapa detik.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Batal</AlertDialogCancel>
            <AlertDialogAction onClick={run} data-testid="sync-confirm">Ya, Sinkronkan</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
