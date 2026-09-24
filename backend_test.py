#!/usr/bin/env python3
"""Backend API testing for Semoyo Joyo BATPay integration - partial config state verification."""
import json
import os
import sys
import time
import uuid
from datetime import datetime

import requests

BASE_URL = "https://batpay-e2e-testing.preview.emergentagent.com"
WEBHOOK_TOKEN = "dev-webhook-token-semoyo"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.owner_token = None
        self.admin_token = None
        self.results = []

    def log(self, status, test_name, message="", details=None):
        """Log test result"""
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
        else:  # INFO
            print(f"{Colors.BLUE}ℹ INFO{Colors.END} - {test_name}: {message}")
        
        self.results.append({
            "test": test_name,
            "status": status,
            "message": message,
            "details": details
        })

    def login_owner(self):
        """Login as owner"""
        try:
            r = requests.post(f"{self.base_url}/api/admin/login", 
                            json={"username": "owner", "password": "owner123"}, timeout=10)
            if r.status_code == 200:
                self.owner_token = r.json()["access_token"]
                self.log("PASS", "Owner login", "Successfully logged in as owner")
                return True
            else:
                self.log("FAIL", "Owner login", f"Status {r.status_code}", r.text[:200])
                return False
        except Exception as e:
            self.log("FAIL", "Owner login", f"Exception: {e}")
            return False

    def login_admin(self):
        """Login as admin"""
        try:
            r = requests.post(f"{self.base_url}/api/admin/login", 
                            json={"username": "admin", "password": "admin123"}, timeout=10)
            if r.status_code == 200:
                self.admin_token = r.json()["access_token"]
                self.log("PASS", "Admin login", "Successfully logged in as admin")
                return True
            else:
                self.log("FAIL", "Admin login", f"Status {r.status_code}", r.text[:200])
                return False
        except Exception as e:
            self.log("FAIL", "Admin login", f"Exception: {e}")
            return False

    def test_health(self):
        """Test GET /api/health"""
        try:
            r = requests.get(f"{self.base_url}/api/health", timeout=10)
            if r.status_code != 200:
                self.log("FAIL", "GET /api/health", f"Status {r.status_code}", r.text[:200])
                return
            
            data = r.json()
            # Check db_connected
            if not data.get("db_connected"):
                self.log("FAIL", "GET /api/health - db_connected", "Expected true", data)
                return
            
            # Check payment_mode is batpay_placeholder (private key missing)
            payment_mode = data.get("payment_mode", "")
            if payment_mode != "batpay_placeholder":
                self.log("FAIL", "GET /api/health - payment_mode", 
                        f"Expected 'batpay_placeholder', got '{payment_mode}'", data)
                return
            
            self.log("PASS", "GET /api/health", 
                    f"db_connected=true, payment_mode='{payment_mode}'")
        except Exception as e:
            self.log("FAIL", "GET /api/health", f"Exception: {e}")

    def test_payment_settings_owner(self):
        """Test GET /api/admin/settings/payments (OWNER token)"""
        if not self.owner_token:
            self.log("FAIL", "GET /api/admin/settings/payments (OWNER)", "No owner token")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            r = requests.get(f"{self.base_url}/api/admin/settings/payments", 
                           headers=headers, timeout=10)
            
            if r.status_code != 200:
                self.log("FAIL", "GET /api/admin/settings/payments (OWNER)", 
                        f"Status {r.status_code}", r.text[:200])
                return
            
            data = r.json()
            
            # Check enabled is false
            if data.get("enabled") != False:
                self.log("FAIL", "settings/payments - enabled", 
                        f"Expected false, got {data.get('enabled')}", data)
                return
            
            # Check partial is true
            if data.get("partial") != True:
                self.log("FAIL", "settings/payments - partial", 
                        f"Expected true, got {data.get('partial')}", data)
                return
            
            # Check missing contains only 'private_key'
            missing = data.get("missing", [])
            if missing != ["private_key"]:
                self.log("FAIL", "settings/payments - missing", 
                        f"Expected ['private_key'], got {missing}", data)
                return
            
            # Check base_url
            if data.get("base_url") != "https://sg-openapi.batbiz.id":
                self.log("FAIL", "settings/payments - base_url", 
                        f"Expected 'https://sg-openapi.batbiz.id', got {data.get('base_url')}", data)
                return
            
            # Check merchant_id
            if data.get("merchant_id") != "000000000001473":
                self.log("FAIL", "settings/payments - merchant_id", 
                        f"Expected '000000000001473', got {data.get('merchant_id')}", data)
                return
            
            # Check configured fields
            configured = data.get("configured", {})
            if not (configured.get("partner_id") and configured.get("client_id") and 
                   configured.get("secret_key") and configured.get("merchant_id")):
                self.log("FAIL", "settings/payments - configured", 
                        "Expected partner_id/client_id/secret_key/merchant_id to be true", configured)
                return
            
            if configured.get("private_key") != False:
                self.log("FAIL", "settings/payments - configured.private_key", 
                        f"Expected false, got {configured.get('private_key')}", configured)
                return
            
            # Check fees
            fees = data.get("fees", {}).get("default", {})
            if fees.get("percent") != 0.7 or fees.get("fixed") != 0:
                self.log("FAIL", "settings/payments - fees.default", 
                        f"Expected percent=0.7, fixed=0, got {fees}", data)
                return
            
            # Check webhook_url
            webhook_url = data.get("webhook_url", "")
            if not webhook_url.endswith("/api/payments/batpay/webhook"):
                self.log("FAIL", "settings/payments - webhook_url", 
                        f"Expected to end with '/api/payments/batpay/webhook', got {webhook_url}", data)
                return
            
            # Check no secret values in response
            response_text = r.text.lower()
            # Don't check for full secret key value, just ensure it's not exposed
            if "ujq52ijfqb713x14wx3unszkhwah8nkb" in response_text:
                self.log("FAIL", "settings/payments - secret exposure", 
                        "Secret key value found in response", "SECURITY ISSUE")
                return
            
            self.log("PASS", "GET /api/admin/settings/payments (OWNER)", 
                    f"enabled=false, partial=true, missing=['private_key'], base_url correct, merchant_id correct")
            
        except Exception as e:
            self.log("FAIL", "GET /api/admin/settings/payments (OWNER)", f"Exception: {e}")

    def test_payment_settings_admin_403(self):
        """Test GET /api/admin/settings/payments (ADMIN token) -> 403"""
        if not self.admin_token:
            self.log("FAIL", "GET /api/admin/settings/payments (ADMIN)", "No admin token")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            r = requests.get(f"{self.base_url}/api/admin/settings/payments", 
                           headers=headers, timeout=10)
            
            if r.status_code == 403:
                self.log("PASS", "GET /api/admin/settings/payments (ADMIN) -> 403", 
                        "Correctly rejected admin token")
            else:
                self.log("FAIL", "GET /api/admin/settings/payments (ADMIN) -> 403", 
                        f"Expected 403, got {r.status_code}", r.text[:200])
        except Exception as e:
            self.log("FAIL", "GET /api/admin/settings/payments (ADMIN) -> 403", f"Exception: {e}")

    def test_payment_test_endpoint(self):
        """Test POST /api/admin/settings/payments/test (OWNER)"""
        if not self.owner_token:
            self.log("FAIL", "POST /api/admin/settings/payments/test (OWNER)", "No owner token")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            r = requests.post(f"{self.base_url}/api/admin/settings/payments/test", 
                            headers=headers, timeout=10)
            
            if r.status_code != 200:
                self.log("FAIL", "POST /api/admin/settings/payments/test (OWNER)", 
                        f"Status {r.status_code}", r.text[:200])
                return
            
            data = r.json()
            
            # Check ok is false
            if data.get("ok") != False:
                self.log("FAIL", "settings/payments/test - ok", 
                        f"Expected false, got {data.get('ok')}", data)
                return
            
            # Check step is 'config'
            if data.get("step") != "config":
                self.log("FAIL", "settings/payments/test - step", 
                        f"Expected 'config', got {data.get('step')}", data)
                return
            
            # Check missing contains 'private_key'
            missing = data.get("missing", [])
            if "private_key" not in missing:
                self.log("FAIL", "settings/payments/test - missing", 
                        f"Expected 'private_key' in missing, got {missing}", data)
                return
            
            self.log("PASS", "POST /api/admin/settings/payments/test (OWNER)", 
                    f"ok=false, step='config', missing={missing}")
            
        except Exception as e:
            self.log("FAIL", "POST /api/admin/settings/payments/test (OWNER)", f"Exception: {e}")

    def test_payment_test_admin_403(self):
        """Test POST /api/admin/settings/payments/test (ADMIN) -> 403"""
        if not self.admin_token:
            self.log("FAIL", "POST /api/admin/settings/payments/test (ADMIN)", "No admin token")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            r = requests.post(f"{self.base_url}/api/admin/settings/payments/test", 
                            headers=headers, timeout=10)
            
            if r.status_code == 403:
                self.log("PASS", "POST /api/admin/settings/payments/test (ADMIN) -> 403", 
                        "Correctly rejected admin token")
            else:
                self.log("FAIL", "POST /api/admin/settings/payments/test (ADMIN) -> 403", 
                        f"Expected 403, got {r.status_code}", r.text[:200])
        except Exception as e:
            self.log("FAIL", "POST /api/admin/settings/payments/test (ADMIN) -> 403", f"Exception: {e}")

    def test_audit_log_for_test(self):
        """Check audit log contains test entry"""
        if not self.owner_token:
            self.log("FAIL", "Check audit log for test entry", "No owner token")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            r = requests.get(f"{self.base_url}/api/admin/audit-logs", 
                           headers=headers, timeout=10)
            
            if r.status_code != 200:
                self.log("FAIL", "GET /api/admin/audit-logs", 
                        f"Status {r.status_code}", r.text[:200])
                return
            
            data = r.json()
            # Handle both list and dict responses
            if isinstance(data, list):
                logs = data
            else:
                logs = data.get("logs", [])
            
            # Find test action with label 'Bayar Online'
            test_log = None
            for log in logs:
                if log.get("action") == "test" and "Bayar Online" in log.get("entity_label", ""):
                    test_log = log
                    break
            
            if test_log:
                self.log("PASS", "Audit log contains test entry", 
                        f"Found action='test', label='{test_log.get('entity_label')}'")
            else:
                self.log("FAIL", "Audit log contains test entry", 
                        "No test action with label 'Bayar Online' found", 
                        f"Total logs: {len(logs)}")
        except Exception as e:
            self.log("FAIL", "Check audit log for test entry", f"Exception: {e}")

    def test_payments_config(self):
        """Test GET /api/payments/config"""
        try:
            r = requests.get(f"{self.base_url}/api/payments/config", timeout=10)
            
            if r.status_code != 200:
                self.log("FAIL", "GET /api/payments/config", 
                        f"Status {r.status_code}", r.text[:200])
                return
            
            data = r.json()
            methods = data.get("methods", [])
            
            # Check exactly 3 methods
            if len(methods) != 3:
                self.log("FAIL", "payments/config - method count", 
                        f"Expected 3 methods, got {len(methods)}", methods)
                return
            
            # Check method keys
            keys = [m.get("key") for m in methods]
            if keys != ["cash", "piutang", "online"]:
                self.log("FAIL", "payments/config - method keys", 
                        f"Expected ['cash', 'piutang', 'online'], got {keys}", methods)
                return
            
            # Check online.available is false
            online = methods[2]
            if online.get("available") != False:
                self.log("FAIL", "payments/config - online.available", 
                        f"Expected false, got {online.get('available')}", online)
                return
            
            # Check online channels
            channels = online.get("channels", [])
            channel_keys = [c.get("key") for c in channels]
            
            if "qris" not in channel_keys:
                self.log("FAIL", "payments/config - channels", 
                        "Expected 'qris' in channels", channel_keys)
                return
            
            va_channels = [k for k in channel_keys if k.startswith("va_")]
            expected_va = ["va_bca", "va_mandiri", "va_cimb", "va_danamon"]
            if not all(va in channel_keys for va in expected_va):
                self.log("FAIL", "payments/config - VA channels", 
                        f"Expected {expected_va}, got {va_channels}", channel_keys)
                return
            
            self.log("PASS", "GET /api/payments/config", 
                    f"3 methods, online.available=false, channels: {channel_keys}")
            
        except Exception as e:
            self.log("FAIL", "GET /api/payments/config", f"Exception: {e}")

    def test_checkout_flows(self):
        """Test checkout flows: cash, piutang, online"""
        # Get a product first
        try:
            r = requests.get(f"{self.base_url}/api/products", timeout=10)
            if r.status_code != 200:
                self.log("FAIL", "Get products for checkout", f"Status {r.status_code}")
                return
            
            products = r.json()
            items = products if isinstance(products, list) else products.get("items", [])
            if not items:
                self.log("FAIL", "Get products for checkout", "No products available")
                return
            
            product = items[0]
            
            # Test cash checkout
            self.test_cash_checkout(product)
            
            # Test piutang checkout
            self.test_piutang_checkout(product)
            
            # Test online checkout
            self.test_online_checkout(product)
            
        except Exception as e:
            self.log("FAIL", "Checkout flows", f"Exception: {e}")

    def test_cash_checkout(self, product):
        """Test POST /api/checkout cash"""
        try:
            payload = {
                "full_name": f"TEST_CASH_{uuid.uuid4().hex[:6]}",
                "phone": "081234567890",
                "address": "Test Address",
                "payment_method": "cash",
                "items": [{"product_id": product["id"], "qty": max(1, product.get("min_order", 1))}]
            }
            
            r = requests.post(f"{self.base_url}/api/checkout", json=payload, timeout=10)
            
            if r.status_code != 200:
                self.log("FAIL", "POST /api/checkout cash", 
                        f"Status {r.status_code}", r.text[:200])
                return None
            
            data = r.json()
            order = data.get("order", {})
            
            # Check payment_status is 'proses'
            if order.get("payment_status") != "proses":
                self.log("FAIL", "checkout cash - payment_status", 
                        f"Expected 'proses', got {order.get('payment_status')}", order)
                return None
            
            # Check order_status is 'diproses'
            if order.get("order_status") != "diproses":
                self.log("FAIL", "checkout cash - order_status", 
                        f"Expected 'diproses', got {order.get('order_status')}", order)
                return None
            
            self.log("PASS", "POST /api/checkout cash", 
                    f"payment_status='proses', order_status='diproses'")
            
            return order
            
        except Exception as e:
            self.log("FAIL", "POST /api/checkout cash", f"Exception: {e}")
            return None

    def test_piutang_checkout(self, product):
        """Test POST /api/checkout piutang"""
        try:
            payload = {
                "full_name": f"TEST_PIUTANG_{uuid.uuid4().hex[:6]}",
                "phone": "081234567890",
                "address": "Test Address",
                "payment_method": "piutang",
                "items": [{"product_id": product["id"], "qty": max(1, product.get("min_order", 1))}]
            }
            
            r = requests.post(f"{self.base_url}/api/checkout", json=payload, timeout=10)
            
            if r.status_code != 200:
                self.log("FAIL", "POST /api/checkout piutang", 
                        f"Status {r.status_code}", r.text[:200])
                return None
            
            data = r.json()
            order = data.get("order", {})
            
            # Check payment_status is 'piutang'
            if order.get("payment_status") != "piutang":
                self.log("FAIL", "checkout piutang - payment_status", 
                        f"Expected 'piutang', got {order.get('payment_status')}", order)
                return None
            
            self.log("PASS", "POST /api/checkout piutang", 
                    f"payment_status='piutang'")
            
            # Check if appears in receivables
            if self.owner_token:
                self.check_receivables(order.get("order_number"))
            
            return order
            
        except Exception as e:
            self.log("FAIL", "POST /api/checkout piutang", f"Exception: {e}")
            return None

    def check_receivables(self, order_number):
        """Check if order appears in receivables"""
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            r = requests.get(f"{self.base_url}/api/admin/receivables", 
                           headers=headers, timeout=10)
            
            if r.status_code != 200:
                self.log("FAIL", "GET /api/admin/receivables", 
                        f"Status {r.status_code}", r.text[:200])
                return
            
            data = r.json()
            orders = data.get("orders", [])
            order_numbers = [o.get("order_number") for o in orders]
            
            if order_number in order_numbers:
                self.log("PASS", "Piutang in receivables", 
                        f"Order {order_number} found in receivables")
            else:
                self.log("FAIL", "Piutang in receivables", 
                        f"Order {order_number} not found in receivables", 
                        f"Found: {order_numbers[:5]}")
        except Exception as e:
            self.log("FAIL", "Check receivables", f"Exception: {e}")

    def test_online_checkout(self, product):
        """Test POST /api/checkout online qris"""
        try:
            payload = {
                "full_name": f"TEST_ONLINE_{uuid.uuid4().hex[:6]}",
                "phone": "081234567890",
                "address": "Test Address",
                "payment_method": "online",
                "payment_channel": "qris",
                "items": [{"product_id": product["id"], "qty": max(1, product.get("min_order", 1))}]
            }
            
            r = requests.post(f"{self.base_url}/api/checkout", json=payload, timeout=10)
            
            if r.status_code != 200:
                self.log("FAIL", "POST /api/checkout online qris", 
                        f"Status {r.status_code}", r.text[:200])
                return None
            
            data = r.json()
            order = data.get("order", {})
            payment = data.get("payment", {})
            
            # Check payment_status is 'pending'
            if order.get("payment_status") != "pending":
                self.log("FAIL", "checkout online - payment_status", 
                        f"Expected 'pending', got {order.get('payment_status')}", order)
                return None
            
            # Check service_fee > 0
            if order.get("service_fee", 0) <= 0:
                self.log("FAIL", "checkout online - service_fee", 
                        f"Expected > 0, got {order.get('service_fee')}", order)
                return None
            
            # Check instructions status is 'awaiting_integration' (placeholder)
            instructions = payment.get("instructions", {})
            if instructions.get("status") != "awaiting_integration":
                self.log("FAIL", "checkout online - instructions.status", 
                        f"Expected 'awaiting_integration', got {instructions.get('status')}", instructions)
                return None
            
            self.log("PASS", "POST /api/checkout online qris", 
                    f"payment_status='pending', service_fee={order.get('service_fee')}, status='awaiting_integration'")
            
            return order
            
        except Exception as e:
            self.log("FAIL", "POST /api/checkout online qris", f"Exception: {e}")
            return None

    def test_webhook(self):
        """Test webhook POST /api/payments/batpay/webhook"""
        # First create an online order
        try:
            r = requests.get(f"{self.base_url}/api/products", timeout=10)
            if r.status_code != 200:
                self.log("FAIL", "Get products for webhook test", f"Status {r.status_code}")
                return
            
            products = r.json()
            items = products if isinstance(products, list) else products.get("items", [])
            if not items:
                self.log("FAIL", "Get products for webhook test", "No products available")
                return
            
            product = items[0]
            
            payload = {
                "full_name": f"TEST_WEBHOOK_{uuid.uuid4().hex[:6]}",
                "phone": "081234567890",
                "address": "Test Address",
                "payment_method": "online",
                "payment_channel": "qris",
                "items": [{"product_id": product["id"], "qty": max(1, product.get("min_order", 1))}]
            }
            
            r = requests.post(f"{self.base_url}/api/checkout", json=payload, timeout=10)
            if r.status_code != 200:
                self.log("FAIL", "Create order for webhook test", f"Status {r.status_code}")
                return
            
            order = r.json().get("order", {})
            order_number = order.get("order_number")
            total = order.get("total")
            
            # Test webhook with correct token
            webhook_payload = {
                "originalPartnerReferenceNo": order_number,
                "originalReferenceNo": "R-TEST",
                "latestTransactionStatus": "00",
                "amount": {"value": f"{total:.2f}", "currency": "IDR"}
            }
            
            headers = {"X-CALLBACK-TOKEN": WEBHOOK_TOKEN}
            r = requests.post(f"{self.base_url}/api/payments/batpay/webhook", 
                            json=webhook_payload, headers=headers, timeout=10)
            
            if r.status_code != 200:
                self.log("FAIL", "POST webhook with correct token", 
                        f"Status {r.status_code}", r.text[:200])
                return
            
            webhook_response = r.json()
            if webhook_response.get("responseCode") != "2005200":
                self.log("FAIL", "webhook response code", 
                        f"Expected '2005200', got {webhook_response.get('responseCode')}", webhook_response)
                return
            
            # Check order is now paid and selesai
            time.sleep(0.5)  # Give it a moment
            r = requests.get(f"{self.base_url}/api/orders/{order_number}", timeout=10)
            if r.status_code == 200:
                updated_order = r.json()
                if updated_order.get("payment_status") == "paid" and updated_order.get("order_status") == "selesai":
                    self.log("PASS", "Webhook marks order paid + selesai", 
                            f"Order {order_number}: payment_status='paid', order_status='selesai'")
                else:
                    self.log("FAIL", "Webhook marks order paid + selesai", 
                            f"Expected paid+selesai, got {updated_order.get('payment_status')}+{updated_order.get('order_status')}", 
                            updated_order)
            
            # Test webhook with wrong token
            headers_wrong = {"X-CALLBACK-TOKEN": "wrong-token"}
            r = requests.post(f"{self.base_url}/api/payments/batpay/webhook", 
                            json=webhook_payload, headers=headers_wrong, timeout=10)
            
            if r.status_code == 401:
                self.log("PASS", "Webhook rejects wrong token", "Status 401 as expected")
            else:
                self.log("FAIL", "Webhook rejects wrong token", 
                        f"Expected 401, got {r.status_code}", r.text[:200])
            
        except Exception as e:
            self.log("FAIL", "Webhook test", f"Exception: {e}")

    def test_legacy_methods_rejected(self):
        """Test legacy methods are rejected"""
        try:
            r = requests.get(f"{self.base_url}/api/products", timeout=10)
            if r.status_code != 200:
                self.log("FAIL", "Get products for legacy test", f"Status {r.status_code}")
                return
            
            products = r.json()
            items = products if isinstance(products, list) else products.get("items", [])
            if not items:
                self.log("FAIL", "Get products for legacy test", "No products available")
                return
            
            product = items[0]
            
            legacy_methods = ["cod", "bank_transfer", "qris", "ewallet", "transfer_va"]
            all_rejected = True
            
            for method in legacy_methods:
                payload = {
                    "full_name": f"TEST_LEGACY_{uuid.uuid4().hex[:6]}",
                    "phone": "081234567890",
                    "address": "Test Address",
                    "payment_method": method,
                    "items": [{"product_id": product["id"], "qty": max(1, product.get("min_order", 1))}]
                }
                
                r = requests.post(f"{self.base_url}/api/checkout", json=payload, timeout=10)
                
                if r.status_code != 422:
                    self.log("FAIL", f"Legacy method '{method}' rejected", 
                            f"Expected 422, got {r.status_code}", r.text[:200])
                    all_rejected = False
                    break
            
            if all_rejected:
                self.log("PASS", "Legacy methods rejected", 
                        f"All legacy methods ({', '.join(legacy_methods)}) return 422")
            
        except Exception as e:
            self.log("FAIL", "Legacy methods test", f"Exception: {e}")

    def test_legacy_endpoints_gone(self):
        """Test legacy endpoints return 404"""
        legacy_endpoints = [
            "/api/payments/midtrans/notification",
            "/api/payments/travoy/notification"
        ]
        
        all_gone = True
        for endpoint in legacy_endpoints:
            try:
                r = requests.post(f"{self.base_url}{endpoint}", json={}, timeout=10)
                if r.status_code != 404:
                    self.log("FAIL", f"Legacy endpoint {endpoint} -> 404", 
                            f"Expected 404, got {r.status_code}", r.text[:200])
                    all_gone = False
            except Exception as e:
                self.log("FAIL", f"Legacy endpoint {endpoint} test", f"Exception: {e}")
                all_gone = False
        
        if all_gone:
            self.log("PASS", "Legacy endpoints gone", 
                    f"All legacy endpoints return 404")

    def run_all_tests(self):
        """Run all backend tests"""
        print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
        print(f"{Colors.BLUE}Backend API Testing - Semoyo Joyo BATPay Integration{Colors.END}")
        print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")
        
        # Login
        if not self.login_owner():
            print(f"\n{Colors.RED}Cannot proceed without owner login{Colors.END}")
            return
        
        self.login_admin()
        
        # Run tests
        print(f"\n{Colors.YELLOW}--- Health & Configuration ---{Colors.END}")
        self.test_health()
        self.test_payment_settings_owner()
        self.test_payment_settings_admin_403()
        
        print(f"\n{Colors.YELLOW}--- Test Connection Endpoint ---{Colors.END}")
        self.test_payment_test_endpoint()
        self.test_payment_test_admin_403()
        self.test_audit_log_for_test()
        
        print(f"\n{Colors.YELLOW}--- Payment Config ---{Colors.END}")
        self.test_payments_config()
        
        print(f"\n{Colors.YELLOW}--- Checkout Flows ---{Colors.END}")
        self.test_checkout_flows()
        
        print(f"\n{Colors.YELLOW}--- Webhook ---{Colors.END}")
        self.test_webhook()
        
        print(f"\n{Colors.YELLOW}--- Legacy Methods & Endpoints ---{Colors.END}")
        self.test_legacy_methods_rejected()
        self.test_legacy_endpoints_gone()
        
        # Summary
        print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
        print(f"{Colors.BLUE}Test Summary{Colors.END}")
        print(f"{Colors.BLUE}{'='*70}{Colors.END}")
        print(f"Total tests: {self.tests_run}")
        print(f"{Colors.GREEN}Passed: {self.tests_passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.tests_failed}{Colors.END}")
        
        if self.tests_failed == 0:
            print(f"\n{Colors.GREEN}✓ All tests passed!{Colors.END}\n")
            return 0
        else:
            print(f"\n{Colors.RED}✗ Some tests failed{Colors.END}\n")
            return 1

if __name__ == "__main__":
    tester = APITester()
    sys.exit(tester.run_all_tests())
