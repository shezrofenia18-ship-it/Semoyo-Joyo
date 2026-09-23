import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

const CART_KEY = "mbg_cart_v1";
const CartContext = createContext(null);

function load() {
  try {
    const raw = localStorage.getItem(CART_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function CartProvider({ children }) {
  const [items, setItems] = useState(load);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem(CART_KEY, JSON.stringify(items));
  }, [items]);

  const addItem = useCallback((product, qty) => {
    setItems((prev) => {
      const idx = prev.findIndex((i) => i.product_id === product.id);
      const q = Math.max(qty || product.min_order || 1, 1);
      if (idx >= 0) {
        const next = [...prev];
        next[idx] = { ...next[idx], qty: Math.min(next[idx].qty + q, product.stock ?? Infinity) };
        return next;
      }
      return [
        ...prev,
        {
          product_id: product.id,
          name: product.name,
          price: Number(product.price),
          unit: product.unit,
          min_order: product.min_order || 1,
          stock: product.stock,
          image_url: product.image_url,
          qty: Math.min(q, product.stock ?? Infinity),
        },
      ];
    });
  }, []);

  const setQty = useCallback((productId, qty) => {
    setItems((prev) =>
      prev.map((i) => {
        if (i.product_id !== productId) return i;
        const clamped = Math.max(i.min_order, Math.min(Number(qty) || i.min_order, i.stock ?? Infinity));
        return { ...i, qty: clamped };
      })
    );
  }, []);

  const removeItem = useCallback((productId) => {
    setItems((prev) => prev.filter((i) => i.product_id !== productId));
  }, []);

  const clear = useCallback(() => setItems([]), []);

  const subtotal = useMemo(() => items.reduce((s, i) => s + i.price * i.qty, 0), [items]);
  const count = useMemo(() => items.length, [items]);

  const value = useMemo(
    () => ({ items, addItem, setQty, removeItem, clear, subtotal, count, open, setOpen }),
    [items, addItem, setQty, removeItem, clear, subtotal, count, open]
  );
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export const useCart = () => {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used within CartProvider");
  return ctx;
};
