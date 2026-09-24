#!/usr/bin/env python3
"""E2E API test - Semoyo Joyo: alur pesanan & pembayaran (Cash / Bayar Nanti / Bayar Online via BATPay).

Skrip ini HANYA berjalan dalam mode placeholder (tidak ada panggilan ke server BATPay). Bila backend ternyata
dalam mode aktif (payment_mode != batpay_placeholder), skrip berhenti lebih dulu sebagai pengaman.

Ekspektasi konfigurasi dihitung dari backend/.env (bukan hard-code) sehingga skrip valid di workspace mana pun:
  - kredensial lengkap + BATPAY_FORCE_PLACEHOLDER=true  -> status "held" (ditahan), partial=false, missing=[]
  - kredensial sebagian                                 -> status "partial", missing=[variabel kosong]
  - kredensial kosong                                   -> status "placeholder"

Jalankan: python backend_test.py   (REACT_APP_BACKEND_URL opsional; default dibaca dari frontend/.env)
"""
import os
import sys
import time
import uuid
from pathlib import Path

import requests
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent
BACKEND_ENV = dotenv_values(ROOT / "backend" / ".env")
FRONTEND_ENV = dotenv_values(ROOT / "frontend" / ".env")

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or FRONTEND_ENV.get("REACT_APP_BACKEND_URL") or "http://localhost:8001").rstrip("/")
WEBHOOK_TOKEN = (BACKEND_ENV.get("BATPAY_WEBHOOK_TOKEN") or "").strip()
OWNER = (BACKEND_ENV.get("OWNER_USERNAME") or "owner", BACKEND_ENV.get("OWNER_PASSWORD") or "owner123")
ADMIN = (BACKEND_ENV.get("ADMIN_USERNAME") or "admin", BACKEND_ENV.get("ADMIN_PASSWORD") or "admin123")

REQUIRED_KEYS = {"partner_id": "BATPAY_PARTNER_ID", "client_id": "BATPAY_CLIENT_ID", "secret_key": "BATPAY_SECRET_KEY",
                 "private_key": "BATPAY_PRIVATE_KEY", "merchant_id": "BATPAY_MERCHANT_ID"}
LEGACY_METHODS = ["cod", "bank_transfer", "qris", "ewallet", "transfer_va"]
# Endpoint gateway lama yang sudah dicabut - hanya /api/payments/batpay/* yang boleh ada
LEGACY_ENDPOINTS = ["/api/payments/simulate", "/api/payments/notification"]


def _env(name: str) -> str:
    return (BACKEND_ENV.get(name) or "").strip()


def _truthy(v: str) -> bool:
    return v.strip().lower() in ("1", "true", "yes", "on", "ya")


def expected_config() -> dict:
    configured = {k: bool(_env(env)) for k, env in REQUIRED_KEYS.items()}
    complete = all(configured.values())
    force = _truthy(_env("BATPAY_FORCE_PLACEHOLDER"))
    enabled = complete and not force
    env = (_env("BATPAY_ENV") or "sandbox").lower()
    default_base = "https://openapi.batbiz.id" if env == "production" else "https://openapi.sandbox.batbiz.id"
    status = "active" if enabled else "held" if force else "partial" if any(configured.values()) else "placeholder"
    return {
        "configured": configured, "complete": complete, "force": force, "enabled": enabled, "status": status,
        "partial": (not complete) and any(configured.values()), "missing": [k for k, v in configured.items() if not v],
        "base_url": (_env("BATPAY_BASE_URL") or default_base).rstrip("/"), "merchant_id": _env("BATPAY_MERCHANT_ID"),
        "fee_percent": float(_env("BATPAY_FEE_PERCENT") or 0.7), "fee_fixed": float(_env("BATPAY_FEE_FIXED") or 0),
    }


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"


