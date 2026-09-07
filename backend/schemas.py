"""Pydantic schemas (request/response) for the API."""
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

PaymentMethod = Literal["cod", "bank_transfer", "qris", "ewallet"]
OrderStatus = Literal["baru", "diproses", "dikirim", "selesai", "dibatalkan"]
PaymentStatus = Literal["pending", "paid", "failed", "expired", "cod"]


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
    unit: str = Field(min_length=1, max_length=30)
    min_order: int = Field(ge=1, default=1)
    stock: int = Field(ge=0, default=0)
    image_url: Optional[str] = None
    is_active: bool = True


class OrderStatusUpdateIn(BaseModel):
    order_status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None


class DashboardOut(BaseModel):
    total_orders: int
    orders_today: int
    pending_payments: int
    revenue_paid: float
    total_products: int
    total_categories: int
    total_customers: int
    low_stock_products: int
    recent_orders: list[OrderOut]
    status_breakdown: dict[str, int]
