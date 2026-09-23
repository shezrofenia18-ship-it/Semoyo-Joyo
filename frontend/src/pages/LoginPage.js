import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, UserRound } from "lucide-react";
import { toast } from "sonner";
import { api, errorMessage } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function LoginPage() {
  const { loginCustomer } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", phone: "" });
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post("/auth/customer/login", form);
      loginCustomer(data.access_token, data.user);
      toast.success(`Selamat datang kembali, ${data.user.full_name}`);
      navigate("/pesanan");
    } catch (err) {
      toast.error(errorMessage(err, "Gagal masuk"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-md px-4 py-12 sm:px-6">
      <Card>
        <CardHeader>
          <span className="mb-2 flex h-11 w-11 items-center justify-center rounded-xl bg-accent text-accent-foreground">
            <UserRound className="h-5 w-5" />
          </span>
          <CardTitle className="font-display text-2xl">Masuk Pelanggan</CardTitle>
          <CardDescription>Masukkan Nama / Nama usaha dan No. Telp/WA yang sama seperti saat checkout untuk melihat riwayat pesanan.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="login-name">Nama / Nama usaha</Label>
              <Input id="login-name" data-testid="login-full-name-input" className="h-11 bg-card" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="login-phone">No. Telp / WA</Label>
              <Input id="login-phone" data-testid="login-phone-input" className="h-11 bg-card" placeholder="08xxxxxxxxxx" inputMode="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} required />
            </div>
            <Button type="submit" className="h-11 w-full gap-2" disabled={loading} data-testid="login-submit-button">
              {loading && <Loader2 className="h-4 w-4 animate-spin" />} Masuk
            </Button>
            <p className="text-center text-xs text-muted-foreground">Belum pernah memesan? Akun dibuat otomatis saat checkout pertama.</p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
