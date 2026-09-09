"""SQLAlchemy ORM models for MBG B2B E-Commerce + Mini ERP."""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    username: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20), default="customer", nullable=False)  # customer | admin | owner
    password_hash: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    orders: Mapped[list["Order"]] = relationship(back_populates="user")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    category_id: Mapped[str] = mapped_column(String(36), ForeignKey("categories.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")  # harga beli / modal
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default="kg")
    min_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    image_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    category: Mapped["Category"] = relationship(back_populates="products")
    stock_movements: Mapped[list["StockMovement"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class StockMovement(Base):
    """Riwayat mutasi stok (masuk / keluar / penyesuaian manual / pesanan)."""

    __tablename__ = "stock_movements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(20), nullable=False)  # in | out | adjust
    qty: Mapped[int] = mapped_column(Integer, nullable=False)  # positif = bertambah, negatif = berkurang
    stock_before: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_after: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    reference: Mapped[str | None] = mapped_column(String(120))  # mis. nomor pesanan
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")  # manual | order | cancel
    created_by: Mapped[str | None] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    product: Mapped["Product"] = relationship(back_populates="stock_movements")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    order_number: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    customer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    shipping_fee: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)  # cod | bank_transfer | qris | ewallet | piutang
    payment_channel: Mapped[str | None] = mapped_column(String(40))  # bca, bni, gopay, ovo, ...
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending|paid|failed|expired|cod|piutang
    order_status: Mapped[str] = mapped_column(String(20), nullable=False, default="baru")  # baru|diproses|dikirim|selesai|dibatalkan
    payment_ref: Mapped[str | None] = mapped_column(String(120))
    payment_payload: Mapped[dict | None] = mapped_column(JSONB)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan", lazy="selectin")
    transactions: Mapped[list["PaymentTransaction"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("products.id", ondelete="SET NULL"))
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(String(30), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    cost_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))  # snapshot modal saat pesanan dibuat
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")


class AuditLog(Base):
    """Jejak audit aktivitas akun admin/owner (dipantau oleh Owner)."""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    actor_id: Mapped[str | None] = mapped_column(String(36), index=True)
    actor_username: Mapped[str] = mapped_column(String(150), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(20), nullable=False)
    action: Mapped[str] = mapped_column(String(40), nullable=False, index=True)  # login|create|update|delete|stock_adjust|status|settle|sync
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)  # product|category|order|stock|auth|expense|settings
    entity_id: Mapped[str | None] = mapped_column(String(64))
    entity_label: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)  # midtrans | simulation | manual
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    channel: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(120))
    raw: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    order: Mapped["Order"] = relationship(back_populates="transactions")


class Expense(Base):
    """Pengeluaran operasional (ongkos angkut, listrik, gaji, dll) - mengurangi laba bersih."""

    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False, index=True)  # angkut|operasional|gaji|sewa|listrik_air|perlengkapan|lainnya
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False, default="cash")  # cash | transfer
    reference: Mapped[str | None] = mapped_column(String(160))  # mis. nama produk / no. nota
    note: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")  # manual | stock_in
    created_by: Mapped[str | None] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class StoreProfile(Base):
    """Identitas toko (singleton, id='default') - dikelola Owner di Pengaturan."""

    __tablename__ = "store_profile"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default="default")
    store_name: Mapped[str] = mapped_column(String(150), nullable=False, default="Semoyo Joyo")
    tagline: Mapped[str | None] = mapped_column(String(200), default="Solusi Belanja Terpercaya")
    owner_name: Mapped[str | None] = mapped_column(String(150))
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(30))
    whatsapp: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text)
    operating_hours: Mapped[str | None] = mapped_column(String(150))
    bank_name: Mapped[str | None] = mapped_column(String(60))
    bank_account: Mapped[str | None] = mapped_column(String(60))
    bank_holder: Mapped[str | None] = mapped_column(String(150))
    updated_by: Mapped[str | None] = mapped_column(String(150))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
