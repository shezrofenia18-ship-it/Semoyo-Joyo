"""Public catalog endpoints: categories, products, home."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Category, Product
from schemas import CategoryOut, CategoryWithProducts, HomeOut, ProductOut

router = APIRouter(tags=["catalog"])


def product_out(p: Product, category_name: Optional[str] = None, include_cost: bool = False) -> ProductOut:
    """Serialize product. Harga beli/laba hanya disertakan untuk admin (include_cost=True)."""
    price = float(p.price)
    cost = float(p.cost_price or 0) if include_cost else 0.0
    profit = price - cost if include_cost else 0.0
    margin = round((profit / price) * 100, 1) if include_cost and price > 0 else 0.0
    return ProductOut(
        id=p.id, category_id=p.category_id, category_name=category_name, name=p.name, slug=p.slug,
        description=p.description, price=price, cost_price=cost, profit_per_unit=profit, margin_pct=margin,
        unit=p.unit, min_order=p.min_order, stock=p.stock, image_url=p.image_url, is_active=p.is_active,
    )


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Category, func.count(Product.id))
        .outerjoin(Product, (Product.category_id == Category.id) & (Product.is_active.is_(True)))
        .where(Category.is_active.is_(True))
        .group_by(Category.id)
        .order_by(Category.sort_order, Category.name)
    )
    rows = (await db.execute(stmt)).all()
    out = []
    for cat, cnt in rows:
        c = CategoryOut.model_validate(cat)
        c.product_count = cnt
        out.append(c)
    return out


@router.get("/products", response_model=list[ProductOut])
async def list_products(
    category: Optional[str] = Query(default=None, description="category id or slug"),
    q: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Product, Category.name).join(Category).where(Product.is_active.is_(True), Category.is_active.is_(True))
    if category:
        stmt = stmt.where((Category.id == category) | (Category.slug == category))
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q.strip()}%"))
    stmt = stmt.order_by(Category.sort_order, Product.name)
    rows = (await db.execute(stmt)).all()
    return [product_out(p, cname) for p, cname in rows]


@router.get("/products/{product_id}", response_model=ProductOut)
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(Product, Category.name).join(Category).where((Product.id == product_id) | (Product.slug == product_id)))).first()
    if not row:
        raise HTTPException(404, "Produk tidak ditemukan")
    return product_out(row[0], row[1])


@router.get("/home", response_model=HomeOut)
async def home(q: Optional[str] = Query(default=None), db: AsyncSession = Depends(get_db)):
    """Beranda: semua kategori aktif beserta produk aktifnya (terkelompok)."""
    cats = (await db.execute(select(Category).where(Category.is_active.is_(True)).order_by(Category.sort_order, Category.name))).scalars().all()
    stmt = select(Product).where(Product.is_active.is_(True)).order_by(Product.name)
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q.strip()}%"))
    prods = (await db.execute(stmt)).scalars().all()
    by_cat: dict[str, list[ProductOut]] = {}
    for p in prods:
        by_cat.setdefault(p.category_id, []).append(product_out(p))
    out = []
    for c in cats:
        items = by_cat.get(c.id, [])
        if q and not items:
            continue
        out.append(CategoryWithProducts(
            id=c.id, name=c.name, slug=c.slug, description=c.description, image_url=c.image_url,
            sort_order=c.sort_order, is_active=c.is_active, product_count=len(items), products=items,
        ))
    return HomeOut(categories=out, total_products=len(prods))
