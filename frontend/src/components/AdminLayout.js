import { useEffect } from "react";
import { NavLink, Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";
import { LayoutDashboard, Package, Tags, ClipboardList, LogOut, Store, Boxes, ScrollText, Bell, BellOff, ShieldCheck, UserCog, FileBarChart2, HandCoins, ReceiptText, Settings } from "lucide-react";
import { toast } from "sonner";
import { ADMIN_LOGIN_PATH } from "@/hooks/useAdminGuard";
import { useAdminEvents } from "@/hooks/useAdminEvents";
import { BrandIcon, BRAND_NAME } from "@/components/Brand";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { ADMIN_TOKEN_KEY } from "@/lib/api";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard, testid: "admin-nav-dashboard" },
  { to: "/admin/pesanan", label: "Pesanan", icon: ClipboardList, testid: "admin-nav-orders" },
  { to: "/admin/piutang", label: "Piutang", icon: HandCoins, testid: "admin-nav-receivables" },
  { to: "/admin/pengeluaran", label: "Pengeluaran", icon: ReceiptText, testid: "admin-nav-expenses" },
  { to: "/admin/produk", label: "Produk", icon: Package, testid: "admin-nav-products" },
  { to: "/admin/stok", label: "Stok Barang", icon: Boxes, testid: "admin-nav-stock" },
  { to: "/admin/kategori", label: "Kategori", icon: Tags, testid: "admin-nav-categories" },
];

const RoleBadge = ({ isOwner }) => (
  <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold", isOwner ? "bg-brand-yellow text-brand-yellow-foreground" : "bg-secondary text-secondary-foreground")} data-testid="admin-role-badge">
    {isOwner ? <ShieldCheck className="h-3 w-3" /> : <UserCog className="h-3 w-3" />} {isOwner ? "Owner" : "Admin"}
  </span>
);

const UnreadDot = ({ to, unread }) => (to === "/admin/pesanan" && unread > 0 ? (
  <span className="ml-auto flex h-5 min-w-5 items-center justify-center rounded-full bg-rose-500 px-1.5 text-[11px] font-bold text-white" data-testid="admin-unread-orders-badge">{unread}</span>
) : null);

const OWNER_NAV = [
  { to: "/admin/laporan", label: "Laporan", icon: FileBarChart2, testid: "admin-nav-reports", ownerOnly: true },
  { to: "/admin/audit-log", label: "Audit Log", icon: ScrollText, testid: "admin-nav-audit-log", ownerOnly: true },
  { to: "/admin/pengaturan", label: "Pengaturan", icon: Settings, testid: "admin-nav-settings", ownerOnly: true },
];

export const AdminLayout = () => {
  const { admin, logoutAdmin, isOwner, refreshAdmin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem(ADMIN_TOKEN_KEY);
  const { connected, unread, clearUnread, requestPermission } = useAdminEvents(!!token);

  useEffect(() => {
    refreshAdmin(); // sinkronkan role (owner/admin) dari server
    requestPermission(); // izin push notification browser
  }, [refreshAdmin, requestPermission]);

  useEffect(() => {
    if (location.pathname.startsWith("/admin/pesanan")) clearUnread();
  }, [location.pathname, clearUnread]);

  useEffect(() => {
    if (new URLSearchParams(location.search).get("denied") === "owner") {
      toast.error("Halaman tersebut hanya dapat diakses oleh Owner");
      navigate("/admin/dashboard", { replace: true });
    }
  }, [location.search, navigate]);

  if (!token) return <Navigate to={ADMIN_LOGIN_PATH} replace />;
  const nav = isOwner ? [...NAV, ...OWNER_NAV] : NAV;

  const logout = () => {
    logoutAdmin();
    navigate("/");
  };


  return (
    <div className="flex min-h-screen bg-background">
      <aside className="hidden w-60 shrink-0 flex-col border-r bg-primary text-primary-foreground lg:flex">
        <div className="flex h-16 items-center gap-2 border-b border-white/15 px-5">
          <BrandIcon className="border-0" />
          <div className="leading-tight">
            <p className="font-display text-sm font-bold">{BRAND_NAME}</p>
            <p className="text-[11px] text-primary-foreground/70">Admin / Mini ERP</p>
          </div>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {nav.map(({ to, label, icon: I, testid }) => (
            <NavLink key={to} to={to} data-testid={testid} className={({ isActive }) => cn("flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors", isActive ? "bg-brand-yellow text-brand-yellow-foreground shadow-sm" : "text-primary-foreground/80 hover:bg-white/10 hover:text-white")}>
              <I className="h-4 w-4" /> {label} <UnreadDot to={to} unread={unread} />
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-white/15 p-3">
          <NavLink to="/" className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-primary-foreground/80 hover:bg-white/10 hover:text-white"><Store className="h-4 w-4" /> Lihat Toko</NavLink>
          <button onClick={logout} data-testid="admin-logout-button" className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-primary-foreground/80 hover:bg-white/10 hover:text-white"><LogOut className="h-4 w-4" /> Keluar</button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-background/95 px-4 backdrop-blur sm:px-6">
          <div className="flex items-center gap-2 lg:hidden">
            <BrandIcon size="h-8 w-8" />
            <p className="font-display text-sm font-bold"><span className="text-primary">Admin</span> {BRAND_NAME}</p>
          </div>
          <p className="hidden items-center gap-2 text-sm text-muted-foreground lg:flex">Panel Admin &middot; {admin?.full_name || "Administrator"} <RoleBadge isOwner={isOwner} /></p>
          <div className="flex items-center gap-2">
            <span className={cn("hidden items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium sm:inline-flex", connected ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-border bg-muted text-muted-foreground")} title={connected ? "Notifikasi real-time aktif" : "Menghubungkan notifikasi..."} data-testid="admin-realtime-status">
              {connected ? <Bell className="h-3.5 w-3.5" /> : <BellOff className="h-3.5 w-3.5" />} {connected ? "Notifikasi aktif" : "Menghubungkan..."}
            </span>
            <Button variant="ghost" size="sm" className="gap-2" onClick={() => navigate("/")}><Store className="h-4 w-4" /> <span className="hidden sm:inline">Toko</span></Button>
            <Button variant="outline" size="sm" className="gap-2 lg:hidden" onClick={logout}><LogOut className="h-4 w-4" /></Button>
          </div>
        </header>
        <nav className="no-scrollbar flex gap-1 overflow-x-auto border-b bg-card px-3 py-2 lg:hidden">
          {nav.map(({ to, label, icon: I }) => (
            <NavLink key={to} to={to} className={({ isActive }) => cn("flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium", isActive ? "bg-primary text-primary-foreground" : "text-muted-foreground")}>
              <I className="h-4 w-4" /> {label} <UnreadDot to={to} unread={unread} />
            </NavLink>
          ))}
        </nav>
        <main className="flex-1 p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
