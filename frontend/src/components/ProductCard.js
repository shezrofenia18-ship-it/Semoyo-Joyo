import { useState } from "react";
import { Check, Eye } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ProductImage } from "@/components/ProductImage";
import { ProductDetailDialog } from "@/components/ProductDetailDialog";
import { useCart } from "@/context/CartContext";
import { rupiah } from "@/lib/format";

/**
 * Kartu produk katalog: hanya Gambar, Nama, Harga, Deskripsi singkat.
 * Klik kartu -> pop-up detail dengan input jumlah + "Masukkan ke Keranjang".
 */
export const ProductCard = ({ product }) => {
  const { items } = useCart();
  const [open, setOpen] = useState(false);
  const inCart = items.find((i) => i.product_id === product.id);
  const outOfStock = product.stock <= 0 || product.stock < product.min_order;

  return (
    <>
      <Card
        data-testid="product-card"
        role="button"
        tabIndex={0}
        onClick={() => setOpen(true)}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), setOpen(true))}
        className="group flex h-full cursor-pointer flex-col overflow-hidden border bg-card shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        <div className="relative aspect-square w-full overflow-hidden bg-muted">
          <ProductImage
            src={product.image_url}
            alt={product.name}
            testId="product-image"
            className="h-full w-full transition-transform duration-300 group-hover:scale-[1.04]"
            iconClassName="h-10 w-10"
          />
          {inCart && (
            <span className="absolute left-2 top-2 inline-flex items-center gap-1 rounded-full bg-primary px-2 py-0.5 text-[11px] font-semibold text-primary-foreground" data-testid="product-in-cart-badge">
              <Check className="h-3 w-3" /> {inCart.qty} {product.unit}
            </span>
          )}
          {outOfStock && (
            <span className="absolute right-2 top-2 rounded-full bg-rose-600 px-2 py-0.5 text-[11px] font-semibold text-white">Stok Habis</span>
          )}
          <span className="pointer-events-none absolute bottom-2 right-2 inline-flex items-center gap-1 rounded-full bg-white/90 px-2 py-0.5 text-[11px] font-medium text-primary opacity-0 shadow-sm transition-opacity group-hover:opacity-100">
            <Eye className="h-3 w-3" /> Lihat detail
          </span>
        </div>
        <div className="flex flex-1 flex-col p-3 sm:p-4">
          <h3 data-testid="product-name" className="line-clamp-2 min-h-[2.5rem] text-sm font-semibold leading-5 sm:text-base">
            {product.name}
          </h3>
          <p data-testid="product-price" className="mt-1.5 font-display text-base font-semibold text-primary sm:text-lg">
            {rupiah(product.price)}
            <span className="ml-1 text-xs font-normal text-muted-foreground">/ {product.unit}</span>
          </p>
          {product.description ? (
            <p data-testid="product-description" className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-muted-foreground">{product.description}</p>
          ) : (
            <p className="mt-1.5 text-xs italic text-muted-foreground/70">Belum ada deskripsi.</p>
          )}
          <div className="mt-auto flex flex-wrap items-center gap-1.5 pt-3 text-[11px] text-muted-foreground">
            <Badge variant="secondary" className="rounded-md px-1.5 py-0 font-medium">Min. {product.min_order} {product.unit}</Badge>
            {!outOfStock && <span>Stok {product.stock}</span>}
          </div>
        </div>
      </Card>
      <ProductDetailDialog product={product} open={open} onOpenChange={setOpen} />
    </>
  );
};
