#!/usr/bin/env python3
"""
Seed de produtos para o Restaurante Mutxutxu (company_id=10)
Segue o mesmo padrão utilizado para ferragem e reprografia
"""

from argparse import ArgumentParser
from uuid import uuid4
from sqlalchemy import select, func

from app.database.connection import SessionLocal
from app.models.branch import Branch
from app.models.company import Company
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_stock import ProductStock
from app.models.stock_location import StockLocation

# Dados dos produtos do Mutxutxu extraídos do PDF
MUTXUTXU_PRODUCTS = [
    {"name": "2M garrafa", "price": 80.00, "stock": 100, "category": "Bebidas"},
    {"name": "2M lata", "price": 90.00, "stock": 100, "category": "Bebidas"},
    {"name": "Agua Pequena", "price": 50.00, "stock": 100, "category": "Bebidas"},
    {"name": "Agua Tonica", "price": 60.00, "stock": 100, "category": "Bebidas"},
    {"name": "Agua grande", "price": 100.00, "stock": 100, "category": "Bebidas"},
    {"name": "Amarula", "price": 1400.00, "stock": 100, "category": "Bebidas"},
    {"name": "Azinhas", "price": 300.00, "stock": 104, "category": "Bebidas"},
    {"name": "Bife Completo", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "Bull dog", "price": 3300.00, "stock": 100, "category": "Bebidas"},
    {"name": "C double burger", "price": 500.00, "stock": 10, "category": "Pratos"},
    {"name": "Cabeca de Peixe", "price": 200.00, "stock": 10, "category": "Pratos"},
    {"name": "Cabeca de Vaca", "price": 200.00, "stock": 10, "category": "Pratos"},
    {"name": "Caldo verde", "price": 150.00, "stock": 10, "category": "Pratos"},
    {"name": "Cappy", "price": 80.00, "stock": 100, "category": "Bebidas"},
    {"name": "Carne de porco", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "Ceres", "price": 200.00, "stock": 100, "category": "Bebidas"},
    {"name": "Champanhe Anabela", "price": 1300.00, "stock": 100, "category": "Bebidas"},
    {"name": "Champanhe JS", "price": 1200.00, "stock": 100, "category": "Bebidas"},
    {"name": "Champanhe Martini Rose", "price": 1200.00, "stock": 100, "category": "Bebidas"},
    {"name": "Champanhe Toste", "price": 1500.00, "stock": 100, "category": "Bebidas"},
    {"name": "Chamussas", "price": 25.00, "stock": 10, "category": "Pratos"},
    {"name": "Chourico", "price": 300.00, "stock": 10, "category": "Pratos"},
    {"name": "Cochinhas", "price": 30.00, "stock": 9, "category": "Pratos"},
    {"name": "Compal", "price": 200.00, "stock": 100, "category": "Bebidas"},
    {"name": "Dobrada", "price": 200.00, "stock": 10, "category": "Pratos"},
    {"name": "Dry Lemon", "price": 150.00, "stock": 100, "category": "Bebidas"},
    {"name": "Escape Vodka", "price": 1000.00, "stock": 100, "category": "Bebidas"},
    {"name": "Four Causin Grade", "price": 1600.00, "stock": 100, "category": "Bebidas"},
    {"name": "Frango 1 quarto", "price": 300.00, "stock": 10, "category": "Pratos"},
    {"name": "Frango a Passarinho", "price": 1250.00, "stock": 10, "category": "Pratos"},
    {"name": "Frango assado 1", "price": 1200.00, "stock": 10, "category": "Pratos"},
    {"name": "Frango assado meio", "price": 600.00, "stock": 10, "category": "Pratos"},
    {"name": "Galinha Fumado", "price": 1500.00, "stock": 10, "category": "Pratos"},
    {"name": "Galo Dourado", "price": 1100.00, "stock": 100, "category": "Bebidas"},
    {"name": "Gatao", "price": 1500.00, "stock": 100, "category": "Bebidas"},
    {"name": "Gordon", "price": 1100.00, "stock": 100, "category": "Bebidas"},
    {"name": "Grants", "price": 1800.00, "stock": 100, "category": "Bebidas"},
    {"name": "HENICKER", "price": 100.00, "stock": 500, "category": "Bebidas"},
    {"name": "Hamburger Completo", "price": 300.00, "stock": 8, "category": "Pratos"},
    {"name": "Hanked Bannister", "price": 1100.00, "stock": 100, "category": "Bebidas"},
    {"name": "Havelock", "price": 1100.00, "stock": 100, "category": "Bebidas"},
    {"name": "Humburger S", "price": 250.00, "stock": 10, "category": "Pratos"},
    {"name": "Joh walker red", "price": 1800.00, "stock": 100, "category": "Bebidas"},
    {"name": "John Walker black", "price": 3500.00, "stock": 100, "category": "Bebidas"},
    {"name": "Maicgregor", "price": 1500.00, "stock": 100, "category": "Bebidas"},
    {"name": "Martine", "price": 1400.00, "stock": 100, "category": "Bebidas"},
    {"name": "Mutxutxu de galinha", "price": 200.00, "stock": 110, "category": "Pratos"},
    {"name": "Pizza 4 estacoes", "price": 100.00, "stock": 10, "category": "Pratos"},
    {"name": "Pizza de atum", "price": 700.00, "stock": 10, "category": "Pratos"},
    {"name": "Pizza de frango", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "Pizza vegetariana", "price": 700.00, "stock": 10, "category": "Pratos"},
    {"name": "Quinta da bolota", "price": 1200.00, "stock": 100, "category": "Bebidas"},
    {"name": "Red Bull", "price": 150.00, "stock": 100, "category": "Bebidas"},
    {"name": "Refresco em lata", "price": 60.00, "stock": 97, "category": "Bebidas"},
    {"name": "Rose Grande", "price": 1600.00, "stock": 100, "category": "Bebidas"},
    {"name": "Rusian", "price": 1000.00, "stock": 100, "category": "Bebidas"},
    {"name": "Silk spice", "price": 1800.00, "stock": 100, "category": "Bebidas"},
    {"name": "Sopa de Feijao", "price": 150.00, "stock": 10, "category": "Pratos"},
    {"name": "Sopa de legumes", "price": 150.00, "stock": 10, "category": "Pratos"},
    {"name": "Takeaway", "price": 30.00, "stock": 100, "category": "Pratos"},
    {"name": "Tbone", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "Tostas com batata frita", "price": 300.00, "stock": 10, "category": "Pratos"},
    {"name": "Worce", "price": 300.00, "stock": 10, "category": "Pratos"},
    {"name": "altum", "price": 800.00, "stock": 10, "category": "Bebidas"},
    {"name": "bermine", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "bife trinchado", "price": 700.00, "stock": 101, "category": "Pratos"},
    {"name": "brizer", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "brutal", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "budweiser", "price": 100.00, "stock": 10, "category": "Bebidas"},
    {"name": "cape ruby", "price": 1100.00, "stock": 10, "category": "Bebidas"},
    {"name": "casal garcia", "price": 1200.00, "stock": 10, "category": "Bebidas"},
    {"name": "castle lite", "price": 100.00, "stock": 10, "category": "Bebidas"},
    {"name": "celler cast", "price": 1100.00, "stock": 100, "category": "Bebidas"},
    {"name": "chima", "price": 100.00, "stock": 10, "category": "Sobremesas"},
    {"name": "dose de arroz", "price": 100.00, "stock": 10, "category": "Pratos"},
    {"name": "dose de batata", "price": 100.00, "stock": 10, "category": "Pratos"},
    {"name": "drosdy hof", "price": 800.00, "stock": 10, "category": "Bebidas"},
    {"name": "duas quintas", "price": 1100.00, "stock": 10, "category": "Bebidas"},
    {"name": "filetes", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "gazela", "price": 1100.00, "stock": 10, "category": "Bebidas"},
    {"name": "hunters dray", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "hunters gold", "price": 100.00, "stock": 10, "category": "Bebidas"},
    {"name": "jamson", "price": 1500.00, "stock": 100, "category": "Bebidas"},
    {"name": "lemone", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "lulas", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "mao de vaca", "price": 200.00, "stock": 9, "category": "Pratos"},
    {"name": "pandora", "price": 1100.00, "stock": 10, "category": "Bebidas"},
    {"name": "peixe chambo grande", "price": 1000.00, "stock": 10, "category": "Pratos"},
    {"name": "peixe chambo medio", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "peixe chambo pequeno", "price": 600.00, "stock": 10, "category": "Pratos"},
    {"name": "prego no pao", "price": 300.00, "stock": 10, "category": "Pratos"},
    {"name": "prego no prato", "price": 450.00, "stock": 10, "category": "Pratos"},
    {"name": "preta grande", "price": 80.00, "stock": 10, "category": "Bebidas"},
    {"name": "preta lata", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "preta pequena", "price": 100.00, "stock": 10, "category": "Bebidas"},
    {"name": "saladas", "price": 75.00, "stock": 10, "category": "Sobremesas"},
    {"name": "sande de ovo", "price": 200.00, "stock": 10, "category": "Pratos"},
    {"name": "segredo sao miguel", "price": 1200.00, "stock": 10, "category": "Bebidas"},
    {"name": "spin", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "super bock", "price": 80.00, "stock": 10, "category": "Bebidas"},
    {"name": "vinho cabriz", "price": 1200.00, "stock": 10, "category": "Bebidas"},
    {"name": "vinho portada", "price": 1200.00, "stock": 10, "category": "Bebidas"}
]

