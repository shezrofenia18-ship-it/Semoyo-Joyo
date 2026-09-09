"""Midtrans Core API integration (Bank Transfer VA, E-Wallet, QRIS) with SIMULATION fallback.

When MIDTRANS_SERVER_KEY is empty the service runs in simulation mode: it generates realistic
payment instructions (VA numbers, deeplinks) and exposes a `simulate_paid` flow for testing.
When keys are configured, real charges are sent to Midtrans and status is verified via
GET /v2/{order_id}/status + HTTP notification webhook (SHA512 signature).
"""
import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx

BANKS = {
    "bca": "BCA Virtual Account",
    "bni": "BNI Virtual Account",
    "bri": "BRI Virtual Account",
    "mandiri": "Mandiri Bill Payment",
    "permata": "Permata Virtual Account",
}
EWALLETS = {
    "gopay": "GoPay",
    "shopeepay": "ShopeePay",
    "ovo": "OVO",
    "dana": "DANA",
}


class MidtransService:
    def __init__(self) -> None:
        self.server_key = os.environ.get("MIDTRANS_SERVER_KEY", "").strip()
        self.client_key = os.environ.get("MIDTRANS_CLIENT_KEY", "").strip()
        self.is_production = os.environ.get("MIDTRANS_IS_PRODUCTION", "false").lower() == "true"
        self.app_url = os.environ.get("APP_URL", "").rstrip("/")
        self.core_url = "https://api.midtrans.com" if self.is_production else "https://api.sandbox.midtrans.com"
        self.snap_url = (
            "https://app.midtrans.com/snap/v1/transactions"
            if self.is_production
            else "https://app.sandbox.midtrans.com/snap/v1/transactions"
        )

    # ---------- helpers ----------
    @property
    def enabled(self) -> bool:
        return bool(self.server_key)

    @property
    def mode(self) -> str:
        if not self.enabled:
            return "simulation"
        return "production" if self.is_production else "sandbox"

    def _headers(self) -> dict[str, str]:
        encoded = base64.b64encode(f"{self.server_key}:".encode()).decode()
        return {"Accept": "application/json", "Content-Type": "application/json", "Authorization": f"Basic {encoded}"}

    async def _post(self, url: str, body: dict) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url, json=body, headers=self._headers())
        data = r.json()
        if r.status_code >= 400 or str(data.get("status_code", "200")).startswith(("4", "5")):
            raise RuntimeError(f"Midtrans error: {data.get('status_message') or data}")
        return data

    async def _get(self, url: str) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(url, headers=self._headers())
        return r.json()

    @staticmethod
    def map_status(transaction_status: Optional[str], fraud_status: Optional[str] = None) -> str:
        s = (transaction_status or "").lower()
        if s in {"settlement", "capture"} and fraud_status not in {"deny", "challenge"}:
            return "paid"
        if s in {"pending", "authorize"}:
            return "pending"
        if s in {"expire", "expired"}:
            return "expired"
        if s in {"deny", "cancel", "failure", "failed", "refund", "partial_refund"}:
            return "failed"
        return "pending"

    def verify_signature(self, payload: dict) -> bool:
        raw = (
            str(payload.get("order_id", ""))
            + str(payload.get("status_code", ""))
            + str(payload.get("gross_amount", ""))
            + self.server_key
        )
        expected = hashlib.sha512(raw.encode()).hexdigest()
        return hmac.compare_digest(expected, str(payload.get("signature_key", "")))

    # ---------- charge ----------
    async def create_charge(
        self,
        order_number: str,
        amount: int,
        method: str,
        channel: Optional[str],
        customer_name: str,
        phone: str,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Return a normalized instruction dict for the frontend."""
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

        if method == "cod":
            return {
                "provider": "manual",
                "simulation": False,
                "reference": None,
                "payment_status": "cod",
                "instructions": {
                    "type": "cod",
                    "title": "Bayar di Tempat (COD)",
                    "steps": [
                        "Pesanan akan diproses oleh tim kami.",
                        "Kurir menghubungi No. Telp/WA Anda sebelum pengiriman.",
                        "Siapkan pembayaran tunai/transfer sesuai total saat barang diterima.",
                    ],
                },
                "raw": {"mode": "manual"},
            }

        if method == "piutang":
            return {
                "provider": "manual",
                "simulation": False,
                "reference": None,
                "payment_status": "piutang",
                "instructions": {
                    "type": "piutang",
                    "title": "Bayar Nanti (Piutang / Kasbon)",
                    "steps": [
                        "Pesanan dicatat sebagai piutang atas nama Anda dan akan diproses oleh tim kami.",
                        "Barang dikirim/diambil terlebih dahulu, pembayaran dilakukan belakangan sesuai kesepakatan.",
                        "Admin akan menandai pesanan LUNAS setelah pembayaran diterima (tunai/transfer).",
                    ],
                },
                "raw": {"mode": "manual", "receivable": True},
            }

        if not self.enabled:
            return self._simulate(order_number, amount, method, channel, phone, expires_at)

        # ---- real Midtrans charge ----
        body: dict[str, Any] = {
            "transaction_details": {"order_id": order_number, "gross_amount": amount},
            "customer_details": {"first_name": customer_name[:50], "phone": phone},
            "item_details": [
                {"id": i["id"][:50], "price": int(i["price"]), "quantity": int(i["qty"]), "name": i["name"][:50]}
                for i in items
            ],
        }
        callback = f"{self.app_url}/pembayaran/{order_number}" if self.app_url else None
        use_snap = False

        if method == "bank_transfer":
            bank = (channel or "bca").lower()
            if bank == "mandiri":
                body.update({"payment_type": "echannel", "echannel": {"bill_info1": "Pembayaran", "bill_info2": f"Pesanan {order_number}"}})
            else:
                body.update({"payment_type": "bank_transfer", "bank_transfer": {"bank": bank}})
        elif method == "qris":
            body.update({"payment_type": "qris", "qris": {"acquirer": "gopay"}})
        elif method == "ewallet":
            wallet = (channel or "gopay").lower()
            if wallet == "gopay":
                body.update({"payment_type": "gopay", "gopay": {"enable_callback": True, "callback_url": callback}})
            elif wallet == "shopeepay":
                body.update({"payment_type": "shopeepay", "shopeepay": {"callback_url": callback}})
            else:
                use_snap = True  # OVO / DANA hanya tersedia via Snap

        if use_snap:
            snap_body = {
                "transaction_details": body["transaction_details"],
                "customer_details": body["customer_details"],
                "item_details": body["item_details"],
                "enabled_payments": ["gopay", "shopeepay", "other_qris", "dana", "ovo"],
            }
            if callback:
                snap_body["callbacks"] = {"finish": callback}
            data = await self._post(self.snap_url, snap_body)
            return {
                "provider": "midtrans",
                "simulation": False,
                "reference": data.get("token"),
                "payment_status": "pending",
                "instructions": {
                    "type": "ewallet",
                    "channel": channel,
                    "channel_name": EWALLETS.get(channel or "", "E-Wallet"),
                    "redirect_url": data.get("redirect_url"),
                    "expires_at": expires_at,
                    "steps": ["Klik tombol Bayar untuk membuka halaman pembayaran.", "Selesaikan pembayaran di aplikasi e-wallet Anda."],
                },
                "raw": data,
            }

        data = await self._post(f"{self.core_url}/v2/charge", body)
        status = self.map_status(data.get("transaction_status"), data.get("fraud_status"))
        instructions: dict[str, Any] = {"type": method, "channel": channel, "expires_at": data.get("expiry_time") or expires_at}
        if method == "bank_transfer":
            if data.get("va_numbers"):
                va = data["va_numbers"][0]
                instructions.update({"bank": va.get("bank"), "bank_name": BANKS.get(va.get("bank", ""), va.get("bank")), "va_number": va.get("va_number")})
            elif data.get("permata_va_number"):
                instructions.update({"bank": "permata", "bank_name": BANKS["permata"], "va_number": data["permata_va_number"]})
            elif data.get("bill_key"):
                instructions.update({"bank": "mandiri", "bank_name": BANKS["mandiri"], "bill_key": data["bill_key"], "biller_code": data.get("biller_code")})
            instructions["steps"] = self._bank_steps(instructions.get("bank_name", "bank"))
        elif method == "qris":
            qr_url = next((a["url"] for a in data.get("actions", []) if a.get("name") == "generate-qr-code"), None)
            instructions.update({"qr_url": qr_url, "qr_string": data.get("qr_string"), "static": False, "steps": self._qris_steps()})
        elif method == "ewallet":
            deeplink = next((a["url"] for a in data.get("actions", []) if a.get("name") == "deeplink-redirect"), None)
            qr_url = next((a["url"] for a in data.get("actions", []) if a.get("name") == "generate-qr-code"), None)
            instructions.update({"channel_name": EWALLETS.get(channel or "", "E-Wallet"), "deeplink": deeplink, "qr_url": qr_url, "steps": self._ewallet_steps()})
        return {
            "provider": "midtrans",
            "simulation": False,
            "reference": data.get("transaction_id"),
            "payment_status": status,
            "instructions": instructions,
            "raw": data,
        }

    # ---------- simulation ----------
    def _simulate(self, order_number: str, amount: int, method: str, channel: Optional[str], phone: str, expires_at: str) -> dict[str, Any]:
        ref = f"SIM-{order_number}"
        digits = "".join(ch for ch in phone if ch.isdigit()) or "0000000000"
        instructions: dict[str, Any] = {"type": method, "channel": channel, "expires_at": expires_at, "simulation": True}
        if method == "bank_transfer":
            bank = (channel or "bca").lower()
            prefix = {"bca": "39012", "bni": "98800", "bri": "26215", "permata": "85200", "mandiri": "70012"}.get(bank, "39012")
            va = prefix + digits[-10:].rjust(10, "0")
            instructions.update({"bank": bank, "bank_name": BANKS.get(bank, bank.upper()), "va_number": va})
            if bank == "mandiri":
                instructions.update({"biller_code": "70012", "bill_key": digits[-11:].rjust(11, "0")})
            instructions["steps"] = self._bank_steps(instructions["bank_name"])
        elif method == "qris":
            instructions.update({"static": True, "qr_url": None, "qr_string": None, "steps": self._qris_steps()})
        elif method == "ewallet":
            wallet = (channel or "gopay").lower()
            instructions.update({
                "channel": wallet,
                "channel_name": EWALLETS.get(wallet, wallet.upper()),
                "deeplink": None,
                "steps": self._ewallet_steps(),
            })
        return {
            "provider": "simulation",
            "simulation": True,
            "reference": ref,
            "payment_status": "pending",
            "instructions": instructions,
            "raw": {"mode": "simulation", "order_id": order_number, "gross_amount": amount, "transaction_status": "pending"},
        }

    async def get_status(self, order_number: str) -> Optional[dict[str, Any]]:
        if not self.enabled:
            return None
        data = await self._get(f"{self.core_url}/v2/{order_number}/status")
        return {"status": self.map_status(data.get("transaction_status"), data.get("fraud_status")), "raw": data}

    @staticmethod
    def _bank_steps(bank_name: str) -> list[str]:
        return [
            f"Buka m-banking / ATM {bank_name}.",
            "Pilih menu Transfer > Virtual Account / Pembayaran.",
            "Masukkan nomor Virtual Account di atas.",
            "Pastikan nominal sesuai total pesanan, lalu konfirmasi.",
            "Status pesanan akan terverifikasi otomatis setelah pembayaran diterima.",
        ]

    @staticmethod
    def _qris_steps() -> list[str]:
        return [
            "Buka aplikasi e-wallet / m-banking yang mendukung QRIS.",
            "Pilih Scan QR, lalu arahkan kamera ke kode QR di atas.",
            "Periksa nominal dan nama merchant, lalu konfirmasi pembayaran.",
        ]

    @staticmethod
    def _ewallet_steps() -> list[str]:
        return [
            "Klik tombol Bayar untuk membuka aplikasi e-wallet Anda.",
            "Periksa nominal pembayaran, lalu konfirmasi dengan PIN.",
            "Kembali ke halaman ini, status akan diperbarui otomatis.",
        ]


midtrans = MidtransService()
