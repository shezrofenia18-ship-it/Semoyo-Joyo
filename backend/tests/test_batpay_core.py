"""POC/unit test integrasi BATPay: signature SNAP, biaya layanan gross-up, verifikasi webhook, parsing notifikasi.

Tidak memerlukan jaringan/kredensial. Jalankan: cd /app/backend && python -m pytest tests/test_batpay_core.py -q
"""
import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:y@localhost:5432/z")

from payments import batpay as bp  # noqa: E402

PRIV, PUB = bp.generate_rsa_keypair()


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("BATPAY_CLIENT_ID", "client-key-123")
    monkeypatch.setenv("BATPAY_PARTNER_ID", "partner-456")
    monkeypatch.setenv("BATPAY_SECRET_KEY", "secret-abc")
    monkeypatch.setenv("BATPAY_PRIVATE_KEY", PRIV.replace("\n", "\\n"))  # bentuk env satu baris
    monkeypatch.setenv("BATPAY_MERCHANT_ID", "000000000000005")
    monkeypatch.setenv("BATPAY_PUBLIC_KEY", PUB)  # simulasi: BATPay menandatangani dengan kunci pasangan kita
    monkeypatch.setenv("BATPAY_WEBHOOK_TOKEN", "tok-internal")
    return bp.BatpayClient()


# ---------------- signature ----------------
def test_rsa_sign_verify_roundtrip():
    ts = bp.wib_timestamp()
    s = bp.token_string_to_sign("client-key-123", ts)
    sig = bp.rsa_sign(PRIV, s)
    assert bp.rsa_verify(PUB, s, sig)
    assert not bp.rsa_verify(PUB, s + "x", sig)


def test_transaction_string_to_sign_matches_snap_spec():
    body = {"b": 1, "a": {"x": "y"}}
    ts = "2025-03-04T14:06:00+07:00"
    s = bp.transaction_string_to_sign("post", "/api/v1.0/qr/qr-mpm-generate", "TOKEN", body, ts)
    digest = hashlib.sha256(json.dumps(body, separators=(",", ":")).encode()).hexdigest().lower()
    assert s == f"POST:/api/v1.0/qr/qr-mpm-generate:TOKEN:{digest}:{ts}"
    # minify dari string JSON yang berspasi harus menghasilkan digest yang sama
    assert bp.sha256_hex(bp.minify(json.dumps(body, indent=2))) == digest


def test_hmac_sha512_is_base64_and_deterministic():
    a = bp.hmac_sha512("secret", "payload")
    b = bp.hmac_sha512("secret", "payload")
    assert a == b and len(a) == 88  # 64 byte -> base64 88 char


def test_wib_timestamp_format():
    ts = bp.wib_timestamp()
    assert ts.endswith("+07:00") and len(ts) == 25


def test_money_format_two_decimals():
    assert bp.money(45000) == {"value": "45000.00", "currency": "IDR"}


# ---------------- biaya layanan ----------------
@pytest.mark.parametrize("base,pct,fixed", [(100000, 0.7, 0), (312500, 0.7, 0), (10000, 0, 4000), (250000, 1.5, 2500), (999, 0.7, 0)])
def test_gross_up_fee_leaves_store_amount_intact(base, pct, fixed):
    fee = bp.gross_up_fee(base, pct, fixed)
    total = base + fee
    net = total - total * pct / 100 - fixed  # yang diterima toko setelah potongan BATPay
    assert net >= base - 1e-6, f"toko menerima {net} < {base}"
    assert fee >= 0 and isinstance(fee, int)
    # tidak berlebihan: mengurangi 1 rupiah saja sudah membuat toko rugi
    if fee > 0:
        t2 = total - 1
        assert t2 - t2 * pct / 100 - fixed < base


def test_fee_zero_for_zero_amount():
    assert bp.gross_up_fee(0, 0.7, 0) == 0


def test_client_channel_fees(client, monkeypatch):
    # default global: BATPAY_FEE_PERCENT=0.7, BATPAY_FEE_FIXED=0 berlaku untuk QRIS & VA
    fee_qris = client.service_fee(100000, "qris")
    fee_va = client.service_fee(100000, "va_bca")
    assert fee_qris == 705  # 100000/(1-0.007) = 100704.7 -> 100705
    assert fee_va == 705
    assert client.normalize_channel("VA_BCA") == "va_bca"
    assert client.normalize_channel("apa-ini") == "qris"
    keys = [c["key"] for c in client.channels()]
    assert keys[0] == "qris" and "va_bca" in keys and "va_mandiri" in keys
    # override global + per kanal
    monkeypatch.setenv("BATPAY_FEE_PERCENT", "1")
    monkeypatch.setenv("BATPAY_FEE_FIXED", "500")
    monkeypatch.setenv("BATPAY_VA_FEE_PERCENT", "0")
    monkeypatch.setenv("BATPAY_VA_FEE_FIXED", "4000")
    c2 = bp.BatpayClient()
    assert c2.fees["qris"] == {"percent": 1.0, "fixed": 500.0}
    assert c2.fees["va"] == {"percent": 0.0, "fixed": 4000.0}
    assert c2.service_fee(100000, "va_mandiri") == 4000
    assert c2.public_config()["fees"]["default"] == {"percent": 1.0, "fixed": 500.0}


