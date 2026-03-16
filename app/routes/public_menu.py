from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.branch import Branch
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_image import ProductImage
from app.models.product_stock import ProductStock
from app.schemas.public_menu import (
    PublicMenuCategoryOut,
    PublicMenuOut,
    PublicMenuProductOut,
    PublicOrderCreate,
    PublicOrderCreatedOut,
)

router = APIRouter()


def _extract_effective_host(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-host")
    host = (forwarded or request.headers.get("host") or "").strip().lower()
    if not host:
        return host
    # Some proxies send a comma-separated list. Use the first value.
    if "," in host:
        host = host.split(",", 1)[0].strip()
    # remove port if present
    if ":" in host:
        host = host.split(":", 1)[0]
    return host


def _resolve_branch_from_request(db: Session, request: Request) -> Branch:
    host = _extract_effective_host(request)
    if not host:
        raise HTTPException(status_code=400, detail="Host inválido")

    # Prefer custom domain mapping
    branch = db.scalar(select(Branch).where(Branch.public_menu_custom_domain == host))
    if branch:
        if not branch.public_menu_enabled:
            raise HTTPException(status_code=404, detail="Menu indisponível")
        return branch

    parts = host.split(".")
    if len(parts) < 3:
        # e.g. menu.vuchada.com or vuchada.com without subdomain
        raise HTTPException(status_code=404, detail="Menu não encontrado")

    subdomain = parts[0]
    if subdomain in {"www"}:
        raise HTTPException(status_code=404, detail="Menu não encontrado")

    branch = db.scalar(select(Branch).where(Branch.public_menu_subdomain == subdomain))
    if not branch or not branch.public_menu_enabled:
        raise HTTPException(status_code=404, detail="Menu não encontrado")

    return branch


def _resolve_branch_from_slug(db: Session, slug: str) -> Branch:
    subdomain = (slug or "").strip().lower()
    if not subdomain or subdomain in {"www"}:
        raise HTTPException(status_code=404, detail="Menu não encontrado")
    branch = db.scalar(select(Branch).where(Branch.public_menu_subdomain == subdomain))
    if not branch or not branch.public_menu_enabled:
        raise HTTPException(status_code=404, detail="Menu não encontrado")
    return branch


@router.get("/menu", response_model=PublicMenuOut)
def get_public_menu(request: Request, db: Session = Depends(get_db)):
    branch = _resolve_branch_from_request(db, request)
    business_type = (branch.business_type or "").strip().lower()
    if business_type != "restaurant":
        raise HTTPException(status_code=404, detail="Menu não encontrado")

    products = db.scalars(
        select(Product)
        .where(Product.company_id == branch.company_id)
        .where(Product.branch_id == branch.id)
        .where(Product.business_type == "restaurant")
        .where(Product.is_active.is_(True))
        .where(Product.show_in_menu.is_(True))
        .order_by(Product.category_id.asc().nulls_last(), Product.name.asc(), Product.id.asc())
    ).all()

    category_ids = sorted({int(p.category_id) for p in products if p.category_id is not None})
    categories: list[PublicMenuCategoryOut] = []
    if category_ids:
        cats = db.scalars(
            select(ProductCategory)
            .where(ProductCategory.company_id == branch.company_id)
            .where(ProductCategory.business_type == "restaurant")
            .where(ProductCategory.id.in_(category_ids))
            .order_by(ProductCategory.name.asc(), ProductCategory.id.asc())
        ).all()
        categories = [PublicMenuCategoryOut(id=c.id, name=c.name) for c in cats]

    # Latest image per product
    if products:
        prod_ids = [p.id for p in products]
        images = db.scalars(
            select(ProductImage)
            .where(ProductImage.company_id == branch.company_id)
            .where(ProductImage.product_id.in_(prod_ids))
            .order_by(ProductImage.product_id.asc(), ProductImage.id.desc())
        ).all()
        latest_by_product: dict[int, ProductImage] = {}
        for img in images:
            if img.product_id not in latest_by_product:
                latest_by_product[img.product_id] = img
    else:
        latest_by_product = {}

    out_products: list[PublicMenuProductOut] = []
    for p in products:
        img = latest_by_product.get(p.id)
        out_products.append(
            PublicMenuProductOut(
                id=p.id,
                name=p.name,
                price=float(p.price or 0),
                category_id=p.category_id,
                image_url=(f"/uploads/{img.file_path}" if img else None),
            )
        )

    return PublicMenuOut(
        branch_id=branch.id,
        branch_name=branch.name,
        categories=categories,
        products=out_products,
    )


@router.post("/orders", response_model=PublicOrderCreatedOut)
def create_public_order(payload: PublicOrderCreate, request: Request, db: Session = Depends(get_db)):
    branch = _resolve_branch_from_request(db, request)
    business_type = (branch.business_type or "").strip().lower()
    if business_type != "restaurant":
        raise HTTPException(status_code=404, detail="Indisponível")

    if not payload.items:
        raise HTTPException(status_code=400, detail="Pedido deve ter itens")

    order = Order(
        company_id=branch.company_id,
        branch_id=branch.id,
        business_type="restaurant",
        status="open",
        table_number=int(payload.table_number),
        seat_number=int(payload.seat_number),
    )
    db.add(order)
    db.flush()

    for it in payload.items:
        product = db.get(Product, int(it.product_id))
        if (
            not product
            or product.company_id != branch.company_id
            or product.branch_id != branch.id
            or (product.business_type or "").strip().lower() != "restaurant"
            or not bool(product.is_active)
            or not bool(product.show_in_menu)
        ):
            raise HTTPException(status_code=400, detail="Produto inválido")

        qty = float(it.qty or 0)
        if qty <= 0:
            raise HTTPException(status_code=400, detail="Quantidade inválida")

        price = float(product.price or 0)
        cost = float(product.cost or 0)
        line_total = round(price * qty, 2)

        db.add(
            OrderItem(
                company_id=branch.company_id,
                branch_id=branch.id,
                order_id=order.id,
                product_id=product.id,
                qty=qty,
                price_at_order=price,
                cost_at_order=cost,
                line_total=line_total,
            )
        )

    db.commit()
    return PublicOrderCreatedOut(order_id=order.id, status="open")


@router.get("/menu/produtos", response_model=list[dict])
def list_public_menu_products(request: Request, q: str | None = None, db: Session = Depends(get_db)):
    branch = _resolve_branch_from_request(db, request)
    business_type = (branch.business_type or "").strip().lower()
    if business_type != "restaurant":
        raise HTTPException(status_code=404, detail="Menu não encontrado")

    image_file_subq = (
        select(ProductImage.file_path)
        .where(ProductImage.company_id == branch.company_id)
        .where(ProductImage.product_id == Product.id)
        .order_by(ProductImage.id.desc())
        .limit(1)
        .scalar_subquery()
    )

    stock_qty_expr = func.coalesce(ProductStock.qty_on_hand, 0)

    stmt = (
        select(
            Product,
            ProductCategory.name.label("category_name"),
            image_file_subq.label("image_file_path"),
            stock_qty_expr.label("stock_qty"),
        )
        .outerjoin(
            ProductCategory,
            (ProductCategory.company_id == branch.company_id)
            & (ProductCategory.business_type == "restaurant")
            & (ProductCategory.id == Product.category_id),
        )
        .outerjoin(
            ProductStock,
            (ProductStock.company_id == branch.company_id)
            & (ProductStock.branch_id == branch.id)
            & (ProductStock.product_id == Product.id)
            & (ProductStock.location_id == Product.default_location_id),
        )
        .where(Product.company_id == branch.company_id)
        .where(Product.branch_id == branch.id)
        .where(Product.business_type == "restaurant")
        .where(Product.is_active.is_(True))
        .where(Product.show_in_menu.is_(True))
    )

    if q and q.strip():
        stmt = stmt.where(Product.name.ilike(f"%{q.strip()}%"))

    rows = db.execute(stmt.order_by(Product.name.asc(), Product.id.asc())).all()
    out: list[dict] = []
    for product, category_name, image_file_path, stock_qty in rows:
        desc_txt = ""
        try:
            desc_txt = str((getattr(product, "attributes", None) or {}).get("description") or "")
        except Exception:
            desc_txt = ""

        out.append(
            {
                "id": product.id,
                "nome": product.name,
                "descricao": desc_txt,
                "preco_venda": float(product.price or 0),
                "imagem": (f"/uploads/{image_file_path}" if image_file_path else None),
                "categoria_id": product.category_id,
                "categoria_nome": category_name,
                "ativo": bool(product.is_active),
                "estoque": float(stock_qty or 0),
            }
        )
    return out


@router.get("/menu/{slug}/produtos", response_model=list[dict], include_in_schema=False)
def list_public_menu_products_by_slug(slug: str, q: str | None = None, db: Session = Depends(get_db)):
    branch = _resolve_branch_from_slug(db, slug)
    business_type = (branch.business_type or "").strip().lower()
    if business_type != "restaurant":
        raise HTTPException(status_code=404, detail="Menu não encontrado")

    image_file_subq = (
        select(ProductImage.file_path)
        .where(ProductImage.company_id == branch.company_id)
        .where(ProductImage.product_id == Product.id)
        .order_by(ProductImage.id.desc())
        .limit(1)
        .scalar_subquery()
    )

    stock_qty_expr = func.coalesce(ProductStock.qty_on_hand, 0)

    stmt = (
        select(
            Product,
            ProductCategory.name.label("category_name"),
            image_file_subq.label("image_file_path"),
            stock_qty_expr.label("stock_qty"),
        )
        .outerjoin(
            ProductCategory,
            (ProductCategory.company_id == branch.company_id)
            & (ProductCategory.business_type == "restaurant")
            & (ProductCategory.id == Product.category_id),
        )
        .outerjoin(
            ProductStock,
            (ProductStock.company_id == branch.company_id)
            & (ProductStock.branch_id == branch.id)
            & (ProductStock.product_id == Product.id)
            & (ProductStock.location_id == Product.default_location_id),
        )
        .where(Product.company_id == branch.company_id)
        .where(Product.branch_id == branch.id)
        .where(Product.business_type == "restaurant")
        .where(Product.is_active.is_(True))
        .where(Product.show_in_menu.is_(True))
    )

    if q and q.strip():
        stmt = stmt.where(Product.name.ilike(f"%{q.strip()}%"))

    rows = db.execute(stmt.order_by(Product.name.asc(), Product.id.asc())).all()
    out: list[dict] = []
    for product, category_name, image_file_path, stock_qty in rows:
        desc_txt = ""
        try:
            desc_txt = str((getattr(product, "attributes", None) or {}).get("description") or "")
        except Exception:
            desc_txt = ""

        out.append(
            {
                "id": product.id,
                "nome": product.name,
                "descricao": desc_txt,
                "preco_venda": float(product.price or 0),
                "imagem": (f"/uploads/{image_file_path}" if image_file_path else None),
                "categoria_id": product.category_id,
                "categoria_nome": category_name,
                "ativo": bool(product.is_active),
                "estoque": float(stock_qty or 0),
            }
        )
    return out