class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.exp = expected_config()
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.owner_token = None
        self.admin_token = None
        self.results = []

    # ------------------------------------------------------------------ util
    def log(self, status, test_name, message="", details=None):
        if status in ("PASS", "FAIL"):
            self.tests_run += 1
        if status == "PASS":
            self.tests_passed += 1
            print(f"{Colors.GREEN}✓ PASS{Colors.END} - {test_name}")
            if message:
                print(f"  {message}")
        elif status == "FAIL":
            self.tests_failed += 1
            print(f"{Colors.RED}✗ FAIL{Colors.END} - {test_name}")
            print(f"  {message}")
            if details:
                print(f"  Details: {details}")
        else:
            print(f"{Colors.BLUE}ℹ INFO{Colors.END} - {test_name}: {message}")
        self.results.append({"test": test_name, "status": status, "message": message, "details": details})

    def _h(self, token):
        return {"Authorization": f"Bearer {token}"}

    def _login(self, creds, label):
        try:
            r = requests.post(f"{self.base_url}/api/admin/login", json={"username": creds[0], "password": creds[1]}, timeout=15)
            if r.status_code == 200:
                self.log("PASS", f"{label} login", f"Berhasil login sebagai {creds[0]}")
                return r.json()["access_token"]
            self.log("FAIL", f"{label} login", f"Status {r.status_code}", r.text[:200])
        except Exception as e:  # noqa: BLE001
            self.log("FAIL", f"{label} login", f"Exception: {e}")
        return None

    def _product(self):
        r = requests.get(f"{self.base_url}/api/products", timeout=15)
        if r.status_code != 200:
            raise RuntimeError(f"GET /api/products -> {r.status_code}")
        products = r.json()
        items = products if isinstance(products, list) else products.get("items", [])
        items = [p for p in items if p.get("stock", 0) > 50] or items
        if not items:
            raise RuntimeError("Tidak ada produk")
        return items[0]

    def _payload(self, product, method, channel=None, tag="TEST"):
        p = {"full_name": f"{tag}_{uuid.uuid4().hex[:6]}", "phone": "081234567890", "address": "Alamat uji", "payment_method": method,
             "items": [{"product_id": product["id"], "qty": max(1, product.get("min_order", 1))}]}
        if channel:
            p["payment_channel"] = channel
        return p

    # ------------------------------------------------------------ safety guard
    def guard_placeholder_mode(self) -> bool:
        """Pengaman: skrip hanya boleh berjalan bila backend dalam mode placeholder (tidak ada panggilan ke BATPay)."""
        try:
            r = requests.get(f"{self.base_url}/api/health", timeout=15)
            mode = r.json().get("payment_mode", "") if r.status_code == 200 else ""
        except Exception as e:  # noqa: BLE001
            self.log("FAIL", "Safety guard", f"Health tidak dapat diakses: {e}")
            return False
        if mode != "batpay_placeholder":
            self.log("FAIL", "Safety guard",
                     f"Backend dalam mode '{mode}' (AKTIF). Skrip dihentikan agar tidak memicu panggilan ke server BATPay. "
                     "Set BATPAY_FORCE_PLACEHOLDER=true lalu restart backend untuk menjalankan E2E placeholder.")
            return False
        self.log("PASS", "Safety guard", "payment_mode='batpay_placeholder' - aman, tidak ada panggilan ke BATPay")
        return True

    # ---------------------------------------------------------------- tests
    def test_health(self):
        try:
            r = requests.get(f"{self.base_url}/api/health", timeout=15)
            if r.status_code != 200:
                return self.log("FAIL", "GET /api/health", f"Status {r.status_code}", r.text[:200])
            data = r.json()
            if not data.get("db_connected"):
                return self.log("FAIL", "GET /api/health - db_connected", "Expected true", data)
            expected_mode = "batpay_placeholder" if not self.exp["enabled"] else f"batpay_{(_env('BATPAY_ENV') or 'sandbox').lower()}"
            if data.get("payment_mode") != expected_mode:
                return self.log("FAIL", "GET /api/health - payment_mode", f"Expected '{expected_mode}', got '{data.get('payment_mode')}'", data)
            self.log("PASS", "GET /api/health", f"db_connected=true, payment_mode='{data.get('payment_mode')}'")
        except Exception as e:  # noqa: BLE001
            self.log("FAIL", "GET /api/health", f"Exception: {e}")

    def test_payment_settings_owner(self):
        name = "GET /api/admin/settings/payments (OWNER)"
        if not self.owner_token:
            return self.log("FAIL", name, "No owner token")
        try:
            r = requests.get(f"{self.base_url}/api/admin/settings/payments", headers=self._h(self.owner_token), timeout=15)
            if r.status_code != 200:
                return self.log("FAIL", name, f"Status {r.status_code}", r.text[:200])
            d = r.json()
            e = self.exp
            checks = [
                ("enabled", d.get("enabled"), e["enabled"]),
                ("status", d.get("status"), e["status"]),
                ("force_placeholder", d.get("force_placeholder"), e["force"]),
                ("credentials_complete", d.get("credentials_complete"), e["complete"]),
                ("partial", d.get("partial"), e["partial"]),
                ("missing", d.get("missing"), e["missing"]),
                ("base_url", d.get("base_url"), e["base_url"]),
                ("merchant_id", d.get("merchant_id"), e["merchant_id"]),
                ("fees.default.percent", (d.get("fees") or {}).get("default", {}).get("percent"), e["fee_percent"]),
                ("fees.default.fixed", (d.get("fees") or {}).get("default", {}).get("fixed"), e["fee_fixed"]),
            ]
            for label, got, want in checks:
                if got != want:
                    return self.log("FAIL", f"settings/payments - {label}", f"Expected {want!r}, got {got!r}", d)
            configured = d.get("configured", {})
            for k, want in e["configured"].items():
                if configured.get(k) != want:
                    return self.log("FAIL", f"settings/payments - configured.{k}", f"Expected {want}, got {configured.get(k)}", configured)
            if not str(d.get("webhook_url", "")).endswith("/api/payments/batpay/webhook"):
                return self.log("FAIL", "settings/payments - webhook_url", f"Got {d.get('webhook_url')}", d)
            keys = [c.get("key") for c in d.get("channels", [])]
            if "qris" not in keys or not any(k.startswith("va_") for k in keys):
                return self.log("FAIL", "settings/payments - channels", f"Got {keys}", d)
            # Rahasia tidak boleh bocor
            text = r.text
            for secret_env in ("BATPAY_SECRET_KEY", "BATPAY_PRIVATE_KEY"):
                val = _env(secret_env)
                if val and (val in text or val[:24] in text):
                    return self.log("FAIL", "settings/payments - secret exposure", f"Nilai {secret_env} ditemukan di respons", "SECURITY ISSUE")
            self.log("PASS", name, f"status='{d.get('status')}', enabled={d.get('enabled')}, force_placeholder={d.get('force_placeholder')}, missing={d.get('missing')}, base_url={d.get('base_url')}")
        except Exception as e:  # noqa: BLE001
            self.log("FAIL", name, f"Exception: {e}")

    def test_payment_settings_admin_403(self):
        name = "GET /api/admin/settings/payments (ADMIN) -> 403"
        if not self.admin_token:
            return self.log("FAIL", name, "No admin token")
        try:
            r = requests.get(f"{self.base_url}/api/admin/settings/payments", headers=self._h(self.admin_token), timeout=15)
            self.log("PASS" if r.status_code == 403 else "FAIL", name, f"Status {r.status_code}", None if r.status_code == 403 else r.text[:200])
        except Exception as e:  # noqa: BLE001
            self.log("FAIL", name, f"Exception: {e}")

    def test_payment_test_endpoint(self):
        """POST /api/admin/settings/payments/test - hanya dipanggil bila TIDAK aktif (tidak ada panggilan jaringan ke BATPay)."""
        name = "POST /api/admin/settings/payments/test (OWNER)"
        if self.exp["enabled"]:
            return self.log("INFO", name, "DILEWATI - mode aktif akan memanggil server BATPay")
        if not self.owner_token:
            return self.log("FAIL", name, "No owner token")
        try:
            r = requests.post(f"{self.base_url}/api/admin/settings/payments/test", headers=self._h(self.owner_token), timeout=15)
            if r.status_code != 200:
                return self.log("FAIL", name, f"Status {r.status_code}", r.text[:200])
            d = r.json()
            if d.get("ok") is not False or d.get("step") != "config":
                return self.log("FAIL", name, f"Expected ok=false, step='config'; got {d}")
            if self.exp["force"] and d.get("held") is not True:
                return self.log("FAIL", name, f"Expected held=true saat BATPAY_FORCE_PLACEHOLDER; got {d}")
            if not self.exp["complete"] and set(self.exp["missing"]) - set(d.get("missing", [])):
                return self.log("FAIL", name, f"Expected missing ⊇ {self.exp['missing']}; got {d.get('missing')}")
            self.log("PASS", name, f"ok=false, step='config', held={d.get('held')}, missing={d.get('missing')}")
        except Exception as e:  # noqa: BLE001
            self.log("FAIL", name, f"Exception: {e}")

    def test_payment_test_admin_403(self):
        name = "POST /api/admin/settings/payments/test (ADMIN) -> 403"
        if not self.admin_token:
            return self.log("FAIL", name, "No admin token")
        try:
            r = requests.post(f"{self.base_url}/api/admin/settings/payments/test", headers=self._h(self.admin_token), timeout=15)
            self.log("PASS" if r.status_code == 403 else "FAIL", name, f"Status {r.status_code}", None if r.status_code == 403 else r.text[:200])
        except Exception as e:  # noqa: BLE001
            self.log("FAIL", name, f"Exception: {e}")

    def test_audit_log_for_test(self):
        name = "Audit log berisi entri uji koneksi 'Bayar Online'"
        if self.exp["enabled"]:
            return self.log("INFO", name, "DILEWATI - uji koneksi tidak dijalankan pada mode aktif")
        if not self.owner_token:
            return self.log("FAIL", name, "No owner token")
        try:
            r = requests.get(f"{self.base_url}/api/admin/audit-logs", headers=self._h(self.owner_token), timeout=15)
            if r.status_code != 200:
                return self.log("FAIL", "GET /api/admin/audit-logs", f"Status {r.status_code}", r.text[:200])
            data = r.json()
            logs = data if isinstance(data, list) else data.get("logs") or data.get("items") or []
            found = next((l for l in logs if l.get("action") == "test" and "Bayar Online" in str(l.get("entity_label", ""))), None)
            if found:
                self.log("PASS", name, f"action='test', label='{found.get('entity_label')}'")
            else:
                self.log("FAIL", name, "Tidak ada action='test' dengan label 'Bayar Online'", f"Total logs: {len(logs)}")
        except Exception as e:  # noqa: BLE001
            self.log("FAIL", name, f"Exception: {e}")

    def test_payments_config(self):
        name = "GET /api/payments/config"
        try:
            r = requests.get(f"{self.base_url}/api/payments/config", timeout=15)
            if r.status_code != 200:
                return self.log("FAIL", name, f"Status {r.status_code}", r.text[:200])
            d = r.json()
            methods = d.get("methods", [])
            keys = [m.get("key") for m in methods]
            if keys != ["cash", "piutang", "online"]:
                return self.log("FAIL", f"{name} - method keys", f"Expected ['cash','piutang','online'], got {keys}")
            online = methods[2]
            if online.get("available") != self.exp["enabled"]:
                return self.log("FAIL", f"{name} - online.available", f"Expected {self.exp['enabled']}, got {online.get('available')}")
            if d.get("online_enabled") != self.exp["enabled"]:
                return self.log("FAIL", f"{name} - online_enabled", f"Expected {self.exp['enabled']}, got {d.get('online_enabled')}")
            ch = [c.get("key") for c in online.get("channels", [])]
            if "qris" not in ch or not all(v in ch for v in ("va_bca", "va_mandiri", "va_cimb", "va_danamon")):
                return self.log("FAIL", f"{name} - channels", f"Got {ch}")
            self.log("PASS", name, f"3 metode, online.available={online.get('available')}, channels={ch}")
        except Exception as e:  # noqa: BLE001
            self.log("FAIL", name, f"Exception: {e}")

    def test_fee_preview(self):
        name = "GET /api/payments/fee?amount=100000&channel=qris"
        try:
            r = requests.get(f"{self.base_url}/api/payments/fee", params={"amount": 100000, "channel": "qris"}, timeout=15)
            if r.status_code != 200:
                return self.log("FAIL", name, f"Status {r.status_code}", r.text[:200])
            d = r.json()
            import math
            pct, fixed = self.exp["fee_percent"], self.exp["fee_fixed"]
            want = max(0, int(math.ceil((100000 + fixed) / (1 - pct / 100) - 1e-9)) - 100000)
            if d.get("service_fee") != want or d.get("total") != 100000 + want:
                return self.log("FAIL", name, f"Expected fee {want}, got {d.get('service_fee')} (total {d.get('total')})", d)
            self.log("PASS", name, f"service_fee={want} (gross-up {pct}% + Rp{fixed:g})")
        except Exception as e:  # noqa: BLE001
            self.log("FAIL", name, f"Exception: {e}")

    # ----- alur checkout
    def test_cash_flow(self, product):
        name = "Cash: checkout -> proses/diproses -> complete-cash -> paid/selesai"
        try:
            r = requests.post(f"{self.base_url}/api/checkout", json=self._payload(product, "cash", tag="TEST_CASH"), timeout=15)
            if r.status_code != 200:
                return self.log("FAIL", name, f"checkout status {r.status_code}", r.text[:200])
            o = r.json().get("order", {})
            if (o.get("payment_status"), o.get("order_status")) != ("proses", "diproses") or float(o.get("service_fee") or 0) != 0:
                return self.log("FAIL", name, f"Status awal salah: {o.get('payment_status')}/{o.get('order_status')} fee={o.get('service_fee')}")
            if not self.admin_token:
                return self.log("FAIL", name, "No admin token untuk complete-cash")
            r2 = requests.post(f"{self.base_url}/api/admin/orders/{o['id']}/complete-cash", headers=self._h(self.admin_token), timeout=15)
            if r2.status_code != 200:
                return self.log("FAIL", name, f"complete-cash status {r2.status_code}", r2.text[:200])
            o2 = requests.get(f"{self.base_url}/api/orders/{o['order_number']}", timeout=15).json()
            if (o2.get("payment_status"), o2.get("order_status")) != ("paid", "selesai") or not o2.get("paid_at"):
                return self.log("FAIL", name, f"Setelah complete-cash: {o2.get('payment_status')}/{o2.get('order_status')}")
            r3 = requests.post(f"{self.base_url}/api/admin/orders/{o['id']}/complete-cash", headers=self._h(self.admin_token), timeout=15)
            if r3.status_code != 400:
                return self.log("FAIL", name, f"complete-cash kedua harus 400, got {r3.status_code}")
            self.log("PASS", name, f"{o['order_number']} lunas & selesai; pemanggilan ulang ditolak 400")
        except Exception as e:  # noqa: BLE001
            self.log("FAIL", name, f"Exception: {e}")

    def test_piutang_flow(self, product):
        name = "Bayar Nanti: checkout -> piutang -> muncul di /admin/receivables"
        try:
            r = requests.post(f"{self.base_url}/api/checkout", json=self._payload(product, "piutang", tag="TEST_PIUTANG"), timeout=15)
            if r.status_code != 200:
                return self.log("FAIL", name, f"checkout status {r.status_code}", r.text[:200])
            o = r.json().get("order", {})
            if o.get("payment_status") != "piutang":
                return self.log("FAIL", name, f"Expected 'piutang', got {o.get('payment_status')}")
            if not self.owner_token:
                return self.log("FAIL", name, "No owner token")
            r2 = requests.get(f"{self.base_url}/api/admin/receivables", headers=self._h(self.owner_token), timeout=15)
            if r2.status_code != 200:
                return self.log("FAIL", name, f"receivables status {r2.status_code}", r2.text[:200])
            nums = [x.get("order_number") for x in r2.json().get("orders", [])]
            if o["order_number"] not in nums:
                return self.log("FAIL", name, f"{o['order_number']} tidak ada di piutang", nums[:5])
            self.log("PASS", name, f"{o['order_number']} tercatat sebagai piutang")
        except Exception as e:  # noqa: BLE001
            self.log("FAIL", name, f"Exception: {e}")

    def test_online_flow(self, product):
        """Bayar Online dalam mode placeholder: pending + biaya layanan + instructions.status='awaiting_integration'."""
        name = "Bayar Online (placeholder): checkout qris -> pending, service_fee>0, awaiting_integration"
        try:
            r = requests.post(f"{self.base_url}/api/checkout", json=self._payload(product, "online", "qris", tag="TEST_ONLINE"), timeout=15)
            if r.status_code != 200:
                return self.log("FAIL", name, f"checkout status {r.status_code}", r.text[:200])
            data = r.json()
            o, pay = data.get("order", {}), data.get("payment", {})
            if o.get("payment_status") != "pending":
                return self.log("FAIL", name, f"Expected 'pending', got {o.get('payment_status')}")
            if float(o.get("service_fee") or 0) <= 0:
                return self.log("FAIL", name, f"service_fee harus > 0, got {o.get('service_fee')}")
            ins = pay.get("instructions", {})
            if ins.get("status") != "awaiting_integration" or ins.get("provider") != "batpay":
                return self.log("FAIL", name, f"instructions salah: {ins}")
            # VA channel juga tercatat
            r2 = requests.post(f"{self.base_url}/api/checkout", json=self._payload(product, "online", "va_bca", tag="TEST_ONLINE_VA"), timeout=15)
            o2 = r2.json().get("order", {}) if r2.status_code == 200 else {}
            if o2.get("payment_channel") != "va_bca":
                return self.log("FAIL", name, f"payment_channel VA salah: {o2.get('payment_channel')}")
            self.log("PASS", name, f"{o['order_number']} pending, fee={o.get('service_fee')}, total={o.get('total')}; VA channel ok")
            return o
        except Exception as e:  # noqa: BLE001
            self.log("FAIL", name, f"Exception: {e}")
            return None

    def test_change_method(self, product):
        name = "Admin ubah metode: cash -> piutang -> online(qris) -> cash (fee ditambah/dihapus)"
        if not self.admin_token:
            return self.log("FAIL", name, "No admin token")
        try:
            r = requests.post(f"{self.base_url}/api/checkout", json=self._payload(product, "cash", tag="TEST_SWITCH"), timeout=15)
            o = r.json()["order"]
            base_total = float(o["total"])
            h = self._h(self.admin_token)
            r1 = requests.patch(f"{self.base_url}/api/admin/orders/{o['id']}/payment-method", json={"payment_method": "piutang"}, headers=h, timeout=15)
            if r1.status_code != 200 or r1.json().get("payment_status") != "piutang":
                return self.log("FAIL", name, f"-> piutang gagal: {r1.status_code} {r1.text[:150]}")
            r2 = requests.patch(f"{self.base_url}/api/admin/orders/{o['id']}/payment-method", json={"payment_method": "online", "payment_channel": "qris"}, headers=h, timeout=15)
            d2 = r2.json() if r2.status_code == 200 else {}
            if d2.get("payment_status") != "pending" or float(d2.get("service_fee") or 0) <= 0 or float(d2.get("total")) <= base_total:
                return self.log("FAIL", name, f"-> online gagal: {r2.status_code} {r2.text[:150]}")
            r3 = requests.patch(f"{self.base_url}/api/admin/orders/{o['id']}/payment-method", json={"payment_method": "cash"}, headers=h, timeout=15)
            d3 = r3.json() if r3.status_code == 200 else {}
            if d3.get("payment_status") != "proses" or float(d3.get("service_fee") or 0) != 0 or float(d3.get("total")) != base_total:
                return self.log("FAIL", name, f"-> cash gagal: {r3.status_code} {r3.text[:150]}")
            self.log("PASS", name, f"{o['order_number']}: total kembali {base_total:g} tanpa biaya layanan")
        except Exception as e:  # noqa: BLE001
            self.log("FAIL", name, f"Exception: {e}")

    def test_webhook(self, product):
        name = "Webhook BATPay (X-CALLBACK-TOKEN): lunas -> paid+selesai; token salah -> 401; nominal kurang -> 4045213"
        if not WEBHOOK_TOKEN:
            return self.log("INFO", name, "DILEWATI - BATPAY_WEBHOOK_TOKEN kosong di backend/.env")
        try:
            r = requests.post(f"{self.base_url}/api/checkout", json=self._payload(product, "online", "qris", tag="TEST_WEBHOOK"), timeout=15)
            o = r.json()["order"]
            total = float(o["total"])
            body = {"originalPartnerReferenceNo": o["order_number"], "originalReferenceNo": "R-TEST", "latestTransactionStatus": "00",
                    "amount": {"value": f"{total:.2f}", "currency": "IDR"}}
            bad = requests.post(f"{self.base_url}/api/payments/batpay/webhook", json=body, headers={"X-CALLBACK-TOKEN": "salah"}, timeout=15)
            if bad.status_code != 401:
                return self.log("FAIL", name, f"Token salah harus 401, got {bad.status_code}")
            ok = requests.post(f"{self.base_url}/api/payments/batpay/webhook", json=body, headers={"X-CALLBACK-TOKEN": WEBHOOK_TOKEN}, timeout=15)
            if ok.status_code != 200 or ok.json().get("responseCode") != "2005200":
                return self.log("FAIL", name, f"Webhook valid gagal: {ok.status_code} {ok.text[:200]}")
            time.sleep(0.3)
            o2 = requests.get(f"{self.base_url}/api/orders/{o['order_number']}", timeout=15).json()
            if (o2.get("payment_status"), o2.get("order_status")) != ("paid", "selesai"):
                return self.log("FAIL", name, f"Setelah webhook: {o2.get('payment_status')}/{o2.get('order_status')}")
            # nominal kurang pada pesanan lain -> ditolak
            r3 = requests.post(f"{self.base_url}/api/checkout", json=self._payload(product, "online", "va_bca", tag="TEST_WEBHOOK_VA"), timeout=15)
            o3 = r3.json()["order"]
            va_body = {"trxId": o3["order_number"], "paymentRequestId": "P-1", "paidAmount": {"value": "1.00", "currency": "IDR"}}
            r4 = requests.post(f"{self.base_url}/api/payments/batpay/webhook", json=va_body, headers={"X-CALLBACK-TOKEN": WEBHOOK_TOKEN}, timeout=15)
            if r4.status_code != 404 or r4.json().get("responseCode") != "4045213":
                return self.log("FAIL", name, f"Nominal kurang harus 404/4045213, got {r4.status_code} {r4.text[:150]}")
            o4 = requests.get(f"{self.base_url}/api/orders/{o3['order_number']}", timeout=15).json()
            if o4.get("payment_status") != "pending":
                return self.log("FAIL", name, f"Pesanan nominal-kurang harus tetap pending, got {o4.get('payment_status')}")
            self.log("PASS", name, f"{o['order_number']} lunas via webhook; {o3['order_number']} tetap pending")
        except Exception as e:  # noqa: BLE001
            self.log("FAIL", name, f"Exception: {e}")

    def test_inbound_token_disabled(self):
        name = "POST /api/payments/batpay/access-token/b2b tanpa integrasi aktif -> 503 SNAP"
        if self.exp["enabled"]:
            return self.log("INFO", name, "DILEWATI - mode aktif")
        try:
            r = requests.post(f"{self.base_url}/api/payments/batpay/access-token/b2b", json={"grantType": "client_credentials"}, timeout=15)
            if r.status_code != 503 or r.json().get("responseCode") != "5037300":
                return self.log("FAIL", name, f"Got {r.status_code} {r.text[:150]}")
            self.log("PASS", name, "responseCode=5037300")
        except Exception as e:  # noqa: BLE001
            self.log("FAIL", name, f"Exception: {e}")

    # ----- pembersihan gateway lama
    def test_legacy_methods_rejected(self, product):
        name = "Metode lama ditolak 422"
        try:
            for m in LEGACY_METHODS:
                r = requests.post(f"{self.base_url}/api/checkout", json=self._payload(product, m, tag="TEST_LEGACY"), timeout=15)
                if r.status_code != 422:
                    return self.log("FAIL", name, f"'{m}' expected 422, got {r.status_code}", r.text[:200])
            self.log("PASS", name, f"{', '.join(LEGACY_METHODS)} -> 422")
        except Exception as e:  # noqa: BLE001
            self.log("FAIL", name, f"Exception: {e}")

    def test_legacy_endpoints_gone(self):
        name = "Endpoint gateway lama sudah dicabut (404/405)"
        try:
            for ep in LEGACY_ENDPOINTS + ["/api/payments/SJ-XXXX/simulate"]:
                r = requests.post(f"{self.base_url}{ep}", json={}, timeout=15)
                if r.status_code not in (404, 405):
                    return self.log("FAIL", name, f"{ep} expected 404/405, got {r.status_code}", r.text[:200])
            self.log("PASS", name, f"{', '.join(LEGACY_ENDPOINTS)}, /{{order}}/simulate -> 404/405")
        except Exception as e:  # noqa: BLE001
            self.log("FAIL", name, f"Exception: {e}")

    # ------------------------------------------------------------------ run
    def run_all_tests(self):
        print(f"\n{Colors.BLUE}{'=' * 70}{Colors.END}")
        print(f"{Colors.BLUE}E2E API Testing - Semoyo Joyo (BATPay placeholder mode){Colors.END}")
        print(f"{Colors.BLUE}{'=' * 70}{Colors.END}")
        print(f"Base URL : {self.base_url}")
        e = self.exp
        print(f"Env      : status={e['status']} complete={e['complete']} force_placeholder={e['force']} missing={e['missing']} base_url={e['base_url']}\n")

        if not self.guard_placeholder_mode():
            self._summary()
            return 1

        self.owner_token = self._login(OWNER, "Owner")
        self.admin_token = self._login(ADMIN, "Admin")
        if not self.owner_token:
            print(f"\n{Colors.RED}Tidak bisa lanjut tanpa login owner{Colors.END}")
            self._summary()
            return 1

        print(f"\n{Colors.YELLOW}--- Health & Konfigurasi ---{Colors.END}")
        self.test_health()
        self.test_payment_settings_owner()
        self.test_payment_settings_admin_403()

        print(f"\n{Colors.YELLOW}--- Uji Koneksi (tanpa panggilan jaringan) ---{Colors.END}")
        self.test_payment_test_endpoint()
        self.test_payment_test_admin_403()
        self.test_audit_log_for_test()

        print(f"\n{Colors.YELLOW}--- Konfigurasi Publik ---{Colors.END}")
        self.test_payments_config()
        self.test_fee_preview()

        try:
            product = self._product()
        except Exception as ex:  # noqa: BLE001
            self.log("FAIL", "Ambil produk", str(ex))
            self._summary()
            return 1

        print(f"\n{Colors.YELLOW}--- Alur Checkout ---{Colors.END}")
        self.test_cash_flow(product)
        self.test_piutang_flow(product)
        self.test_online_flow(product)
        self.test_change_method(product)

        print(f"\n{Colors.YELLOW}--- Webhook & Inbound ---{Colors.END}")
        self.test_webhook(product)
        self.test_inbound_token_disabled()

        print(f"\n{Colors.YELLOW}--- Pembersihan Gateway Lama ---{Colors.END}")
        self.test_legacy_methods_rejected(product)
        self.test_legacy_endpoints_gone()

        return self._summary()

    def _summary(self):
        print(f"\n{Colors.BLUE}{'=' * 70}{Colors.END}")
        print(f"Total: {self.tests_run}  {Colors.GREEN}Passed: {self.tests_passed}{Colors.END}  {Colors.RED}Failed: {self.tests_failed}{Colors.END}")
        if self.tests_failed == 0:
            print(f"{Colors.GREEN}✓ Semua tes lulus{Colors.END}\n")
            return 0
        print(f"{Colors.RED}✗ Ada tes yang gagal{Colors.END}\n")
        return 1


if __name__ == "__main__":
    sys.exit(APITester().run_all_tests())
