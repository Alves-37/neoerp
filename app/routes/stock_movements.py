from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.schemas.stock_movements import StockMovementOut

router = APIRouter()


@router.get("", response_model=list[StockMovementOut])
@router.get("/", response_model=list[StockMovementOut], include_in_schema=False)
def list_stock_movements(
    product_id: int | None = None,
    location_id: int | None = None,
    movement_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = 200,
    offset: int = 0,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    stmt = select(StockMovement).where(StockMovement.company_id == current_user.company_id)
    if is_admin:
        if branch_id is not None:
            stmt = stmt.where(StockMovement.branch_id == int(branch_id))
    else:
        stmt = stmt.where(StockMovement.branch_id == int(current_user.branch_id))

    if product_id is not None:
        stmt = stmt.where(StockMovement.product_id == product_id)
    if location_id is not None:
        stmt = stmt.where(StockMovement.location_id == location_id)
    if movement_type:
        stmt = stmt.where(StockMovement.movement_type == movement_type)
    if date_from is not None:
        stmt = stmt.where(StockMovement.created_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(StockMovement.created_at <= date_to)

    try:
        rows = db.scalars(stmt.order_by(desc(StockMovement.id)).limit(limit).offset(offset)).all()
        return rows
    except ProgrammingError as ex:
        msg = str(ex).lower()
        if "undefinedtable" in msg or "does not exist" in msg or "relation" in msg and "stock_movements" in msg:
            return []
        raise
