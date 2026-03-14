import random
from argparse import ArgumentParser

from sqlalchemy import select, update

from app.database.connection import SessionLocal
from app.models.branch import Branch
from app.models.company import Company
from app.models.product import Product
from app.models.product_stock import ProductStock
from app.models.stock_location import StockLocation
from app.models.supplier import Supplier


def _product_min_stock(bt: str) -> float:
    if bt == "restaurant":
        return round(random.uniform(5, 20), 0)
    if bt == "bar":
        return round(random.uniform(10, 30), 0)
    if bt == "butcher":
        return round(random.uniform(15, 40), 0)
    if bt == "services":
        return 0
    return round(random.uniform(8, 25), 0)


def _product_initial_stock(bt: str, min_stock: float) -> float:
    if bt == "services":
        return 0
    buffer_factor = random.uniform(1.5, 3.0)
    qty = round(min_stock * buffer_factor, 0)
    return max(qty, min_stock + 5)


def _ensure_default_locations(db, *, company_id: int, branch_id: int) -> None:
    existing = db.scalars(
        select(StockLocation)
        .where(StockLocation.company_id == company_id)
        .where(StockLocation.branch_id == branch_id)
    ).all()
    if existing:
        return

    loja = StockLocation(
        company_id=company_id,
        branch_id=branch_id,
        type="store",
        name="Loja Principal",
        is_default=True,
        is_active=True,
    )
    armazem = StockLocation(
        company_id=company_id,
        branch_id=branch_id,
        type="warehouse",
        name="Armazém",
        is_default=False,
        is_active=True,
    )
    db.add(loja)
    db.add(armazem)
    db.commit()


def main() -> None:
    parser = ArgumentParser(description="Atualizar min_stock e criar stock inicial para produtos existentes.")
    parser.add_argument("--company-id", type=int, default=None, help="ID da empresa para limitar atualização (opcional).")
    parser.add_argument("--dry-run", action="store_true", help="Apenas mostrar o que seria feito, sem executar.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        stmt = select(Product)
        if args.company_id:
            stmt = stmt.where(Product.company_id == args.company_id)
        products = db.scalars(stmt).all()

        if not products:
            print("Nenhum produto encontrado.")
            return

        print(f"Encontrados {len(products)} produtos para verificar.")

        for product in products:
            # Atualizar min_stock se for None ou 0
            if product.min_stock is None or product.min_stock == 0:
                new_min = _product_min_stock(product.business_type or "retail")
                if args.dry_run:
                    print(f"[DRY-RUN] Produto {product.id} ({product.name}): min_stock -> {new_min}")
                else:
                    product.min_stock = new_min
                    print(f"Produto {product.id} ({product.name}): min_stock -> {new_min}")
            else:
                new_min = product.min_stock

            # Garantir local padrão para a filial
            _ensure_default_locations(db, company_id=product.company_id, branch_id=product.branch_id)

            # Obter local padrão da filial
            default_loc = db.scalar(
                select(StockLocation)
                .where(StockLocation.company_id == product.company_id)
                .where(StockLocation.branch_id == product.branch_id)
                .where(StockLocation.is_default == True)
                .where(StockLocation.type == "store")
            )
            if not default_loc:
                print(f"[AVISO] Produto {product.id}: sem local padrão da loja para criar stock.")
                continue

            # Verificar se já existe stock para este produto no local padrão
            existing_stock = db.scalar(
                select(ProductStock)
                .where(ProductStock.product_id == product.id)
                .where(ProductStock.location_id == default_loc.id)
            )

            if product.track_stock and not existing_stock:
                initial_qty = _product_initial_stock(product.business_type or "retail", new_min)
                if args.dry_run:
                    print(f"[DRY-RUN] Produto {product.id} ({product.name}): criar stock qty_on_hand={initial_qty} na location {default_loc.id}")
                else:
                    stock = ProductStock(
                        company_id=product.company_id,
                        branch_id=product.branch_id,
                        product_id=product.id,
                        location_id=default_loc.id,
                        qty_on_hand=initial_qty,
                    )
                    db.add(stock)
                    print(f"Produto {product.id} ({product.name}): criado stock qty_on_hand={initial_qty} na location {default_loc.id}")

        if not args.dry_run:
            db.commit()
            print("Atualizações concluídas e salvas.")
        else:
            print("Modo dry-run: nenhuma alteração foi salva.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
