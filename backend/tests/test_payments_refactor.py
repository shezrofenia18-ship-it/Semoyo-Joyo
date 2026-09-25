"""Tes alur pesanan & pembayaran: Cash (proses -> Selesai/Terima Uang), Bayar Nanti (piutang), Bayar Online (BATPay), ubah metode, webhook.

Jalankan terhadap backend yang berjalan: REACT_APP_BACKEND_URL=<url> python -m pytest tests/test_payments_refactor.py -q
Mode BATPay placeholder (kredensial kosong) diasumsikan; webhook diuji via BATPAY_WEBHOOK_TOKEN bila diset.
"""
import os
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
WEBHOOK_TOKEN = os.environ.get("BATPAY_WEBHOOK_TOKEN", "")


@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module", autouse=True)
def _guard_placeholder_mode(s):
    """Pengaman: suite ini membuat pesanan Bayar Online. Hanya boleh berjalan bila backend dalam mode placeholder
    (payment_mode='batpay_placeholder'), agar tidak memicu tagihan nyata ke server BATPay."""
    mode = s.get(f"{BASE_URL}/api/health", timeout=15).json().get("payment_mode")
    if mode != "batpay_placeholder":
        pytest.exit(f"Backend dalam mode '{mode}' (AKTIF). Set BATPAY_FORCE_PLACEHOLDER=true lalu restart backend sebelum menjalankan suite ini.", returncode=2)


@pytest.fixture(scope="module")
def owner_token(s):
    r = s.post(f"{BASE_URL}/api/admin/login", json={"username": os.environ.get("OWNER_USERNAME", "owner"), "password": os.environ.get("OWNER_PASSWORD", "owner123")})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture(scope="module")
def product(s):
    prods = s.get(f"{BASE_URL}/api/products").json()
    items = prods if isinstance(prods, list) else prods.get("items", [])
    items = [p for p in items if p.get("stock", 0) > 50]
    return items[0]


def _payload(product, method, channel=None):
    body = {
        "full_name": f"TEST_{uuid.uuid4().hex[:6]}",
        "phone": "081298765432",
        "address": "Jl. Payment Test 1",
        "payment_method": method,
        "items": [{"product_id": product["id"], "qty": max(1, product.get("min_order", 1))}],
    }
    if channel:
        body["payment_channel"] = channel
    return body


# ---------- Health & Config ----------
def test_health_payment_mode(s):
    r = s.get(f"{BASE_URL}/api/health")
    assert r.status_code == 200
    assert r.json()["payment_mode"].startswith("batpay_")


def test_payments_config_three_methods(s):
    r = s.get(f"{BASE_URL}/api/payments/config")
    assert r.status_code == 200
    j = r.json()
    assert [m["key"] for m in j["methods"]] == ["cash", "piutang", "online"]
    online = j["methods"][2]
    assert online["available"] == j["online_enabled"]
    keys = [c["key"] for c in online["channels"]]
    assert keys[0] == "qris" and any(k.startswith("va_") for k in keys)


def test_fee_preview_gross_up(s):
    r = s.get(f"{BASE_URL}/api/payments/fee", params={"amount": 100000, "channel": "qris"})
    assert r.status_code == 200
    j = r.json()
    assert j["service_fee"] >= 0 and j["total"] == 100000 + j["service_fee"]
    by = {c["key"]: c for c in j["channels"]}
    assert by["qris"]["service_fee"] == j["service_fee"]
    assert by["va_bca"]["total"] == 100000 + by["va_bca"]["service_fee"]


