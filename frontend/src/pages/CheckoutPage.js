import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, ShoppingCart, Info } from "lucide-react";
import { toast } from "sonner";
import { api, errorMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { ProductImage } from "@/components/ProductImage";
import { EmptyState } from "@/components/EmptyState";
import { PaymentMethodPicker, usePaymentConfig, useFeePreview, channelFee } from "@/components/PaymentMethodPicker";
import { useCart } from "@/context/CartContext";
import { useAuth } from "@/context/AuthContext";
import { rupiah, PAYMENT_CHANNEL_LABEL } from "@/lib/format";

const SUBMIT_LABEL = { cash: "Buat Pesanan (Tunai)", piutang: "Buat Pesanan (Bayar Nanti)", online: "Buat Pesanan & Bayar Online" };

export default function CheckoutPage() {
  const { items, subtotal, clear } = useCart();
  const { user, loginCustomer } = useAuth();
  const navigate = useNavigate();
  const config = usePaymentConfig();
  const [form, setForm] = useState({ full_name: "", phone: "", address: "", notes: "" });
  const [method, setMethod] = useState("cash");
  const [channel, setChannel] = useState("qris");
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const fee = useFeePreview(subtotal, method === "online");
  const serviceFee = method === "online" ? channelFee(fee, channel) : 0;
  const grandTotal = subtotal + serviceFee;

  useEffect(() => {
    if (user) setForm((f) => ({ ...f, full_name: f.full_name || user.full_name || "", phone: f.phone || user.phone || "", address: f.address || user.address || "" }));
  }, [user]);

  const validate = () => {
    const e = {};
    if (form.full_name.trim().length < 2) e.full_name = "Nama / nama usaha wajib diisi (min. 2 karakter)";
    const digits = form.phone.replace(/\D/g, "");
    if (digits.length < 9) e.phone = "No. Telp/WA tidak valid";
    if (form.address.trim().length < 5) e.address = "Alamat wajib diisi dengan lengkap";
    if (method === "online" && !config?.online_enabled) e.method = "Bayar Online belum aktif, pilih metode lain";
    setErrors(e);
    if (e.method) toast.error(e.method);
    return Object.keys(e).length === 0;
  };

  const submit = async (ev) => {
    ev.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    try {
      const payload = {
        full_name: form.full_name.trim(),
        phone: form.phone.trim(),
        address: form.address.trim(),
        notes: form.notes.trim() || null,
        payment_method: method,
        payment_channel: method === "online" ? channel : null,
        items: items.map((i) => ({ product_id: i.product_id, qty: i.qty })),
      };
      const { data } = await api.post("/checkout", payload);
      loginCustomer(data.access_token, data.user);
      clear();
      toast.success("Pesanan berhasil dibuat", { description: `No. pesanan ${data.order.order_number}` });
      navigate(`/pembayaran/${data.order.order_number}`, { replace: true });
    } catch (err) {
      toast.error(errorMessage(err, "Checkout gagal"));
    } finally {
      setSubmitting(false);
    }
  };

  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
        <EmptyState icon={ShoppingCart} title="Keranjang kosong" description="Tambahkan produk sebelum melanjutkan checkout." actionLabel="Kembali ke Beranda" onAction={() => navigate("/")} testId="checkout-empty-state" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
      <h1 className="font-display text-2xl font-semibold sm:text-3xl">Checkout</h1>
      <p className="mt-1 text-sm text-muted-foreground">Lengkapi data pengiriman dan pilih metode pembayaran.</p>

      <form onSubmit={submit} className="mt-6 grid gap-6 lg:grid-cols-[1fr_380px]" noValidate>
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="font-display text-lg">Data Pemesan & Pengiriman</CardTitle>
              <CardDescription className="flex items-start gap-2">
                <Info className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                Nama / Nama usaha akan digunakan sebagai ID login untuk melihat riwayat pesanan Anda.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="full_name">Nama / Nama usaha *</Label>
                <Input id="full_name" data-testid="checkout-full-name-input" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} className="h-11 bg-card" />
                {errors.full_name && <p className="text-xs text-destructive" data-testid="error-full-name">{errors.full_name}</p>}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="phone">No. Telp / WA *</Label>
                <Input id="phone" data-testid="checkout-phone-input" placeholder="08xxxxxxxxxx" inputMode="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="h-11 bg-card" />
                {errors.phone && <p className="text-xs text-destructive" data-testid="error-phone">{errors.phone}</p>}
              </div>
              <div className="space-y-1.5 sm:col-span-2">
                <Label htmlFor="address">Alamat Pengiriman *</Label>
                <Textarea id="address" data-testid="checkout-address-textarea" placeholder="Nama jalan, kecamatan, kota/kabupaten, patokan" rows={3} value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} className="bg-card" />
                {errors.address && <p className="text-xs text-destructive" data-testid="error-address">{errors.address}</p>}
              </div>
              <div className="space-y-1.5 sm:col-span-2">
                <Label htmlFor="notes">Catatan (opsional)</Label>
                <Textarea id="notes" data-testid="checkout-notes-textarea" placeholder="Contoh: Kirim pagi sebelum jam 09.00" rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className="bg-card" />
              </div>
            </CardContent>
          </Card>

          <Card data-testid="checkout-payment-card">
            <CardHeader>
              <CardTitle className="font-display text-lg">Metode Pembayaran</CardTitle>
              <CardDescription>Pilih salah satu: Cash (Tunai), Bayar Nanti, atau Bayar Online.</CardDescription>
            </CardHeader>
            <CardContent>
              <PaymentMethodPicker method={method} onMethodChange={setMethod} channel={channel} onChannelChange={setChannel} amount={subtotal} config={config} idPrefix="checkout" />
            </CardContent>
          </Card>
        </div>

        <div className="lg:sticky lg:top-24 lg:self-start">
          <Card data-testid="checkout-order-summary">
            <CardHeader className="pb-3">
              <CardTitle className="font-display text-lg">Ringkasan Pesanan</CardTitle>
              <CardDescription>{items.length} jenis produk</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <ul className="max-h-72 space-y-3 overflow-y-auto pr-1">
                {items.map((it) => (
                  <li key={it.product_id} className="flex items-center gap-3 text-sm">
                    <div className="h-11 w-11 shrink-0 overflow-hidden rounded-md bg-muted">
                      <ProductImage src={it.image_url} alt={it.name} iconClassName="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium">{it.name}</p>
                      <p className="text-xs text-muted-foreground">{it.qty} {it.unit} x {rupiah(it.price)}</p>
                    </div>
                    <span className="shrink-0 font-medium">{rupiah(it.qty * it.price)}</span>
                  </li>
                ))}
              </ul>
              <Separator />
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-muted-foreground">Subtotal</span><span data-testid="checkout-subtotal">{rupiah(subtotal)}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Ongkir</span><span className="text-emerald-700">Dikonfirmasi admin</span></div>
                {method === "online" && (
                  <div className="flex justify-between" data-testid="checkout-service-fee-row">
                    <span className="text-muted-foreground">Biaya Layanan ({PAYMENT_CHANNEL_LABEL[channel] || channel})</span>
                    <span data-testid="checkout-service-fee">{fee ? rupiah(serviceFee) : "..."}</span>
                  </div>
                )}
                <div className="flex items-center justify-between pt-1">
                  <span className="font-semibold">Total Pembayaran</span>
                  <span className="font-display text-xl font-semibold" data-testid="checkout-total">{rupiah(grandTotal)}</span>
                </div>
              </div>
              <Button type="submit" disabled={submitting} className="h-11 w-full gap-2 active:scale-[0.98]" data-testid="checkout-submit-button">
                {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                {submitting ? "Memproses..." : SUBMIT_LABEL[method]}
              </Button>
              <p className="text-center text-xs text-muted-foreground">Dengan memesan, Anda menyetujui ketentuan pembelian B2B kami.</p>
            </CardContent>
          </Card>
        </div>
      </form>
    </div>
  );
}