COMPANY_ID = 10
BUSINESS_TYPE = "restaurant"

def _ensure_default_categories(db, *, company_id: int, business_type: str) -> list[ProductCategory]:
    """Garante que as categorias padrão existam para a empresa"""
    defaults = ["Entradas", "Pratos", "Bebidas", "Sobremesas", "Outros"]
    
    existing = {
        (r.name or "").strip().lower(): r
        for r in db.scalars(
            select(ProductCategory)
            .where(ProductCategory.company_id == company_id)
            .where(ProductCategory.business_type == business_type)
        ).all()
    }
    
    created_any = False
    for name in defaults:
        key = name.strip().lower()
        if key in existing:
            continue
        cat = ProductCategory(company_id=company_id, business_type=business_type, name=name)
        db.add(cat)
        created_any = True
    
    if created_any:
        db.commit()
    
    rows = db.scalars(
        select(ProductCategory)
        .where(ProductCategory.company_id == company_id)
        .where(ProductCategory.business_type == business_type)
        .order_by(ProductCategory.name.asc())
    ).all()
    return list(rows or [])

def _ensure_default_locations(db, *, company_id: int, branch_id: int):
    """Garante que as localizações padrão existam"""
    loja = StockLocation(
        company_id=company_id,
        branch_id=branch_id,
        type="store",
        name="Loja",
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

def _get_default_store_location_id(db, *, company_id: int, branch_id: int) -> int:
    """Obtém o ID da localização padrão (store)"""
    _ensure_default_locations(db, company_id=company_id, branch_id=branch_id)
    
    loc_id = db.scalar(
        select(StockLocation.id)
        .where(StockLocation.company_id == company_id)
        .where(StockLocation.branch_id == branch_id)
        .where(StockLocation.type == "store")
        .where(StockLocation.is_default.is_(True))
        .where(StockLocation.is_active.is_(True))
        .limit(1)
    )
    if not loc_id:
        raise RuntimeError(f"Sem local padrão (store) para company_id={company_id} branch_id={branch_id}")
    return int(loc_id)

def _get_category_id_by_name(categories: list[ProductCategory], name: str) -> int | None:
    """Obtém o ID da categoria pelo nome"""
    for cat in categories:
        if cat.name and cat.name.strip().lower() == name.strip().lower():
            return cat.id
    return None

def main():
    parser = ArgumentParser(description="Seed de produtos para o Restaurante Mutxutxu")
    parser.add_argument("--force", action="store_true", help="Força a recriação dos produtos")
    args = parser.parse_args()
    
    print("🍽️ SEED DE PRODUTOS - RESTAURANTE MUTXUTXU")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # 1. Identificar a empresa
        company = db.execute(
            select(Company).where(Company.id == COMPANY_ID)
        ).scalar_one_or_none()
        
        if not company:
            print(f"❌ Empresa {COMPANY_ID} não encontrada!")
            return
        
        print(f"✅ Empresa encontrada: {company.name} (ID: {company.id})")
        
        # 2. Identificar a filial do restaurante
        branch = db.execute(
            select(Branch)
            .where(Branch.company_id == COMPANY_ID)
            .where(Branch.business_type == BUSINESS_TYPE)
            .where(Branch.is_active.is_(True))
        ).scalar_one_or_none()
        
        if not branch:
            print(f"❌ Filial do tipo '{BUSINESS_TYPE}' não encontrada para a empresa {COMPANY_ID}!")
            return
        
        print(f"✅ Filial encontrada: {branch.name} (ID: {branch.id}) | Tipo: {branch.business_type}")
        
        # 3. Garantir categorias
        print("\n📁 Verificando categorias...")
        categories = _ensure_default_categories(db, company_id=COMPANY_ID, business_type=BUSINESS_TYPE)
        print(f"✅ {len(categories)} categorias prontas:")
        for cat in categories:
            print(f"   - {cat.name} (ID: {cat.id})")
        
        # 4. Obter localização padrão
        print("\n📍 Verificando localização padrão...")
        default_location_id = _get_default_store_location_id(db, company_id=COMPANY_ID, branch_id=branch.id)
        print(f"✅ Localização padrão: ID {default_location_id}")
        
        # 5. Verificar produtos existentes
        existing_count = db.scalar(
            select(func.count(Product.id))
            .where(Product.company_id == COMPANY_ID)
            .where(Product.branch_id == branch.id)
            .where(Product.business_type == BUSINESS_TYPE)
        )
        
        if existing_count > 0 and not args.force:
            print(f"\n⚠️  Já existem {existing_count} produtos na filial.")
            print("   Use --force para recriar todos os produtos.")
            return
        
        if args.force and existing_count > 0:
            print(f"\n🗑️  Removendo {existing_count} produtos existentes...")
            # Remover stocks primeiro
            from sqlalchemy import delete
            db.execute(
                delete(ProductStock)
                .where(ProductStock.company_id == COMPANY_ID)
                .where(ProductStock.branch_id == branch.id)
            )
            # Remover produtos
            db.execute(
                delete(Product)
                .where(Product.company_id == COMPANY_ID)
                .where(Product.branch_id == branch.id)
                .where(Product.business_type == BUSINESS_TYPE)
            )
            db.commit()
            print("✅ Produtos existentes removidos.")
        
        # 6. Criar produtos
        print(f"\n🚀 Criando {len(MUTXUTXU_PRODUCTS)} produtos...")
        
        success_count = 0
        error_count = 0
        
        for i, product_data in enumerate(MUTXUTXU_PRODUCTS, 1):
            try:
                # Mapear categoria
                category_id = _get_category_id_by_name(categories, product_data["category"])
                if not category_id:
                    print(f"❌ {i:3d}. {product_data['name']} - Categoria '{product_data['category']}' não encontrada")
                    error_count += 1
                    continue
                
                # Criar produto
                product = Product(
                    company_id=COMPANY_ID,
                    branch_id=branch.id,
                    default_location_id=default_location_id,
                    category_id=category_id,
                    business_type=BUSINESS_TYPE,
                    name=product_data["name"],
                    sku=f"RES-{COMPANY_ID}-{i:03d}",
                    barcode=None,
                    unit="un",
                    price=product_data["price"],
                    cost=product_data["price"] * 0.7,  # 70% do preço
                    tax_rate=0,
                    min_stock=max(1, product_data["stock"] // 4),
                    track_stock=True,
                    is_active=True,
                    attributes={"description": f"Produto do cardápio: {product_data['name']}"}
                )
                db.add(product)
                db.flush()
                
                # Criar registro de estoque
                stock = ProductStock(
                    company_id=COMPANY_ID,
                    branch_id=branch.id,
                    product_id=product.id,
                    location_id=default_location_id,
                    qty_on_hand=product_data["stock"],
                )
                db.add(stock)
                
                print(f"✅ {i:3d}. {product_data['name']} - MZN {product_data['price']:7.2f} | {product_data['category']} | Estoque: {product_data['stock']}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ {i:3d}. {product_data['name']} - ERRO: {e}")
                error_count += 1
                db.rollback()
                continue
        
        db.commit()
        
        print(f"\n" + "=" * 60)
        print(f"🎉 SEED CONCLUÍDO!")
        print(f"✅ Sucesso: {success_count} produtos")
        print(f"❌ Erros: {error_count} produtos")
        print(f"📊 Total: {success_count + error_count} produtos")
        
        if success_count > 0:
            print(f"\n🌐 Os produtos do Mutxutxu estão prontos!")
            print(f"📦 Acesse o sistema para verificar os produtos.")
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
