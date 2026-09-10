"""Verification tests for the fresh Semoyo Joyo import (schema-aware)."""

import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://tarik-preview.preview.emergentagent.com").rstrip("/")


@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def owner_token(s):
    r = s.post(f"{BASE_URL}/api/admin/login", json={"username": "owner", "password": "owner123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_token(s):
    r = s.post(f"{BASE_URL}/api/admin/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


# ---------- Health ----------
def test_health(s):
    r = s.get(f"{BASE_URL}/api/health")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok"
    assert j["db_connected"] is True
    assert j["payment_mode"] == "simulation"


# ---------- Public catalog ----------
def test_categories(s):
    r = s.get(f"{BASE_URL}/api/categories")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) == 7


def test_products(s):
    r = s.get(f"{BASE_URL}/api/products")
    assert r.status_code == 200
    data = r.json()
    items = data if isinstance(data, list) else data.get("items", [])
    assert len(items) == 58


# ---------- Customer checkout ----------
@pytest.fixture(scope="module")
def created_order(s):
    products = s.get(f"{BASE_URL}/api/products").json()
    p = products[0]
    payload = {
        "full_name": f"TEST_{uuid.uuid4().hex[:6]}",
        "phone": "081234567890",
        "address": "Jl. Test No. 1, Jakarta",
        "payment_method": "cod",
        "items": [{"product_id": p["id"], "qty": max(1, p.get("min_order", 1))}],
    }
    r = s.post(f"{BASE_URL}/api/checkout", json=payload)
    assert r.status_code in (200, 201), r.text
    j = r.json()
    return j["order"], j["access_token"]


def test_order_created_with_sj_prefix(created_order):
    order, _ = created_order
    assert order["order_number"].startswith("SJ-")


def test_order_in_admin_list(s, created_order, owner_token):
    order, _ = created_order
    r = s.get(f"{BASE_URL}/api/admin/orders", headers=_h(owner_token))
    assert r.status_code == 200
    nums = [o["order_number"] for o in r.json()]
    assert order["order_number"] in nums


def test_order_status_change(s, created_order, owner_token):
    order, _ = created_order
    r = s.patch(f"{BASE_URL}/api/admin/orders/{order['id']}/status",
                json={"order_status": "diproses"}, headers=_h(owner_token))
    assert r.status_code == 200, r.text
    assert r.json()["order_status"] == "diproses"


def test_order_history_by_customer(s, created_order):
    _, tok = created_order
    r = s.get(f"{BASE_URL}/api/orders/me", headers=_h(tok))
    assert r.status_code == 200
    assert len(r.json()) >= 1


# ---------- Dashboard RBAC ----------
def test_owner_dashboard_has_finance(s, owner_token):
    r = s.get(f"{BASE_URL}/api/admin/dashboard", headers=_h(owner_token))
    assert r.status_code == 200
    d = r.json()
    # Owner should see keys AND populated (or at least present)
    for k in ("gross_profit", "net_profit", "cost_paid", "total_expenses"):
        assert k in d


def test_admin_dashboard_finance_zeroed(s, admin_token):
    """Admin gets same schema but finance values are forced to 0."""
    r = s.get(f"{BASE_URL}/api/admin/dashboard", headers=_h(admin_token))
    assert r.status_code == 200
    d = r.json()
    assert d.get("gross_profit", 0) == 0
    assert d.get("net_profit", 0) == 0
    assert d.get("cost_paid", 0) == 0
    assert d.get("total_expenses", 0) == 0
    assert d.get("profit_by_product") in ([], None)


# ---------- Expenses ----------
def test_create_expense(s, owner_token):
    payload = {
        "expense_date": "2026-01-15",
        "category": "operasional",
        "description": "TEST_expense import verify",
        "amount": 50000,
        "payment_method": "cash",
    }
    r = s.post(f"{BASE_URL}/api/admin/expenses", json=payload, headers=_h(owner_token))
    assert r.status_code in (200, 201), r.text
    assert r.json().get("id")


# ---------- Reports & exports ----------
def test_sales_report(s, owner_token):
    r = s.get(f"{BASE_URL}/api/admin/reports/sales", headers=_h(owner_token))
    assert r.status_code == 200


def test_sales_export_xlsx(s, owner_token):
    r = s.get(f"{BASE_URL}/api/admin/reports/sales/export.xlsx", headers=_h(owner_token))
    assert r.status_code == 200
    assert len(r.content) > 200


def test_sales_export_pdf(s, owner_token):
    r = s.get(f"{BASE_URL}/api/admin/reports/sales/export.pdf", headers=_h(owner_token))
    assert r.status_code == 200
    assert len(r.content) > 200


# ---------- RBAC: admin blocked from owner-only routes ----------
@pytest.mark.parametrize("path", [
    "/api/admin/reports/sales",
    "/api/admin/staff",              # settings staff list is owner-only
    "/api/admin/settings/store",
    "/api/admin/audit-logs",
])
def test_admin_blocked_from_owner_routes(s, admin_token, path):
    r = s.get(f"{BASE_URL}{path}", headers=_h(admin_token))
    assert r.status_code == 403, f"{path} -> {r.status_code} {r.text[:120]}"
