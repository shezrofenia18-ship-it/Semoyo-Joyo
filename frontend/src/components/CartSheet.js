import { useNavigate } from "react-router-dom";
import { ShoppingCart, Trash2, ArrowRight } from "lucide-react";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { QtyStepper } from "@/components/QtyStepper";
import { ProductImage } from "@/components/ProductImage";
import { useCart } from "@/context/CartContext";
import { rupiah } from "@/lib/format";

export const CartSheet = () => {
  const { items, open, setOpen, setQty, removeItem, subtotal } = useCart();
  const navigate = useNavigate();

  const go = (path) => {
    setOpen(false);
    navigate(path);
  };

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetContent className="flex w-full flex-col bg-background p-0 sm:max-w-md" data-testid="cart-sheet">
        <SheetHeader className="border-b px-5 py-4 text-left">
          <SheetTitle className="font-display">Keranjang Belanja</SheetTitle>
          <SheetDescription>{items.length} jenis produk</SheetDescription>
        </SheetHeader>

        {items.length === 0 ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center" data-testid="cart-empty-state">
            <span className="flex h-14 w-14 items-center justify-center rounded-full bg-accent text-accent-foreground">
              <ShoppingCart className="h-6 w-6" />
            </span>
            <p className="font-semibold">Keranjang masih kosong</p>
            <p className="text-sm text-muted-foreground">Pilih produk untuk mulai belanja.</p>
            <Button variant="secondary" onClick={() => go("/")}>Kembali ke Beranda</Button>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto px-5 py-4">
              <ul className="space-y-4">
                {items.map((it) => (
                  <li key={it.product_id} className="flex gap-3" data-testid="cart-sheet-item">
                    <div className="h-16 w-16 shrink-0 overflow-hidden rounded-lg bg-muted">
                      <ProductImage src={it.image_url} alt={it.name} iconClassName="h-5 w-5" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold">{it.name}</p>
                      <p className="text-xs text-muted-foreground">{rupiah(it.price)} / {it.unit} &middot; min. {it.min_order}</p>
                      <div className="mt-2 flex items-center justify-between gap-2">
                        <QtyStepper size="sm" value={it.qty} min={it.min_order} max={it.stock} onChange={(v) => setQty(it.product_id, v)} />
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" aria-label="Hapus" data-testid="cart-remove-item-button" onClick={() => removeItem(it.product_id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    <p className="shrink-0 text-sm font-semibold">{rupiah(it.price * it.qty)}</p>
                  </li>
                ))}
              </ul>
            </div>
            <div className="border-t bg-card px-5 py-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Subtotal</span>
                <span className="font-display text-lg font-semibold" data-testid="cart-sheet-subtotal">{rupiah(subtotal)}</span>
              </div>
              <Separator className="my-3" />
              <div className="grid grid-cols-2 gap-2">
                <Button variant="secondary" onClick={() => go("/keranjang")} data-testid="cart-sheet-view-button">Lihat Keranjang</Button>
                <Button onClick={() => go("/checkout")} className="gap-2" data-testid="cart-checkout-button">
                  Checkout <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
};
