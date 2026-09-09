"""
Comprehensive backend API test for Semoyo Joyo B2B E-Commerce + Mini ERP
Tests: Piutang, Expenses, RBAC, Settings, Sync, Dashboard consistency
"""
import requests
import sys
from datetime import datetime, date

BASE_URL = "https://great-chaplygin-9.preview.emergentagent.com/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

class APITester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_token = None
        self.owner_token = None
        self.test_order_id = None
        self.test_expense_id = None
        self.test_product_id = None

    def log(self, msg, color=Colors.BLUE):
        print(f"{color}{msg}{Colors.END}")

    def test(self, name, method, endpoint, expected_status, data=None, token=None, params=None):
        """Run a single API test"""
        url = f"{BASE_URL}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        self.log(f"\n🔍 Test {self.tests_run}: {name}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASS - Status: {response.status_code}", Colors.GREEN)
                try:
                    return True, response.json() if response.text else {}
                except:
                    return True, {}
            else:
                self.log(f"❌ FAIL - Expected {expected_status}, got {response.status_code}", Colors.RED)
                try:
                    self.log(f"   Response: {response.text[:200]}", Colors.YELLOW)
                except:
                    pass
                return False, {}

        except Exception as e:
            self.log(f"❌ FAIL - Error: {str(e)}", Colors.RED)
            return False, {}

    def run_all_tests(self):
        self.log("=" * 80, Colors.BLUE)
        self.log("SEMOYO JOYO BACKEND API TEST SUITE", Colors.BLUE)
        self.log("=" * 80, Colors.BLUE)

        # 1. Health & Basic Endpoints
        self.log("\n" + "=" * 80, Colors.BLUE)
        self.log("1. HEALTH & BASIC ENDPOINTS", Colors.BLUE)
        self.log("=" * 80, Colors.BLUE)
        
        self.test("Health check", "GET", "/health", 200)
        success, home = self.test("Home page with products", "GET", "/home", 200)
        if success and home.get('categories'):
            self.log(f"   Found {len(home['categories'])} categories", Colors.GREEN)
        
        success, config = self.test("Payment config includes piutang", "GET", "/payments/config", 200)
        if success:
            methods = [m['key'] for m in config.get('methods', [])]
            if 'piutang' in methods:
                self.log(f"   ✓ Piutang method found in config", Colors.GREEN)
            else:
                self.log(f"   ✗ Piutang method NOT found", Colors.RED)
        
        success, profile = self.test("Store profile (public)", "GET", "/store/profile", 200)
        if success:
            if profile.get('bank_account') is None and profile.get('bank_name') is None:
                self.log(f"   ✓ Bank details are hidden (null)", Colors.GREEN)
            else:
                self.log(f"   ✗ Bank details should be null in public endpoint", Colors.RED)

        # 2. Admin & Owner Login
        self.log("\n" + "=" * 80, Colors.BLUE)
        self.log("2. AUTHENTICATION", Colors.BLUE)
        self.log("=" * 80, Colors.BLUE)
        
        success, admin_resp = self.test("Admin login", "POST", "/admin/login", 200, 
                                       {"username": "admin", "password": "admin123"})
        if success and admin_resp.get('access_token'):
            self.admin_token = admin_resp['access_token']
            self.log(f"   ✓ Admin token obtained", Colors.GREEN)
        
        success, owner_resp = self.test("Owner login", "POST", "/admin/login", 200,
                                       {"username": "owner", "password": "owner123"})
        if success and owner_resp.get('access_token'):
            self.owner_token = owner_resp['access_token']
            self.log(f"   ✓ Owner token obtained", Colors.GREEN)

        # 3. Piutang Flow
        self.log("\n" + "=" * 80, Colors.BLUE)
        self.log("3. PIUTANG (ACCOUNTS RECEIVABLE) FLOW", Colors.BLUE)
        self.log("=" * 80, Colors.BLUE)
        
        # Get a product for checkout
        if home and home.get('categories') and home['categories'][0].get('products'):
            product = home['categories'][0]['products'][0]
            self.test_product_id = product['id']
            
            # Checkout with piutang
            checkout_data = {
                "full_name": "Toko Uji Piutang",
                "phone": "081234567890",
                "address": "Jl. Test Piutang No. 1, Malang",
                "notes": "Test piutang order",
                "payment_method": "piutang",
                "payment_channel": None,
                "items": [{"product_id": product['id'], "qty": product['min_order']}]
            }
            success, checkout_resp = self.test("Checkout with piutang method", "POST", "/checkout", 200, checkout_data)
            
            if success and checkout_resp.get('order'):
                order = checkout_resp['order']
                self.test_order_id = order['id']
                order_number = order['order_number']
                
                # Verify order details
                if order['payment_status'] == 'piutang':
                    self.log(f"   ✓ Payment status is 'piutang'", Colors.GREEN)
                else:
                    self.log(f"   ✗ Payment status should be 'piutang', got '{order['payment_status']}'", Colors.RED)
                
                if order['order_number'].startswith('SJ-'):
                    self.log(f"   ✓ Order number has SJ- prefix: {order_number}", Colors.GREEN)
                else:
                    self.log(f"   ✗ Order number should start with SJ-", Colors.RED)
                
                # Check payment instructions
                payment_info = checkout_resp.get('payment', {})
                instructions = payment_info.get('instructions', {})
                if 'piutang' in str(instructions).lower():
                    self.log(f"   ✓ Payment instructions mention 'piutang'", Colors.GREEN)
                
                # Try to simulate payment on piutang order (should fail)
                self.test("Simulate payment on piutang order (should fail)", "POST", 
                         f"/payments/{order_number}/simulate", 400)
                
                # Get receivables list
                success, receivables = self.test("Get receivables list", "GET", "/admin/receivables", 
                                                200, token=self.admin_token)
                if success:
                    if receivables.get('total', 0) > 0:
                        self.log(f"   ✓ Receivables total: Rp {receivables['total']:,.0f}", Colors.GREEN)
                    if receivables.get('count', 0) >= 1:
                        self.log(f"   ✓ Receivables count: {receivables['count']}", Colors.GREEN)
                    
                    # Check by_customer
                    by_customer = receivables.get('by_customer', [])
                    if by_customer:
                        customer = by_customer[0]
                        self.log(f"   ✓ Customer with receivable: {customer.get('customer_name')}", Colors.GREEN)
                
                # Settle the piutang order
                settle_data = {"method": "transfer", "note": "Test settlement"}
                success, settled = self.test("Settle piutang order", "POST", 
                                            f"/admin/orders/{self.test_order_id}/settle", 
                                            200, settle_data, token=self.admin_token)
                
                if success and settled.get('payment_status') == 'paid':
                    self.log(f"   ✓ Order marked as paid", Colors.GREEN)
                    if settled.get('paid_at'):
                        self.log(f"   ✓ paid_at timestamp set", Colors.GREEN)
                    if settled.get('order_status') == 'diproses':
                        self.log(f"   ✓ Order status changed to 'diproses'", Colors.GREEN)
                
                # Try to settle again (should fail)
                self.test("Settle already paid order (should fail)", "POST",
                         f"/admin/orders/{self.test_order_id}/settle", 400, 
                         settle_data, token=self.admin_token)
                
                # Check receivables decreased
                success, receivables_after = self.test("Get receivables after settlement", "GET", 
                                                      "/admin/receivables", 200, token=self.admin_token)
                if success and receivables:
                    if receivables_after.get('count', 0) < receivables.get('count', 0):
                        self.log(f"   ✓ Receivables count decreased", Colors.GREEN)
                    if receivables_after.get('settled_total', 0) > 0:
                        self.log(f"   ✓ Settled total increased: Rp {receivables_after['settled_total']:,.0f}", Colors.GREEN)

        # 4. Expenses Module
        self.log("\n" + "=" * 80, Colors.BLUE)
        self.log("4. EXPENSES MODULE", Colors.BLUE)
        self.log("=" * 80, Colors.BLUE)
        
        # Get expense categories
        success, categories = self.test("Get expense categories", "GET", "/admin/expenses/categories", 
                                       200, token=self.admin_token)
        if success and len(categories) == 8:
            self.log(f"   ✓ Found 8 expense categories", Colors.GREEN)
        
        # Create expense
        today_str = date.today().isoformat()
        expense_data = {
            "expense_date": today_str,
            "category": "angkut",
            "description": "Ongkos angkut test",
            "amount": 150000,
            "payment_method": "cash",
            "reference": "TEST-001",
            "note": "Test expense"
        }
        success, expense = self.test("Create expense", "POST", "/admin/expenses", 201, 
                                     expense_data, token=self.admin_token)
        if success and expense.get('id'):
            self.test_expense_id = expense['id']
            self.log(f"   ✓ Expense created with ID: {self.test_expense_id}", Colors.GREEN)
        
        # Get expenses list
        success, expenses_list = self.test("Get expenses list", "GET", "/admin/expenses", 200,
                                          token=self.admin_token, params={"start": today_str, "end": today_str})
        if success:
            if expenses_list.get('total', 0) >= 150000:
                self.log(f"   ✓ Total expenses: Rp {expenses_list['total']:,.0f}", Colors.GREEN)
            if expenses_list.get('count', 0) >= 1:
                self.log(f"   ✓ Expense count: {expenses_list['count']}", Colors.GREEN)
            
            by_category = expenses_list.get('by_category', [])
            angkut_cat = next((c for c in by_category if c['category'] == 'angkut'), None)
            if angkut_cat:
                self.log(f"   ✓ Angkut category total: Rp {angkut_cat['total']:,.0f}", Colors.GREEN)
        
        # Update expense
        if self.test_expense_id:
            update_data = {**expense_data, "amount": 175000}
            self.test("Update expense", "PUT", f"/admin/expenses/{self.test_expense_id}", 
                     200, update_data, token=self.admin_token)
        
        # Validation tests
        invalid_expense = {**expense_data, "amount": 0}
        self.test("Create expense with amount 0 (should fail)", "POST", "/admin/expenses", 
                 422, invalid_expense, token=self.admin_token)
        
        future_date = "2027-12-31"
        future_expense = {**expense_data, "expense_date": future_date}
        self.test("Create expense with future date (should fail)", "POST", "/admin/expenses",
                 400, future_expense, token=self.admin_token)
        
        # Delete by admin (should fail)
        if self.test_expense_id:
            self.test("Delete expense as admin (should fail)", "DELETE", 
                     f"/admin/expenses/{self.test_expense_id}", 403, token=self.admin_token)
            
            # Delete by owner (should succeed)
            self.test("Delete expense as owner", "DELETE", 
                     f"/admin/expenses/{self.test_expense_id}", 200, token=self.owner_token)

        # 5. Stock-in with Expense
        self.log("\n" + "=" * 80, Colors.BLUE)
        self.log("5. STOCK-IN WITH EXPENSE", Colors.BLUE)
        self.log("=" * 80, Colors.BLUE)
        
        if self.test_product_id:
            # Get current stock
            success, stock_before = self.test("Get stock summary before", "GET", "/admin/stock",
                                             200, token=self.admin_token)
            
            # Add stock with expense
            stock_adjust_data = {
                "movement_type": "in",
                "qty": 5,
                "note": "Test restock with shipping cost",
                "expense_amount": 50000,
                "expense_description": "Ongkos angkut restock test"
            }
            success, stock_result = self.test("Add stock with expense", "POST",
                                             f"/admin/stock/{self.test_product_id}/adjust",
                                             200, stock_adjust_data, token=self.admin_token)
            
            if success:
                self.log(f"   ✓ Stock increased by 5", Colors.GREEN)
                
                # Check if expense was created
                success, expenses_check = self.test("Check expenses after stock-in", "GET",
                                                   "/admin/expenses", 200, token=self.admin_token,
                                                   params={"start": today_str, "end": today_str})
                
                if success:
                    items = expenses_check.get('items', [])
                    stock_expense = next((e for e in items if e.get('source') == 'stock_in' and 
                                        e.get('category') == 'angkut'), None)
                    if stock_expense:
                        self.log(f"   ✓ Expense auto-created from stock-in: Rp {stock_expense['amount']:,.0f}", Colors.GREEN)
                    else:
                        self.log(f"   ✗ Stock-in expense not found", Colors.RED)

        # 6. RBAC Tests
        self.log("\n" + "=" * 80, Colors.BLUE)
        self.log("6. RBAC (ROLE-BASED ACCESS CONTROL)", Colors.BLUE)
        self.log("=" * 80, Colors.BLUE)
        
        # Admin trying to access owner-only endpoints (should fail)
        self.test("Admin access to staff settings (should fail)", "GET", "/admin/settings/staff",
                 403, token=self.admin_token)
        self.test("Admin access to customers analytics (should fail)", "GET", "/admin/settings/customers",
                 403, token=self.admin_token)
        self.test("Admin access to sync (should fail)", "POST", "/admin/settings/sync",
                 403, token=self.admin_token)
        self.test("Admin access to store settings (should fail)", "GET", "/admin/settings/store",
                 403, token=self.admin_token)
        self.test("Admin access to sales reports (should fail)", "GET", "/admin/reports/sales",
                 403, token=self.admin_token)
        self.test("Admin access to audit logs (should fail)", "GET", "/admin/audit-logs",
                 403, token=self.admin_token)
        
        # Owner accessing same endpoints (should succeed)
        self.test("Owner access to staff settings", "GET", "/admin/settings/staff",
                 200, token=self.owner_token)
        self.test("Owner access to customers analytics", "GET", "/admin/settings/customers",
                 200, token=self.owner_token)
        self.test("Owner access to store settings", "GET", "/admin/settings/store",
                 200, token=self.owner_token)
        self.test("Owner access to sales reports", "GET", "/admin/reports/sales",
                 200, token=self.owner_token, params={"start": "2026-01-01", "end": "2026-12-31"})
        self.test("Owner access to audit logs", "GET", "/admin/audit-logs",
                 200, token=self.owner_token)

        # 7. Settings - Staff Management
        self.log("\n" + "=" * 80, Colors.BLUE)
        self.log("7. SETTINGS - STAFF MANAGEMENT", Colors.BLUE)
        self.log("=" * 80, Colors.BLUE)
        
        success, staff_list = self.test("Get staff list", "GET", "/admin/settings/staff",
                                       200, token=self.owner_token)
        if success:
            staff_count = len(staff_list)
            self.log(f"   ✓ Found {staff_count} staff members", Colors.GREEN)
            admin_user = next((u for u in staff_list if u['role'] == 'admin'), None)
            owner_user = next((u for u in staff_list if u['role'] == 'owner'), None)
            
            if admin_user and owner_user:
                self.log(f"   ✓ Admin and Owner accounts found", Colors.GREEN)
                
                # Try to update admin credentials with wrong owner password
                wrong_pw_data = {
                    "owner_password": "wrongpassword",
                    "full_name": "Test Update"
                }
                self.test("Update staff with wrong owner password (should fail)", "PUT",
                         f"/admin/settings/staff/{admin_user['id']}/credentials",
                         403, wrong_pw_data, token=self.owner_token)
                
                # Update admin full_name only (will revert later)
                update_name_data = {
                    "owner_password": "owner123",
                    "full_name": "Administrator Toko"
                }
                success, updated = self.test("Update admin full_name", "PUT",
                                            f"/admin/settings/staff/{admin_user['id']}/credentials",
                                            200, update_name_data, token=self.owner_token)
                
                if success and updated.get('full_name') == "Administrator Toko":
                    self.log(f"   ✓ Admin name updated", Colors.GREEN)
                    
                    # Revert the name
                    revert_data = {
                        "owner_password": "owner123",
                        "full_name": "Administrator"
                    }
                    self.test("Revert admin full_name", "PUT",
                             f"/admin/settings/staff/{admin_user['id']}/credentials",
                             200, revert_data, token=self.owner_token)
                
                # Try username that's already taken
                taken_username_data = {
                    "owner_password": "owner123",
                    "username": "owner"
                }
                self.test("Update to taken username (should fail)", "PUT",
                         f"/admin/settings/staff/{admin_user['id']}/credentials",
                         400, taken_username_data, token=self.owner_token)
                
                # Create new admin
                new_admin_data = {
                    "owner_password": "owner123",
                    "username": "stafuji",
                    "password": "stafuji123",
                    "full_name": "Staf Uji"
                }
                success, new_admin = self.test("Create new admin", "POST", "/admin/settings/staff",
                                              201, new_admin_data, token=self.owner_token)
                
                if success and new_admin.get('id'):
                    new_admin_id = new_admin['id']
                    self.log(f"   ✓ New admin created: {new_admin['username']}", Colors.GREEN)
                    
                    # Delete the new admin
                    self.test("Delete new admin", "DELETE", f"/admin/settings/staff/{new_admin_id}",
                             200, token=self.owner_token)
                
                # Try to delete owner (should fail)
                self.test("Delete owner account (should fail)", "DELETE",
                         f"/admin/settings/staff/{owner_user['id']}", 400, token=self.owner_token)

        # 8. Settings - Store Profile
        self.log("\n" + "=" * 80, Colors.BLUE)
        self.log("8. SETTINGS - STORE PROFILE", Colors.BLUE)
        self.log("=" * 80, Colors.BLUE)
        
        store_data = {
            "store_name": "Semoyo Joyo",
            "tagline": "Solusi Belanja Terpercaya",
            "address": "Jl. Raya Semoyo 1",
            "city": "Malang",
            "phone": "0341123456",
            "whatsapp": "08123456789",
            "email": "halo@semoyojoyo.id",
            "bank_name": "BCA",
            "bank_account": "1234567890",
            "bank_holder": "Owner Semoyo"
        }
        success, store_updated = self.test("Update store profile", "PUT", "/admin/settings/store",
                                          200, store_data, token=self.owner_token)
        
        if success:
            self.log(f"   ✓ Store profile updated", Colors.GREEN)
            
            # Verify public endpoint doesn't expose bank details
            success, public_profile = self.test("Get public store profile", "GET", "/store/profile", 200)
            if success:
                if public_profile.get('address') == "Jl. Raya Semoyo 1":
                    self.log(f"   ✓ Public address visible", Colors.GREEN)
                if public_profile.get('phone') == "0341123456":
                    self.log(f"   ✓ Public phone visible", Colors.GREEN)
                if public_profile.get('bank_account') is None:
                    self.log(f"   ✓ Bank account hidden in public endpoint", Colors.GREEN)
                else:
                    self.log(f"   ✗ Bank account should be null in public endpoint", Colors.RED)

        # 9. Settings - Customers Analytics
        self.log("\n" + "=" * 80, Colors.BLUE)
        self.log("9. SETTINGS - CUSTOMERS ANALYTICS", Colors.BLUE)
        self.log("=" * 80, Colors.BLUE)
        
        success, customers = self.test("Get customers analytics", "GET", "/admin/settings/customers",
                                      200, token=self.owner_token)
        if success:
            self.log(f"   ✓ Total customers: {customers.get('total_customers', 0)}", Colors.GREEN)
            self.log(f"   ✓ Regular customers: {customers.get('regular_customers', 0)}", Colors.GREEN)
            self.log(f"   ✓ New this month: {customers.get('new_this_month', 0)}", Colors.GREEN)
            self.log(f"   ✓ With receivables: {customers.get('with_receivables', 0)}", Colors.GREEN)
            
            customer_list = customers.get('customers', [])
            if customer_list:
                sample = customer_list[0]
                required_fields = ['order_count', 'total_spent', 'receivable_total', 'segment']
                if all(field in sample for field in required_fields):
                    self.log(f"   ✓ Customer data has all required fields", Colors.GREEN)
                    if sample['segment'] in ['tetap', 'aktif', 'baru', 'pasif']:
                        self.log(f"   ✓ Valid segment: {sample['segment']}", Colors.GREEN)

        # 10. Settings - Data Sync
        self.log("\n" + "=" * 80, Colors.BLUE)
        self.log("10. SETTINGS - DATA SYNCHRONIZATION", Colors.BLUE)
        self.log("=" * 80, Colors.BLUE)
        
        success, sync_result = self.test("Run data sync", "POST", "/admin/settings/sync",
                                        200, {}, token=self.owner_token)
        
        if success:
            self.log(f"   ✓ Sync completed in {sync_result.get('duration_ms', 0)} ms", Colors.GREEN)
            self.log(f"   ✓ Total checked: {sync_result.get('total_checked', 0)}", Colors.GREEN)
            self.log(f"   ✓ Total fixed: {sync_result.get('total_fixed', 0)}", Colors.GREEN)
            self.log(f"   ✓ Total warnings: {sync_result.get('total_warnings', 0)}", Colors.GREEN)
            
            checks = sync_result.get('checks', [])
            if len(checks) == 6:
                self.log(f"   ✓ All 6 checks present", Colors.GREEN)
                check_keys = [c['key'] for c in checks]
                expected_keys = ['order_items', 'orders', 'products', 'expenses', 'customers', 'receivables']
                if all(k in check_keys for k in expected_keys):
                    self.log(f"   ✓ All expected check keys present", Colors.GREEN)
            
            snapshot = sync_result.get('snapshot', {})
            if snapshot:
                self.log(f"   ✓ Snapshot - Sales revenue: Rp {snapshot.get('sales_revenue', 0):,.0f}", Colors.GREEN)
                self.log(f"   ✓ Snapshot - Total expenses: Rp {snapshot.get('total_expenses', 0):,.0f}", Colors.GREEN)
                self.log(f"   ✓ Snapshot - Net profit: Rp {snapshot.get('net_profit', 0):,.0f}", Colors.GREEN)
                self.log(f"   ✓ Snapshot - Receivables: Rp {snapshot.get('receivables_total', 0):,.0f}", Colors.GREEN)
        
        # Run sync again (should be safe, no changes)
        success, sync_result2 = self.test("Run data sync again (idempotent)", "POST", "/admin/settings/sync",
                                         200, {}, token=self.owner_token)
        if success and sync_result2.get('total_fixed', 0) == 0:
            self.log(f"   ✓ Second sync made no changes (idempotent)", Colors.GREEN)
        
        # Get last sync result
        success, last_sync = self.test("Get last sync result", "GET", "/admin/settings/sync/last",
                                      200, token=self.owner_token)
        if success and last_sync:
            self.log(f"   ✓ Last sync result retrieved", Colors.GREEN)

        # 11. Dashboard Consistency
        self.log("\n" + "=" * 80, Colors.BLUE)
        self.log("11. DASHBOARD & REPORTS CONSISTENCY", Colors.BLUE)
        self.log("=" * 80, Colors.BLUE)
        
        # Owner dashboard
        success, owner_dash = self.test("Owner dashboard", "GET", "/admin/dashboard",
                                       200, token=self.owner_token)
        if success:
            required_fields = ['total_expenses', 'expenses_month', 'net_profit', 'revenue_paid',
                             'receivables_total', 'receivables_count']
            if all(field in owner_dash for field in required_fields):
                self.log(f"   ✓ Owner dashboard has all finance fields", Colors.GREEN)
                self.log(f"   ✓ Revenue paid: Rp {owner_dash['revenue_paid']:,.0f}", Colors.GREEN)
                self.log(f"   ✓ Total expenses: Rp {owner_dash['total_expenses']:,.0f}", Colors.GREEN)
                self.log(f"   ✓ Net profit: Rp {owner_dash['net_profit']:,.0f}", Colors.GREEN)
                self.log(f"   ✓ Receivables: Rp {owner_dash['receivables_total']:,.0f} ({owner_dash['receivables_count']} orders)", Colors.GREEN)
        
        # Admin dashboard (should have limited finance data)
        success, admin_dash = self.test("Admin dashboard", "GET", "/admin/dashboard",
                                       200, token=self.admin_token)
        if success:
            if admin_dash.get('cost_paid', 0) == 0 and admin_dash.get('gross_profit', 0) == 0:
                self.log(f"   ✓ Admin dashboard hides cost/profit data", Colors.GREEN)
            if admin_dash.get('total_expenses', 0) == 0 and admin_dash.get('net_profit', 0) == 0:
                self.log(f"   ✓ Admin dashboard hides expense/net profit data", Colors.GREEN)
            if len(admin_dash.get('profit_by_product', [])) == 0:
                self.log(f"   ✓ Admin dashboard hides profit by product", Colors.GREEN)
        
        # Sales report
        success, report = self.test("Sales report", "GET", "/admin/reports/sales",
                                   200, token=self.owner_token,
                                   params={"start": "2026-01-01", "end": "2026-12-31"})
        if success:
            summary = report.get('summary', {})
            if 'total_expenses' in summary and 'net_profit_after_expenses' in summary:
                self.log(f"   ✓ Report includes expenses and net profit", Colors.GREEN)
                self.log(f"   ✓ Report total expenses: Rp {summary['total_expenses']:,.0f}", Colors.GREEN)
                self.log(f"   ✓ Report net profit: Rp {summary['net_profit_after_expenses']:,.0f}", Colors.GREEN)
        
        # Export endpoints
        self.test("Export Excel", "GET", "/admin/reports/sales/export.xlsx",
                 200, token=self.owner_token, params={"start": "2026-01-01", "end": "2026-12-31"})
        self.test("Export PDF", "GET", "/admin/reports/sales/export.pdf",
                 200, token=self.owner_token, params={"start": "2026-01-01", "end": "2026-12-31"})

        # 12. Verify credentials still work
        self.log("\n" + "=" * 80, Colors.BLUE)
        self.log("12. VERIFY CREDENTIALS STILL WORK", Colors.BLUE)
        self.log("=" * 80, Colors.BLUE)
        
        self.test("Admin login still works", "POST", "/admin/login", 200,
                 {"username": "admin", "password": "admin123"})
        self.test("Owner login still works", "POST", "/admin/login", 200,
                 {"username": "owner", "password": "owner123"})

        # Final Summary
        self.log("\n" + "=" * 80, Colors.BLUE)
        self.log("TEST SUMMARY", Colors.BLUE)
        self.log("=" * 80, Colors.BLUE)
        
        pass_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        self.log(f"\n📊 Tests Run: {self.tests_run}", Colors.BLUE)
        self.log(f"✅ Tests Passed: {self.tests_passed}", Colors.GREEN)
        self.log(f"❌ Tests Failed: {self.tests_run - self.tests_passed}", Colors.RED)
        self.log(f"📈 Pass Rate: {pass_rate:.1f}%\n", Colors.BLUE)
        
        return 0 if self.tests_passed == self.tests_run else 1

def main():
    tester = APITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
