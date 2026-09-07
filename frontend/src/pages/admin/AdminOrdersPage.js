import { useCallback, useEffect, useState } from "react";
import { Search, ClipboardList, Loader2, Eye } from "lucide-react";
import { toast } from "sonner";
import { api, errorMessage } from "@/lib/api";
import { useAdminGuard } from "@/hooks/useAdminGuard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Label } from "@/components/ui/label";
import { PaymentStatusBadge, OrderStatusBadge } from "@/components/StatusBadge";
import { rupiah, formatDate, ORDER_STATUS_LABEL, PAYMENT_STATUS_LABEL, PAYMENT_METHOD_LABEL, CHANNEL_LABEL } from "@/lib/format";

export default function AdminOrdersPage() {
  const guard = useAdminGuard();
  const [orders, setOrders] = useState(null);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("all");
  const [pay, setPay] = useState("all");
  const [selected, setSelected] = useState(null);
  const [updating, setUpdating] = useState(false);

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

  const update = async (field, value) => {
    if (!selected) return;
    setUpdating(true);
    try {
      const { data } = await api.patch(`/admin/orders/${selected.id}/status`, { [field]: value });
      setSelected(data);
      setOrders((prev) => prev.map((o) => (o.id === data.id ? data : o)));
      toast.success("Status diperbarui");
    } catch (e) {
      if (!guard(e)) toast.error(errorMessage(e));
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-display text-2xl font-semibold">Pesanan</h1>
        <p className="text-sm text-muted-foreground">Pantau pembayaran dan perbarui status pengiriman.</p>
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
          <SelectTrigger className="bg-card sm:w-52" data-testid="admin-order-filter-payment"><SelectValue /></SelectTrigger>
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
                  <TableRow key={o.id} data-testid="admin-order-row" className="cursor-pointer" onClick={() => setSelected(o)}>
                    <TableCell>
                      <p className="font-medium">{o.order_number}</p>
                      <p className="text-xs text-muted-foreground">{formatDate(o.created_at)}</p>
                    </TableCell>
                    <TableCell>
                      <p className="font-medium">{o.customer_name}</p>
                      <p className="text-xs text-muted-foreground">{o.phone}</p>
                    </TableCell>
                    <TableCell className="text-sm">{PAYMENT_METHOD_LABEL[o.payment_method]}{o.payment_channel ? ` (${CHANNEL_LABEL[o.payment_channel] || o.payment_channel})` : ""}</TableCell>
                    <TableCell className="text-right font-medium">{rupiah(o.total)}</TableCell>
                    <TableCell><PaymentStatusBadge status={o.payment_status} /></TableCell>
                    <TableCell><OrderStatusBadge status={o.order_status} /></TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Detail" data-testid="admin-order-detail-button"><Eye className="h-4 w-4" /></Button>
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

                <div className="rounded-xl border bg-card p-4 text-sm">
                  <p className="font-semibold">{selected.customer_name}</p>
                  <p className="text-muted-foreground">{selected.phone}</p>
                  <p className="text-muted-foreground">{selected.address}</p>
                  {selected.notes && <p className="mt-2 text-xs italic text-muted-foreground">Catatan: {selected.notes}</p>}
                </div>

                <div className="rounded-xl border bg-card p-4 text-sm">
                  <p className="mb-2 font-semibold">Pembayaran</p>
                  <p>{PAYMENT_METHOD_LABEL[selected.payment_method]}{selected.payment_channel ? ` - ${CHANNEL_LABEL[selected.payment_channel] || selected.payment_channel}` : ""}</p>
                  {selected.payment_ref && <p className="break-all text-xs text-muted-foreground">Ref: {selected.payment_ref}</p>}
                  {selected.paid_at && <p className="text-xs text-emerald-700">Lunas {formatDate(selected.paid_at)}</p>}
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
                  <div className="flex justify-between font-semibold"><span>Total</span><span className="font-display text-base">{rupiah(selected.total)}</span></div>
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
