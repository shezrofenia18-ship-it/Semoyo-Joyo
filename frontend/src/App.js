import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { CartProvider } from "@/context/CartContext";
import { AuthProvider } from "@/context/AuthContext";
import { StoreLayout } from "@/components/StoreLayout";
import { AdminLayout } from "@/components/AdminLayout";
import { OwnerRoute } from "@/components/OwnerRoute";
import { ADMIN_TOKEN_KEY } from "@/lib/api";
import HomePage from "@/pages/HomePage";
import CartPage from "@/pages/CartPage";
import CheckoutPage from "@/pages/CheckoutPage";
import PaymentPage from "@/pages/PaymentPage";
import OrdersPage from "@/pages/OrdersPage";
import OrderDetailPage from "@/pages/OrderDetailPage";
import LoginPage from "@/pages/LoginPage";
import ReceiptPage from "@/pages/ReceiptPage";
import AdminLoginPage from "@/pages/admin/AdminLoginPage";
import AdminDashboardPage from "@/pages/admin/AdminDashboardPage";
import AdminProductsPage from "@/pages/admin/AdminProductsPage";
import AdminCategoriesPage from "@/pages/admin/AdminCategoriesPage";
import AdminOrdersPage from "@/pages/admin/AdminOrdersPage";
import AdminStockPage from "@/pages/admin/AdminStockPage";
import AdminAuditLogPage from "@/pages/admin/AdminAuditLogPage";
import AdminReportsPage from "@/pages/admin/AdminReportsPage";
import AdminReceivablesPage from "@/pages/admin/AdminReceivablesPage";
import AdminExpensesPage from "@/pages/admin/AdminExpensesPage";
import AdminSettingsPage from "@/pages/admin/AdminSettingsPage";

/** Akses login staf bersifat stealth: hanya lewat URL langsung /rahasia-admin. */
export const ADMIN_LOGIN_PATH = "/rahasia-admin";

const AdminIndexRedirect = () => <Navigate to={localStorage.getItem(ADMIN_TOKEN_KEY) ? "/admin/dashboard" : "/"} replace />;

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <CartProvider>
          <BrowserRouter>
            <Routes>
              <Route element={<StoreLayout />}>
                <Route path="/" element={<HomePage />} />
                <Route path="/keranjang" element={<CartPage />} />
                <Route path="/checkout" element={<CheckoutPage />} />
                <Route path="/pembayaran/:orderNumber" element={<PaymentPage />} />
                <Route path="/pesanan" element={<OrdersPage />} />
                <Route path="/pesanan/:orderNumber" element={<OrderDetailPage />} />
                <Route path="/masuk" element={<LoginPage />} />
                <Route path="/struk/:orderNumber" element={<ReceiptPage />} />
              </Route>
              <Route path={ADMIN_LOGIN_PATH} element={<AdminLoginPage />} />
              <Route path="/admin" element={<AdminLayout />}>
                <Route index element={<AdminIndexRedirect />} />
                <Route path="dashboard" element={<AdminDashboardPage />} />
                <Route path="produk" element={<AdminProductsPage />} />
                <Route path="kategori" element={<AdminCategoriesPage />} />
                <Route path="pesanan" element={<AdminOrdersPage />} />
                <Route path="piutang" element={<AdminReceivablesPage />} />
                <Route path="pengeluaran" element={<AdminExpensesPage />} />
                <Route path="stok" element={<AdminStockPage />} />
                <Route path="audit-log" element={<OwnerRoute><AdminAuditLogPage /></OwnerRoute>} />
                <Route path="laporan" element={<OwnerRoute><AdminReportsPage /></OwnerRoute>} />
                <Route path="pengaturan" element={<OwnerRoute><AdminSettingsPage /></OwnerRoute>} />
              </Route>
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
          <Toaster position="top-center" richColors closeButton />
        </CartProvider>
      </AuthProvider>
    </div>
  );
}

export default App;
