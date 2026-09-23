import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { Lock, LayoutDashboard, MapPin, Phone, Mail, Clock3 } from "lucide-react";
import { Brand, BRAND_NAME, BRAND_TAGLINE } from "@/components/Brand";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";

const ADMIN_LOGIN_PATH = "/rahasia-admin";

export const Footer = () => {
  const { isAdminLoggedIn } = useAuth();
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    api.get("/store/profile").then((r) => setProfile(r.data)).catch(() => {});
  }, []);

  const name = profile?.store_name || BRAND_NAME;
  const tagline = profile?.tagline || BRAND_TAGLINE;
  const hasContact = profile && (profile.address || profile.phone || profile.whatsapp || profile.email || profile.operating_hours);

  return (
    <footer className="mt-16 border-t bg-card">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-10 sm:flex-row sm:items-start sm:justify-between sm:px-6">
        <div className="max-w-sm">
          <Brand to="/" variant="full" />
          <p className="mt-3 text-sm text-muted-foreground" data-testid="footer-description">
            {profile?.description || `${name} - ${tagline}. Mitra pasokan bahan baku segar dan berkualitas untuk dapur dan UMKM. Harga B2B transparan, pengiriman terjadwal.`}
          </p>
          {hasContact && (
            <ul className="mt-4 space-y-1.5 text-sm text-muted-foreground" data-testid="footer-store-contact">
              {(profile.address || profile.city) && (
                <li className="flex items-start gap-2"><MapPin className="mt-0.5 h-4 w-4 shrink-0 text-primary" /> <span>{[profile.address, profile.city].filter(Boolean).join(", ")}</span></li>
              )}
              {(profile.phone || profile.whatsapp) && (
                <li className="flex items-center gap-2"><Phone className="h-4 w-4 shrink-0 text-primary" /> <span>{[profile.phone, profile.whatsapp && `WA ${profile.whatsapp}`].filter(Boolean).join(" / ")}</span></li>
              )}
              {profile.email && <li className="flex items-center gap-2"><Mail className="h-4 w-4 shrink-0 text-primary" /> <span>{profile.email}</span></li>}
              {profile.operating_hours && <li className="flex items-center gap-2"><Clock3 className="h-4 w-4 shrink-0 text-primary" /> <span>{profile.operating_hours}</span></li>}
            </ul>
          )}
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
              {isAdminLoggedIn && (
                <li>
                  <Link className="inline-flex items-center gap-1 hover:text-foreground" to="/admin/dashboard" data-testid="footer-admin-dashboard-link">
                    <LayoutDashboard className="h-3.5 w-3.5" /> Dashboard Admin
                  </Link>
                </li>
              )}
            </ul>
          </div>
        </div>
      </div>
      <div className="border-t">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} {name}. Sistem B2B E-Commerce &amp; Mini ERP.
          </p>
          {/* Akses staf/owner bersifat stealth: ikon gembok kecil transparan */}
          <Link
            to={isAdminLoggedIn ? "/admin/dashboard" : ADMIN_LOGIN_PATH}
            aria-label="Akses staf"
            title=""
            data-testid="stealth-admin-link"
            className="inline-flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground/30 transition-colors hover:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Lock className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>
    </footer>
  );
};
