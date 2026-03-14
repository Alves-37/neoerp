from fastapi import APIRouter, Depends
from sqlalchemy import asc, func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.product import Product
from app.models.product_stock import ProductStock
from app.models.stock_location import StockLocation
from app.models.user import User
from app.schemas.product_stocks import LowStockRowOut, ProductStockOut

router = APIRouter()


@router.get("", response_model=list[ProductStockOut])
@router.get("/", response_model=list[ProductStockOut], include_in_schema=False)
def list_product_stocks(
    product_id: int | None = None,
    location_id: int | None = None,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    stmt = select(ProductStock).where(ProductStock.company_id == current_user.company_id)
    if is_admin:
        if branch_id is not None:
            stmt = stmt.where(ProductStock.branch_id == int(branch_id))
    else:
        stmt = stmt.where(ProductStock.branch_id == int(current_user.branch_id))

    if product_id is not None:
        stmt = stmt.where(ProductStock.product_id == product_id)
    if location_id is not None:
        stmt = stmt.where(ProductStock.location_id == location_id)

    rows = db.scalars(stmt.order_by(asc(ProductStock.location_id), asc(ProductStock.product_id))).all()
    return rows


@router.get("/low-stock", response_model=list[LowStockRowOut])
def list_low_stock(
    scope: str = "warehouse",  # warehouse | default
    limit: int = 200,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scope = (scope or "warehouse").strip().lower()
    if scope not in {"warehouse", "default"}:
        scope = "warehouse"

    loc_stmt = select(StockLocation.id).where(StockLocation.company_id == current_user.company_id).where(
        StockLocation.branch_id == int(current_user.branch_id)
    )
    if scope == "warehouse":
        loc_stmt = loc_stmt.where(StockLocation.type == "warehouse")

    loc_ids = [int(x) for x in db.scalars(loc_stmt).all()]
    if not loc_ids:
        return []

    qty_expr = func.coalesce(ProductStock.qty_on_hand, 0)

    stmt = (
        select(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            StockLocation.id.label("location_id"),
            StockLocation.name.label("location_name"),
            StockLocation.type.label("location_type"),
            qty_expr.label("qty_on_hand"),
            func.coalesce(Product.min_stock, 0).label("min_stock"),
        )
        .select_from(Product)
        .join(StockLocation, StockLocation.id.in_(loc_ids))
        .outerjoin(
            ProductStock,
            (ProductStock.company_id == current_user.company_id)
            & (ProductStock.branch_id == int(current_user.branch_id))
            & (ProductStock.product_id == Product.id)
            & (ProductStock.location_id == StockLocation.id),
        )
        .where(Product.company_id == current_user.company_id)
        .where(Product.branch_id == int(current_user.branch_id))
        .where(Product.track_stock.is_(True))
        .where(Product.is_active.is_(True))
        .where(func.coalesce(Product.min_stock, 0) > 0)
    )

    if scope == "default":
        stmt = stmt.where(StockLocation.id == Product.default_location_id)

    stmt = stmt.where(qty_expr < func.coalesce(Product.min_stock, 0)).order_by(qty_expr.asc(), Product.name.asc())

    rows = db.execute(stmt.limit(limit).offset(offset)).all()
    return [
        {
            "product_id": int(r.product_id),
            "product_name": r.product_name,
            "location_id": int(r.location_id),
            "location_name": r.location_name,
            "location_type": r.location_type,
            "qty_on_hand": float(r.qty_on_hand or 0),
            "min_stock": float(r.min_stock or 0),
        }
        for r in rows
    ]