def test_fee_policy_qris_tiered_and_va_flat(s):
    """QRIS: <= ambang gratis, di atasnya persen gross-up. VA: flat per bank (BCA 4000, BSI 2500, lain 2000) - default kode."""
    pol = s.get(f"{BASE_URL}/api/payments/config").json()["fee_policy"]
    thr, pct = pol["qris"]["threshold"], pol["qris"]["percent_above"]
    assert pol["qris"]["type"] == "tiered_percent" and pol["va"]["type"] == "flat"
    fee = lambda amount, ch: s.get(f"{BASE_URL}/api/payments/fee", params={"amount": amount, "channel": ch}).json()["service_fee"]  # noqa: E731
    assert fee(thr, "qris") == 0 and fee(min(thr, 100000), "qris") == 0
    above = fee(thr + 100000, "qris")
    total = thr + 100000 + above
    assert above > 0 and total - total * pct / 100 >= thr + 100000 - 1e-6  # gross-up: dana toko utuh
    assert fee(50000, "va_bca") == pol["va"]["by_bank"]["bca"] == fee(5000000, "va_bca")  # flat, tak tergantung nominal
    assert fee(50000, "va_bsi") == pol["va"]["by_bank"]["bsi"]
    for b in ("mandiri", "bri", "bni", "cimb", "danamon", "permata", "btn", "bjb", "neo"):
        assert fee(50000, f"va_{b}") == pol["va"]["by_bank"][b]
    # tanpa override env: nilai default kode
    if not os.environ.get("BATPAY_VA_FLAT_FEES") and not os.environ.get("BATPAY_QRIS_FEE_THRESHOLD"):
        assert thr == 500000 and pct == 0.3 and pol["va"]["by_bank"]["bca"] == 4000 and pol["va"]["by_bank"]["bsi"] == 2500 and pol["va"]["default"] == 2000


def test_checkout_new_va_banks_and_invalid_channel(s, product):
    for ch in ("va_bri", "va_bni", "va_bsi", "va_permata", "va_btn", "va_bjb", "va_neo"):
        r = s.post(f"{BASE_URL}/api/checkout", json=_payload(product, "online", ch))
        assert r.status_code == 200, f"{ch}: {r.text}"
        o = r.json()["order"]
        assert o["payment_channel"] == ch and o["service_fee"] == s.get(f"{BASE_URL}/api/payments/fee", params={"amount": 1000, "channel": ch}).json()["service_fee"]
    for bad in ("va_bankpalsu", "gopay", "VA-BCA"):
        r = s.post(f"{BASE_URL}/api/checkout", json=_payload(product, "online", bad))
        assert r.status_code == 422, f"{bad}: {r.status_code} {r.text}"
    r = s.post(f"{BASE_URL}/api/checkout", json=_payload(product, "online", "VA_BCA"))
    assert r.status_code == 200 and r.json()["order"]["payment_channel"] == "va_bca"


# ---------- Cash ----------
@pytest.fixture(scope="module")
def cash_order(s, product):
    r = s.post(f"{BASE_URL}/api/checkout", json=_payload(product, "cash"))
    assert r.status_code == 200, r.text
    return r.json()


def test_cash_checkout_is_proses(cash_order):
    order = cash_order["order"]
    assert order["payment_status"] == "proses"
    assert order["order_status"] == "diproses"
    assert order["paid_at"] is None
    assert order["service_fee"] == 0
    assert cash_order["payment"]["provider"] == "cash"


def test_cash_complete_receive_money(s, cash_order, owner_token):
    oid = cash_order["order"]["id"]
    r = s.post(f"{BASE_URL}/api/admin/orders/{oid}/complete-cash", headers=_h(owner_token))
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["payment_status"] == "paid" and j["order_status"] == "selesai" and j["paid_at"]
    # idempoten: kedua kali ditolak
    r2 = s.post(f"{BASE_URL}/api/admin/orders/{oid}/complete-cash", headers=_h(owner_token))
    assert r2.status_code == 400


def test_complete_cash_rejected_for_non_cash(s, product, owner_token):
    r = s.post(f"{BASE_URL}/api/checkout", json=_payload(product, "piutang"))
    oid = r.json()["order"]["id"]
    r2 = s.post(f"{BASE_URL}/api/admin/orders/{oid}/complete-cash", headers=_h(owner_token))
    assert r2.status_code == 400


# ---------- Piutang ----------
@pytest.fixture(scope="module")
def piutang_order(s, product):
    r = s.post(f"{BASE_URL}/api/checkout", json=_payload(product, "piutang"))
    assert r.status_code == 200, r.text
    return r.json()


def test_piutang_checkout(piutang_order):
    order = piutang_order["order"]
    assert order["payment_status"] == "piutang"
    assert order["order_status"] == "baru"


