from datetime import date, datetime, time, timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends
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
from app.schemas.dashboard import DashboardSummaryOut, SalesSeriesPointOut

router = APIRouter()


_APP_TZ = "Africa/Maputo"


def _get_app_tz():
    try:
        return ZoneInfo(_APP_TZ)
    except ZoneInfoNotFoundError:
        return timezone(timedelta(hours=2))


@router.get("/summary", response_model=DashboardSummaryOut)
def get_dashboard_summary(
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

    products_total = db.scalar(
        select(func.count(Product.id))
        .where(Product.company_id == current_user.company_id)
        .where(Product.branch_id == branch_id)
        .where(Product.business_type == business_type)
    )

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

    low_stock_default_count = db.scalar(
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

    low_stock_warehouse_count = db.scalar(
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

    stock_values = db.execute(
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
    ).one()

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
