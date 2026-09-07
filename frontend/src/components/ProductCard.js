import { useState } from "react";
import { ShoppingCart, Check } from "lucide-react";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { QtyStepper } from "@/components/QtyStepper";
import { ProductImage } from "@/components/ProductImage";
import { useCart } from "@/context/CartContext";
import { rupiah } from "@/lib/format";

export const ProductCard = ({ product }) => {
  const { addItem, items } = useCart();
  const [qty, setQty] = useState(product.min_order || 1);
  const inCart = items.find((i) => i.product_id === product.id);
  const outOfStock = product.stock <= 0 || product.stock < product.min_order;

  const add = () => {
    addItem(product, qty);
    toast.success(`${product.name} ditambahkan`, { description: `${qty} ${product.unit} masuk ke keranjang` });
  };

  return (
    <Card
      data-testid="product-card"
      className="group flex h-full flex-col overflow-hidden border bg-card shadow-sm transition-shadow hover:shadow-md"
    >
      <div className="relative aspect-square w-full overflow-hidden bg-muted">
        <ProductImage
          src={product.image_url}
          alt={product.name}
          testId="product-image"
          className="h-full w-full transition-transform duration-300 group-hover:scale-[1.03]"
          iconClassName="h-10 w-10"
        />
        {inCart && (
          <span className="absolute left-2 top-2 inline-flex items-center gap-1 rounded-full bg-primary px-2 py-0.5 text-[11px] font-semibold text-primary-foreground">
            <Check className="h-3 w-3" /> {inCart.qty} {product.unit}
          </span>
        )}
        {outOfStock && (
          <span className="absolute right-2 top-2 rounded-full bg-rose-600 px-2 py-0.5 text-[11px] font-semibold text-white">Stok Habis</span>
        )}
      </div>
      <div className="flex flex-1 flex-col p-3 sm:p-4">
        <h3 data-testid="product-name" className="line-clamp-2 min-h-[2.5rem] text-sm font-semibold leading-5 sm:text-base">
          {product.name}
        </h3>
        <div className="mt-1 flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
          <Badge variant="secondary" className="rounded-md px-1.5 py-0 font-medium">
            per {product.unit}
          </Badge>
          <span>Min. {product.min_order} {product.unit}</span>
        </div>
        <p data-testid="product-price" className="mt-2 font-display text-base font-semibold text-foreground sm:text-lg">
          {rupiah(product.price)}
          <span className="ml-1 text-xs font-normal text-muted-foreground">/ {product.unit}</span>
        </p>
        <div className="mt-auto flex flex-col gap-2 pt-3">
          <QtyStepper size="sm" value={qty} min={product.min_order || 1} max={product.stock} onChange={setQty} className="w-full justify-between [&>input]:flex-1" />
          <Button
            data-testid="add-to-cart-button"
            onClick={add}
            disabled={outOfStock}
            className="h-9 w-full gap-2 active:scale-[0.98]"
          >
            <ShoppingCart className="h-4 w-4" />
            Tambah
          </Button>
        </div>
      </div>
    </Card>
  );
};