def test_piutang_in_receivables(s, piutang_order, owner_token):
    r = s.get(f"{BASE_URL}/api/admin/receivables", headers=_h(owner_token))
    assert r.status_code == 200, r.text
    nums = [o["order_number"] for o in r.json().get("orders", [])]
    assert piutang_order["order"]["order_number"] in nums


def test_piutang_settle(s, piutang_order, owner_token):
    oid = piutang_order["order"]["id"]
    r = s.post(f"{BASE_URL}/api/admin/orders/{oid}/settle", json={"method": "cash"}, headers=_h(owner_token))
    assert r.status_code == 200, r.text
    on = piutang_order["order"]["order_number"]
    assert s.get(f"{BASE_URL}/api/payments/{on}").json()["payment_status"] == "paid"


# ---------- Bayar Online (BATPay) ----------
@pytest.fixture(scope="module")
def online_order(s, product):
    r = s.post(f"{BASE_URL}/api/checkout", json=_payload(product, "online", "qris"))
    assert r.status_code == 200, r.text
    return r.json()


def test_online_checkout_pending_with_service_fee(online_order):
    order = online_order["order"]
    assert order["payment_status"] == "pending"
    assert order["payment_method"] == "online" and order["payment_channel"] == "qris"
    assert order["service_fee"] >= 0
    assert round(order["total"], 2) == round(order["subtotal"] + order["shipping_fee"] + order["service_fee"], 2)
    pay = online_order["payment"]
    assert pay["provider"] == "batpay"
    assert pay["instructions"]["status"] in ("awaiting_integration", "active")


def test_online_va_channel_fee_differs(s, product):
    r = s.post(f"{BASE_URL}/api/checkout", json=_payload(product, "online", "va_bca"))
    assert r.status_code == 200, r.text
    o = r.json()["order"]
    assert o["payment_channel"] == "va_bca"
    fee = s.get(f"{BASE_URL}/api/payments/fee", params={"amount": o["subtotal"], "channel": "va_bca"}).json()["service_fee"]
    assert o["service_fee"] == fee


def test_online_status_pending(s, online_order):
    on = online_order["order"]["order_number"]
    r = s.get(f"{BASE_URL}/api/payments/{on}/status")
    assert r.status_code == 200
    assert r.json()["payment_status"] == "pending"


def test_customer_switch_online_to_cash_removes_fee(s, product):
    r = s.post(f"{BASE_URL}/api/checkout", json=_payload(product, "online", "qris"))
    on = r.json()["order"]["order_number"]
    r2 = s.post(f"{BASE_URL}/api/payments/{on}/create", json={"payment_method": "cash"})
    assert r2.status_code == 200, r2.text
    assert r2.json()["payment_status"] == "proses" and r2.json()["service_fee"] == 0
    o = s.get(f"{BASE_URL}/api/orders/{on}").json()
    assert o["total"] == o["subtotal"] + o["shipping_fee"]


# ---------- Admin: Ubah Metode Pembayaran ----------
def test_admin_change_method_cash_to_piutang(s, product, owner_token):
    r = s.post(f"{BASE_URL}/api/checkout", json=_payload(product, "cash"))
    oid = r.json()["order"]["id"]
    r2 = s.patch(f"{BASE_URL}/api/admin/orders/{oid}/payment-method", json={"payment_method": "piutang"}, headers=_h(owner_token))
    assert r2.status_code == 200, r2.text
    assert r2.json()["payment_status"] == "piutang" and r2.json()["payment_method"] == "piutang"


def test_admin_change_method_to_online_adds_fee(s, product, owner_token):
    r = s.post(f"{BASE_URL}/api/checkout", json=_payload(product, "cash"))
    o = r.json()["order"]
    r2 = s.patch(f"{BASE_URL}/api/admin/orders/{o['id']}/payment-method", json={"payment_method": "online", "payment_channel": "va_mandiri"}, headers=_h(owner_token))
    assert r2.status_code == 200, r2.text
    j = r2.json()
    assert j["payment_method"] == "online" and j["payment_channel"] == "va_mandiri" and j["payment_status"] == "pending"
    assert j["total"] == o["subtotal"] + o["shipping_fee"] + j["service_fee"]


