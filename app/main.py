from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import os
import time

from app.routes import auth, branches, companies, customers, dashboard, debts, debug_menu, fiscal_documents, legacy_public_api, orders, product_categories, product_stocks, products, public_menu, quotes, reports, restaurant_tables, sales, stock_adjustments, stock_locations, stock_movements, stock_transfers, supplier_payments, supplier_purchases, suppliers, users
from app.settings import Settings

settings = Settings()

logger = logging.getLogger(__name__)

app = FastAPI(title="ERPCRM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=500)


@app.middleware("http")
async def add_process_time_header(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}"
    return response

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(branches.router, prefix="/branches", tags=["branches"])
app.include_router(companies.router, prefix="/companies", tags=["companies"])
app.include_router(customers.router, prefix="/customers", tags=["customers"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(restaurant_tables.router, prefix="/restaurant-tables", tags=["restaurant-tables"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(sales.router, prefix="/sales", tags=["sales"])
app.include_router(debts.router, prefix="/debts", tags=["debts"])
app.include_router(fiscal_documents.router, prefix="/fiscal-documents", tags=["fiscal-documents"])
app.include_router(quotes.router, prefix="/quotes", tags=["quotes"])
app.include_router(public_menu.router, prefix="/public", tags=["public"])
app.include_router(debug_menu.router, prefix="/public", tags=["debug"])
app.include_router(legacy_public_api.router, prefix="/api", tags=["public-legacy"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(stock_adjustments.router, prefix="/stock-adjustments", tags=["stock-adjustments"])
app.include_router(product_stocks.router, prefix="/product-stocks", tags=["product-stocks"])
app.include_router(stock_locations.router, prefix="/stock-locations", tags=["stock-locations"])
app.include_router(stock_movements.router, prefix="/stock-movements", tags=["stock-movements"])
app.include_router(stock_transfers.router, prefix="/stock-transfers", tags=["stock-transfers"])
app.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
app.include_router(supplier_purchases.router, prefix="/supplier-purchases", tags=["supplier-purchases"])
app.include_router(supplier_payments.router, prefix="/supplier-payments", tags=["supplier-payments"])
app.include_router(product_categories.router, prefix="/product-categories", tags=["product-categories"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(users.router, prefix="/users", tags=["users"])

os.makedirs(settings.upload_dir, exist_ok=True)
logger.warning("UPLOAD_DIR=%s", settings.upload_dir)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/health")
def health():
    return {"status": "ok"}
