import { useCallback, useEffect, useState } from "react";
import { Search, ScrollText, ShieldCheck, UserCog, LogIn, Plus, Pencil, Trash2, Boxes, RefreshCw, Download } from "lucide-react";
import { toast } from "sonner";
import { api, errorMessage } from "@/lib/api";
import { useAdminGuard } from "@/hooks/useAdminGuard";
import { useAuth } from "@/context/AuthContext";
import { Navigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";

const ACTION = {
  login: { label: "Masuk", icon: LogIn, cls: "bg-slate-50 text-slate-700 border-slate-200" },
  create: { label: "Tambah", icon: Plus, cls: "bg-emerald-50 text-emerald-800 border-emerald-200" },
  update: { label: "Ubah", icon: Pencil, cls: "bg-sky-50 text-sky-800 border-sky-200" },
  status: { label: "Status", icon: RefreshCw, cls: "bg-indigo-50 text-indigo-800 border-indigo-200" },
  stock_adjust: { label: "Stok", icon: Boxes, cls: "bg-amber-50 text-amber-800 border-amber-200" },
  delete: { label: "Hapus", icon: Trash2, cls: "bg-rose-50 text-rose-800 border-rose-200" },
  export: { label: "Unduh Laporan", icon: Download, cls: "bg-violet-50 text-violet-800 border-violet-200" },
};
const ENTITY = { auth: "Autentikasi", product: "Produk", category: "Kategori", order: "Pesanan", stock: "Stok", report: "Laporan" };

export default function AdminAuditLogPage() {
  const guard = useAdminGuard();
  const { isOwner } = useAuth();
  const [rows, setRows] = useState(null);
  const [staff, setStaff] = useState([]);
  const [q, setQ] = useState("");
  const [actor, setActor] = useState("all");
  const [action, setAction] = useState("all");
  const [entity, setEntity] = useState("all");

  const load = useCallback(() => {
    const params = { limit: 200 };
    if (actor !== "all") params.actor = actor;
    if (action !== "all") params.action = action;
    if (entity !== "all") params.entity_type = entity;
    if (q.trim()) params.q = q.trim();
    api.get("/admin/audit-logs", { params }).then((r) => setRows(r.data)).catch((e) => { if (!guard(e)) toast.error(errorMessage(e)); });
  }, [guard, actor, action, entity, q]);

  useEffect(() => {
    if (!isOwner) return;
    api.get("/admin/staff").then((r) => setStaff(r.data)).catch(() => {});
  }, [isOwner]);

  useEffect(() => {
    if (!isOwner) return undefined;
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
  }, [load, isOwner]);

  if (!isOwner) return <Navigate to="/admin/dashboard" replace />;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 font-display text-2xl font-semibold"><ScrollText className="h-6 w-6 text-primary" /> Audit Log</h1>
          <p className="text-sm text-muted-foreground">Riwayat semua aktivitas akun Admin & Owner di panel: login, tambah/ubah/hapus data, perubahan stok dan status pesanan.</p>
        </div>
        <Button variant="outline" size="sm" className="gap-2" onClick={load} data-testid="audit-refresh"><RefreshCw className="h-4 w-4" /> Muat ulang</Button>
      </div>

      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-[1fr_180px_180px_180px]">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cari aktivitas / nama produk / no. pesanan..." className="bg-card pl-9" data-testid="audit-search" />
        </div>
        <Select value={actor} onValueChange={setActor}>
          <SelectTrigger className="bg-card" data-testid="audit-filter-actor"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Semua akun</SelectItem>
            {staff.map((u) => <SelectItem key={u.id} value={u.username}>{u.username} ({u.role})</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={action} onValueChange={setAction}>
          <SelectTrigger className="bg-card" data-testid="audit-filter-action"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Semua aksi</SelectItem>
            {Object.entries(ACTION).map(([k, v]) => <SelectItem key={k} value={k}>{v.label}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={entity} onValueChange={setEntity}>
          <SelectTrigger className="bg-card" data-testid="audit-filter-entity"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Semua objek</SelectItem>
            {Object.entries(ENTITY).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      <Card className="overflow-hidden">
        {!rows ? (
          <div className="space-y-2 p-4">{[...Array(8)].map((_, i) => <Skeleton key={i} className="h-10" />)}</div>
        ) : rows.length === 0 ? (
          <div className="flex flex-col items-center gap-2 p-10 text-center text-sm text-muted-foreground"><ScrollText className="h-8 w-8" /> Belum ada aktivitas yang cocok.</div>
        ) : (
          <div className="overflow-x-auto">
            <Table data-testid="audit-log-table">
              <TableHeader>
                <TableRow>
                  <TableHead>Waktu</TableHead>
                  <TableHead>Akun</TableHead>
                  <TableHead>Aksi</TableHead>
                  <TableHead>Objek</TableHead>
                  <TableHead>Keterangan</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((r) => {
                  const a = ACTION[r.action] || { label: r.action, icon: Pencil, cls: "" };
                  const I = a.icon;
                  return (
                    <TableRow key={r.id} data-testid="audit-log-row">
                      <TableCell className="whitespace-nowrap text-xs text-muted-foreground">{formatDate(r.created_at)}</TableCell>
                      <TableCell>
                        <span className="inline-flex items-center gap-1.5 text-sm font-medium">
                          {r.actor_role === "owner" ? <ShieldCheck className="h-3.5 w-3.5 text-primary" /> : <UserCog className="h-3.5 w-3.5 text-muted-foreground" />}
                          {r.actor_username}
                        </span>
                        <p className="text-[11px] capitalize text-muted-foreground">{r.actor_role}</p>
                      </TableCell>
                      <TableCell><Badge variant="outline" className={cn("gap-1 rounded-md font-medium", a.cls)}><I className="h-3 w-3" /> {a.label}</Badge></TableCell>
                      <TableCell className="text-sm">{ENTITY[r.entity_type] || r.entity_type}{r.entity_label && <p className="max-w-[180px] truncate text-xs text-muted-foreground">{r.entity_label}</p>}</TableCell>
                      <TableCell className="max-w-md text-sm">{r.description}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>
    </div>
  );
}
