import { useEffect, useRef, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { API_URL, ADMIN_TOKEN_KEY } from "@/lib/api";
import { rupiah } from "@/lib/format";

const UNREAD_KEY = "sj_admin_unread_orders";

/** Bunyi notifikasi singkat via WebAudio (tanpa file audio). */
function beep() {
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return;
    const ctx = new Ctx();
    const play = (freq, start, dur) => {
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = "sine";
      o.frequency.value = freq;
      g.gain.setValueAtTime(0.0001, ctx.currentTime + start);
      g.gain.exponentialRampToValueAtTime(0.25, ctx.currentTime + start + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + start + dur);
      o.connect(g).connect(ctx.destination);
      o.start(ctx.currentTime + start);
      o.stop(ctx.currentTime + start + dur + 0.05);
    };
    play(880, 0, 0.18);
    play(1175, 0.2, 0.25);
  } catch {
    /* ignore */
  }
}

function browserNotify(title, body) {
  try {
    if (!("Notification" in window) || Notification.permission !== "granted") return;
    const n = new Notification(title, { body, icon: "/logo-icon.png", badge: "/logo-icon.png", tag: title + body });
    n.onclick = () => { window.focus(); n.close(); };
  } catch {
    /* ignore */
  }
}

/**
 * Terhubung ke SSE /api/admin/events dan menampilkan push notification saat ada
 * pesanan masuk / pembayaran lunas. Mengembalikan { connected, unread, clearUnread, requestPermission }.
 * Juga men-dispatch window event "admin:event" agar halaman lain bisa auto-refresh.
 */
export function useAdminEvents(enabled = true) {
  const navigate = useNavigate();
  const [connected, setConnected] = useState(false);
  const [unread, setUnread] = useState(() => Number(sessionStorage.getItem(UNREAD_KEY) || 0));
  const esRef = useRef(null);
  const retryRef = useRef(null);

  const clearUnread = useCallback(() => {
    setUnread(0);
    sessionStorage.setItem(UNREAD_KEY, "0");
  }, []);

  const requestPermission = useCallback(() => {
    if ("Notification" in window && Notification.permission === "default") Notification.requestPermission();
  }, []);

  useEffect(() => {
    if (!enabled) return undefined;
    const token = localStorage.getItem(ADMIN_TOKEN_KEY);
    if (!token) return undefined;
    let closed = false;

    const connect = () => {
      if (closed) return;
      const es = new EventSource(`${API_URL}/admin/events?token=${encodeURIComponent(token)}`);
      esRef.current = es;
      es.addEventListener("connected", () => setConnected(true));
      es.addEventListener("order.new", (e) => {
        const { data } = JSON.parse(e.data);
        setUnread((u) => {
          sessionStorage.setItem(UNREAD_KEY, String(u + 1));
          return u + 1;
        });
        beep();
        const body = `${data.customer_name} · ${rupiah(data.total)} · ${data.payment_method === "cod" ? "COD" : "Menunggu pembayaran"}`;
        toast.success(`Pesanan baru ${data.order_number}`, {
          description: body,
          duration: 12000,
          action: { label: "Lihat", onClick: () => navigate(`/admin/pesanan?q=${encodeURIComponent(data.order_number)}`) },
        });
        browserNotify(`Pesanan baru ${data.order_number}`, body);
        window.dispatchEvent(new CustomEvent("admin:event", { detail: { type: "order.new", data } }));
      });
      es.addEventListener("payment.paid", (e) => {
        const { data } = JSON.parse(e.data);
        beep();
        const body = `${data.customer_name} · ${rupiah(data.total)}`;
        toast.success(`Pembayaran lunas ${data.order_number}`, {
          description: body,
          duration: 10000,
          action: { label: "Lihat", onClick: () => navigate(`/admin/pesanan?q=${encodeURIComponent(data.order_number)}`) },
        });
        browserNotify(`Pembayaran lunas ${data.order_number}`, body);
        window.dispatchEvent(new CustomEvent("admin:event", { detail: { type: "payment.paid", data } }));
      });
      es.addEventListener("order.updated", (e) => {
        const { data } = JSON.parse(e.data);
        window.dispatchEvent(new CustomEvent("admin:event", { detail: { type: "order.updated", data } }));
      });
      es.onerror = () => {
        setConnected(false);
        es.close();
        if (!closed) retryRef.current = setTimeout(connect, 4000);
      };
    };
    connect();

    return () => {
      closed = true;
      clearTimeout(retryRef.current);
      esRef.current?.close();
    };
  }, [enabled, navigate]);

  return { connected, unread, clearUnread, requestPermission };
}
