import { NavLink, Navigate, Outlet, useNavigate } from "react-router-dom";
import { LayoutDashboard, Package, Tags, ClipboardList, LogOut, Leaf, Store } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { ADMIN_TOKEN_KEY } from "@/lib/api";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard, testid: "admin-nav-dashboard" },
  { to: "/admin/pesanan", label: "Pesanan", icon: ClipboardList, testid: "admin-nav-orders" },
  { to: "/admin/produk", label: "Produk", icon: Package, testid: "admin-nav-products" },
  { to: "/admin/kategori", label: "Kategori", icon: Tags, testid: "admin-nav-categories" },
];

export const AdminLayout = () => {
  const { admin, logoutAdmin } = useAuth();
  const navigate = useNavigate();
  const token = localStorage.getItem(ADMIN_TOKEN_KEY);
  if (!token) return <Navigate to="/admin" replace />;

  const logout = () => {
    logoutAdmin();
    navigate("/admin");
  };

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="hidden w-60 shrink-0 flex-col border-r bg-card lg:flex">
        <div className="flex h-16 items-center gap-2 border-b px-5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground"><Leaf className="h-5 w-5" /></span>
          <div className="leading-tight">
            <p className="font-display text-sm font-semibold">Supplier MBG</p>
            <p className="text-[11px] text-muted-foreground">Admin / Mini ERP</p>
          </div>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {NAV.map(({ to, label, icon: I, testid }) => (
            <NavLink key={to} to={to} data-testid={testid} className={({ isActive }) => cn("flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors", isActive ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground")}>
              <I className="h-4 w-4" /> {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t p-3">
          <NavLink to="/" className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground"><Store className="h-4 w-4" /> Lihat Toko</NavLink>
          <button onClick={logout} data-testid="admin-logout-button" className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground"><LogOut className="h-4 w-4" /> Keluar</button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-background/95 px-4 backdrop-blur sm:px-6">
          <div className="flex items-center gap-2 lg:hidden">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground"><Leaf className="h-4 w-4" /></span>
            <p className="font-display text-sm font-semibold">Admin MBG</p>
          </div>
          <p className="hidden text-sm text-muted-foreground lg:block">Panel Admin &middot; {admin?.full_name || "Administrator"}</p>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" className="gap-2" onClick={() => navigate("/")}><Store className="h-4 w-4" /> <span className="hidden sm:inline">Toko</span></Button>
            <Button variant="outline" size="sm" className="gap-2 lg:hidden" onClick={logout}><LogOut className="h-4 w-4" /></Button>
          </div>
        </header>
        <nav className="no-scrollbar flex gap-1 overflow-x-auto border-b bg-card px-3 py-2 lg:hidden">
          {NAV.map(({ to, label, icon: I }) => (
            <NavLink key={to} to={to} className={({ isActive }) => cn("flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium", isActive ? "bg-accent text-accent-foreground" : "text-muted-foreground")}>
              <I className="h-4 w-4" /> {label}
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
