#!/usr/bin/env python3
"""Backend API regression tests for Semoyo Joyo B2B e-commerce app.
Tests all critical endpoints after dependency fix.
"""
import sys
import requests

BASE_URL = "https://great-chaplygin-9.preview.emergentagent.com/api"

class TestRunner:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_token = None
        self.owner_token = None
        self.order_number = None

    def test(self, name, method, endpoint, expected_status, data=None, headers=None, files=None):
        """Run a single API test"""
        url = f"{BASE_URL}{endpoint}"
        self.tests_run += 1
        print(f"\n🔍 Test {self.tests_run}: {name}")
        
        try:
            h = headers or {}
            if method == 'GET':
                response = requests.get(url, headers=h, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=h, timeout=30)
                else:
                    h['Content-Type'] = 'application/json'
                    response = requests.post(url, json=data, headers=h, timeout=30)
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASS - Status: {response.status_code}")
                return True, response
            else:
                print(f"❌ FAIL - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False, response
        except Exception as e:
            print(f"❌ FAIL - Error: {str(e)}")
            return False, None

    def run_all_tests(self):
        print("=" * 60)
        print("SEMOYO JOYO BACKEND API TESTS")
        print("=" * 60)
        
        # 1. Health check
        success, resp = self.test("Health check", "GET", "/health", 200)
        if success:
            data = resp.json()
            if data.get('status') == 'ok' and data.get('db_connected') and data.get('payment_mode') == 'simulation':
                print("   ✓ Health check passed: status ok, db connected, payment simulation mode")
            else:
                print(f"   ⚠ Health check response unexpected: {data}")
        
        # 2. Home endpoint - check products and categories
        success, resp = self.test("Home endpoint", "GET", "/home", 200)
        if success:
            data = resp.json()
            categories = data.get('categories', [])
            total_products = sum(len(cat.get('products', [])) for cat in categories)
            print(f"   ✓ Found {len(categories)} categories with {total_products} products")
            if total_products < 50:
                print(f"   ⚠ Expected ~58 products, found {total_products}")
        
        # 3. Admin login
        success, resp = self.test("Admin login", "POST", "/admin/login", 200, 
                                  data={"username": "admin", "password": "admin123"})
        if success:
            self.admin_token = resp.json().get('access_token')
            print("   ✓ Admin token obtained")
        
        # 4. Admin dashboard
        if self.admin_token:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            success, resp = self.test("Admin dashboard", "GET", "/admin/dashboard", 200, headers=headers)
            if success:
                data = resp.json()
                print(f"   ✓ Dashboard data: {list(data.keys())}")
        
        # 5. Owner login
        success, resp = self.test("Owner login", "POST", "/admin/login", 200,
                                  data={"username": "owner", "password": "owner123"})
        if success:
            self.owner_token = resp.json().get('access_token')
            print("   ✓ Owner token obtained")
        
        # 6. Sales report
        if self.owner_token:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            success, resp = self.test("Sales report", "GET", 
                                     "/admin/reports/sales?start=2026-01-01&end=2026-12-31", 
                                     200, headers=headers)
            if success:
                data = resp.json()
                print("   ✓ Sales report retrieved")
        
        # 7. Export XLSX (tests openpyxl dependency)
        if self.owner_token:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            success, resp = self.test("Export sales XLSX", "GET",
                                     "/admin/reports/sales/export.xlsx?start=2026-01-01&end=2026-12-31",
                                     200, headers=headers)
            if success and resp.headers.get('content-type', '').startswith('application/vnd.openxmlformats'):
                print("   ✓ XLSX file generated (openpyxl working)")
        
        # 8. Export PDF (tests reportlab/pillow dependencies)
        if self.owner_token:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            success, resp = self.test("Export sales PDF", "GET",
                                     "/admin/reports/sales/export.pdf?start=2026-01-01&end=2026-12-31",
                                     200, headers=headers)
            if success and resp.headers.get('content-type', '').startswith('application/pdf'):
                print("   ✓ PDF file generated (reportlab/pillow working)")
        
        # 9. Get products list
        if self.admin_token:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            success, resp = self.test("Admin products list", "GET", "/admin/products", 200, headers=headers)
            if success:
                products = resp.json()
                print(f"   ✓ Retrieved {len(products)} products")
        
        # 10. Get stock list
        if self.admin_token:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            success, resp = self.test("Admin stock list", "GET", "/admin/stock", 200, headers=headers)
            if success:
                stock = resp.json()
                print("   ✓ Retrieved stock data")
        
        # 11. Get orders list
        if self.admin_token:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            success, resp = self.test("Admin orders list", "GET", "/admin/orders", 200, headers=headers)
            if success:
                orders = resp.json()
                print("   ✓ Retrieved orders list")
        
        # 12. Customer checkout flow
        # First get a product ID from home
        success, resp = self.test("Get product for checkout", "GET", "/home", 200)
        product_id = None
        if success:
            data = resp.json()
            for cat in data.get('categories', []):
                products = cat.get('products', [])
                if products:
                    product_id = products[0]['id']
                    min_order = products[0].get('min_order', 1)
                    break
        
        if product_id:
            checkout_data = {
                "full_name": "Test Customer",
                "phone": "081234567890",
                "address": "Jl. Test No. 123, Jakarta",
                "notes": "Test order",
                "items": [{"product_id": product_id, "qty": min_order}],
                "payment_method": "bank_transfer",
                "payment_channel": "bca"
            }
            success, resp = self.test("Customer checkout", "POST", "/checkout", 200, data=checkout_data)
            if success:
                data = resp.json()
                self.order_number = data.get('order', {}).get('order_number')
                print(f"   ✓ Order created: {self.order_number}")
                
                # 13. Create payment
                if self.order_number:
                    success, resp = self.test("Create payment", "POST", 
                                            f"/payments/{self.order_number}/create", 200, data={})
                    if success:
                        print("   ✓ Payment created")
                    
                    # 14. Simulate payment
                    success, resp = self.test("Simulate payment", "POST",
                                            f"/payments/{self.order_number}/simulate", 200)
                    if success:
                        print("   ✓ Payment simulated (order should be paid)")
                    
                    # 15. Get order details
                    success, resp = self.test("Get order details", "GET",
                                            f"/orders/{self.order_number}", 200)
                    if success:
                        order = resp.json()
                        print(f"   ✓ Order retrieved: status={order.get('payment_status')}")
        
        # 16. Upload test (tests python-multipart + pillow)
        if self.admin_token:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            # Create a minimal test image
            try:
                from PIL import Image
                import io
                img = Image.new('RGB', (100, 100), color='red')
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
                files = {'file': ('test.png', img_bytes, 'image/png')}
                success, resp = self.test("Upload image", "POST", "/admin/upload",
                                        200, files=files, headers=headers)
                if success:
                    print("   ✓ Image upload working (python-multipart + pillow)")
            except Exception as e:
                print(f"   ⚠ Upload test skipped: {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print(f"RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        print("=" * 60)
        
        return 0 if self.tests_passed == self.tests_run else 1

if __name__ == "__main__":
    runner = TestRunner()
    sys.exit(runner.run_all_tests())
