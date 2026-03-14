import argparse
from sqlalchemy import delete, select

from app.database.connection import SessionLocal
from app.models.branch import Branch
from app.models.company import Company
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_stock import ProductStock
from app.models.sale_item import SaleItem
from app.models.stock_movement import StockMovement
from app.models.quote_item import QuoteItem


def clear_branch_products(branch_id: int, dry_run: bool = False) -> None:
    """
    Apaga todos os produtos (e registos relacionados) de uma filial específica.
    Remove: StockMovement, OrderItem, SaleItem, QuoteItem, ProductStock, ProductImage e Product.
    """
    db = SessionLocal()
    try:
        branch = db.scalar(select(Branch).where(Branch.id == branch_id))
        if not branch:
            print(f"Filial com ID {branch_id} não encontrada.")
            return

        company = db.scalar(select(Company).where(Company.id == branch.company_id))
        print(f"Filial encontrada: {company.name} / {branch.name} (business_type={branch.business_type})")

        # Contar produtos a apagar
        products = db.scalars(select(Product).where(Product.branch_id == branch_id)).all()
        if not products:
            print("Nenhum produto encontrado nesta filial.")
            return

        product_ids = [p.id for p in products]
        print(f"Encontrados {len(products)} produtos para apagar.")

        if dry_run:
            print("[DRY-RUN] Nenhuma alteração será feita.")
            for p in products:
                print(f" - {p.id}: {p.name}")
            return

        # Apagar stock_movements que referenciam estes produtos
        del_stock_movements = delete(StockMovement).where(StockMovement.product_id.in_(product_ids))
        result_stock_movements = db.execute(del_stock_movements)
        print(f"Apagados {result_stock_movements.rowcount} registos de stock_movements.")

        # Apagar order_items que referenciam estes produtos
        del_order_items = delete(OrderItem).where(OrderItem.product_id.in_(product_ids))
        result_order_items = db.execute(del_order_items)
        print(f"Apagados {result_order_items.rowcount} registos de order_items.")

        # Apagar sale_items que referenciam estes produtos
        del_sale_items = delete(SaleItem).where(SaleItem.product_id.in_(product_ids))
        result_sale_items = db.execute(del_sale_items)
        print(f"Apagados {result_sale_items.rowcount} registos de sale_items.")

        # Apagar quote_items que referenciam estes produtos
        del_quote_items = delete(QuoteItem).where(QuoteItem.product_id.in_(product_ids))
        result_quote_items = db.execute(del_quote_items)
        print(f"Apagados {result_quote_items.rowcount} registos de quote_items.")

        # Apagar stock dos produtos
        del_stock = delete(ProductStock).where(ProductStock.product_id.in_(product_ids))
        result_stock = db.execute(del_stock)
        print(f"Apagados {result_stock.rowcount} registos de stock.")

        # Apagar imagens dos produtos
        del_img = delete(ProductImage).where(ProductImage.product_id.in_(product_ids))
        result_img = db.execute(del_img)
        print(f"Apagados {result_img.rowcount} registos de imagem.")

        # Apagar os produtos
        del_prod = delete(Product).where(Product.branch_id == branch_id)
        result_prod = db.execute(del_prod)
        print(f"Apagados {result_prod.rowcount} produtos.")

        db.commit()
        print("Produtos e dados relacionados apagados com sucesso.")

    finally:
        db.close()


def list_branches() -> None:
    """Lista todas as filiais com ID, nome da empresa, nome da filial e business_type."""
    db = SessionLocal()
    try:
        # Fazer join para carregar a empresa
        branches = db.scalars(
            select(Branch)
            .join(Company, Branch.company_id == Company.id)
            .order_by(Company.name, Branch.name)
        ).all()
        if not branches:
            print("Nenhuma filial encontrada.")
            return
        print("Filiais disponíveis:")
        print("-" * 60)
        for b in branches:
            # Carregar a empresa explicitamente
            company = db.scalar(select(Company).where(Company.id == b.company_id))
            print(f"[{b.id}] {company.name} / {b.name} ({b.business_type})")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Apagar todos os produtos de uma filial específica.")
    parser.add_argument("--branch-id", type=int, help="ID da filal para apagar produtos.")
    parser.add_argument("--list", action="store_true", help="Listar todas as filiais e sair.")
    parser.add_argument("--dry-run", action="store_true", help="Apenas mostrar o que seria apagado, sem executar.")
    args = parser.parse_args()

    if args.list:
        list_branches()
        return

    if not args.branch_id:
        parser.error("É necessário informar --branch-id ou usar --list para ver as filiais.")

    clear_branch_products(args.branch_id, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