# ---------------- konfigurasi ----------------
def test_client_enabled_and_pem_from_escaped_env(client):
    assert client.enabled
    assert client.mode == "batpay_sandbox"
    assert "-----BEGIN PRIVATE KEY-----" in client.private_key
    assert client.base_url == bp.SANDBOX_BASE_URL


def test_client_placeholder_when_empty(monkeypatch):
    for k in ("BATPAY_CLIENT_ID", "BATPAY_PARTNER_ID", "BATPAY_SECRET_KEY", "BATPAY_CLIENT_KEY", "BATPAY_CLIENT_SECRET", "BATPAY_PRIVATE_KEY", "BATPAY_MERCHANT_ID", "BATPAY_WEBHOOK_TOKEN"):
        monkeypatch.delenv(k, raising=False)
    c = bp.BatpayClient()
    assert not c.enabled and c.mode == "batpay_placeholder" and not c.webhook_ready
    ins = c.placeholder_instructions(10000, "qris")
    assert ins["status"] == "awaiting_integration"


def test_outbound_headers_signature(client):
    body = {"partnerReferenceNo": "SJ-1", "amount": bp.money(1000)}
    h = client._headers(bp.PATH_QR_GENERATE, "TOKEN", body)
    expected = bp.hmac_sha512("secret-abc", bp.transaction_string_to_sign("POST", bp.PATH_QR_GENERATE, "TOKEN", body, h["X-TIMESTAMP"]))
    assert h["X-SIGNATURE"] == expected
    assert h["X-PARTNER-ID"] == "partner-456" and h["X-EXTERNAL-ID"].isdigit() and h["Authorization"] == "Bearer TOKEN"
    # Token request memakai Client ID di X-CLIENT-KEY (berbeda dari Partner ID)
    assert client.client_id == "client-key-123" and client.partner_id == "partner-456"


# ---------------- inbound (BATPay -> kita) ----------------
def test_inbound_token_request_verification(client):
    ts = bp.wib_timestamp()
    sig = bp.rsa_sign(PRIV, bp.token_string_to_sign("client-key-123", ts))
    ok, reason = client.verify_inbound_token_request({"X-CLIENT-KEY": "client-key-123", "X-TIMESTAMP": ts, "X-SIGNATURE": sig})
    assert ok, reason
    ok, reason = client.verify_inbound_token_request({"X-CLIENT-KEY": "other", "X-TIMESTAMP": ts, "X-SIGNATURE": sig})
    assert not ok and "Unknown Client" in reason
    ok, _ = client.verify_inbound_token_request({"X-CLIENT-KEY": "client-key-123", "X-TIMESTAMP": ts, "X-SIGNATURE": "abcd"})
    assert not ok


def test_webhook_verify_snap_flow(client):
    token, exp = client.issue_inbound_token("jwt-secret")
    assert exp == 900
    body = json.dumps({"originalPartnerReferenceNo": "SJ-20250101-ABCD", "latestTransactionStatus": "00", "amount": {"value": "10000.00", "currency": "IDR"}})
    ts = bp.wib_timestamp()
    sig = bp.hmac_sha512("secret-abc", bp.transaction_string_to_sign("POST", bp.WEBHOOK_PATH, token, body, ts))
    ok, how = client.verify_webhook({"Authorization": f"Bearer {token}", "X-TIMESTAMP": ts, "X-SIGNATURE": sig}, body, "jwt-secret")
    assert ok and how == "snap"
    # body diubah -> gagal
    ok, _ = client.verify_webhook({"Authorization": f"Bearer {token}", "X-TIMESTAMP": ts, "X-SIGNATURE": sig}, body + " ", "jwt-secret")
    assert ok is False or bp.minify(body + " ") == bp.minify(body)  # minify menormalkan spasi -> tetap valid; ubah nilai:
    ok, _ = client.verify_webhook({"Authorization": f"Bearer {token}", "X-TIMESTAMP": ts, "X-SIGNATURE": sig}, body.replace("00", "06"), "jwt-secret")
    assert not ok
    # token palsu -> gagal
    ok, reason = client.verify_webhook({"Authorization": "Bearer nope", "X-TIMESTAMP": ts, "X-SIGNATURE": sig}, body, "jwt-secret")
    assert not ok and "Token" in reason


def test_webhook_verify_internal_token(client):
    ok, how = client.verify_webhook({"X-CALLBACK-TOKEN": "tok-internal"}, "{}", "jwt-secret")
    assert ok and how == "token"
    ok, _ = client.verify_webhook({"X-CALLBACK-TOKEN": "salah"}, "{}", "jwt-secret")
    assert not ok


def test_parse_notification_qris_and_va():
    q = bp.BatpayClient.parse_notification({"originalPartnerReferenceNo": "SJ-1", "originalReferenceNo": "R1", "latestTransactionStatus": "00", "amount": {"value": "10000.00"}})
    assert q == {"kind": "qris", "reference": "SJ-1", "status": "paid", "paid_amount": 10000.0, "provider_ref": "R1"}
    q2 = bp.BatpayClient.parse_notification({"originalPartnerReferenceNo": "SJ-1", "latestTransactionStatus": "05"})
    assert q2["status"] == "expired"
    v = bp.BatpayClient.parse_notification({"trxId": "SJ-2", "paymentRequestId": "P1", "paidAmount": {"value": "300000.00", "currency": "IDR"}})
    assert v["kind"] == "va" and v["status"] == "paid" and v["paid_amount"] == 300000.0 and v["reference"] == "SJ-2"
