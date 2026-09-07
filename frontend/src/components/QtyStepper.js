import { Minus, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export const QtyStepper = ({ value, min = 1, max, step = 1, onChange, size = "md", className }) => {
  const dec = () => onChange(Math.max(min, value - step));
  const inc = () => onChange(max != null ? Math.min(max, value + step) : value + step);
  const h = size === "sm" ? "h-8" : "h-10";
  const w = size === "sm" ? "w-8" : "w-10";
  return (
    <div className={cn("inline-flex items-center overflow-hidden rounded-lg border bg-card", className)}>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        aria-label="Kurangi jumlah"
        data-testid="cart-qty-decrease-button"
        className={cn(h, w, "rounded-none")}
        disabled={value <= min}
        onClick={dec}
      >
        <Minus className="h-4 w-4" />
      </Button>
      <input
        type="number"
        min={min}
        max={max}
        value={value}
        data-testid="cart-qty-value"
        onChange={(e) => {
          const v = parseInt(e.target.value, 10);
          if (!Number.isNaN(v)) onChange(v);
        }}
        onBlur={(e) => {
          const v = parseInt(e.target.value, 10);
          if (Number.isNaN(v) || v < min) onChange(min);
          else if (max != null && v > max) onChange(max);
        }}
        className={cn(h, "w-14 border-x bg-card text-center text-sm font-semibold outline-none [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none")}
      />
      <Button
        type="button"
        variant="ghost"
        size="icon"
        aria-label="Tambah jumlah"
        data-testid="cart-qty-increase-button"
        className={cn(h, w, "rounded-none")}
        disabled={max != null && value >= max}
        onClick={inc}
      >
        <Plus className="h-4 w-4" />
      </Button>
    </div>
  );
};
