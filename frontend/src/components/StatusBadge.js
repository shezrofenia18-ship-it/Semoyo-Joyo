import { Badge } from "@/components/ui/badge";
import { CUSTOMER_SEGMENT_LABEL, ORDER_STATUS_LABEL, PAYMENT_STATUS_LABEL } from "@/lib/format";
import { cn } from "@/lib/utils";

const PAYMENT = {
  pending: "bg-amber-50 text-amber-800 border-amber-200",
  paid: "bg-emerald-50 text-emerald-800 border-emerald-200",
  failed: "bg-rose-50 text-rose-800 border-rose-200",
  expired: "bg-zinc-50 text-zinc-700 border-zinc-200",
  cod: "bg-sky-50 text-sky-800 border-sky-200",
  piutang: "bg-violet-50 text-violet-800 border-violet-200",
};
const ORDER = {
  baru: "bg-slate-50 text-slate-800 border-slate-200",
  diproses: "bg-amber-50 text-amber-800 border-amber-200",
  dikirim: "bg-sky-50 text-sky-800 border-sky-200",
  selesai: "bg-emerald-50 text-emerald-800 border-emerald-200",
  dibatalkan: "bg-rose-50 text-rose-800 border-rose-200",
};
const SEGMENT = {
  tetap: "bg-brand-yellow/30 text-amber-900 border-brand-yellow",
  aktif: "bg-emerald-50 text-emerald-800 border-emerald-200",
  baru: "bg-sky-50 text-sky-800 border-sky-200",
  pasif: "bg-zinc-50 text-zinc-700 border-zinc-200",
};

export const PaymentStatusBadge = ({ status, className, ...props }) => (
  <Badge variant="outline" className={cn("rounded-md font-medium", PAYMENT[status] || PAYMENT.pending, className)} {...props}>
    {PAYMENT_STATUS_LABEL[status] || status}
  </Badge>
);

export const OrderStatusBadge = ({ status, className, ...props }) => (
  <Badge variant="outline" className={cn("rounded-md font-medium", ORDER[status] || ORDER.baru, className)} {...props}>
    {ORDER_STATUS_LABEL[status] || status}
  </Badge>
);

export const SegmentBadge = ({ segment, className, ...props }) => (
  <Badge variant="outline" className={cn("rounded-md font-medium", SEGMENT[segment] || SEGMENT.pasif, className)} {...props}>
    {CUSTOMER_SEGMENT_LABEL[segment] || segment}
  </Badge>
);
