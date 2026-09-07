import axios from "axios";

export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";
export const API_URL = `${BACKEND_URL}/api`;

export const TOKEN_KEY = "mbg_customer_token";
export const ADMIN_TOKEN_KEY = "mbg_admin_token";

export const api = axios.create({ baseURL: API_URL, timeout: 30000 });

api.interceptors.request.use((config) => {
  const isAdmin = (config.url || "").startsWith("/admin") && !(config.url || "").startsWith("/admin/login");
  const token = localStorage.getItem(isAdmin ? ADMIN_TOKEN_KEY : TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export function errorMessage(err, fallback = "Terjadi kesalahan, silakan coba lagi") {
  const d = err?.response?.data?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d) && d.length) {
    const first = d[0];
    const field = Array.isArray(first?.loc) ? first.loc[first.loc.length - 1] : "";
    return `${field ? field + ": " : ""}${first?.msg || fallback}`;
  }
  if (err?.message === "Network Error") return "Tidak dapat terhubung ke server";
  return fallback;
}

/** Resolve image URL (supports relative /api/uploads/... paths). */
export function resolveImage(url) {
  if (!url) return null;
  if (url.startsWith("/api/")) return `${BACKEND_URL}${url}`;
  return url;
}
