from datetime import datetime
from uuid import uuid4

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
from app.models.delivery_zone import DeliveryZone
from app.models.restaurant_table import RestaurantTable
from app.schemas.public_menu import (
    PublicMenuCategoryOut,
    PublicMenuOut,
    PublicMesaOut,
    PublicMenuProductOut,
    PublicDistanceCheckoutCreate,
    PublicDistanceCheckoutOut,
    PublicPedidoCreate,
    PublicPedidoCreatedOut,
    PublicPedidoTrackItemOut,
    PublicPedidoTrackOut,
    PublicOrderCreate,
    PublicOrderCreatedOut,
)
from app.schemas.delivery_zones import PublicDeliveryZoneOut

router = APIRouter()


@router.get("/mesas", response_model=list[PublicMesaOut])
def list_public_tables(
    request: Request,
    host: str | None = None,
    domain: str | None = None,
    db: Session = Depends(get_db),
):
    branch = _resolve_branch_from_request_or_host(db, request, domain or host)
    business_type = (branch.business_type or "").strip().lower()
    if business_type != "restaurant":
        raise HTTPException(status_code=404, detail="Indisponível")

    rows = db.scalars(
        select(RestaurantTable)
        .where(RestaurantTable.company_id == branch.company_id)
        .where(RestaurantTable.branch_id == branch.id)
        .where(RestaurantTable.is_active.is_(True))
        .order_by(RestaurantTable.number.asc(), RestaurantTable.id.asc())
    ).all()

    table_numbers = [int(r.number) for r in rows if getattr(r, "number", None) is not None]
    occupied_by_table: dict[int, int] = {}
    if table_numbers:
        occ_rows = db.execute(
            select(Order.table_number, func.count(func.distinct(Order.seat_number)))
            .where(Order.company_id == branch.company_id)
            .where(Order.branch_id == branch.id)
            .where(Order.business_type == "restaurant")
            .where(Order.status.in_(["open", "in_progress"]))
            .where(Order.table_number.in_(table_numbers))
            .group_by(Order.table_number)
        ).all()
        occupied_by_table = {int(tn): int(cnt or 0) for (tn, cnt) in occ_rows if tn is not None}

    return [
        PublicMesaOut(
            id=r.id,
            numero=int(r.number),
            capacity=int(getattr(r, "capacity", 0) or 0) or None,
            occupied_seats=int(occupied_by_table.get(int(r.number), 0)),
        )
        for r in rows
    ]


@router.get("/delivery-zones", response_model=list[PublicDeliveryZoneOut])
def list_public_delivery_zones(
    request: Request,
    host: str | None = None,
    domain: str | None = None,
    db: Session = Depends(get_db),
):
    branch = _resolve_branch_from_request_or_host(db, request, domain or host)
    business_type = (branch.business_type or "").strip().lower()
    if business_type != "restaurant":
        raise HTTPException(status_code=404, detail="Indisponível")

    rows = db.scalars(
        select(DeliveryZone)
        .where(DeliveryZone.company_id == branch.company_id)
        .where(DeliveryZone.branch_id == branch.id)
        .where(DeliveryZone.is_active.is_(True))
        .order_by(DeliveryZone.name.asc(), DeliveryZone.id.asc())
    ).all()

    return [
        PublicDeliveryZoneOut(
            id=r.id,
            name=r.name,
            fee=float(r.fee or 0),
            keywords=(list(r.keywords) if getattr(r, "keywords", None) else []),
        )
        for r in rows
    ]


def _normalize_host_value(value: str) -> str:
    host = (value or "").strip().lower()
    if not host:
        return host
    # Some proxies send a comma-separated list. Use the first value.
    if "," in host:
        host = host.split(",", 1)[0].strip()
    # remove port if present
    if ":" in host:
        host = host.split(":", 1)[0]
    return host


def _extract_effective_host(request: Request) -> str:
    # Vercel sometimes uses x-vercel-forwarded-host
    forwarded = request.headers.get("x-vercel-forwarded-host") or request.headers.get("x-forwarded-host")
    raw = forwarded or request.headers.get("host") or ""
    return _normalize_host_value(raw)


def _resolve_branch_from_host(db: Session, host: str) -> Branch:
    host = _normalize_host_value(host)
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


