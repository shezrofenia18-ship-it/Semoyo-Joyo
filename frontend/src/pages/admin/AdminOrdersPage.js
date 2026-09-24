import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Search, ClipboardList, Loader2, Eye, Pencil, Trash2, Save, CheckCircle2, HandCoins, Banknote, ArrowLeftRight, RefreshCw, QrCode, Landmark, CreditCard } from "lucide-react";
import { toast } from "sonner";
import { api, errorMessage } from "@/lib/api";
import { useAdminGuard } from "@/hooks/useAdminGuard";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { PaymentStatusBadge, OrderStatusBadge } from "@/components/StatusBadge";
import { PaymentMethodPicker, usePaymentConfig } from "@/components/PaymentMethodPicker";
import { rupiah, formatDate, paymentLabel, ORDER_STATUS_LABEL, PAYMENT_STATUS_LABEL, PAYMENT_METHOD_LABEL, PAYMENT_CHANNEL_LABEL, SETTLE_METHOD_LABEL } from "@/lib/format";

export default function AdminOrdersPage() {
  const guard = useAdminGuard();
  const { isOwner } = useAuth();
  const [searchParams] = useSearchParams();
  const config = usePaymentConfig();
  const [orders, setOrders] = useState(null);
  const [q, setQ] = useState(searchParams.get("q") || "");
  const [status, setStatus] = useState("all");
  const [pay, setPay] = useState("all");
  const [selected, setSelected] = useState(null);
  const [updating, setUpdating] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [settleTarget, setSettleTarget] = useState(null);
  const [settleForm, setSettleForm] = useState({ method: "cash", note: "" });
  const [cashTarget, setCashTarget] = useState(null);
  const [methodTarget, setMethodTarget] = useState(null);
  const [methodForm, setMethodForm] = useState({ payment_method: "cash", payment_channel: "qris", note: "" });

  const replaceOrder = (data) => {
    setOrders((prev) => (prev ? prev.map((o) => (o.id === data.id ? data : o)) : prev));
    setSelected((cur) => (cur?.id === data.id ? data : cur));
  };

  const submitSettle = async (e) => {
    e.preventDefault();
    if (!settleTarget) return;
    setUpdating(true);
    try {
      const { data } = await api.post(`/admin/orders/${settleTarget.id}/settle`, { method: settleForm.method, note: settleForm.note || null });
      replaceOrder(data);
      toast.success(`Pesanan ${data.order_number} ditandai LUNAS`);
      setSettleTarget(null);
    } catch (err) {
      if (!guard(err)) toast.error(errorMessage(err));
    } finally {
      setUpdating(false);
    }
  };

  const completeCash = async () => {
    if (!cashTarget) return;
    setUpdating(true);
    try {
      const { data } = await api.post(`/admin/orders/${cashTarget.id}/complete-cash`);
      replaceOrder(data);
      toast.success(`Uang tunai ${rupiah(data.total)} diterima`, { description: `Pesanan ${data.order_number} LUNAS & SELESAI` });
      setCashTarget(null);
    } catch (err) {
      if (!guard(err)) toast.error(errorMessage(err));
    } finally {
      setUpdating(false);
    }
  };

  const openMethodDialog = (o) => {
    setMethodForm({ payment_method: o.payment_method, payment_channel: o.payment_channel || "qris", note: "" });
    setMethodTarget(o);
  };

  const submitMethodChange = async (e) => {
    e.preventDefault();
    if (!methodTarget) return;
    if (methodForm.payment_method === "online" && !config?.online_enabled) return toast.error("Bayar Online belum aktif (kredensial BATPay belum dikonfigurasi)");
    setUpdating(true);
    try {
      const payload = { payment_method: methodForm.payment_method, payment_channel: methodForm.payment_method === "online" ? methodForm.payment_channel : null, note: methodForm.note || null };
      const { data } = await api.patch(`/admin/orders/${methodTarget.id}/payment-method`, payload);
      replaceOrder(data);
      toast.success("Metode pembayaran diubah", { description: `${data.order_number} -> ${paymentLabel(data)} · Total ${rupiah(data.total)}` });
      setMethodTarget(null);
    } catch (err) {
      if (!guard(err)) toast.error(errorMessage(err));
    } finally {
      setUpdating(false);
    }
  };

  const syncPayment = async (o) => {
    setUpdating(true);
    try {
      const { data } = await api.post(`/admin/orders/${o.id}/sync-payment`);
      replaceOrder(data);
      toast[data.payment_status === "paid" ? "success" : "info"](data.payment_status === "paid" ? "Pembayaran terverifikasi LUNAS" : `Status BATPay: ${PAYMENT_STATUS_LABEL[data.payment_status] || data.payment_status}`);
    } catch (err) {
      if (!guard(err)) toast.error(errorMessage(err));
    } finally {
      setUpdating(false);
    }
  };

  const openDetail = (o, edit = false) => {
    setSelected(o);
    setEditing(edit);
    setEditForm({ customer_name: o.customer_name, phone: o.phone, address: o.address, notes: o.notes || "", shipping_fee: o.shipping_fee ?? 0 });
  };

  const saveEdit = async (e) => {
    e.preventDefault();
    if (!selected || !editForm) return;
    if (!editForm.customer_name.trim() || editForm.customer_name.trim().length < 2) return toast.error("Nama pelanggan minimal 2 karakter");
    if (!editForm.address.trim() || editForm.address.trim().length < 5) return toast.error("Alamat minimal 5 karakter");
    setUpdating(true);
    try {
      const payload = { ...editForm, notes: editForm.notes || null, shipping_fee: Number(editForm.shipping_fee) || 0 };
      const { data } = await api.put(`/admin/orders/${selected.id}`, payload);
      replaceOrder(data);
      setEditing(false);
      toast.success("Data pesanan diperbarui");
    } catch (err) {
      if (!guard(err)) toast.error(errorMessage(err));
    } finally {
      setUpdating(false);
    }
  };

  const remove = async () => {
    if (!deleteTarget) return;
    try {
      await api.delete(`/admin/orders/${deleteTarget.id}`);
      setOrders((prev) => prev.filter((o) => o.id !== deleteTarget.id));
      if (selected?.id === deleteTarget.id) setSelected(null);
      toast.success(`Pesanan ${deleteTarget.order_number} dihapus`);
      setDeleteTarget(null);
    } catch (err) {
      if (!guard(err)) toast.error(errorMessage(err));
    }
  };

  const load = useCallback(() => {
    const params = {};
    if (status !== "all") params.status = status;
    if (pay !== "all") params.payment_status = pay;
    if (q.trim()) params.q = q.trim();
    api.get("/admin/orders", { params }).then((r) => setOrders(r.data)).catch((e) => { if (!guard(e)) toast.error(errorMessage(e)); });
  }, [guard, status, pay, q]);

  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
  }, [load]);

  // Auto-refresh saat ada notifikasi real-time (pesanan baru / pembayaran lunas)
  useEffect(() => {
    const onEvent = () => load();
    window.addEventListener("admin:event", onEvent);
    return () => window.removeEventListener("admin:event", onEvent);
  }, [load]);

  useEffect(() => {
    const qp = searchParams.get("q");
    if (qp) setQ(qp);
  }, [searchParams]);

  const update = async (field, value) => {
    if (!selected) return;
    setUpdating(true);
    try {
      const { data } = await api.patch(`/admin/orders/${selected.id}/status`, { [field]: value });
      replaceOrder(data);
      toast.success("Status diperbarui");
    } catch (e) {
      if (!guard(e)) toast.error(errorMessage(e));
    } finally {
      setUpdating(false);
    }
  };

  const unpaid = (o) => o && o.payment_status !== "paid" && o.order_status !== "dibatalkan";
  const ins = selected?.payment_payload?.instructions || {};

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-display text-2xl font-semibold">Pesanan</h1>
        <p className="text-sm text-muted-foreground">Pantau pembayaran (Cash, Bayar Nanti, Bayar Online) dan perbarui status pengiriman.</p>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cari no. pesanan / nama / telp..." className="bg-card pl-9" data-testid="admin-order-search" />
        </div>
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="bg-card sm:w-48" data-testid="admin-order-filter-status"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Semua status</SelectItem>
            {Object.entries(ORDER_STATUS_LABEL).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={pay} onValueChange={setPay}>
          <SelectTrigger className="bg-card sm:w-56" data-testid="admin-order-filter-payment"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Semua pembayaran</SelectItem>
            {Object.entries(PAYMENT_STATUS_LABEL).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      <Card className="overflow-hidden">
        {!orders ? (
          <div className="space-y-2 p-4">{[...Array(6)].map((_, i) => <Skeleton key={i} className="h-12" />)}</div>
        ) : orders.length === 0 ? (
          <div className="flex flex-col items-center gap-2 p-10 text-center text-sm text-muted-foreground"><ClipboardList className="h-8 w-8" /> Tidak ada pesanan.</div>
        ) : (
          <div className="overflow-x-auto">
            <Table data-testid="admin-orders-table">
              <TableHeader>
                <TableRow>
                  <TableHead>No. Pesanan</TableHead>
                  <TableHead>Pelanggan</TableHead>
                  <TableHead>Metode</TableHead>
                  <TableHead className="text-right">Total</TableHead>
                  <TableHead>Pembayaran</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Aksi</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {orders.map((o) => (
                  <TableRow key={o.id} data-testid="admin-order-row" className="cursor-pointer" onClick={() => openDetail(o)}>
                    <TableCell>
                      <p className="font-medium">{o.order_number}</p>
                      <p className="text-xs text-muted-foreground">{formatDate(o.created_at)}</p>
                    </TableCell>
                    <TableCell>
                      <p className="font-medium">{o.customer_name}</p>
                      <p className="text-xs text-muted-foreground">{o.phone}</p>
                    </TableCell>
                    <TableCell className="text-sm">
                      <p>{PAYMENT_METHOD_LABEL[o.payment_method] || o.payment_method}</p>
                      {o.payment_channel && <p className="text-xs text-muted-foreground">{PAYMENT_CHANNEL_LABEL[o.payment_channel] || o.payment_channel}</p>}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {rupiah(o.total)}
                      {Number(o.service_fee) > 0 && <p className="text-[11px] font-normal text-muted-foreground">termasuk layanan {rupiah(o.service_fee)}</p>}
                    </TableCell>
                    <TableCell><PaymentStatusBadge status={o.payment_status} /></TableCell>
                    <TableCell><OrderStatusBadge status={o.order_status} /></TableCell>
                    <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex justify-end gap-1">
                        {o.payment_method === "cash" && unpaid(o) && (
                          <Button size="sm" className="h-8 gap-1 bg-emerald-600 text-white hover:bg-emerald-700" title="Selesai / Terima Uang" onClick={() => setCashTarget(o)} data-testid="admin-order-complete-cash-button">
                            <Banknote className="h-3.5 w-3.5" /> Terima Uang
                          </Button>
                        )}
                        <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Detail" title="Detail" onClick={() => openDetail(o)} data-testid="admin-order-detail-button"><Eye className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Edit" title="Edit pesanan" onClick={() => openDetail(o, true)} data-testid="admin-edit-order-button"><Pencil className="h-4 w-4" /></Button>
                        {isOwner && <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" aria-label="Hapus" title="Hapus pesanan" onClick={() => setDeleteTarget(o)} data-testid="admin-delete-order-button"><Trash2 className="h-4 w-4" /></Button>}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>

      <Sheet open={!!selected} onOpenChange={(o) => !o && setSelected(null)}>
        <SheetContent className="w-full overflow-y-auto bg-background sm:max-w-lg" data-testid="admin-order-sheet">
          {selected && (
            <>
              <SheetHeader className="text-left">
                <SheetTitle className="font-display">{selected.order_number}</SheetTitle>
                <SheetDescription>{formatDate(selected.created_at)}</SheetDescription>
              </SheetHeader>
              <div className="mt-5 space-y-5">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label>Status Pesanan</Label>
                    <Select value={selected.order_status} onValueChange={(v) => update("order_status", v)} disabled={updating}>
                      <SelectTrigger data-testid="admin-order-status-select"><SelectValue /></SelectTrigger>
                      <SelectContent>{Object.entries(ORDER_STATUS_LABEL).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <Label>Status Pembayaran</Label>
                    <Select value={selected.payment_status} onValueChange={(v) => update("payment_status", v)} disabled={updating}>
                      <SelectTrigger data-testid="admin-payment-status-select"><SelectValue /></SelectTrigger>
                      <SelectContent>{Object.entries(PAYMENT_STATUS_LABEL).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                </div>
                {updating && <p className="flex items-center gap-2 text-xs text-muted-foreground"><Loader2 className="h-3 w-3 animate-spin" /> Menyimpan...</p>}

                {editing && editForm ? (
                  <form onSubmit={saveEdit} className="space-y-3 rounded-xl border border-primary/30 bg-card p-4 text-sm" data-testid="admin-order-edit-form">
                    <p className="font-semibold">Edit Data Pesanan</p>
                    <div className="space-y-1.5">
                      <Label>Nama Pelanggan *</Label>
                      <Input value={editForm.customer_name} onChange={(e) => setEditForm({ ...editForm, customer_name: e.target.value })} data-testid="order-edit-name" required />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1.5">
                        <Label>No. Telp/WA *</Label>
                        <Input value={editForm.phone} onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })} data-testid="order-edit-phone" required />
                      </div>
                      <div className="space-y-1.5">
                        <Label>Ongkir (Rp)</Label>
                        <Input type="number" min="0" value={editForm.shipping_fee} onChange={(e) => setEditForm({ ...editForm, shipping_fee: e.target.value })} data-testid="order-edit-shipping" />
                      </div>
                    </div>
                    <div className="space-y-1.5">
                      <Label>Alamat *</Label>
                      <Textarea rows={2} value={editForm.address} onChange={(e) => setEditForm({ ...editForm, address: e.target.value })} data-testid="order-edit-address" required />
                    </div>
                    <div className="space-y-1.5">
                      <Label>Catatan</Label>
                      <Textarea rows={2} value={editForm.notes} onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })} data-testid="order-edit-notes" />
                    </div>
                    <div className="flex justify-end gap-2">
                      <Button type="button" variant="ghost" size="sm" onClick={() => setEditing(false)}>Batal</Button>
                      <Button type="submit" size="sm" className="gap-2" disabled={updating} data-testid="order-edit-save">
                        {updating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Simpan
                      </Button>
                    </div>
                  </form>
                ) : (
                  <div className="rounded-xl border bg-card p-4 text-sm">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="font-semibold">{selected.customer_name}</p>
                        <p className="text-muted-foreground">{selected.phone}</p>
                        <p className="text-muted-foreground">{selected.address}</p>
                        {selected.notes && <p className="mt-2 text-xs italic text-muted-foreground">Catatan: {selected.notes}</p>}
                      </div>
                      <Button variant="outline" size="sm" className="shrink-0 gap-1" onClick={() => setEditing(true)} data-testid="order-sheet-edit-button"><Pencil className="h-3.5 w-3.5" /> Edit</Button>
                    </div>
                  </div>
                )}

                {/* ---------- Pembayaran ---------- */}
                <div className="rounded-xl border bg-card p-4 text-sm" data-testid="order-sheet-payment-card">
                  <div className="mb-2 flex items-start justify-between gap-2">
                    <p className="font-semibold">Pembayaran</p>
                    <PaymentStatusBadge status={selected.payment_status} />
                  </div>
                  <p className="flex items-center gap-1.5 font-medium" data-testid="order-sheet-payment-method">
                    {selected.payment_method === "cash" ? <Banknote className="h-4 w-4 text-sky-700" /> : selected.payment_method === "piutang" ? <HandCoins className="h-4 w-4 text-violet-700" /> : String(selected.payment_channel || "").startsWith("va_") ? <Landmark className="h-4 w-4 text-primary" /> : <QrCode className="h-4 w-4 text-primary" />}
                    {paymentLabel(selected)}
                  </p>
                  {selected.payment_ref && <p className="break-all text-xs text-muted-foreground">Ref: {selected.payment_ref}</p>}
                  {selected.paid_at && <p className="text-xs text-emerald-700">Lunas {formatDate(selected.paid_at)}</p>}
                  {selected.payment_status === "proses" && <p className="mt-1 text-xs text-sky-800">Menunggu kasir menerima uang tunai.</p>}
                  {selected.payment_status === "piutang" && (
                    <p className="mt-1 flex items-center gap-1 text-xs text-violet-800"><HandCoins className="h-3.5 w-3.5" /> Piutang / kasbon - belum dibayar</p>
                  )}
                  {selected.payment_method === "online" && selected.payment_status === "pending" && (
                    <p className="mt-1 text-xs text-amber-800">
                      {ins.status === "active" ? `Tagihan BATPay aktif${ins.va_number ? ` · VA ${ins.va_number}` : ""}${ins.expires_at ? ` · berlaku s/d ${formatDate(ins.expires_at)}` : ""}` : "BATPay belum aktif - tagihan menunggu aktivasi integrasi."}
                    </p>
                  )}
                  {selected.payment_payload?.method_changed && (
                    <p className="mt-1 text-[11px] text-muted-foreground">
                      Metode diubah oleh {selected.payment_payload.method_changed.by}: {PAYMENT_METHOD_LABEL[selected.payment_payload.method_changed.from] || selected.payment_payload.method_changed.from} -&gt; {PAYMENT_METHOD_LABEL[selected.payment_payload.method_changed.to] || selected.payment_payload.method_changed.to}
                    </p>
                  )}

                  {unpaid(selected) && (
                    <div className="mt-3 space-y-2">
                      {selected.payment_method === "cash" && (
                        <Button size="sm" className="w-full gap-2 bg-emerald-600 text-white hover:bg-emerald-700" onClick={() => setCashTarget(selected)} disabled={updating} data-testid="order-sheet-complete-cash-button">
                          <Banknote className="h-4 w-4" /> Selesai / Terima Uang
                        </Button>
                      )}
                      {selected.payment_method !== "cash" && (
                        <Button size="sm" className="w-full gap-2 bg-emerald-600 text-white hover:bg-emerald-700" onClick={() => { setSettleForm({ method: "cash", note: "" }); setSettleTarget(selected); }} disabled={updating} data-testid="order-sheet-settle-button">
                          <CheckCircle2 className="h-4 w-4" /> Tandai Lunas (pembayaran diterima)
                        </Button>
                      )}
                      <div className="grid grid-cols-2 gap-2">
                        <Button size="sm" variant="outline" className="gap-1.5" onClick={() => openMethodDialog(selected)} disabled={updating} data-testid="order-sheet-change-method-button">
                          <ArrowLeftRight className="h-3.5 w-3.5" /> Ubah Metode Pembayaran
                        </Button>
                        {selected.payment_method === "online" && (
                          <Button size="sm" variant="outline" className="gap-1.5" onClick={() => syncPayment(selected)} disabled={updating || !config?.online_enabled} title={config?.online_enabled ? "Cek status ke BATPay" : "BATPay belum aktif"} data-testid="order-sheet-sync-payment-button">
                            <RefreshCw className="h-3.5 w-3.5" /> Cek Status BATPay
                          </Button>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                <div className="rounded-xl border bg-card p-4 text-sm">
                  <p className="mb-2 font-semibold">Item ({selected.items.length})</p>
                  <ul className="space-y-1.5">
                    {selected.items.map((it) => (
                      <li key={it.id} className="flex justify-between gap-2">
                        <span className="min-w-0 truncate">{it.product_name} <span className="text-muted-foreground">x{it.qty} {it.unit}</span></span>
                        <span className="shrink-0">{rupiah(it.subtotal)}</span>
                      </li>
                    ))}
                  </ul>
                  <Separator className="my-3" />
                  <div className="flex justify-between text-muted-foreground"><span>Subtotal</span><span>{rupiah(selected.subtotal)}</span></div>
                  {Number(selected.shipping_fee) > 0 && <div className="flex justify-between text-muted-foreground"><span>Ongkir</span><span>{rupiah(selected.shipping_fee)}</span></div>}
                  {Number(selected.service_fee) > 0 && <div className="flex justify-between text-muted-foreground" data-testid="order-sheet-service-fee"><span>Biaya Layanan (BATPay)</span><span>{rupiah(selected.service_fee)}</span></div>}
                  <div className="flex justify-between font-semibold"><span>Total</span><span className="font-display text-base" data-testid="order-sheet-total">{rupiah(selected.total)}</span></div>
                </div>

                {isOwner && (
                  <Button variant="outline" className="w-full gap-2 border-destructive/40 text-destructive hover:bg-destructive/10" onClick={() => setDeleteTarget(selected)} data-testid="order-sheet-delete-button">
                    <Trash2 className="h-4 w-4" /> Hapus Pesanan
                  </Button>
                )}
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>

      {/* ---------- Dialog: Selesai / Terima Uang (Cash) ---------- */}
      <AlertDialog open={!!cashTarget} onOpenChange={(o) => !o && setCashTarget(null)}>
        <AlertDialogContent className="bg-card" data-testid="complete-cash-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2"><Banknote className="h-5 w-5 text-emerald-600" /> Selesai / Terima Uang</AlertDialogTitle>
            <AlertDialogDescription>
              Konfirmasi uang tunai <b className="text-foreground">{rupiah(cashTarget?.total)}</b> dari <b className="text-foreground">{cashTarget?.customer_name}</b> untuk pesanan {cashTarget?.order_number} telah diterima.
              Status pembayaran menjadi <b>Lunas</b> dan pesanan menjadi <b>Selesai</b>.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={updating}>Batal</AlertDialogCancel>
            <AlertDialogAction onClick={(e) => { e.preventDefault(); completeCash(); }} disabled={updating} className="gap-2 bg-emerald-600 text-white hover:bg-emerald-700" data-testid="confirm-complete-cash">
              {updating ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />} Ya, Uang Diterima
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* ---------- Dialog: Ubah Metode Pembayaran ---------- */}
      <Dialog open={!!methodTarget} onOpenChange={(o) => !o && setMethodTarget(null)}>
        <DialogContent className="max-h-[90vh] overflow-y-auto bg-card sm:max-w-lg" data-testid="change-method-dialog">
          {methodTarget && (
            <form onSubmit={submitMethodChange} className="space-y-4">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2 font-display"><CreditCard className="h-5 w-5 text-primary" /> Ubah Metode Pembayaran</DialogTitle>
                <DialogDescription>
                  {methodTarget.order_number} &middot; {methodTarget.customer_name} &middot; saat ini <b className="text-foreground">{paymentLabel(methodTarget)}</b> ({rupiah(methodTarget.total)})
                </DialogDescription>
              </DialogHeader>
              <PaymentMethodPicker
                method={methodForm.payment_method}
                onMethodChange={(v) => setMethodForm((f) => ({ ...f, payment_method: v }))}
                channel={methodForm.payment_channel}
                onChannelChange={(v) => setMethodForm((f) => ({ ...f, payment_channel: v }))}
                amount={Number(methodTarget.subtotal) + Number(methodTarget.shipping_fee || 0)}
                config={config}
                compact
                idPrefix="admin-method"
                disabled={updating}
              />
              <div className="space-y-1.5">
                <Label>Catatan (opsional)</Label>
                <Textarea rows={2} placeholder="mis. Pelanggan minta bayar nanti" value={methodForm.note} onChange={(e) => setMethodForm({ ...methodForm, note: e.target.value })} data-testid="change-method-note" />
              </div>
              <DialogFooter>
                <Button type="button" variant="ghost" onClick={() => setMethodTarget(null)} disabled={updating}>Batal</Button>
                <Button type="submit" disabled={updating || (methodForm.payment_method === methodTarget.payment_method && (methodForm.payment_method !== "online" || methodForm.payment_channel === methodTarget.payment_channel))} className="gap-2" data-testid="change-method-submit">
                  {updating ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowLeftRight className="h-4 w-4" />} Simpan Metode
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* ---------- Dialog: Tandai Lunas ---------- */}
      <Dialog open={!!settleTarget} onOpenChange={(o) => !o && setSettleTarget(null)}>
        <DialogContent className="bg-card sm:max-w-md" data-testid="order-settle-dialog">
          {settleTarget && (
            <form onSubmit={submitSettle} className="space-y-4">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2 font-display"><CheckCircle2 className="h-5 w-5 text-emerald-600" /> Konfirmasi Pelunasan</DialogTitle>
                <DialogDescription>{settleTarget.order_number} &middot; {settleTarget.customer_name} &middot; <b className="text-foreground">{rupiah(settleTarget.total)}</b></DialogDescription>
              </DialogHeader>
              <div className="space-y-1.5">
                <Label>Diterima melalui *</Label>
                <Select value={settleForm.method} onValueChange={(v) => setSettleForm({ ...settleForm, method: v })}>
                  <SelectTrigger data-testid="order-settle-method"><SelectValue /></SelectTrigger>
                  <SelectContent>{Object.entries(SETTLE_METHOD_LABEL).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Catatan</Label>
                <Textarea rows={2} placeholder="mis. Transfer diterima di rekening toko" value={settleForm.note} onChange={(e) => setSettleForm({ ...settleForm, note: e.target.value })} data-testid="order-settle-note" />
              </div>
              <DialogFooter>
                <Button type="button" variant="ghost" onClick={() => setSettleTarget(null)}>Batal</Button>
                <Button type="submit" disabled={updating} className="gap-2 bg-emerald-600 text-white hover:bg-emerald-700" data-testid="order-settle-submit">
                  {updating ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />} Tandai Lunas
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!deleteTarget} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <AlertDialogContent className="bg-card">
          <AlertDialogHeader>
            <AlertDialogTitle>Hapus pesanan {deleteTarget?.order_number}?</AlertDialogTitle>
            <AlertDialogDescription>
              Pesanan atas nama "{deleteTarget?.customer_name}" akan dihapus permanen. {deleteTarget?.order_status !== "dibatalkan" ? "Stok barang pada pesanan ini akan dikembalikan otomatis." : ""}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Batal</AlertDialogCancel>
            <AlertDialogAction onClick={remove} className="bg-destructive text-destructive-foreground hover:bg-destructive/90" data-testid="confirm-delete-order">Hapus</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
