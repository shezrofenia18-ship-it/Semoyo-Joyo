"""Travoy Pay (Virtual Account) — KERANGKA integrasi, menunggu dokumen API resmi.

Semua method yang menyentuh API Travoy Pay sengaja melempar NotImplementedError sampai dokumen tersedia.
Saat TRAVOY_API_KEY & TRAVOY_BASE_URL kosong, sistem berjalan dalam mode placeholder: pesanan Transfer VA
dibuat dengan status "pending" dan halaman pembayaran menampilkan pemberitahuan "integrasi sedang disiapkan".
"""
import os
from typing import Any

PROVIDER = "travoy"


class TravoyPayClient:
    def __init__(self) -> None:
        self.api_key = os.environ.get("TRAVOY_API_KEY", "").strip()
        self.base_url = os.environ.get("TRAVOY_BASE_URL", "").strip().rstrip("/")
        self.callback_token = os.environ.get("TRAVOY_CALLBACK_TOKEN", "").strip()

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.base_url)

    @property
    def mode(self) -> str:
        return "travoy" if self.enabled else "travoy_placeholder"

    def placeholder_instructions(self, amount: int) -> dict[str, Any]:
        return {
            "type": "transfer_va",
            "provider": PROVIDER,
            "status": "awaiting_integration",
            "amount": amount,
            "message": "Integrasi Travoy Pay sedang disiapkan. Nomor Virtual Account akan tampil di sini setelah aktif.",
        }

    # ---- TODO(travoy): implementasi sesuai dokumen API ----
    async def create_va(self, *, order_number: str, amount: int, customer_name: str, phone: str) -> dict[str, Any]:
        """Buat VA. Harus mengembalikan {reference, va_number, bank_name, expires_at, raw}."""
        raise NotImplementedError("Travoy Pay create_va: menunggu dokumen API")

    async def get_status(self, order_number: str) -> dict[str, Any]:
        """Cek status VA. Harus mengembalikan {status: pending|paid|expired|failed, raw}."""
        raise NotImplementedError("Travoy Pay get_status: menunggu dokumen API")

    def verify_callback(self, headers: dict[str, str], payload: dict[str, Any]) -> bool:
        """Verifikasi signature/token callback Travoy Pay."""
        raise NotImplementedError("Travoy Pay verify_callback: menunggu dokumen API")

    def map_status(self, payload: dict[str, Any]) -> str:
        """Petakan status callback Travoy Pay ke pending|paid|expired|failed."""
        raise NotImplementedError("Travoy Pay map_status: menunggu dokumen API")


travoy = TravoyPayClient()
