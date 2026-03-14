import argparse

from sqlalchemy import delete, func, select

from app.database.connection import SessionLocal
from app.models.branch import Branch
from app.models.company import Company
from app.models.customer import Customer
from app.models.fiscal_document import FiscalDocument
from app.models.fiscal_document_line import FiscalDocumentLine
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_image import ProductImage
from app.models.product_stock import ProductStock
from app.models.quote import Quote
from app.models.quote_item import QuoteItem
from app.models.restaurant_table import RestaurantTable
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.stock_location import StockLocation
from app.models.stock_movement import StockMovement
from app.models.stock_transfer import StockTransfer
from app.models.supplier import Supplier
from app.models.supplier_payment import SupplierPayment
from app.models.supplier_purchase import SupplierPurchase
from app.models.user import User
from app.models.user_role import UserRole


def _count(db, model, company_ids: list[int]) -> int:
    return int(db.scalar(select(func.count()).select_from(model).where(model.company_id.in_(company_ids))) or 0)


def main():
    parser = argparse.ArgumentParser(description="Apaga empresas e dados relacionados por company_id")
    parser.add_argument("--ids", nargs="+", type=int, required=True, help="IDs das empresas para apagar")
    parser.add_argument("--yes", action="store_true", help="Não pedir confirmação")
    args = parser.parse_args()

    company_ids = sorted(set(args.ids))
    if not company_ids:
        print("Nenhum ID informado")
        return

    db = SessionLocal()
    try:
        companies = db.scalars(select(Company).where(Company.id.in_(company_ids)).order_by(Company.id)).all()
        found_ids = [c.id for c in companies]
        missing = [cid for cid in company_ids if cid not in found_ids]

        print("Empresas selecionadas para apagar:")
        for c in companies:
            print(f"- id={c.id} name={c.name} business_type={c.business_type}")
        if missing:
            print(f"IDs não encontrados (serão ignorados): {missing}")

        if not companies:
            print("Nenhuma empresa encontrada para os IDs fornecidos")
            return

        effective_ids = found_ids

        # Prévia de impacto (contagens)
        models = [
            (Branch, "branches"),
            (User, "users"),
            (UserRole, "user_roles"),
            (Customer, "customers"),
            (Supplier, "suppliers"),
            (SupplierPurchase, "supplier_purchases"),
            (SupplierPayment, "supplier_payments"),
            (StockLocation, "stock_locations"),
            (StockTransfer, "stock_transfers"),
            (StockMovement, "stock_movements"),
            (ProductCategory, "product_categories"),
            (Product, "products"),
            (ProductStock, "product_stocks"),
            (ProductImage, "product_images"),
            (Sale, "sales"),
            (SaleItem, "sale_items"),
            (Order, "orders"),
            (OrderItem, "order_items"),
            (Quote, "quotes"),
            (QuoteItem, "quote_items"),
            (RestaurantTable, "restaurant_tables"),
            (FiscalDocument, "fiscal_documents"),
            (FiscalDocumentLine, "fiscal_document_lines"),
        ]

        print("\nPrévia de registos a remover (por tabela):")
        for model, label in models:
            try:
                cnt = _count(db, model, effective_ids)
            except Exception as e:
                print(f"- {label}: erro ao contar ({e})")
                continue
            print(f"- {label}: {cnt}")

        print(f"- companies: {len(companies)}")

        if not args.yes:
            raw = input("\nCONFIRMA apagar PERMANENTEMENTE estes dados? (digite 'SIM' para confirmar): ")
            if raw.strip().upper() != "SIM":
                print("Operação cancelada")
                return

        # Ordem de delete: tabelas filhas -> pais
        delete_steps = [
            (FiscalDocumentLine, "fiscal_document_lines"),
            (SaleItem, "sale_items"),
            (OrderItem, "order_items"),
            (QuoteItem, "quote_items"),
            (ProductImage, "product_images"),
            (ProductStock, "product_stocks"),
            (StockMovement, "stock_movements"),
            (StockTransfer, "stock_transfers"),
            (FiscalDocument, "fiscal_documents"),
            (Sale, "sales"),
            (Order, "orders"),
            (Quote, "quotes"),
            (RestaurantTable, "restaurant_tables"),
            (Product, "products"),
            (ProductCategory, "product_categories"),
            (StockLocation, "stock_locations"),
            (SupplierPayment, "supplier_payments"),
            (SupplierPurchase, "supplier_purchases"),
            (Supplier, "suppliers"),
            (Customer, "customers"),
            (UserRole, "user_roles"),
            (User, "users"),
            (Branch, "branches"),
        ]

        for model, label in delete_steps:
            db.execute(delete(model).where(model.company_id.in_(effective_ids)))

        db.execute(delete(Company).where(Company.id.in_(effective_ids)))

        db.commit()
        print("\nApagado com sucesso!")
        print(f"Empresas removidas: {effective_ids}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
