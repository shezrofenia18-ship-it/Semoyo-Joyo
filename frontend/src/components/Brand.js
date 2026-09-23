import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";

export const BRAND_NAME = "Semoyo Joyo";
export const BRAND_TAGLINE = "Solusi Belanja Terpercaya";
export const LOGO_FULL = "/logo.png";
export const LOGO_ICON = "/logo-icon.png";

/** Ikon logo (mark "SJ") dalam kotak putih. */
export const BrandIcon = ({ className, size = "h-9 w-9" }) => (
  <span className={cn("flex shrink-0 items-center justify-center overflow-hidden rounded-xl border bg-white p-1", size, className)}>
    <img src={LOGO_ICON} alt={BRAND_NAME} className="h-full w-full object-contain" />
  </span>
);

/**
 * Logo + nama brand. variant:
 *  - "full": logo lengkap (ikon + teks) sebagai gambar
 *  - "icon": ikon + teks nama (default)
 */
export const Brand = ({ to = "/", variant = "icon", className, showTagline = true, textClassName, ...props }) => {
  const content =
    variant === "full" ? (
      <img src={LOGO_FULL} alt={`${BRAND_NAME} - ${BRAND_TAGLINE}`} className="h-10 w-auto object-contain sm:h-11" />
    ) : (
      <>
        <BrandIcon />
        <span className={cn("hidden flex-col leading-tight sm:flex", textClassName)}>
          <span className="font-display text-base font-bold tracking-tight">
            <span className="text-primary">SEMOYO</span> <span className="text-brand-yellow">JOYO</span>
          </span>
          {showTagline && <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">{BRAND_TAGLINE}</span>}
        </span>
      </>
    );
  if (!to) return <span className={cn("flex items-center gap-2", className)} {...props}>{content}</span>;
  return (
    <Link to={to} className={cn("flex shrink-0 items-center gap-2", className)} {...props}>
      {content}
    </Link>
  );
};
