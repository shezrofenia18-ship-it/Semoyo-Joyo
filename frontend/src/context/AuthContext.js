import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, TOKEN_KEY, ADMIN_TOKEN_KEY } from "@/lib/api";

const AuthContext = createContext(null);
const USER_KEY = "mbg_customer_user";
const ADMIN_USER_KEY = "mbg_admin_user";

function loadJson(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || "null");
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => loadJson(USER_KEY));
  const [admin, setAdmin] = useState(() => loadJson(ADMIN_USER_KEY));
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setChecking(false);
      return;
    }
    api
      .get("/auth/me")
      .then((r) => {
        setUser(r.data);
        localStorage.setItem(USER_KEY, JSON.stringify(r.data));
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        setUser(null);
      })
      .finally(() => setChecking(false));
  }, []);

  const loginCustomer = useCallback((token, u) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(u));
    setUser(u);
  }, []);

  const logoutCustomer = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
  }, []);

  const loginAdmin = useCallback((token, u) => {
    localStorage.setItem(ADMIN_TOKEN_KEY, token);
    localStorage.setItem(ADMIN_USER_KEY, JSON.stringify(u));
    setAdmin(u);
  }, []);

  const logoutAdmin = useCallback(() => {
    localStorage.removeItem(ADMIN_TOKEN_KEY);
    localStorage.removeItem(ADMIN_USER_KEY);
    setAdmin(null);
  }, []);

  const value = useMemo(
    () => ({ user, admin, checking, loginCustomer, logoutCustomer, loginAdmin, logoutAdmin, isAdminLoggedIn: !!localStorage.getItem(ADMIN_TOKEN_KEY) }),
    [user, admin, checking, loginCustomer, logoutCustomer, loginAdmin, logoutAdmin]
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};
