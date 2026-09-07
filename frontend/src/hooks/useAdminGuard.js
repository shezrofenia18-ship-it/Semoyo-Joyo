import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";

/** Returns a handler: call with an axios error; redirects to /admin on 401/403. */
export const useAdminGuard = () => {
  const navigate = useNavigate();
  const { logoutAdmin } = useAuth();
  return useCallback(
    (err) => {
      const s = err?.response?.status;
      if (s === 401 || s === 403) {
        logoutAdmin();
        toast.error("Sesi admin berakhir, silakan masuk kembali");
        navigate("/admin", { replace: true });
        return true;
      }
      return false;
    },
    [navigate, logoutAdmin]
  );
};
