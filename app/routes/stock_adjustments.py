from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.product import Product
from app.models.product_stock import ProductStock
from app.models.stock_location import StockLocation
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.schemas.stock_adjustments import StockAdjustmentCreate

router = APIRouter()


def _get_or_create_stock_row(db: Session, company_id: int, product_id: int, location_id: int) -> ProductStock:
    row = db.scalar(
        select(ProductStock)
        .where(ProductStock.company_id == company_id)
        .where(ProductStock.branch_id == int(getattr(db, "_branch_id", 0) or 0))
        .where(ProductStock.product_id == product_id)
        .where(ProductStock.location_id == location_id)
        .with_for_update()
    )
    if row:
        return row

    row = ProductStock(
        company_id=company_id,
        branch_id=int(getattr(db, "_branch_id", 0) or 0),
        product_id=product_id,
        location_id=location_id,
        qty_on_hand=0,
    )
    db.add(row)
    db.flush()

    row = db.scalar(
        select(ProductStock)
        .where(ProductStock.company_id == company_id)
        .where(ProductStock.branch_id == int(getattr(db, "_branch_id", 0) or 0))
        .where(ProductStock.product_id == product_id)
        .where(ProductStock.location_id == location_id)
        .with_for_update()
    )
    return row


@router.post("")
@router.post("/", include_in_schema=False)
def create_adjustment(
    payload: StockAdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.get(Product, payload.product_id)
    if not product or product.company_id != current_user.company_id or getattr(product, "branch_id", None) != current_user.branch_id:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    if bool(getattr(product, "is_service", False)):
        raise HTTPException(status_code=400, detail="Serviço não possui stock")

    location = db.get(StockLocation, payload.location_id)
    if not location or location.company_id != current_user.company_id or not location.is_active:
        raise HTTPException(status_code=400, detail="Local inválido")

    if getattr(location, "branch_id", None) != current_user.branch_id:
        raise HTTPException(status_code=400, detail="Local inválido")

    qty_delta = float(payload.qty_delta)
    if qty_delta == 0:
        raise HTTPException(status_code=400, detail="Quantidade inválida")

    setattr(db, "_branch_id", int(current_user.branch_id))
    stock = _get_or_create_stock_row(db, current_user.company_id, product.id, location.id)
    before = float(stock.qty_on_hand or 0)
    after = before + qty_delta
    if after < 0:
        raise HTTPException(status_code=400, detail="Ajuste deixaria stock negativo")

    try:
        stock.qty_on_hand = after

        mv = StockMovement(
            company_id=current_user.company_id,
            branch_id=int(current_user.branch_id),
            product_id=product.id,
            location_id=location.id,
            movement_type="adjustment",
            qty_delta=qty_delta,
            reference_type="adjustment",
            reference_id=None,
            notes=payload.notes,
            created_by=current_user.id,
        )
        db.add(mv)

        db.commit()
        return {"ok": True, "before": before, "after": after}
    except Exception:
        db.rollback()
        raise
