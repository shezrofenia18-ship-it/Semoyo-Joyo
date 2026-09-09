import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * RBAC di sisi klien: halaman khusus Owner. Admin biasa dialihkan ke dashboard.
 * Role diverifikasi ulang dari server (refreshAdmin) agar tidak bisa dimanipulasi dari localStorage.
 */
export const OwnerRoute = ({ children }) => {
  const { admin, refreshAdmin } = useAuth();
  const [role, setRole] = useState(admin?.role || null);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    let alive = true;
    refreshAdmin().then((u) => {
      if (!alive) return;
      setRole(u?.role || null);
      setChecked(true);
    });
    return () => { alive = false; };
  }, [refreshAdmin]);

  if (!checked && role !== "owner") {
    return (
      <div className="space-y-3" data-testid="owner-route-loading">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }
  if (role !== "owner") {
    return <Navigate to="/admin/dashboard?denied=owner" replace />;
  }
  return children;
};