def test_admin_change_method_rejected_when_paid(s, product, owner_token):
    r = s.post(f"{BASE_URL}/api/checkout", json=_payload(product, "cash"))
    oid = r.json()["order"]["id"]
    s.post(f"{BASE_URL}/api/admin/orders/{oid}/complete-cash", headers=_h(owner_token))
    r2 = s.patch(f"{BASE_URL}/api/admin/orders/{oid}/payment-method", json={"payment_method": "piutang"}, headers=_h(owner_token))
    assert r2.status_code == 400


# ---------- Webhook BATPay ----------
def test_webhook_rejects_without_credentials(s, online_order):
    on = online_order["order"]["order_number"]
    r = s.post(f"{BASE_URL}/api/payments/batpay/webhook", json={"originalPartnerReferenceNo": on, "latestTransactionStatus": "00"})
    assert r.status_code in (401, 503)
    assert s.get(f"{BASE_URL}/api/payments/{on}").json()["payment_status"] == "pending"


@pytest.mark.skipif(not WEBHOOK_TOKEN, reason="BATPAY_WEBHOOK_TOKEN tidak diset")
def test_webhook_marks_paid_with_internal_token(s, product):
    r = s.post(f"{BASE_URL}/api/checkout", json=_payload(product, "online", "qris"))
    o = r.json()["order"]
    body = {"originalPartnerReferenceNo": o["order_number"], "originalReferenceNo": "R-TEST", "latestTransactionStatus": "00",
            "transactionStatusDesc": "success", "amount": {"value": f"{o['total']:.2f}", "currency": "IDR"}}
    r2 = s.post(f"{BASE_URL}/api/payments/batpay/webhook", json=body, headers={"X-CALLBACK-TOKEN": WEBHOOK_TOKEN})
    assert r2.status_code == 200, r2.text
    assert r2.json()["responseCode"] == "2005200"
    j = s.get(f"{BASE_URL}/api/orders/{o['order_number']}").json()
    assert j["payment_status"] == "paid" and j["order_status"] == "selesai" and j["paid_at"]


@pytest.mark.skipif(not WEBHOOK_TOKEN, reason="BATPAY_WEBHOOK_TOKEN tidak diset")
def test_webhook_rejects_amount_mismatch(s, product):
    r = s.post(f"{BASE_URL}/api/checkout", json=_payload(product, "online", "va_bca"))
    o = r.json()["order"]
    body = {"trxId": o["order_number"], "paymentRequestId": "P-1", "paidAmount": {"value": "1.00", "currency": "IDR"}}
    r2 = s.post(f"{BASE_URL}/api/payments/batpay/webhook", json=body, headers={"X-CALLBACK-TOKEN": WEBHOOK_TOKEN})
    assert r2.status_code == 404 and r2.json()["responseCode"] == "4045213"
    assert s.get(f"{BASE_URL}/api/orders/{o['order_number']}").json()["payment_status"] == "pending"


# ---------- Metode lama ditolak / endpoint lama hilang ----------
@pytest.mark.parametrize("method", ["cod", "bank_transfer", "qris", "ewallet", "transfer_va"])
def test_legacy_methods_rejected(s, product, method):
    r = s.post(f"{BASE_URL}/api/checkout", json=_payload(product, method))
    assert r.status_code == 422, f"{method} expected 422 got {r.status_code}"


@pytest.mark.parametrize("path", ["/api/payments/simulate", "/api/payments/notification"])
def test_old_gateway_endpoints_gone(s, path):
    """Endpoint gateway lama sudah dicabut total - hanya /api/payments/batpay/* yang ada."""
    assert s.post(f"{BASE_URL}{path}", json={}).status_code in (404, 405)


def test_batpay_inbound_token_requires_credentials(s):
    r = s.post(f"{BASE_URL}/api/payments/batpay/access-token/b2b", json={"grantType": "client_credentials"})
    assert r.status_code in (400, 401, 503)
    assert "responseCode" in r.json()
