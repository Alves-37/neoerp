from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.product import Product
from app.models.product_stock import ProductStock
from app.models.stock_location import StockLocation
from app.models.stock_movement import StockMovement
from app.models.stock_transfer import StockTransfer
from app.models.user import User
from app.schemas.stock_transfers import StockTransferCreate, StockTransferOut

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


@router.get("", response_model=list[StockTransferOut])
@router.get("/", response_model=list[StockTransferOut], include_in_schema=False)
def list_transfers(
    limit: int = 50,
    offset: int = 0,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    stmt = select(StockTransfer).where(StockTransfer.company_id == current_user.company_id)
    if is_admin:
        if branch_id is not None:
            stmt = stmt.where(StockTransfer.branch_id == int(branch_id))
    else:
        stmt = stmt.where(StockTransfer.branch_id == int(current_user.branch_id))

    rows = db.scalars(stmt.order_by(desc(StockTransfer.id)).limit(limit).offset(offset)).all()
    return rows


@router.post("", response_model=StockTransferOut)
@router.post("/", response_model=StockTransferOut, include_in_schema=False)
def create_transfer(
    payload: StockTransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.from_location_id == payload.to_location_id:
        raise HTTPException(status_code=400, detail="Origem e destino não podem ser iguais")

    product = db.get(Product, payload.product_id)
    if not product or product.company_id != current_user.company_id or getattr(product, "branch_id", None) != current_user.branch_id:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    from_loc = db.get(StockLocation, payload.from_location_id)
    to_loc = db.get(StockLocation, payload.to_location_id)

    if not from_loc or from_loc.company_id != current_user.company_id or not from_loc.is_active:
        raise HTTPException(status_code=400, detail="Local de origem inválido")

    if getattr(from_loc, "branch_id", None) != current_user.branch_id:
        raise HTTPException(status_code=400, detail="Local de origem inválido")

    if not to_loc or to_loc.company_id != current_user.company_id or not to_loc.is_active:
        raise HTTPException(status_code=400, detail="Local de destino inválido")

    if getattr(to_loc, "branch_id", None) != current_user.branch_id:
        raise HTTPException(status_code=400, detail="Local de destino inválido")

    # pass branch_id to helper through session attribute
    setattr(db, "_branch_id", int(current_user.branch_id))

    # Lock rows by selecting FOR UPDATE to avoid race conditions on stock
    from_stock = _get_or_create_stock_row(db, current_user.company_id, product.id, from_loc.id)
    to_stock = _get_or_create_stock_row(db, current_user.company_id, product.id, to_loc.id)

    from_qty = float(from_stock.qty_on_hand or 0)
    qty = float(payload.qty)

    if qty <= 0:
        raise HTTPException(status_code=400, detail="Quantidade inválida")

    if from_qty < qty:
        raise HTTPException(status_code=400, detail="Quantidade maior que o stock disponível na origem")

    transfer = StockTransfer(
        company_id=current_user.company_id,
        branch_id=int(current_user.branch_id),
        product_id=product.id,
        from_location_id=from_loc.id,
        to_location_id=to_loc.id,
        qty=qty,
        notes=(payload.notes or None),
        created_by=current_user.id,
    )

    try:
        # Update balances
        from_stock.qty_on_hand = from_qty - qty
        to_stock.qty_on_hand = float(to_stock.qty_on_hand or 0) + qty

        db.add(transfer)
        db.flush()

        # Movements (out/in)
        out_mv = StockMovement(
            company_id=current_user.company_id,
            branch_id=int(current_user.branch_id),
            product_id=product.id,
            location_id=from_loc.id,
            movement_type="transfer_out",
            qty_delta=-qty,
            reference_type="transfer",
            reference_id=transfer.id,
            notes=payload.notes,
            created_by=current_user.id,
        )
        in_mv = StockMovement(
            company_id=current_user.company_id,
            branch_id=int(current_user.branch_id),
            product_id=product.id,
            location_id=to_loc.id,
            movement_type="transfer_in",
            qty_delta=qty,
            reference_type="transfer",
            reference_id=transfer.id,
            notes=payload.notes,
            created_by=current_user.id,
        )
        db.add(out_mv)
        db.add(in_mv)

        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(transfer)
    return transfer
