"""BATPay (batbiz.id) SNAP API client - Bayar Online (QRIS MPM dinamis & Virtual Account).

Referensi: https://developer.batbiz.id (Postman collection "BATPay Developer Site", SNAP - API v1.0).

Ringkasan protokol SNAP yang diimplementasikan:
  1. B2B Access Token  POST /api/v1.0/access-token/b2b
     Header X-CLIENT-KEY, X-TIMESTAMP (WIB, +07:00), X-SIGNATURE = base64(SHA256withRSA(clientKey + "|" + timestamp, privateKey))
  2. Transaksional (QRIS generate/query/cancel, VA create/status)
     Header Authorization: Bearer <token>, X-PARTNER-ID, X-EXTERNAL-ID (numerik unik/hari), X-TIMESTAMP, CHANNEL-ID,
     X-SIGNATURE = base64(HMAC_SHA512(clientSecret, METHOD:PATH:token:lowercase(hex(sha256(minify(body)))):timestamp))
  3. Notifikasi (BATPay -> partner): BATPay meminta token B2B ke partner (signature RSA dengan private key BATPay,
     diverifikasi dengan public key BATPay), lalu memanggil URL notifikasi dengan Bearer token + X-SIGNATURE HMAC_SHA512.

Mode:
  - enabled  : BATPAY_PARTNER_ID, BATPAY_CLIENT_ID, BATPAY_SECRET_KEY, BATPAY_PRIVATE_KEY, BATPAY_MERCHANT_ID terisi -> tagihan dibuat nyata.
  - partial  : sebagian terisi (mis. private key belum ada) -> tetap placeholder, UI Owner menampilkan variabel yang kurang.
  - placeholder: kredensial kosong -> pesanan Bayar Online tetap dibuat (pending + biaya layanan), instruksi "menunggu aktivasi".

Biaya layanan (gross-up) agar dana yang cair ke toko utuh:
  total_tagihan = ceil((dasar + biaya_tetap) / (1 - persen/100)); biaya_layanan = total_tagihan - dasar
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import math
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

import httpx
import jwt
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

logger = logging.getLogger("mbg.batpay")

PROVIDER = "batpay"
WIB = timezone(timedelta(hours=7))

SANDBOX_BASE_URL = "https://openapi.sandbox.batbiz.id"
PRODUCTION_BASE_URL = "https://openapi.batbiz.id"

# Public key BATPay (dari dokumentasi resmi, bagian "Digital Signature") - dipakai memverifikasi permintaan token dari BATPay.
BATPAY_PUBLIC_KEYS = {
    "sandbox": (
        "-----BEGIN PUBLIC KEY-----\n"
        "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC1YYedtMfVpE9wn1/NtHk1F7sz\n"
        "9HqojRcquUju0V7/Vq71cIw2eDCizmVsjanf36TPl8/gfdo2/0tvtxXNzAN2ePN7\n"
        "s2GEnKExBv4/K2dLGqINefsJEyNQcwlzmOGI1saYT5spm+VM4ZkQyAF2ONGZ3x46\n"
        "HfNJDDPJzs6RoUoDhQIDAQAB\n"
        "-----END PUBLIC KEY-----"
    ),
    "production": (
        "-----BEGIN PUBLIC KEY-----\n"
        "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCKBSQXIsiakfbby1YcL2yil0wG\n"
        "y8mTCEGHTjhg1pXiewVLH/j2JgJXjIN7nTikmAD/g2taaYzctFZ/vMs12aHtSYmy\n"
        "kSQCqQGHF3DjKvTViJ6Wlc15KhaeFDWojfSbxGLU67RbpG81XsOotKRpkf4VOBL1\n"
        "ruWPf6qwW9e7SA8WzQIDAQAB\n"
        "-----END PUBLIC KEY-----"
    ),
}

# Path relatif endpoint SNAP
PATH_TOKEN = "/api/v1.0/access-token/b2b"
PATH_QR_GENERATE = "/api/v1.0/qr/qr-mpm-generate"
PATH_QR_QUERY = "/api/v1.0/qr/qr-mpm-query"
PATH_QR_CANCEL = "/api/v1.0/qr/qr-mpm-cancel"
PATH_VA_CREATE = "/api/v1.0/transfer-va/create-va"
PATH_VA_STATUS = "/api/v1.0/transfer-va/status"
PATH_VA_DELETE = "/api/v1.0/transfer-va/delete-va"

# Path endpoint kita yang dipanggil BATPay (didaftarkan di dashboard BATPay)
INBOUND_TOKEN_PATH = "/api/payments/batpay/access-token/b2b"
WEBHOOK_PATH = "/api/payments/batpay/webhook"

# Status QRIS SNAP (latestTransactionStatus)
QR_STATUS = {"00": "paid", "01": "pending", "02": "pending", "03": "pending", "04": "refunded", "05": "expired", "06": "failed", "07": "failed"}

VA_BANKS = {
    "bca": {"name": "BCA", "payment_type": "BCA_DYNAMIC"},
    "mandiri": {"name": "Mandiri", "payment_type": "MANDIRI_DYNAMIC"},
    "cimb": {"name": "CIMB Niaga", "payment_type": "CIMB_DYNAMIC"},
    "danamon": {"name": "Danamon", "payment_type": "DANAMON_DYNAMIC"},
}


class BatpayError(Exception):
    """Kesalahan dari API BATPay (responseCode non-2xx atau HTTP error)."""

    def __init__(self, message: str, code: str = "", raw: Any = None):
        super().__init__(message)
        self.code = code
        self.raw = raw


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _env_float(name: str, default: float) -> float:
    try:
        return float(_env(name, str(default)) or default)
    except ValueError:
        return default


def _load_pem(value: str) -> str:
    """Terima PEM langsung, PEM dengan \\n literal, path file, atau base64 dari PEM."""
    v = (value or "").strip()
    if not v:
        return ""
    if "-----BEGIN" in v:
        return v.replace("\\n", "\n")
    p = Path(v)
    if p.exists() and p.is_file():
        return p.read_text().strip()
    try:
        decoded = base64.b64decode(v).decode()
        if "-----BEGIN" in decoded:
            return decoded
    except Exception:  # noqa: BLE001
        pass
    return v


def wib_timestamp(dt: Optional[datetime] = None) -> str:
    """YYYY-MM-DDTHH:mm:ss+07:00 (Jakarta time) - format wajib SNAP."""
    d = (dt or datetime.now(timezone.utc)).astimezone(WIB)
    return d.strftime("%Y-%m-%dT%H:%M:%S") + "+07:00"


def minify(body: Any) -> str:
    if body is None or body == "":
        return ""
    if isinstance(body, (bytes, bytearray)):
        body = body.decode()
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            return body
    return json.dumps(body, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest().lower()


def money(amount: Decimal | float | int) -> dict[str, str]:
    return {"value": f"{Decimal(str(amount)):.2f}", "currency": "IDR"}


def external_id() -> str:
    """Numeric string, unik per hari (maks 36 karakter)."""
    return f"{int(time.time() * 1000)}{uuid.uuid4().int % 10**8:08d}"


# --------------------------------------------------------------------------------------
# Signature helpers (murni, bisa diuji tanpa jaringan)
# --------------------------------------------------------------------------------------
def rsa_sign(private_pem: str, string_to_sign: str) -> str:
    key = serialization.load_pem_private_key(private_pem.encode(), password=None)
    sig = key.sign(string_to_sign.encode(), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(sig).decode()


def rsa_verify(public_pem: str, string_to_sign: str, signature_b64: str) -> bool:
    try:
        key = serialization.load_pem_public_key(public_pem.encode())
        key.verify(base64.b64decode(signature_b64), string_to_sign.encode(), padding.PKCS1v15(), hashes.SHA256())
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False


def token_string_to_sign(client_key: str, timestamp: str) -> str:
    return f"{client_key}|{timestamp}"


def transaction_string_to_sign(method: str, path: str, access_token: str, body: Any, timestamp: str) -> str:
    return f"{method.upper()}:{path}:{access_token}:{sha256_hex(minify(body))}:{timestamp}"


def hmac_sha512(secret: str, string_to_sign: str) -> str:
    return base64.b64encode(hmac.new(secret.encode(), string_to_sign.encode(), hashlib.sha512).digest()).decode()


def generate_rsa_keypair() -> tuple[str, str]:
    """(private_pkcs8_pem, public_pem) RSA-2048 - untuk membuat pasangan kunci partner."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
    pub = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    return priv, pub


