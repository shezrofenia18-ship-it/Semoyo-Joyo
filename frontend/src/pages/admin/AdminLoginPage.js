import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Loader2, ArrowLeft } from "lucide-react";
import { LOGO_FULL, BRAND_NAME } from "@/components/Brand";
import { toast } from "sonner";
import { api, errorMessage, ADMIN_TOKEN_KEY } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function AdminLoginPage() {
  const { loginAdmin } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", password: "" });
  const [loading, setLoading] = useState(false);

  if (localStorage.getItem(ADMIN_TOKEN_KEY)) return <Navigate to="/admin/dashboard" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post("/admin/login", form);
      loginAdmin(data.access_token, data.user);
      toast.success("Berhasil masuk sebagai admin");
      navigate("/admin/dashboard");
    } catch (err) {
      toast.error(errorMessage(err, "Gagal masuk"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-12">
      <div className="w-full max-w-md">
        <Button variant="ghost" className="mb-4 gap-2 px-2" onClick={() => navigate("/")}><ArrowLeft className="h-4 w-4" /> Kembali ke Toko</Button>
        <Card className="border-t-4 border-t-brand-yellow">
          <CardHeader>
            <img src={LOGO_FULL} alt={BRAND_NAME} className="mb-3 h-12 w-auto self-start object-contain" />
            <CardTitle className="font-display text-2xl">Masuk Admin / Owner</CardTitle>
            <CardDescription>Panel pengelolaan produk, stok, pesanan, dan laba/rugi (Mini ERP) {BRAND_NAME}.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={submit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="admin-user">Username</Label>
                <Input id="admin-user" data-testid="admin-username-input" className="h-11 bg-card" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} autoComplete="username" required />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="admin-pass">Password</Label>
                <Input id="admin-pass" type="password" data-testid="admin-password-input" className="h-11 bg-card" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} autoComplete="current-password" required />
              </div>
              <Button type="submit" className="h-11 w-full gap-2" disabled={loading} data-testid="admin-login-button">
                {loading && <Loader2 className="h-4 w-4 animate-spin" />} Masuk
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
