import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";

export const ADMIN_LOGIN_PATH = "/rahasia-admin";

/** Returns a handler: call with an axios error; redirects to login on 401, shows message on 403 (RBAC). */
export const useAdminGuard = () => {
  const navigate = useNavigate();
  const { logoutAdmin } = useAuth();
  return useCallback(
    (err) => {
      const s = err?.response?.status;
      if (s === 401) {
        logoutAdmin();
        toast.error("Sesi admin berakhir, silakan masuk kembali");
        navigate(ADMIN_LOGIN_PATH, { replace: true });
        return true;
      }
      if (s === 403) {
        toast.error(err?.response?.data?.detail || "Akses ditolak: aksi ini khusus Owner");
        return true;
      }
      return false;
    },
    [navigate, logoutAdmin]
  );
};
