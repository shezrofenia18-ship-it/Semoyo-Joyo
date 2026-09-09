"""Pydantic schemas (request/response) for the API."""
from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

PaymentMethod = Literal["cod", "bank_transfer", "qris", "ewallet", "piutang"]
OrderStatus = Literal["baru", "diproses", "dikirim", "selesai", "dibatalkan"]
PaymentStatus = Literal["pending", "paid", "failed", "expired", "cod", "piutang"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Catalog ----------
class CategoryOut(ORMModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    product_count: int = 0


class ProductOut(ORMModel):
    id: str
    category_id: str
    category_name: Optional[str] = None
    name: str
    slug: str
    description: Optional[str] = None
    price: float
    cost_price: float = 0
    profit_per_unit: float = 0
    margin_pct: float = 0
    unit: str
    min_order: int
    stock: int
    image_url: Optional[str] = None
    is_active: bool = True


class CategoryWithProducts(CategoryOut):
    products: list[ProductOut] = []


class HomeOut(BaseModel):
    categories: list[CategoryWithProducts]
    total_products: int


# ---------- Auth ----------
class CustomerLoginIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    phone: str = Field(min_length=6, max_length=30)


class UserOut(ORMModel):
    id: str
    full_name: str
    username: str
    phone: Optional[str] = None
    address: Optional[str] = None
    role: str
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class AdminLoginIn(BaseModel):
    username: str
    password: str


# ---------- Checkout / Orders ----------
class CheckoutItemIn(BaseModel):
    product_id: str
    qty: int = Field(gt=0)


class CheckoutIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    phone: str = Field(min_length=6, max_length=30)
    address: str = Field(min_length=5)
    notes: Optional[str] = None
    payment_method: PaymentMethod
    payment_channel: Optional[str] = None  # bca/bni/bri/mandiri/permata | gopay/ovo/dana/shopeepay
    items: list[CheckoutItemIn] = Field(min_length=1)

    @field_validator("full_name", "address")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()


class OrderItemOut(ORMModel):
    id: str
    product_id: Optional[str] = None
    product_name: str
    image_url: Optional[str] = None
    unit: str
    price: float
    cost_price: Optional[float] = None
    qty: int
    subtotal: float


class OrderOut(ORMModel):
    id: str
    order_number: str
    user_id: str
    customer_name: str
    phone: str
    address: str
    notes: Optional[str] = None
    subtotal: float
    shipping_fee: float
    total: float
    payment_method: str
    payment_channel: Optional[str] = None
    payment_status: str
    order_status: str
    payment_ref: Optional[str] = None
    payment_payload: Optional[dict[str, Any]] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemOut] = []


class CheckoutOut(BaseModel):
    order: OrderOut
    access_token: str
    user: UserOut
    payment: dict[str, Any]


# ---------- Payments ----------
class PaymentCreateIn(BaseModel):
    payment_method: Optional[PaymentMethod] = None
    payment_channel: Optional[str] = None


class PaymentInstructionOut(BaseModel):
    order_number: str
    payment_method: str
    payment_channel: Optional[str] = None
    payment_status: str
    amount: float
    provider: str  # midtrans | simulation | manual
    simulation: bool
    instructions: dict[str, Any]


# ---------- Admin ----------
class CategoryIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class ProductIn(BaseModel):
    category_id: str
    name: str = Field(min_length=2, max_length=200)
    description: Optional[str] = None
    price: float = Field(ge=0)
    cost_price: float = Field(ge=0, default=0)
    unit: str = Field(min_length=1, max_length=30)
    min_order: int = Field(ge=1, default=1)
    stock: int = Field(ge=0, default=0)
    image_url: Optional[str] = None
    is_active: bool = True


class OrderStatusUpdateIn(BaseModel):
    order_status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None


class OrderUpdateIn(BaseModel):
    """Edit data pesanan oleh admin (pelanggan, alamat, catatan, status)."""
    customer_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    phone: Optional[str] = Field(default=None, min_length=6, max_length=30)
    address: Optional[str] = Field(default=None, min_length=5)
    notes: Optional[str] = None
    shipping_fee: Optional[float] = Field(default=None, ge=0)
    order_status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None


class SettleIn(BaseModel):
    """Pelunasan piutang / pembayaran manual oleh admin."""
    method: Literal["cash", "transfer", "qris", "ewallet", "lainnya"] = "cash"
    note: Optional[str] = None
    paid_at: Optional[datetime] = None


class ReceivableCustomerOut(BaseModel):
    user_id: Optional[str] = None
    customer_name: str
    phone: str
    orders: int
    total: float
    oldest_at: datetime


class ReceivablesOut(BaseModel):
    total: float
    count: int
    overdue_count: int  # > 14 hari
    settled_total: float  # piutang yang sudah dilunasi (histori)
    settled_count: int
    by_customer: list[ReceivableCustomerOut]
    orders: list[OrderOut]


# ---------- Stok ----------
StockMovementType = Literal["in", "out", "adjust"]


class StockAdjustIn(BaseModel):
    movement_type: StockMovementType
    qty: int = Field(ge=0, description="in/out: jumlah; adjust: nilai stok baru")
    note: Optional[str] = None
    expense_amount: Optional[float] = Field(default=None, ge=0, description="Biaya angkut/ongkos saat stok masuk (dicatat sebagai pengeluaran)")
    expense_description: Optional[str] = None


class StockMovementOut(ORMModel):
    id: str
    product_id: str
    product_name: str
    movement_type: str
    qty: int
    stock_before: int
    stock_after: int
    note: Optional[str] = None
    reference: Optional[str] = None
    source: str
    created_by: Optional[str] = None
    created_at: datetime


class StockItemOut(BaseModel):
    id: str
    name: str
    slug: str
    category_id: str
    category_name: Optional[str] = None
    unit: str
    min_order: int
    stock: int
    price: float
    cost_price: float
    stock_value: float  # stok x harga beli
    status: str  # habis | menipis | aman
    is_active: bool
    image_url: Optional[str] = None
    last_movement_at: Optional[datetime] = None


class StockSummaryOut(BaseModel):
    total_products: int
    total_units: int
    total_stock_value: float
    out_of_stock: int
    low_stock: int
    items: list[StockItemOut]


class AuditLogOut(ORMModel):
    id: str
    actor_id: Optional[str] = None
    actor_username: str
    actor_role: str
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    entity_label: Optional[str] = None
    description: str
    meta: Optional[dict[str, Any]] = None
    created_at: datetime


class ProductProfitOut(BaseModel):
    product_id: Optional[str] = None
    product_name: str
    qty_sold: int
    revenue: float
    cost: float
    profit: float
    margin_pct: float


class DashboardOut(BaseModel):
    total_orders: int
    orders_today: int
    pending_payments: int
    revenue_paid: float
    total_products: int
    total_categories: int
    total_customers: int
    low_stock_products: int
    # Piutang (semua staf boleh lihat - untuk penagihan)
    receivables_total: float = 0
    receivables_count: int = 0
    # Keuangan (hanya pesanan lunas / COD selesai / piutang selesai) - Owner
    cost_paid: float = 0
    gross_profit: float = 0
    margin_pct: float = 0
    stock_value: float = 0
    total_expenses: float = 0
    expenses_month: float = 0
    net_profit: float = 0
    profit_by_product: list[ProductProfitOut] = []
    recent_orders: list[OrderOut]
    status_breakdown: dict[str, int]


# ---------- Pengeluaran ----------
ExpenseCategory = Literal["angkut", "operasional", "gaji", "sewa", "listrik_air", "perlengkapan", "pembelian", "lainnya"]


class ExpenseIn(BaseModel):
    expense_date: date
    category: ExpenseCategory = "operasional"
    description: str = Field(min_length=2, max_length=255)
    amount: float = Field(gt=0)
    payment_method: Literal["cash", "transfer"] = "cash"
    reference: Optional[str] = Field(default=None, max_length=160)
    note: Optional[str] = None


class ExpenseOut(ORMModel):
    id: str
    expense_date: date
    category: str
    description: str
    amount: float
    payment_method: str
    reference: Optional[str] = None
    note: Optional[str] = None
    source: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ExpenseCategoryTotal(BaseModel):
    category: str
    total: float
    count: int


class ExpenseSummaryOut(BaseModel):
    start_date: date
    end_date: date
    total: float
    count: int
    by_category: list[ExpenseCategoryTotal]
    items: list[ExpenseOut]


# ---------- Pengaturan (Owner) ----------
class StaffCredentialsIn(BaseModel):
    """Ubah username dan/atau password akun staf. Wajib konfirmasi password owner yang sedang login."""
    owner_password: str = Field(min_length=1)
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    password: Optional[str] = Field(default=None, min_length=6, max_length=100)
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=150)


