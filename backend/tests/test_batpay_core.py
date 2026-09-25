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


ENV_KEYS = ("BATPAY_CLIENT_ID", "BATPAY_PARTNER_ID", "BATPAY_SECRET_KEY", "BATPAY_CLIENT_KEY", "BATPAY_CLIENT_SECRET", "BATPAY_PRIVATE_KEY",
            "BATPAY_MERCHANT_ID", "BATPAY_WEBHOOK_TOKEN", "BATPAY_PUBLIC_KEY", "BATPAY_FORCE_PLACEHOLDER", "BATPAY_ENV", "BATPAY_BASE_URL",
            "BATPAY_VA_BANKS", "BATPAY_VA_PAYMENT_TYPES", "BATPAY_QRIS_FEE_THRESHOLD", "BATPAY_QRIS_FEE_PERCENT", "BATPAY_VA_FLAT_FEES",
            "BATPAY_VA_FLAT_FEE_DEFAULT")


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Isolasi: buang env BATPay yang mungkin bocor dari .env / suite lain agar unit test deterministik."""
    for k in ENV_KEYS:
        monkeypatch.delenv(k, raising=False)


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
@pytest.mark.parametrize("base,pct,fixed", [(100000, 0.7, 0), (312500, 0.7, 0), (10000, 0, 4000), (250000, 1.5, 2500), (999, 0.7, 0), (600000, 0.3, 0)])
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


@pytest.mark.parametrize("base,expected", [
    (0, 0), (1, 0), (100_000, 0), (499_999, 0), (500_000, 0),          # <= 500.000 -> gratis
    (500_001, 1505),  # 500001/0.997 = 501505.5 -> ceil 501506 -> fee 1505
    (600_000, 1806),  # 600000/0.997 = 601805.4 -> ceil 601806 -> fee 1806
    (1_000_000, 0),   # diverifikasi lewat invarian gross-up (expected=0 -> lewati cek angka)
])
def test_qris_tiered_fee_policy(monkeypatch, base, expected):
    for k in ("BATPAY_QRIS_FEE_THRESHOLD", "BATPAY_QRIS_FEE_PERCENT"):
        monkeypatch.delenv(k, raising=False)
    fp = bp.FeePolicy()
    assert fp.qris_threshold == 500_000 and fp.qris_percent == 0.3
    fee = fp.qris_fee(base)
    if base <= 500_000:
        assert fee == 0
    else:
        # gross-up: dana toko utuh setelah potongan 0,3% dari total, dan tidak berlebihan
        total = base + fee
        assert total - total * 0.003 >= base - 1e-6
        assert (total - 1) - (total - 1) * 0.003 < base
        assert fee == bp.gross_up_fee(base, 0.3, 0)
        if expected:
            assert fee == expected


def test_va_flat_fee_policy(monkeypatch):
    for k in ("BATPAY_VA_FLAT_FEES", "BATPAY_VA_FLAT_FEE_DEFAULT"):
        monkeypatch.delenv(k, raising=False)
    fp = bp.FeePolicy()
    assert fp.va_fee("bca") == 4000
    assert fp.va_fee("bsi") == 2500
    for b in ("mandiri", "bri", "bni", "cimb", "danamon", "permata", "btn", "bjb", "neo"):
        assert fp.va_fee(b) == 2000, b
    assert fp.va_fee("bank-tak-dikenal") == 2000  # fallback default
    assert fp.va_fee("bca", 0) == 0  # nominal 0 -> tidak ada biaya
    # tarif flat tidak tergantung nominal
    assert fp.fee(10_000, "va_bca") == fp.fee(10_000_000, "va_bca") == 4000
    assert fp.fee(750_000, "va_bsi") == 2500 and fp.fee(750_000, "va_bri") == 2000
    d = fp.describe()
    assert d["qris"]["type"] == "tiered_percent" and d["va"]["type"] == "flat"
    assert d["va"]["by_bank"]["bca"] == 4000 and d["va"]["by_bank"]["neo"] == 2000
    assert "500.000" in d["qris"]["label"] and "0,3" in d["qris"]["label"].replace(".", ",")


def test_fee_policy_env_override(monkeypatch):
    monkeypatch.setenv("BATPAY_QRIS_FEE_THRESHOLD", "1000000")
    monkeypatch.setenv("BATPAY_QRIS_FEE_PERCENT", "0.5")
    monkeypatch.setenv("BATPAY_VA_FLAT_FEES", "bca=5000, bri=3000, rusak=abc, =1")
    monkeypatch.setenv("BATPAY_VA_FLAT_FEE_DEFAULT", "1500")
    fp = bp.FeePolicy()
    assert fp.qris_fee(900_000) == 0 and fp.qris_fee(1_000_001) == bp.gross_up_fee(1_000_001, 0.5, 0)
    assert fp.va_fee("bca") == 5000 and fp.va_fee("bri") == 3000 and fp.va_fee("bsi") == 2500 and fp.va_fee("mandiri") == 1500


def test_client_channel_fees(client, monkeypatch):
    # QRIS bertingkat & VA flat lewat client
    assert client.service_fee(100_000, "qris") == 0
    assert client.service_fee(500_000, "qris") == 0
    assert client.service_fee(600_000, "qris") == 1806
    assert client.service_fee(100_000, "va_bca") == 4000
    assert client.service_fee(100_000, "va_bsi") == 2500
    assert client.service_fee(100_000, "va_mandiri") == 2000
    assert client.service_fee(100_000, "VA_BRI") == 2000
    assert client.normalize_channel("VA_BCA") == "va_bca"
    assert client.normalize_channel("apa-ini") == "qris"
    assert client.is_valid_channel("va_neo") and not client.is_valid_channel("va_xyz")
    keys = [c["key"] for c in client.channels()]
    assert keys[0] == "qris"
    for b in ("bca", "mandiri", "bri", "bni", "bsi", "cimb", "danamon", "permata", "btn", "bjb", "neo"):
        assert f"va_{b}" in keys, b
    by = {c["key"]: c for c in client.channels()}
    assert by["qris"]["fee_type"] == "tiered_percent" and by["qris"]["fee_threshold"] == 500_000
    assert by["va_bca"]["fee_type"] == "flat" and by["va_bca"]["fee_fixed"] == 4000 and by["va_bca"]["payment_type"] == "BCA_DYNAMIC"
    assert by["va_neo"]["payment_type"] == "NEO_DYNAMIC" and "2.000" in by["va_neo"]["fee_label"]
    cfg = client.public_config()
    assert cfg["fee_policy"]["va"]["by_bank"]["bsi"] == 2500 and "fees" not in cfg
    assert len(cfg["va_banks"]) == 11


def test_va_banks_subset_and_payment_type_override(client, monkeypatch):
    monkeypatch.setenv("BATPAY_VA_BANKS", "BCA, BRI, NEO, BANKPALSU")
    monkeypatch.setenv("BATPAY_VA_PAYMENT_TYPES", "neo=NEOBANK_DYNAMIC, bri=bri_dynamic_v2, palsu=X")
    c = bp.BatpayClient()
    assert c.va_banks == ["bca", "bri", "neo"]
    keys = [ch["key"] for ch in c.channels()]
    assert keys == ["qris", "va_bca", "va_bri", "va_neo"]
    assert c.va_payment_types["neo"] == "NEOBANK_DYNAMIC" and c.va_payment_types["bri"] == "BRI_DYNAMIC_V2" and c.va_payment_types["bca"] == "BCA_DYNAMIC"
    # bank yang tidak diaktifkan -> tidak valid & jatuh ke qris saat normalisasi
    assert not c.is_valid_channel("va_mandiri") and c.normalize_channel("va_mandiri") == "qris"


# ---------------- konfigurasi ----------------
def test_client_enabled_and_pem_from_escaped_env(client):
    assert client.enabled
    assert client.mode == "batpay_sandbox"
    assert "-----BEGIN PRIVATE KEY-----" in client.private_key
    assert client.base_url == bp.SANDBOX_BASE_URL


def test_client_placeholder_when_empty():
    c = bp.BatpayClient()  # env sudah dibersihkan oleh fixture _clean_env
    assert not c.enabled and c.mode == "batpay_placeholder" and not c.webhook_ready
    assert c.status == "placeholder" and c.public_config()["status"] == "placeholder"
    ins = c.placeholder_instructions(10000, "qris")
    assert ins["status"] == "awaiting_integration"


def test_client_partial_when_private_key_missing(client, monkeypatch):
    monkeypatch.delenv("BATPAY_PRIVATE_KEY", raising=False)
    c = bp.BatpayClient()
    assert not c.enabled and not c.credentials_complete and c.status == "partial"
    cfg = c.public_config()
    assert cfg["partial"] is True and cfg["missing"] == ["private_key"] and cfg["force_placeholder"] is False


def test_force_placeholder_kill_switch_blocks_everything(client, monkeypatch):
    """BATPAY_FORCE_PLACEHOLDER=true: kredensial lengkap tetapi TIDAK ADA panggilan keluar ke BATPay."""
    import asyncio

    monkeypatch.setenv("BATPAY_FORCE_PLACEHOLDER", "true")
    c = bp.BatpayClient()
    assert c.credentials_complete and not c.enabled and c.force_placeholder
    assert c.mode == "batpay_placeholder" and c.status == "held"
    cfg = c.public_config("https://toko.example")
    assert cfg["enabled"] is False and cfg["force_placeholder"] is True and cfg["credentials_complete"] is True
    assert cfg["partial"] is False and cfg["missing"] == []
    # webhook internal token tetap bisa dipakai untuk uji manual; jalur SNAP dinonaktifkan selama ditahan
    assert c.webhook_ready
    ok, how = c.verify_webhook({"X-CALLBACK-TOKEN": "tok-internal"}, "{}", "jwt-secret")
    assert ok and how == "token"
    # test_connection tidak boleh menyentuh jaringan: patch httpx agar meledak bila dipanggil
    import httpx

    def _boom(*a, **k):  # pragma: no cover - harus tidak pernah terpanggil
        raise AssertionError("HTTP request terkirim padahal integrasi ditahan!")

    monkeypatch.setattr(httpx, "AsyncClient", _boom)
    res = asyncio.run(c.test_connection())
    assert res["ok"] is False and res["step"] == "config" and res.get("held") is True
    with pytest.raises(bp.BatpayError):
        asyncio.run(c.get_token())
    ins = c.placeholder_instructions(10000, "qris")
    assert ins["status"] == "awaiting_integration" and "aktivasi" in ins["message"]
    # nilai selain true -> tidak ditahan
    for v in ("false", "0", "", "off"):
        monkeypatch.setenv("BATPAY_FORCE_PLACEHOLDER", v)
        assert bp.BatpayClient().enabled, f"nilai {v!r} tidak boleh menahan integrasi"


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