def _resolve_branch_from_request(db: Session, request: Request) -> Branch:
    return _resolve_branch_from_host(db, _extract_effective_host(request))


def _resolve_branch_from_request_or_host(db: Session, request: Request, host: str | None) -> Branch:
    if host:
        return _resolve_branch_from_host(db, host)
    return _resolve_branch_from_request(db, request)


def _resolve_branch_from_slug(db: Session, slug: str) -> Branch:
    subdomain = (slug or "").strip().lower()
    if not subdomain or subdomain in {"www"}:
        raise HTTPException(status_code=404, detail="Menu não encontrado")
    branch = db.scalar(select(Branch).where(Branch.public_menu_subdomain == subdomain))
    if not branch or not branch.public_menu_enabled:
        raise HTTPException(status_code=404, detail="Menu não encontrado")
    return branch


@router.get("/menu", response_model=PublicMenuOut)
def get_public_menu(request: Request, host: str | None = None, domain: str | None = None, db: Session = Depends(get_db)):
    branch = _resolve_branch_from_request_or_host(db, request, domain or host)
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

        attrs = getattr(p, "attributes", None) or {}
        try:
            is_daily_dish = bool(attrs.get("is_daily_dish"))
        except Exception:
            is_daily_dish = False
        try:
            promo_enabled = bool(attrs.get("promo_enabled"))
        except Exception:
            promo_enabled = False
        promo_price_raw = attrs.get("promo_price")
        promo_price: float | None
        try:
            promo_price = float(promo_price_raw) if promo_price_raw is not None and promo_price_raw != "" else None
        except Exception:
            promo_price = None

        out_products.append(
            PublicMenuProductOut(
                id=p.id,
                name=p.name,
                price=float(p.price or 0),
                is_daily_dish=is_daily_dish,
                promo_enabled=promo_enabled,
                promo_price=promo_price,
                category_id=p.category_id,
                image_url=(f"/uploads/{img.file_path}" if img else None),
            )
        )

    out_products = sorted(
        out_products,
        key=lambda x: (
            0 if bool(getattr(x, "promo_enabled", False)) else 1,
            0 if bool(getattr(x, "is_daily_dish", False)) else 1,
            1 if getattr(x, "category_id", None) is None else 0,
            getattr(x, "category_id", 0) or 0,
            (getattr(x, "name", "") or "").casefold(),
            getattr(x, "id", 0) or 0,
        ),
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


@router.post("/pedidos", response_model=PublicPedidoCreatedOut)
def create_public_pedido(
    payload: PublicPedidoCreate,
    request: Request,
    host: str | None = None,
    domain: str | None = None,
    db: Session = Depends(get_db),
):
    branch = _resolve_branch_from_request_or_host(db, request, domain or host)
    business_type = (branch.business_type or "").strip().lower()
    if business_type != "restaurant":
        raise HTTPException(status_code=404, detail="Indisponível")

    if not payload.itens:
        raise HTTPException(status_code=400, detail="Pedido deve ter itens")

    mesa = db.get(RestaurantTable, int(payload.mesa_id))
    if not mesa or mesa.company_id != branch.company_id or mesa.branch_id != branch.id or not bool(mesa.is_active):
        raise HTTPException(status_code=400, detail="Mesa inválida")

    seat_number = int(payload.lugar_numero or 1)
    if seat_number <= 0:
        seat_number = 1

    order_uuid = uuid4().hex
    order = Order(
        company_id=branch.company_id,
        branch_id=branch.id,
        business_type="restaurant",
        status="open",
        order_uuid=order_uuid,
        order_type="table",
        table_number=int(mesa.number),
        seat_number=seat_number,
    )
    db.add(order)
    db.flush()

    for it in payload.itens:
        try:
            product_id = int(str(it.produto_id).strip())
        except Exception:
            raise HTTPException(status_code=400, detail="Produto inválido")
        product = db.get(Product, product_id)
        if (
            not product
            or product.company_id != branch.company_id
            or product.branch_id != branch.id
            or (product.business_type or "").strip().lower() != "restaurant"
            or not bool(product.is_active)
            or not bool(product.show_in_menu)
        ):
            raise HTTPException(status_code=400, detail="Produto inválido")

        qty = float(it.quantidade or 0)
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
    return PublicPedidoCreatedOut(pedido_id=order.id, pedido_uuid=order_uuid, status="open")


@router.post("/distancia/checkout", response_model=PublicDistanceCheckoutOut)
def create_public_distance_checkout(
    payload: PublicDistanceCheckoutCreate,
    request: Request,
    host: str | None = None,
    domain: str | None = None,
    db: Session = Depends(get_db),
):
    branch = _resolve_branch_from_request_or_host(db, request, domain or host)
    business_type = (branch.business_type or "").strip().lower()
    if business_type != "restaurant":
        raise HTTPException(status_code=404, detail="Indisponível")

    tipo = (payload.tipo or "").strip().lower()
    if tipo not in {"entrega", "retirada"}:
        raise HTTPException(status_code=400, detail="Tipo inválido")
    if not (payload.cliente_nome or "").strip():
        raise HTTPException(status_code=400, detail="Nome é obrigatório")
    if not (payload.cliente_telefone or "").strip():
        raise HTTPException(status_code=400, detail="Telefone é obrigatório")
    if tipo == "entrega" and not (payload.endereco_entrega or "").strip():
        raise HTTPException(status_code=400, detail="Endereço é obrigatório")
    if not payload.itens:
        raise HTTPException(status_code=400, detail="Pedido deve ter itens")

    order_uuid = uuid4().hex
    order = Order(
        company_id=branch.company_id,
        branch_id=branch.id,
        business_type="restaurant",
        status="open",
        order_uuid=order_uuid,
        order_type="delivery",
        delivery_kind=tipo,
        customer_name=(payload.cliente_nome or "").strip() or None,
        customer_phone=(payload.cliente_telefone or "").strip() or None,
        delivery_address=(payload.endereco_entrega or "").strip() or None,
        delivery_zone_name=(payload.bairro or "").strip() or None,
        delivery_fee=float(payload.taxa_entrega or 0),
        table_number=0,
        seat_number=0,
    )
    db.add(order)
    db.flush()

    for it in payload.itens:
        try:
            product_id = int(str(it.produto_id).strip())
        except Exception:
            raise HTTPException(status_code=400, detail="Produto inválido")
        product = db.get(Product, product_id)
        if (
            not product
            or product.company_id != branch.company_id
            or product.branch_id != branch.id
            or (product.business_type or "").strip().lower() != "restaurant"
            or not bool(product.is_active)
            or not bool(product.show_in_menu)
        ):
            raise HTTPException(status_code=400, detail="Produto inválido")

        qty = float(it.quantidade or 0)
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
    return PublicDistanceCheckoutOut(pedido_id=order.id, pedido_uuid=order_uuid, status="open")


@router.get("/pedidos/uuid/{pedido_uuid}", response_model=PublicPedidoTrackOut)
def get_public_order_by_uuid(
    pedido_uuid: str,
    request: Request,
    host: str | None = None,
    domain: str | None = None,
    db: Session = Depends(get_db),
):
    branch = _resolve_branch_from_request_or_host(db, request, domain or host)
    business_type = (branch.business_type or "").strip().lower()
    if business_type != "restaurant":
        raise HTTPException(status_code=404, detail="Indisponível")

    uuid = (pedido_uuid or "").strip()
    if not uuid:
        raise HTTPException(status_code=400, detail="UUID inválido")

    o = db.scalar(
        select(Order)
        .where(Order.company_id == branch.company_id)
        .where(Order.branch_id == branch.id)
        .where(Order.order_uuid == uuid)
    )
    if not o:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    rows = db.execute(
        select(OrderItem, Product.name)
        .join(Product, Product.id == OrderItem.product_id)
        .where(OrderItem.company_id == branch.company_id)
        .where(OrderItem.branch_id == branch.id)
        .where(OrderItem.order_id == o.id)
        .order_by(OrderItem.id.asc())
    ).all()

    items_out: list[PublicPedidoTrackItemOut] = []
    total = 0.0
    for oi, pname in rows:
        subtotal = float(getattr(oi, "line_total", 0) or 0)
        total = round(total + subtotal, 2)
        items_out.append(
            PublicPedidoTrackItemOut(
                produto_nome=pname,
                quantidade=float(getattr(oi, "qty", 0) or 0),
                subtotal=subtotal,
            )
        )

    updated_at = None
    try:
        dt = getattr(o, "updated_at", None) or getattr(o, "created_at", None)
        if isinstance(dt, datetime):
            updated_at = dt.isoformat()
    except Exception:
        updated_at = None

    return PublicPedidoTrackOut(
        pedido_id=o.id,
        pedido_uuid=uuid,
        status=getattr(o, "status", "open"),
        updated_at=updated_at,
        valor_total=total,
        itens=items_out,
    )


def _list_public_products_for_branch(db: Session, branch: Branch, q: str | None = None, somente_disponiveis: bool = True):
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

    if somente_disponiveis:
        stmt = stmt.where(stock_qty_expr > 0)

    rows = db.execute(stmt.order_by(Product.name.asc(), Product.id.asc())).all()
    out: list[dict] = []
    for product, category_name, image_file_path, stock_qty in rows:
        desc_txt = ""
        try:
            desc_txt = str((getattr(product, "attributes", None) or {}).get("description") or "")
        except Exception:
            desc_txt = ""

        attrs = getattr(product, "attributes", None) or {}
        try:
            is_daily_dish = bool(attrs.get("is_daily_dish"))
        except Exception:
            is_daily_dish = False
        try:
            promo_enabled = bool(attrs.get("promo_enabled"))
        except Exception:
            promo_enabled = False
        promo_price_raw = attrs.get("promo_price")
        try:
            promo_price = float(promo_price_raw) if promo_price_raw is not None and promo_price_raw != "" else None
        except Exception:
            promo_price = None

        out.append(
            {
                "id": product.id,
                "nome": product.name,
                "descricao": desc_txt,
                "preco_venda": float(product.price or 0),
                "is_daily_dish": is_daily_dish,
                "promo_enabled": promo_enabled,
                "promo_price": promo_price,
                "imagem": (f"/uploads/{image_file_path}" if image_file_path else None),
                "categoria_id": product.category_id,
                "categoria_nome": category_name,
                "ativo": bool(product.is_active),
                "estoque": float(stock_qty or 0),
            }
        )
    out = sorted(
        out,
        key=lambda x: (
            0 if bool(x.get("promo_enabled")) else 1,
            0 if bool(x.get("is_daily_dish")) else 1,
            1 if x.get("categoria_id") is None else 0,
            int(x.get("categoria_id") or 0),
            str(x.get("nome") or "").casefold(),
            int(x.get("id") or 0),
        ),
    )
    return out


@router.get("/menu/produtos", response_model=list[dict])
def list_public_products(
    request: Request,
    q: str | None = None,
    somente_disponiveis: bool = True,
    host: str | None = None,
    domain: str | None = None,
    db: Session = Depends(get_db),
):
    branch = _resolve_branch_from_request_or_host(db, request, domain or host)
    return _list_public_products_for_branch(db, branch, q=q, somente_disponiveis=somente_disponiveis)


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

        attrs = getattr(product, "attributes", None) or {}
        try:
            is_daily_dish = bool(attrs.get("is_daily_dish"))
        except Exception:
            is_daily_dish = False
        try:
            promo_enabled = bool(attrs.get("promo_enabled"))
        except Exception:
            promo_enabled = False
        promo_price_raw = attrs.get("promo_price")
        try:
            promo_price = float(promo_price_raw) if promo_price_raw is not None and promo_price_raw != "" else None
        except Exception:
            promo_price = None

        out.append(
            {
                "id": product.id,
                "nome": product.name,
                "descricao": desc_txt,
                "preco_venda": float(product.price or 0),
                "is_daily_dish": is_daily_dish,
                "promo_enabled": promo_enabled,
                "promo_price": promo_price,
                "imagem": (f"/uploads/{image_file_path}" if image_file_path else None),
                "categoria_id": product.category_id,
                "categoria_nome": category_name,
                "ativo": bool(product.is_active),
                "estoque": float(stock_qty or 0),
            }
        )
    out = sorted(
        out,
        key=lambda x: (
            0 if bool(x.get("promo_enabled")) else 1,
            0 if bool(x.get("is_daily_dish")) else 1,
            1 if x.get("categoria_id") is None else 0,
            int(x.get("categoria_id") or 0),
            str(x.get("nome") or "").casefold(),
            int(x.get("id") or 0),
        ),
    )
    return out
