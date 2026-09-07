import { useNavigate } from "react-router-dom";
import { ShoppingCart, Trash2, ArrowRight, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { QtyStepper } from "@/components/QtyStepper";
import { ProductImage } from "@/components/ProductImage";
import { EmptyState } from "@/components/EmptyState";
import { useCart } from "@/context/CartContext";
import { rupiah } from "@/lib/format";

export default function CartPage() {
  const { items, setQty, removeItem, subtotal, clear } = useCart();
  const navigate = useNavigate();

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold sm:text-3xl">Keranjang</h1>
          <p className="mt-1 text-sm text-muted-foreground">{items.length} jenis produk dipilih</p>
        </div>
        <Button variant="ghost" className="gap-2" onClick={() => navigate("/")}>
          <ArrowLeft className="h-4 w-4" /> Lanjut Belanja
        </Button>
      </div>

      {items.length === 0 ? (
        <EmptyState
          icon={ShoppingCart}
          title="Keranjang masih kosong"
          description="Pilih produk untuk mulai belanja."
          actionLabel="Kembali ke Beranda"
          onAction={() => navigate("/")}
          testId="cart-empty-state"
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
          <Card className="overflow-hidden">
            <ul className="divide-y" data-testid="cart-items-list">
              {items.map((it) => (
                <li key={it.product_id} className="flex gap-4 p-4" data-testid="cart-item">
                  <div className="h-20 w-20 shrink-0 overflow-hidden rounded-lg bg-muted sm:h-24 sm:w-24">
                    <ProductImage src={it.image_url} alt={it.name} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="font-semibold" data-testid="cart-item-name">{it.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {rupiah(it.price)} / {it.unit} &middot; Min. {it.min_order} {it.unit}
                        </p>
                      </div>
                      <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" aria-label="Hapus item" data-testid="cart-remove-item-button" onClick={() => removeItem(it.product_id)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
                      <QtyStepper value={it.qty} min={it.min_order} max={it.stock} onChange={(v) => setQty(it.product_id, v)} />
                      <p className="font-display text-base font-semibold" data-testid="cart-item-subtotal">{rupiah(it.price * it.qty)}</p>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </Card>

          <div className="lg:sticky lg:top-24 lg:self-start">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="font-display text-lg">Ringkasan</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex justify-between"><span className="text-muted-foreground">Subtotal</span><span>{rupiah(subtotal)}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Ongkir</span><span className="text-emerald-700">Dihitung saat konfirmasi</span></div>
                <Separator />
                <div className="flex items-center justify-between">
                  <span className="font-semibold">Total</span>
                  <span className="font-display text-xl font-semibold" data-testid="cart-total">{rupiah(subtotal)}</span>
                </div>
                <Button className="mt-2 h-11 w-full gap-2 active:scale-[0.98]" onClick={() => navigate("/checkout")} data-testid="cart-checkout-button">
                  Lanjut Checkout <ArrowRight className="h-4 w-4" />
                </Button>
                <Button variant="ghost" className="w-full text-muted-foreground" onClick={clear} data-testid="cart-clear-button">
                  Kosongkan keranjang
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
