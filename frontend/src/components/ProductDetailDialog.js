import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShoppingCart, Check, PackageCheck, Truck, ArrowRight } from "lucide-react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { QtyStepper } from "@/components/QtyStepper";
import { ProductImage } from "@/components/ProductImage";
import { useCart } from "@/context/CartContext";
import { rupiah } from "@/lib/format";

/** Pop-up detail produk: gambar, nama, harga, deskripsi, input Qty, "Masukkan ke Keranjang". */
export const ProductDetailDialog = ({ product, open, onOpenChange }) => {
  const { addItem, items, setOpen: openCartSheet } = useCart();
  const navigate = useNavigate();
  const min = product.min_order || 1;
  const [qty, setQty] = useState(min);
  const inCart = items.find((i) => i.product_id === product.id);
  const outOfStock = product.stock <= 0 || product.stock < min;

  useEffect(() => {
    if (open) setQty(min);
  }, [open, min]);

  const add = (thenCheckout = false) => {
    const q = Math.min(Math.max(Number(qty) || min, min), product.stock);
    addItem(product, q);
    toast.success(`${product.name} masuk ke keranjang`, {
      description: `${q} ${product.unit} · ${rupiah(q * product.price)}`,
      action: !thenCheckout ? { label: "Lihat Keranjang", onClick: () => openCartSheet(true) } : undefined,
    });
    onOpenChange(false);
    if (thenCheckout) navigate("/checkout");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] overflow-y-auto bg-card p-0 sm:max-w-3xl" data-testid="product-detail-dialog">
        <div className="grid sm:grid-cols-[1fr_1.1fr]">
          <div className="relative aspect-square bg-muted sm:aspect-auto sm:min-h-[420px]">
            <ProductImage src={product.image_url} alt={product.name} className="h-full w-full" iconClassName="h-12 w-12" />
            {outOfStock && <span className="absolute left-3 top-3 rounded-full bg-rose-600 px-2.5 py-1 text-xs font-semibold text-white">Stok Habis</span>}
            {product.category_name && <Badge className="absolute bottom-3 left-3 bg-white/90 text-foreground hover:bg-white">{product.category_name}</Badge>}
          </div>
          <div className="flex flex-col p-5 sm:p-6">
            <DialogHeader className="text-left">
              <DialogTitle className="font-display text-xl leading-tight sm:text-2xl" data-testid="product-detail-name">{product.name}</DialogTitle>
              <DialogDescription className="sr-only">Detail produk {product.name}</DialogDescription>
            </DialogHeader>
            <p className="mt-2 font-display text-2xl font-semibold text-primary" data-testid="product-detail-price">
              {rupiah(product.price)} <span className="text-sm font-normal text-muted-foreground">/ {product.unit}</span>
            </p>
            <div className="mt-3 flex flex-wrap gap-2 text-xs">
              <Badge variant="secondary" className="rounded-md">Min. order {min} {product.unit}</Badge>
              <Badge variant="secondary" className="rounded-md">Stok tersedia: {product.stock} {product.unit}</Badge>
              {inCart && <Badge className="rounded-md bg-primary"><Check className="mr-1 h-3 w-3" /> Di keranjang: {inCart.qty} {product.unit}</Badge>}
            </div>
            <div className="mt-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Deskripsi Produk</p>
              <p className="mt-1 whitespace-pre-line text-sm leading-relaxed text-foreground/90" data-testid="product-detail-description">
                {product.description || "Belum ada deskripsi untuk produk ini."}
              </p>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1.5"><PackageCheck className="h-3.5 w-3.5 text-primary" /> Kualitas terjamin</span>
              <span className="inline-flex items-center gap-1.5"><Truck className="h-3.5 w-3.5 text-primary" /> Pengiriman terjadwal</span>
            </div>

            <div className="mt-auto space-y-3 border-t pt-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-medium">Jumlah ({product.unit})</p>
                  <p className="text-xs text-muted-foreground">Subtotal: <span className="font-semibold text-foreground" data-testid="product-detail-subtotal">{rupiah((Number(qty) || 0) * product.price)}</span></p>
                </div>
                <QtyStepper value={qty} min={min} max={product.stock} onChange={setQty} className="[&>input]:w-16" />
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                <Button onClick={() => add(false)} disabled={outOfStock} className="h-11 gap-2 active:scale-[0.98]" data-testid="add-to-cart-button">
                  <ShoppingCart className="h-4 w-4" /> Masukkan ke Keranjang
                </Button>
                <Button onClick={() => add(true)} disabled={outOfStock} variant="outline" className="h-11 gap-2 border-brand-yellow bg-accent text-accent-foreground hover:bg-brand-yellow/30 active:scale-[0.98]" data-testid="buy-now-button">
                  Beli Sekarang <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