# --------------------------------------------------------------------------------------
# Biaya layanan (gross-up)
# --------------------------------------------------------------------------------------
def gross_up_fee(base_amount: int | float | Decimal, percent: float, fixed: float) -> int:
    """Biaya layanan agar toko menerima `base_amount` utuh setelah potongan `percent`% + `fixed`.

    total = ceil((base + fixed) / (1 - percent/100)); fee = total - base. Dibulatkan ke atas ke rupiah penuh.
    """
    base = float(base_amount or 0)
    if base <= 0:
        return 0
    pct = max(0.0, min(float(percent or 0), 99.0)) / 100.0
    total = (base + float(fixed or 0)) / (1.0 - pct)
    return max(0, int(math.ceil(total - 1e-9)) - int(round(base)))


# --------------------------------------------------------------------------------------
# Client
# --------------------------------------------------------------------------------------
class BatpayClient:
    def __init__(self) -> None:
        self.env = (_env("BATPAY_ENV", "sandbox").lower() or "sandbox")
        if self.env not in ("sandbox", "production"):
            self.env = "sandbox"
        self.base_url = (_env("BATPAY_BASE_URL") or (PRODUCTION_BASE_URL if self.env == "production" else SANDBOX_BASE_URL)).rstrip("/")
        # Kredensial dari dashboard BATPay: Client ID (X-CLIENT-KEY saat minta token), Partner ID (X-PARTNER-ID saat transaksi),
        # Secret Key (HMAC_SHA512). Nama env lama BATPAY_CLIENT_KEY / BATPAY_CLIENT_SECRET tetap diterima sebagai fallback.
        self.client_id = _env("BATPAY_CLIENT_ID") or _env("BATPAY_CLIENT_KEY")
        self.partner_id = _env("BATPAY_PARTNER_ID") or self.client_id
        self.secret_key = _env("BATPAY_SECRET_KEY") or _env("BATPAY_CLIENT_SECRET")
        self.private_key = _load_pem(_env("BATPAY_PRIVATE_KEY"))
        self.merchant_id = _env("BATPAY_MERCHANT_ID")
        self.channel_id = _env("BATPAY_CHANNEL_ID", "95221")
        self.public_key = _load_pem(_env("BATPAY_PUBLIC_KEY")) or BATPAY_PUBLIC_KEYS[self.env]
        self.webhook_token = _env("BATPAY_WEBHOOK_TOKEN")
        self.expire_minutes = int(_env_float("BATPAY_EXPIRE_MINUTES", 60))
        # Biaya layanan: default global BATPAY_FEE_PERCENT (0,7%) & BATPAY_FEE_FIXED (Rp0),
        # bisa di-override per kanal lewat BATPAY_QRIS_FEE_* / BATPAY_VA_FEE_* (opsional, kosong = pakai global).
        self.fee_percent = _env_float("BATPAY_FEE_PERCENT", 0.7)
        self.fee_fixed = _env_float("BATPAY_FEE_FIXED", 0)
        self.fees = {
            "qris": {"percent": _env_float("BATPAY_QRIS_FEE_PERCENT", self.fee_percent), "fixed": _env_float("BATPAY_QRIS_FEE_FIXED", self.fee_fixed)},
            "va": {"percent": _env_float("BATPAY_VA_FEE_PERCENT", self.fee_percent), "fixed": _env_float("BATPAY_VA_FEE_FIXED", self.fee_fixed)},
        }
        banks = [b.strip().lower() for b in _env("BATPAY_VA_BANKS", "BCA,MANDIRI,CIMB,DANAMON").split(",") if b.strip()]
        self.va_banks = [b for b in banks if b in VA_BANKS] or list(VA_BANKS)
        self._token: Optional[str] = None
        self._token_exp: float = 0.0

    # ---------- konfigurasi ----------
    @property
    def enabled(self) -> bool:
        return bool(self.client_id and self.partner_id and self.secret_key and self.private_key and self.merchant_id)

    @property
    def mode(self) -> str:
        return f"batpay_{self.env}" if self.enabled else "batpay_placeholder"

    @property
    def webhook_ready(self) -> bool:
        """Webhook dapat memverifikasi notifikasi: via signature SNAP (enabled) atau token internal."""
        return self.enabled or bool(self.webhook_token)

    def channels(self) -> list[dict[str, Any]]:
        """Daftar kanal Bayar Online untuk checkout (biaya per kanal)."""
        out = [{"key": "qris", "name": "QRIS", "group": "qris", "description": "Scan QR dari semua e-wallet & mobile banking",
                "fee_percent": self.fees["qris"]["percent"], "fee_fixed": self.fees["qris"]["fixed"]}]
        for b in self.va_banks:
            info = VA_BANKS[b]
            out.append({"key": f"va_{b}", "name": f"Virtual Account {info['name']}", "group": "va", "bank": info["name"],
                        "description": f"Transfer ke nomor VA {info['name']} (ATM / m-banking)",
                        "fee_percent": self.fees["va"]["percent"], "fee_fixed": self.fees["va"]["fixed"]})
        return out

    def normalize_channel(self, channel: Optional[str]) -> str:
        c = (channel or "qris").strip().lower()
        valid = {ch["key"] for ch in self.channels()}
        return c if c in valid else "qris"

    def service_fee(self, base_amount: int | float | Decimal, channel: Optional[str]) -> int:
        group = "va" if self.normalize_channel(channel).startswith("va_") else "qris"
        f = self.fees[group]
        return gross_up_fee(base_amount, f["percent"], f["fixed"])

    def public_config(self, app_url: str = "") -> dict[str, Any]:
        base = (app_url or "").rstrip("/")
        configured = {"partner_id": bool(self.partner_id), "client_id": bool(self.client_id), "secret_key": bool(self.secret_key),
                      "private_key": bool(self.private_key), "merchant_id": bool(self.merchant_id), "webhook_token": bool(self.webhook_token)}
        required = {k: v for k, v in configured.items() if k != "webhook_token"}
        return {
            "provider": PROVIDER, "mode": self.mode, "enabled": self.enabled, "env": self.env, "base_url": self.base_url,
            "partial": (not self.enabled) and any(required.values()), "missing": [k for k, v in required.items() if not v],
            "merchant_id": self.merchant_id, "partner_id_hint": (self.partner_id[:6] + "..." + self.partner_id[-4:]) if len(self.partner_id) > 12 else bool(self.partner_id),
            "webhook_ready": self.webhook_ready, "webhook_url": f"{base}{WEBHOOK_PATH}", "token_url": f"{base}{INBOUND_TOKEN_PATH}",
            "channels": self.channels(), "expire_minutes": self.expire_minutes,
            "fees": {"default": {"percent": self.fee_percent, "fixed": self.fee_fixed}, "qris": self.fees["qris"], "va": self.fees["va"]},
            "va_banks": [VA_BANKS[b]["name"] for b in self.va_banks],
            "configured": configured,
        }

    async def test_connection(self) -> dict[str, Any]:
        """Uji koneksi ke BATPay: ambil token B2B baru. Tidak pernah mengembalikan rahasia."""
        if not self.enabled:
            return {"ok": False, "step": "config", "message": "Kredensial belum lengkap", "missing": self.public_config()["missing"]}
        t0 = time.perf_counter()
        try:
            token = await self.get_token(force=True)
            return {"ok": True, "step": "token", "message": "Token B2B berhasil diambil dari BATPay", "base_url": self.base_url,
                    "token_preview": f"{token[:6]}...{token[-4:]}" if len(token) > 12 else "***", "latency_ms": int((time.perf_counter() - t0) * 1000)}
        except BatpayError as e:
            return {"ok": False, "step": "token", "message": str(e), "code": e.code, "raw": e.raw if isinstance(e.raw, (dict, str)) else None,
                    "base_url": self.base_url, "latency_ms": int((time.perf_counter() - t0) * 1000)}
        except httpx.HTTPError as e:
            return {"ok": False, "step": "network", "message": f"Tidak dapat menghubungi {self.base_url}: {e.__class__.__name__}", "base_url": self.base_url,
                    "latency_ms": int((time.perf_counter() - t0) * 1000)}

    def placeholder_instructions(self, amount: int, channel: str) -> dict[str, Any]:
        ch = next((c for c in self.channels() if c["key"] == channel), None) or {"name": "QRIS"}
        return {
            "type": "online", "provider": PROVIDER, "channel": channel, "channel_name": ch["name"], "status": "awaiting_integration", "amount": amount,
            "message": "Pembayaran online BATPay belum aktif (kredensial belum dikonfigurasi). Silakan pilih Cash atau Bayar Nanti, atau hubungi kasir.",
        }

    # ---------- signature outbound ----------
    def sign_token_request(self, timestamp: str) -> str:
        return rsa_sign(self.private_key, token_string_to_sign(self.client_id, timestamp))

    def sign_transaction(self, method: str, path: str, token: str, body: Any, timestamp: str) -> str:
        return hmac_sha512(self.secret_key, transaction_string_to_sign(method, path, token, body, timestamp))

    def _headers(self, path: str, token: str, body: Any) -> dict[str, str]:
        ts = wib_timestamp()
        return {
            "Content-Type": "application/json", "Accept": "application/json", "Authorization": f"Bearer {token}",
            "X-PARTNER-ID": self.partner_id, "X-EXTERNAL-ID": external_id(), "X-TIMESTAMP": ts, "CHANNEL-ID": self.channel_id,
            "X-SIGNATURE": self.sign_transaction("POST", path, token, body, ts),
        }

    # ---------- HTTP ----------
    async def get_token(self, force: bool = False) -> str:
        if not self.enabled:
            raise BatpayError("BATPay belum dikonfigurasi")
        if self._token and not force and time.time() < self._token_exp - 30:
            return self._token
        ts = wib_timestamp()
        headers = {"Content-Type": "application/json", "X-CLIENT-KEY": self.client_id, "X-TIMESTAMP": ts, "X-SIGNATURE": self.sign_token_request(ts),
                   "CHANNEL-ID": self.channel_id}
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(f"{self.base_url}{PATH_TOKEN}", json={"grantType": "client_credentials"}, headers=headers)
        data = self._parse(r, "token")
        self._token = data.get("accessToken", "")
        self._token_exp = time.time() + float(data.get("expiresIn") or 900)
        if not self._token:
            raise BatpayError("BATPay tidak mengembalikan accessToken", raw=data)
        return self._token

    async def _post(self, path: str, body: dict[str, Any], label: str) -> dict[str, Any]:
        token = await self.get_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(f"{self.base_url}{path}", content=minify(body), headers=self._headers(path, token, body))
            if r.status_code == 401:  # token kedaluwarsa -> refresh sekali
                token = await self.get_token(force=True)
                r = await c.post(f"{self.base_url}{path}", content=minify(body), headers=self._headers(path, token, body))
        return self._parse(r, label)

    @staticmethod
    def _parse(r: httpx.Response, label: str) -> dict[str, Any]:
        try:
            data = r.json()
        except ValueError:
            raise BatpayError(f"BATPay {label}: respons bukan JSON (HTTP {r.status_code})", raw=r.text[:500])
        code = str(data.get("responseCode", ""))
        if not code.startswith("2"):
            raise BatpayError(f"BATPay {label} gagal: {data.get('responseMessage', 'Unknown error')} ({code or r.status_code})", code=code, raw=data)
        return data

    # ---------- QRIS ----------
    async def create_qris(self, *, reference: str, amount: int, fee: int) -> dict[str, Any]:
        expires = datetime.now(timezone.utc) + timedelta(minutes=self.expire_minutes)
        body = {"partnerReferenceNo": reference, "merchantId": self.merchant_id, "amount": money(amount), "feeAmount": money(fee),
                "validityPeriod": wib_timestamp(expires), "additionalInfo": {"terminalSource": "WEB"}}
        data = await self._post(PATH_QR_GENERATE, body, "generate QRIS")
        return {"reference": reference, "provider_ref": data.get("referenceNo"), "qr_content": data.get("qrContent"), "qr_url": data.get("qrUrl"),
                "qr_image": data.get("qrImage"), "merchant_name": data.get("merchantName"), "expires_at": expires.isoformat(), "raw": data}

    async def query_qris(self, *, reference: str, provider_ref: Optional[str] = None) -> dict[str, Any]:
        body = {"originalPartnerReferenceNo": reference, "serviceCode": "47", "additionalInfo": {}}
        if provider_ref:
            body["originalReferenceNo"] = provider_ref
        data = await self._post(PATH_QR_QUERY, body, "query QRIS")
        return {"status": QR_STATUS.get(str(data.get("latestTransactionStatus", "")), "pending"), "paid_time": data.get("paidTime"), "raw": data}

    async def cancel_qris(self, *, reference: str, provider_ref: Optional[str], amount: int, reason: str = "Metode pembayaran diubah") -> dict[str, Any]:
        body = {"originalPartnerReferenceNo": reference, "originalReferenceNo": provider_ref or "", "merchantId": self.merchant_id, "reason": reason,
                "amount": money(amount), "additionalInfo": {}}
        return await self._post(PATH_QR_CANCEL, body, "cancel QRIS")

    # ---------- Virtual Account ----------
    async def create_va(self, *, reference: str, bank: str, amount: int, customer_name: str, phone: str) -> dict[str, Any]:
        info = VA_BANKS.get(bank) or VA_BANKS["bca"]
        expires = datetime.now(timezone.utc) + timedelta(minutes=max(self.expire_minutes, 60))
        digits = "".join(ch for ch in (phone or "") if ch.isdigit())[:20] or f"{int(time.time())}"
        body = {"virtualAccountName": "".join(ch for ch in customer_name if ch.isalnum() or ch == " ")[:255] or "Pelanggan", "trxId": reference,
                "totalAmount": money(amount), "expiredDate": wib_timestamp(expires), "additionalInfo": {"accountNo": digits, "paymentType": info["payment_type"]}}
        data = await self._post(PATH_VA_CREATE, body, "create VA")
        va = data.get("virtualAccountData", {})
        return {"reference": reference, "provider_ref": (va.get("virtualAccountNo") or "").strip(), "va_number": (va.get("virtualAccountNo") or "").strip(),
                "bank_name": info["name"], "partner_service_id": va.get("partnerServiceId"), "customer_no": va.get("customerNo"),
                "expires_at": expires.isoformat(), "raw": data}

    @staticmethod
    def _va_body(reference: str, va_info: dict[str, Any]) -> dict[str, Any]:
        return {"partnerServiceId": va_info.get("partner_service_id") or "", "customerNo": va_info.get("customer_no") or "",
                "virtualAccountNo": va_info.get("va_number") or "", "trxId": reference, "additionalInfo": {}}

    async def query_va(self, *, reference: str, va_info: dict[str, Any]) -> dict[str, Any]:
        data = await self._post(PATH_VA_STATUS, self._va_body(reference, va_info), "status VA")
        vd = data.get("virtualAccountData") or {}
        if isinstance(vd, list):
            vd = vd[0] if vd else {}
        paid = float((vd.get("paidAmount") or {}).get("value") or 0)
        reason = json.dumps(vd.get("paymentFlagReason") or {}).lower()
        status = "paid" if paid > 0 and "belum" not in reason and "pending" not in reason else "pending"
        return {"status": status, "paid_amount": paid, "raw": data}

    async def delete_va(self, *, reference: str, va_info: dict[str, Any]) -> dict[str, Any]:
        return await self._post(PATH_VA_DELETE, self._va_body(reference, va_info), "delete VA")

    # ---------- Inbound: BATPay -> kita ----------
    def verify_inbound_token_request(self, headers: dict[str, str]) -> tuple[bool, str]:
        """Verifikasi permintaan B2B token dari BATPay (X-CLIENT-KEY, X-TIMESTAMP, X-SIGNATURE RSA dgn public key BATPay)."""
        h = {k.lower(): v for k, v in headers.items()}
        client_key, ts, sig = h.get("x-client-key", ""), h.get("x-timestamp", ""), h.get("x-signature", "")
        if not (client_key and ts and sig):
            return False, "Invalid Mandatory Field X-CLIENT-KEY/X-TIMESTAMP/X-SIGNATURE"
        if self.client_id and client_key not in (self.client_id, self.partner_id):
            return False, "Unauthorized. Unknown Client"
        if not rsa_verify(self.public_key, token_string_to_sign(client_key, ts), sig):
            return False, "Unauthorized. Signature"
        return True, ""

    def issue_inbound_token(self, jwt_secret: str, expires_in: int = 900) -> tuple[str, int]:
        now = datetime.now(timezone.utc)
        payload = {"sub": "batpay", "aud": "batpay-callback", "iat": now, "exp": now + timedelta(seconds=expires_in), "jti": uuid.uuid4().hex}
        return jwt.encode(payload, jwt_secret, algorithm="HS256"), expires_in

    def verify_webhook(self, headers: dict[str, str], raw_body: bytes | str, jwt_secret: str, path: str = WEBHOOK_PATH) -> tuple[bool, str]:
        """Verifikasi notifikasi pembayaran. Dua jalur: token internal (X-CALLBACK-TOKEN) ATAU signature SNAP (Bearer JWT + HMAC_SHA512)."""
        h = {k.lower(): v for k, v in headers.items()}
        if self.webhook_token and h.get("x-callback-token", "") == self.webhook_token:
            return True, "token"
        if not self.enabled:
            return False, "BATPay belum dikonfigurasi"
        auth = h.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return False, "Invalid Mandatory Field Authorization"
        token = auth.split(" ", 1)[1].strip()
        try:
            jwt.decode(token, jwt_secret, algorithms=["HS256"], audience="batpay-callback")
        except jwt.InvalidTokenError:
            return False, "Unauthorized. Invalid Token"
        ts, sig = h.get("x-timestamp", ""), h.get("x-signature", "")
        if not (ts and sig):
            return False, "Invalid Mandatory Field X-TIMESTAMP/X-SIGNATURE"
        expected = hmac_sha512(self.secret_key, transaction_string_to_sign("POST", path, token, raw_body, ts))
        if not hmac.compare_digest(expected, sig):
            return False, "Unauthorized. Signature"
        return True, "snap"

    @staticmethod
    def parse_notification(payload: dict[str, Any]) -> dict[str, Any]:
        """Petakan payload notifikasi QRIS / VA ke {reference, status, paid_amount, kind}."""
        if "latestTransactionStatus" in payload or "originalPartnerReferenceNo" in payload:
            status = QR_STATUS.get(str(payload.get("latestTransactionStatus", "")), "pending")
            amount = float((payload.get("amount") or {}).get("value") or 0)
            return {"kind": "qris", "reference": payload.get("originalPartnerReferenceNo", ""), "status": status, "paid_amount": amount,
                    "provider_ref": payload.get("originalReferenceNo")}
        if "trxId" in payload or "virtualAccountNo" in payload:
            paid = float((payload.get("paidAmount") or payload.get("totalAmount") or {}).get("value") or 0)
            return {"kind": "va", "reference": payload.get("trxId", ""), "status": "paid" if paid > 0 else "pending", "paid_amount": paid,
                    "provider_ref": payload.get("paymentRequestId") or payload.get("referenceNo")}
        return {"kind": "unknown", "reference": payload.get("reference") or payload.get("order_number", ""), "status": str(payload.get("status", "pending")),
                "paid_amount": float(payload.get("amount") or 0) if not isinstance(payload.get("amount"), dict) else 0.0, "provider_ref": None}


batpay = BatpayClient()