class StaffCreateIn(BaseModel):
    owner_password: str = Field(min_length=1)
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    full_name: str = Field(min_length=2, max_length=150)


class StoreProfileIn(BaseModel):
    store_name: str = Field(min_length=2, max_length=150)
    tagline: Optional[str] = Field(default=None, max_length=200)
    owner_name: Optional[str] = Field(default=None, max_length=150)
    address: Optional[str] = None
    city: Optional[str] = Field(default=None, max_length=120)
    phone: Optional[str] = Field(default=None, max_length=30)
    whatsapp: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=150)
    description: Optional[str] = None
    operating_hours: Optional[str] = Field(default=None, max_length=150)
    bank_name: Optional[str] = Field(default=None, max_length=60)
    bank_account: Optional[str] = Field(default=None, max_length=60)
    bank_holder: Optional[str] = Field(default=None, max_length=150)


class StoreProfileOut(ORMModel):
    store_name: str
    tagline: Optional[str] = None
    owner_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None
    operating_hours: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_holder: Optional[str] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None


class CustomerAnalyticsOut(BaseModel):
    id: str
    full_name: str
    username: str
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime
    order_count: int
    paid_orders: int
    total_spent: float  # dari pesanan terjual
    total_all_orders: float  # semua pesanan tidak dibatalkan
    receivable_total: float
    receivable_count: int
    first_order_at: Optional[datetime] = None
    last_order_at: Optional[datetime] = None
    avg_order_value: float
    segment: str  # tetap | aktif | baru | pasif


class CustomersAnalyticsSummary(BaseModel):
    total_customers: int
    regular_customers: int
    new_this_month: int
    with_receivables: int
    customers: list[CustomerAnalyticsOut]


class SyncCheck(BaseModel):
    key: str
    label: str
    checked: int
    fixed: int
    warnings: list[str] = []
    status: str  # ok | fixed | warning


class SyncResultOut(BaseModel):
    ran_at: datetime
    duration_ms: int
    total_checked: int
    total_fixed: int
    total_warnings: int
    checks: list[SyncCheck]
    snapshot: dict[str, Any]
