import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { ShoppingCart, Search, ClipboardList, UserRound, LogOut, LayoutDashboard } from "lucide-react";
import { Brand } from "@/components/Brand";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCart } from "@/context/CartContext";
import { useAuth } from "@/context/AuthContext";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useEffect, useState } from "react";

export const Navbar = () => {
  const { count, setOpen } = useCart();
  const { user, logoutCustomer, isAdminLoggedIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const [q, setQ] = useState(params.get("q") || "");

  useEffect(() => {
    setQ(new URLSearchParams(location.search).get("q") || "");
  }, [location.search]);

  const submitSearch = (e) => {
    e.preventDefault();
    const term = q.trim();
    navigate(term ? `/?q=${encodeURIComponent(term)}` : "/");
  };

  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/85">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-3 px-4 sm:px-6">
        <Brand to="/" data-testid="app-brand" />

        <form onSubmit={submitSearch} className="relative mx-auto w-full max-w-md">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            data-testid="product-search-input"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Cari bahan baku... (beras, ayam, sayur)"
            className="h-10 rounded-full bg-card pl-9 pr-4"
          />
        </form>

        <nav className="flex shrink-0 items-center gap-1 sm:gap-2">
          <NavLink to="/pesanan" data-testid="nav-orders-link">
            {({ isActive }) => (
              <Button variant={isActive ? "secondary" : "ghost"} size="sm" className="hidden gap-2 sm:inline-flex">
                <ClipboardList className="h-4 w-4" />
                Pesanan
              </Button>
            )}
          </NavLink>

          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="gap-2" data-testid="customer-menu-button">
                  <UserRound className="h-4 w-4" />
                  <span className="hidden max-w-[140px] truncate sm:inline">{user.full_name}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel className="font-normal">
                  <p className="text-sm font-semibold">{user.full_name}</p>
                  <p className="text-xs text-muted-foreground">ID: {user.username}</p>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate("/pesanan")} data-testid="menu-orders">
                  <ClipboardList className="mr-2 h-4 w-4" /> Riwayat Pesanan
                </DropdownMenuItem>
                {isAdminLoggedIn && (
                  <DropdownMenuItem onClick={() => navigate("/admin/dashboard")} data-testid="menu-admin-dashboard">
                    <LayoutDashboard className="mr-2 h-4 w-4" /> Dashboard Admin
                  </DropdownMenuItem>
                )}
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logoutCustomer} data-testid="customer-logout">
                  <LogOut className="mr-2 h-4 w-4" /> Keluar
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Link to="/masuk" data-testid="customer-login-link">
              <Button variant="ghost" size="sm" className="gap-2" data-testid="account-menu-button">
                <UserRound className="h-4 w-4" />
                <span className="hidden sm:inline">Masuk</span>
              </Button>
            </Link>
          )}

          {isAdminLoggedIn && (
            <Link to="/admin/dashboard" data-testid="nav-admin-dashboard-link" aria-label="Dashboard Admin">
              <Button variant="outline" size="sm" className="gap-2 border-primary/40 text-primary hover:bg-secondary">
                <LayoutDashboard className="h-4 w-4" /> <span className="hidden md:inline">Dashboard Admin</span>
              </Button>
            </Link>
          )}

          <Button
            data-testid="open-cart-button"
            onClick={() => setOpen(true)}
            className="relative h-10 gap-2 rounded-full px-3 active:scale-[0.98] sm:px-4"
            aria-label="Buka keranjang"
          >
            <ShoppingCart className="h-4 w-4" />
            <span className="hidden sm:inline">Keranjang</span>
            {count > 0 && (
              <span
                data-testid="cart-count-badge"
                className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-brand-yellow px-1.5 text-[11px] font-bold text-brand-yellow-foreground"
              >
                {count}
              </span>
            )}
          </Button>
        </nav>
      </div>
    </header>
  );
};
