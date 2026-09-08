import { Link } from "react-router-dom";
import { ShieldCheck, ArrowRight, LayoutDashboard } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Brand, BRAND_NAME, BRAND_TAGLINE } from "@/components/Brand";
import { useAuth } from "@/context/AuthContext";

export const Footer = () => {
  const { isAdminLoggedIn } = useAuth();
  const adminTarget = isAdminLoggedIn ? "/admin/dashboard" : "/admin";
  const AdminIcon = isAdminLoggedIn ? LayoutDashboard : ShieldCheck;
  return (
  <footer className="mt-16 border-t bg-card">
    <div className="mx-auto max-w-6xl px-4 pt-10 sm:px-6">
      {/* Owner / Admin portal CTA */}
      <div
        className="flex flex-col gap-4 rounded-2xl border border-primary/20 bg-primary px-5 py-5 text-primary-foreground sm:flex-row sm:items-center sm:justify-between"
        data-testid="admin-portal-cta"
      >
        <div className="flex items-start gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-yellow text-brand-yellow-foreground">
            <AdminIcon className="h-5 w-5" />
          </span>
          <div>
            <p className="font-display text-base font-semibold">Portal Admin / Owner</p>
            <p className="text-sm text-primary-foreground/80">
              Kelola produk, stok barang, pesanan, dan pantau laba/rugi dari panel Mini ERP.
            </p>
          </div>
        </div>
        <Link to={adminTarget} data-testid="footer-admin-link" className="shrink-0">
          <Button className="w-full gap-2 bg-brand-yellow text-brand-yellow-foreground hover:bg-brand-yellow/90 active:scale-[0.98] sm:w-auto">
            {isAdminLoggedIn ? "Buka Dashboard Admin" : "Masuk Portal Admin"} <ArrowRight className="h-4 w-4" />
          </Button>
        </Link>
      </div>
    </div>

    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-10 sm:flex-row sm:items-start sm:justify-between sm:px-6">
      <div className="max-w-sm">
        <Brand to="/" variant="full" />
        <p className="mt-3 text-sm text-muted-foreground">
          {BRAND_NAME} - {BRAND_TAGLINE}. Mitra pasokan bahan baku segar dan berkualitas untuk dapur dan UMKM. Harga B2B transparan, pengiriman terjadwal.
        </p>
      </div>
      <div className="grid grid-cols-2 gap-8 text-sm">
        <div>
          <p className="font-semibold">Belanja</p>
          <ul className="mt-2 space-y-1 text-muted-foreground">
            <li><Link className="hover:text-foreground" to="/">Katalog Produk</Link></li>
            <li><Link className="hover:text-foreground" to="/keranjang">Keranjang</Link></li>
            <li><Link className="hover:text-foreground" to="/pesanan">Riwayat Pesanan</Link></li>
          </ul>
        </div>
        <div>
          <p className="font-semibold">Akun</p>
          <ul className="mt-2 space-y-1 text-muted-foreground">
            <li><Link className="hover:text-foreground" to="/masuk">Masuk Pelanggan</Link></li>
            <li>
              <Link className="inline-flex items-center gap-1 hover:text-foreground" to={adminTarget} data-testid="footer-admin-text-link">
                <AdminIcon className="h-3.5 w-3.5" /> {isAdminLoggedIn ? "Dashboard Admin" : "Portal Admin"}
              </Link>
            </li>
          </ul>
        </div>
      </div>
    </div>
    <div className="border-t">
      <p className="mx-auto max-w-6xl px-4 py-4 text-xs text-muted-foreground sm:px-6">
        &copy; {new Date().getFullYear()} {BRAND_NAME}. Sistem B2B E-Commerce & Mini ERP.
      </p>
    </div>
  </footer>
  );
};
