import { useLocation, useNavigate } from "react-router-dom";
import { ShoppingCart } from "lucide-react";
import { toast } from "sonner";
import { useCart } from "@/context/CartContext";
import { rupiah } from "@/lib/format";
import { cn } from "@/lib/utils";

const HIDDEN_ON = ["/checkout", "/pembayaran", "/struk"];

/** Tombol keranjang melayang (FAB) di kanan bawah — klik: ke halaman checkout. */
export const FloatingCart = () => {
  const { items, count, subtotal } = useCart();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  if (HIDDEN_ON.some((p) => pathname.startsWith(p))) return null;
  const totalQty = items.reduce((s, i) => s + i.qty, 0);

  const go = () => {
    if (count === 0) {
      toast.info("Keranjang masih kosong", { description: "Klik produk untuk melihat detail dan menambahkannya." });
      return;
    }
    navigate("/checkout");
  };

  return (
    <button
      type="button"
      onClick={go}
      aria-label={`Keranjang, ${count} produk. Lanjut ke checkout`}
      data-testid="floating-cart-button"
      className={cn(
        "fixed bottom-5 right-4 z-50 flex items-center gap-3 rounded-full bg-primary pl-4 pr-5 text-primary-foreground shadow-xl shadow-primary/30 transition-all hover:bg-primary/95 hover:shadow-2xl active:scale-95 sm:bottom-6 sm:right-6",
        count > 0 ? "h-14" : "h-14 w-14 justify-center px-0"
      )}
    >
      <span className="relative">
        <ShoppingCart className="h-6 w-6" />
        {count > 0 && (
          <span
            data-testid="floating-cart-badge"
            className="absolute -right-2.5 -top-2.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-brand-yellow px-1.5 text-[11px] font-bold text-brand-yellow-foreground ring-2 ring-primary"
          >
            {count}
          </span>
        )}
      </span>
      {count > 0 && (
        <span className="hidden flex-col items-start leading-tight sm:flex">
          <span className="text-[11px] font-medium text-primary-foreground/80">{totalQty} item &middot; Checkout</span>
          <span className="text-sm font-semibold">{rupiah(subtotal)}</span>
        </span>
      )}
      {count > 0 && <span className="text-sm font-semibold sm:hidden">Checkout</span>}
    </button>
  );
};
