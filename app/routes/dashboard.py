from datetime import date, datetime, time, timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.branch import Branch
from app.models.company import Company
from app.models.product import Product
from app.models.product_stock import ProductStock
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.stock_location import StockLocation
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryOut, ExpiryAlertItemOut, ExpiryAlertsOut, SalesSeriesPointOut

router = APIRouter()


_APP_TZ = "Africa/Maputo"


def _get_app_tz():
    try:
        return ZoneInfo(_APP_TZ)
    except ZoneInfoNotFoundError:
        return timezone(timedelta(hours=2))


def _parse_validade(val: object) -> date | None:
    try:
        if val is None:
            return None
        s = str(val).strip()
        if not s:
            return None
        return date.fromisoformat(s)
    except Exception:
        return None


@router.get("/summary", response_model=DashboardSummaryOut)
def get_dashboard_summary(
    establishment_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    branch = db.get(Branch, int(current_user.branch_id))
    if branch and branch.company_id == current_user.company_id:
        business_type = branch.business_type or "retail"
        branch_id = int(branch.id)
    else:
        company = db.get(Company, current_user.company_id)
        business_type = company.business_type if company else "retail"
        branch_id = int(current_user.branch_id)

    is_cashier = (current_user.role or "").strip().lower() == "cashier"
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    effective_establishment_id: int | None = None
    if is_admin:
        if establishment_id is not None:
            effective_establishment_id = int(establishment_id)
        else:
            if (business_type or "").strip().lower() == "pharmacy":
                if getattr(current_user, "establishment_id", None) is None:
                    raise HTTPException(status_code=400, detail="Ponto inválido")
                effective_establishment_id = int(current_user.establishment_id)
    else:
        if getattr(current_user, "establishment_id", None) is not None:
            effective_establishment_id = int(current_user.establishment_id)

    products_stmt = (
        select(func.count(Product.id))
        .where(Product.company_id == current_user.company_id)
        .where(Product.branch_id == branch_id)
        .where(Product.business_type == business_type)
    )
    if effective_establishment_id is not None:
        products_stmt = products_stmt.where(Product.establishment_id == effective_establishment_id)
    products_total = db.scalar(products_stmt)

    tz = _get_app_tz()
    now_local = datetime.now(tz)
    today_local = now_local.date()
    month_start_local = today_local.replace(day=1)

    today_start_local = datetime.combine(today_local, time.min, tzinfo=tz)
    tomorrow_start_local = today_start_local + timedelta(days=1)
    month_start_dt_local = datetime.combine(month_start_local, time.min, tzinfo=tz)

    today_start_utc = today_start_local.astimezone(timezone.utc)
    tomorrow_start_utc = tomorrow_start_local.astimezone(timezone.utc)
    month_start_utc = month_start_dt_local.astimezone(timezone.utc)

    sales_base = (
        select(func.coalesce(func.sum(Sale.total), 0))
        .where(Sale.company_id == current_user.company_id)
        .where(Sale.branch_id == branch_id)
        .where(func.lower(Sale.business_type) == business_type)
        .where(func.lower(Sale.status) == "paid")
    )
    if effective_establishment_id is not None:
        sales_base = sales_base.where(Sale.establishment_id == effective_establishment_id)
    if is_cashier:
        sales_base = sales_base.where(Sale.cashier_id == current_user.id)

    sales_today = db.scalar(
        sales_base.where(Sale.created_at >= today_start_utc).where(Sale.created_at < tomorrow_start_utc)
    )
    sales_month = db.scalar(
        sales_base.where(Sale.created_at >= month_start_utc).where(Sale.created_at < tomorrow_start_utc)
    )

    profit_base = (
        select(func.coalesce(func.sum((SaleItem.price_at_sale - SaleItem.cost_at_sale) * SaleItem.qty), 0))
        .select_from(SaleItem)
        .join(Sale, Sale.id == SaleItem.sale_id)
        .where(SaleItem.company_id == current_user.company_id)
        .where(SaleItem.branch_id == branch_id)
        .where(Sale.company_id == current_user.company_id)
        .where(Sale.branch_id == branch_id)
        .where(func.lower(Sale.business_type) == business_type)
        .where(func.lower(Sale.status) == "paid")
    )
    if effective_establishment_id is not None:
        profit_base = profit_base.where(Sale.establishment_id == effective_establishment_id)
    if is_cashier:
        profit_base = profit_base.where(Sale.cashier_id == current_user.id)

    profit_today = db.scalar(
        profit_base.where(Sale.created_at >= today_start_utc).where(Sale.created_at < tomorrow_start_utc)
    )
    profit_month = db.scalar(
        profit_base.where(Sale.created_at >= month_start_utc).where(Sale.created_at < tomorrow_start_utc)
    )

    qty_default_expr = func.coalesce(ProductStock.qty_on_hand, 0)
    base_products = (
        select(Product)
        .where(Product.company_id == current_user.company_id)
        .where(Product.branch_id == branch_id)
        .where(Product.business_type == business_type)
        .where(Product.track_stock.is_(True))
        .where(Product.is_active.is_(True))
    )
    if effective_establishment_id is not None:
        base_products = base_products.where(Product.establishment_id == effective_establishment_id)

    low_stock_default_stmt = (
        select(func.coalesce(func.count(Product.id), 0))
        .select_from(Product)
        .outerjoin(
            ProductStock,
            (ProductStock.company_id == current_user.company_id)
            & (ProductStock.branch_id == branch_id)
            & (ProductStock.product_id == Product.id)
            & (ProductStock.location_id == Product.default_location_id),
        )
        .where(Product.company_id == current_user.company_id)
        .where(Product.branch_id == branch_id)
        .where(Product.business_type == business_type)
        .where(Product.track_stock.is_(True))
        .where(Product.is_active.is_(True))
        .where(func.coalesce(Product.min_stock, 0) > 0)
        .where(qty_default_expr < func.coalesce(Product.min_stock, 0))
    )
    if effective_establishment_id is not None:
        low_stock_default_stmt = low_stock_default_stmt.where(Product.establishment_id == effective_establishment_id)
    low_stock_default_count = db.scalar(low_stock_default_stmt)

    low_stock_warehouse_stmt = (
        select(func.coalesce(func.count(func.distinct(Product.id)), 0))
        .select_from(Product)
        .outerjoin(
            ProductStock,
            (ProductStock.company_id == current_user.company_id)
            & (ProductStock.branch_id == branch_id)
            & (ProductStock.product_id == Product.id),
        )
        .outerjoin(
            StockLocation,
            (StockLocation.company_id == current_user.company_id)
            & (StockLocation.branch_id == branch_id)
            & (StockLocation.id == ProductStock.location_id)
            & (StockLocation.type == "warehouse")
            & (StockLocation.is_active.is_(True)),
        )
        .where(Product.company_id == current_user.company_id)
        .where(Product.branch_id == branch_id)
        .where(Product.business_type == business_type)
        .where(Product.track_stock.is_(True))
        .where(Product.is_active.is_(True))
        .where(func.coalesce(Product.min_stock, 0) > 0)
        .where(StockLocation.id.is_not(None))
        .where(func.coalesce(ProductStock.qty_on_hand, 0) < func.coalesce(Product.min_stock, 0))
    )
    if effective_establishment_id is not None:
        low_stock_warehouse_stmt = low_stock_warehouse_stmt.where(Product.establishment_id == effective_establishment_id)
    low_stock_warehouse_count = db.scalar(low_stock_warehouse_stmt)

    stock_values_stmt = (
        select(
            func.coalesce(func.sum(qty_default_expr * func.coalesce(Product.cost, 0)), 0).label("stock_value_cost"),
            func.coalesce(func.sum(qty_default_expr * func.coalesce(Product.price, 0)), 0).label("stock_value_potential"),
        )
        .select_from(Product)
        .outerjoin(
            ProductStock,
            (ProductStock.company_id == current_user.company_id)
            & (ProductStock.branch_id == branch_id)
            & (ProductStock.product_id == Product.id)
            & (ProductStock.location_id == Product.default_location_id),
        )
        .where(Product.company_id == current_user.company_id)
        .where(Product.branch_id == branch_id)
        .where(Product.business_type == business_type)
        .where(Product.track_stock.is_(True))
        .where(Product.is_active.is_(True))
    )
    if effective_establishment_id is not None:
        stock_values_stmt = stock_values_stmt.where(Product.establishment_id == effective_establishment_id)

    stock_values = db.execute(stock_values_stmt).one()

    return DashboardSummaryOut(
        products_total=int(products_total or 0),
        sales_today=float(sales_today or 0),
        sales_month=float(sales_month or 0),
        profit_today=float(profit_today or 0),
        profit_month=float(profit_month or 0),
        low_stock_default_count=int(low_stock_default_count or 0),
        low_stock_warehouse_count=int(low_stock_warehouse_count or 0),
        stock_value_cost=float(stock_values.stock_value_cost or 0),
        stock_value_potential=float(stock_values.stock_value_potential or 0),
    )


@router.get("/sales-series", response_model=list[SalesSeriesPointOut])
def get_sales_series(
    days: int = 30,
    establishment_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    n = int(days or 30)
    if n < 7:
        n = 7
    if n > 365:
        n = 365

    tz = _get_app_tz()
    now_local = datetime.now(tz)
    today_local = now_local.date()
    start_local = today_local - timedelta(days=n - 1)
    start_local_dt = datetime.combine(start_local, time.min, tzinfo=tz)
    tomorrow_local_dt = datetime.combine(today_local, time.min, tzinfo=tz) + timedelta(days=1)
    start_utc = start_local_dt.astimezone(timezone.utc)
    end_utc = tomorrow_local_dt.astimezone(timezone.utc)

    branch = db.get(Branch, int(current_user.branch_id))
    if branch and branch.company_id == current_user.company_id:
        business_type = branch.business_type or "retail"
        branch_id = int(branch.id)
    else:
        company = db.get(Company, current_user.company_id)
        business_type = company.business_type if company else "retail"
        branch_id = int(current_user.branch_id)

    is_cashier = (current_user.role or "").strip().lower() == "cashier"

    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    effective_establishment_id: int | None = None
    if is_admin:
        if establishment_id is not None:
            effective_establishment_id = int(establishment_id)
        else:
            if (business_type or "").strip().lower() == "pharmacy":
                if getattr(current_user, "establishment_id", None) is None:
                    raise HTTPException(status_code=400, detail="Ponto inválido")
                effective_establishment_id = int(current_user.establishment_id)
    else:
        if getattr(current_user, "establishment_id", None) is not None:
            effective_establishment_id = int(current_user.establishment_id)

    created_day = func.date(func.timezone(_APP_TZ, Sale.created_at))

    series_stmt = (
        select(created_day.label("day"), func.coalesce(func.sum(Sale.total), 0).label("total"))
        .where(Sale.company_id == current_user.company_id)
        .where(Sale.branch_id == branch_id)
        .where(func.lower(Sale.business_type) == business_type)
        .where(func.lower(Sale.status) == "paid")
        .where(Sale.created_at >= start_utc)
        .where(Sale.created_at < end_utc)
    )
    if effective_establishment_id is not None:
        series_stmt = series_stmt.where(Sale.establishment_id == effective_establishment_id)
    if is_cashier:
        series_stmt = series_stmt.where(Sale.cashier_id == current_user.id)

    rows = db.execute(
        series_stmt
        .group_by(created_day)
        .order_by(created_day.asc())
    ).all()

    by_day = {r.day: float(r.total or 0) for r in rows}

    points: list[SalesSeriesPointOut] = []
    for i in range(n):
        d = start_local + timedelta(days=i)
        points.append(SalesSeriesPointOut(day=d, total=float(by_day.get(d, 0.0))))

    return points


@router.get("/expiry-alerts", response_model=ExpiryAlertsOut)
def get_expiry_alerts(
    days: int = 30,
    limit: int = 20,
    establishment_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    n = int(days or 30)
    if n < 1:
        n = 1
    if n > 365:
        n = 365

    lim = int(limit or 20)
    if lim < 1:
        lim = 1
    if lim > 200:
        lim = 200

    branch = db.get(Branch, int(current_user.branch_id))
    if branch and branch.company_id == current_user.company_id:
        business_type = (branch.business_type or "retail").strip().lower()
        branch_id = int(branch.id)
    else:
        company = db.get(Company, current_user.company_id)
        business_type = ((company.business_type if company else "retail") or "retail").strip().lower()
        branch_id = int(current_user.branch_id)

    if business_type != "pharmacy":
        raise HTTPException(status_code=400, detail="Alertas de validade disponíveis apenas para farmácia")

    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    effective_establishment_id: int | None = None
    if is_admin:
        if establishment_id is not None:
            effective_establishment_id = int(establishment_id)
        else:
            if getattr(current_user, "establishment_id", None) is not None:
                effective_establishment_id = int(current_user.establishment_id)
    else:
        if getattr(current_user, "establishment_id", None) is not None:
            effective_establishment_id = int(current_user.establishment_id)

    if not effective_establishment_id:
        raise HTTPException(status_code=400, detail="Ponto inválido")

    tz = _get_app_tz()
    today_local = datetime.now(tz).date()
    window_end = today_local + timedelta(days=n)

    rows = db.execute(
        select(Product.id, Product.name, Product.attributes)
        .where(Product.company_id == current_user.company_id)
        .where(Product.branch_id == branch_id)
        .where(Product.establishment_id == effective_establishment_id)
        .where(func.lower(Product.business_type) == business_type)
        .where(Product.is_active.is_(True))
        .order_by(Product.name.asc(), Product.id.asc())
    ).all()

    expired: list[ExpiryAlertItemOut] = []
    expiring: list[ExpiryAlertItemOut] = []

    for pid, name, attrs in rows:
        validade_raw = None
        try:
            validade_raw = (attrs or {}).get("validade")
        except Exception:
            validade_raw = None
        v = _parse_validade(validade_raw)
        if not v:
            continue
        delta = (v - today_local).days
        item = ExpiryAlertItemOut(product_id=int(pid), name=str(name or ""), validade=v.isoformat(), days_to_expire=int(delta))
        if v < today_local:
            expired.append(item)
        elif v <= window_end:
            expiring.append(item)

    expired.sort(key=lambda x: x.days_to_expire)
    expiring.sort(key=lambda x: x.days_to_expire)

    combined = (expired + expiring)[:lim]

    return ExpiryAlertsOut(
        expired_count=len(expired),
        expiring_soon_count=len(expiring),
        days_window=n,
        items=combined,
    )
