import { useEffect, useMemo, useState } from "react";
import { Banknote, HandCoins, CreditCard, QrCode, Landmark, Clock, Info } from "lucide-react";
import { api } from "@/lib/api";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { rupiah } from "@/lib/format";
import { cn } from "@/lib/utils";

/** Tiga metode pembayaran mutlak (urutan tetap). */
export const METHODS = [
  { key: "cash", title: "Cash (Tunai)", desc: "Bayar tunai ke kasir. Status Proses sampai kasir menerima uang", icon: Banknote },
  { key: "piutang", title: "Bayar Nanti", desc: "Ambil barang dulu, otomatis masuk modul Piutang", icon: HandCoins },
  { key: "online", title: "Bayar Online", desc: "QRIS / Virtual Account via BATPay, dikenakan biaya layanan", icon: CreditCard },
];

/** Ambil konfigurasi metode & kanal dari backend. */
export function usePaymentConfig() {
  const [config, setConfig] = useState(null);
  useEffect(() => {
    api.get("/payments/config").then((r) => setConfig(r.data)).catch(() => setConfig({ methods: [], online_enabled: false }));
  }, []);
  return config;
}

/** Pratinjau biaya layanan per kanal untuk nominal tertentu. */
export function useFeePreview(amount, enabled = true) {
  const [fee, setFee] = useState(null);
  useEffect(() => {
    if (!enabled || !(amount > 0)) return undefined;
    let alive = true;
    api.get("/payments/fee", { params: { amount, channel: "qris" } }).then((r) => alive && setFee(r.data)).catch(() => alive && setFee(null));
    return () => { alive = false; };
  }, [amount, enabled]);
  return fee;
}

/**
 * Dropdown metode pembayaran (tepat 3 opsi) + pemilih kanal Bayar Online dengan biaya layanan & total per kanal.
 * Props: method, onMethodChange, channel, onChannelChange, amount (dasar), config (dari usePaymentConfig), compact, idPrefix
 */
export function PaymentMethodPicker({ method, onMethodChange, channel, onChannelChange, amount = 0, config, compact = false, idPrefix = "pm", disabled = false }) {
  const onlineEnabled = !!config?.online_enabled;
  const fee = useFeePreview(amount, method === "online");
  const channels = useMemo(
    () => fee?.channels || config?.methods?.find((m) => m.key === "online")?.channels || [],
    [fee, config],
  );

  useEffect(() => {
    if (method === "online" && channels.length && !channels.some((c) => c.key === channel)) onChannelChange?.(channels[0].key);
  }, [method, channels, channel, onChannelChange]);

  return (
    <div className="space-y-3">
      <div className="space-y-1.5">
        <Label htmlFor={`${idPrefix}-select`}>Metode Pembayaran *</Label>
        <Select value={method} onValueChange={onMethodChange} disabled={disabled}>
          <SelectTrigger id={`${idPrefix}-select`} className="h-11 bg-card" data-testid="payment-method-select">
            <SelectValue placeholder="Pilih metode pembayaran" />
          </SelectTrigger>
          <SelectContent>
            {METHODS.map(({ key, title, desc, icon: I }) => {
              const off = key === "online" && !onlineEnabled;
              return (
                <SelectItem key={key} value={key} disabled={off} data-testid={`payment-method-option-${key}`}>
                  <span className="flex items-center gap-2">
                    <I className="h-4 w-4 text-primary" />
                    <span className="font-medium">{title}</span>
                    {!compact && <span className="hidden text-xs text-muted-foreground sm:inline">— {desc}</span>}
                    {off && <span className="ml-1 rounded border border-amber-300 bg-amber-50 px-1 text-[10px] font-semibold text-amber-800">Belum aktif</span>}
                  </span>
                </SelectItem>
              );
            })}
          </SelectContent>
        </Select>
      </div>

      {method === "cash" && (
        <div className="flex items-start gap-2 rounded-xl border border-sky-200 bg-sky-50 p-3.5 text-sm text-sky-900" data-testid="cash-notice">
          <Banknote className="mt-0.5 h-4 w-4 shrink-0" />
          <p>Pesanan berstatus <b>Proses</b>. Bayar tunai ke kasir; status menjadi <b>Lunas</b> dan pesanan <b>Selesai</b> setelah kasir menekan <b>"Selesai / Terima Uang"</b>.</p>
        </div>
      )}
      {method === "piutang" && (
        <div className="flex items-start gap-2 rounded-xl border border-violet-200 bg-violet-50 p-3.5 text-sm text-violet-900" data-testid="piutang-notice">
          <HandCoins className="mt-0.5 h-4 w-4 shrink-0" />
          <p>Pesanan dicatat sebagai <b>piutang (kasbon)</b> dan otomatis masuk modul Piutang. Status <b>Lunas</b> setelah admin menandai pembayaran diterima.</p>
        </div>
      )}
      {method === "online" && (
        <div className="space-y-2" data-testid="online-channel-picker">
          <p className="text-xs font-medium text-muted-foreground">Pilih kanal pembayaran (biaya layanan BATPay dibebankan ke pembeli):</p>
          {!onlineEnabled && (
            <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900" data-testid="online-inactive-notice">
              <Clock className="mt-0.5 h-3.5 w-3.5 shrink-0" /> Bayar Online belum aktif (kredensial BATPay belum dikonfigurasi). Pilih Cash atau Bayar Nanti.
            </div>
          )}
          <div className={cn("grid gap-2", compact ? "grid-cols-1" : "sm:grid-cols-2")}>
            {channels.map((c) => {
              const I = c.group === "qris" ? QrCode : Landmark;
              const active = channel === c.key;
              const svc = c.service_fee ?? null;
              return (
                <button
                  key={c.key}
                  type="button"
                  disabled={disabled}
                  onClick={() => onChannelChange?.(c.key)}
                  data-testid={`payment-channel-${c.key}`}
                  aria-pressed={active}
                  className={cn(
                    "flex items-start gap-3 rounded-xl border bg-card p-3 text-left shadow-sm transition-colors hover:bg-muted/40",
                    active && "border-primary ring-2 ring-ring"
                  )}
                >
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground"><I className="h-4 w-4" /></span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-semibold">{c.name}</span>
                    <span className="block text-xs text-muted-foreground">
                      Biaya layanan {c.fee_percent > 0 ? `${c.fee_percent}%` : ""}{c.fee_percent > 0 && c.fee_fixed > 0 ? " + " : ""}{c.fee_fixed > 0 ? rupiah(c.fee_fixed) : ""}
                      {svc !== null && amount > 0 && <> · <b className="text-foreground">{rupiah(svc)}</b></>}
                    </span>
                    {svc !== null && amount > 0 && (
                      <span className="mt-1 block text-xs">Total bayar: <b className="font-display text-sm text-primary" data-testid={`channel-total-${c.key}`}>{rupiah(c.total)}</b></span>
                    )}
                  </span>
                </button>
              );
            })}
          </div>
          <p className="flex items-start gap-1.5 text-[11px] text-muted-foreground"><Info className="mt-0.5 h-3 w-3 shrink-0" /> Biaya layanan dihitung otomatis (gross-up) agar dana yang diterima toko tetap utuh.</p>
        </div>
      )}
    </div>
  );
}

/** Biaya layanan untuk kanal terpilih dari hasil pratinjau. */
export function channelFee(fee, channel) {
  return fee?.channels?.find((c) => c.key === channel)?.service_fee ?? 0;
}
