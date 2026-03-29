#!/usr/bin/env python3
"""
Seed de produtos para o Restaurante Mutxutxu (company_id=10)
Versão local usando SQLite direto
"""

import sqlite3
from uuid import uuid4

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

def main():
    print("🍽️ SEED DE PRODUTOS - RESTAURANTE MUTXUTXU (LOCAL)")
    print("=" * 60)
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    try:
        # 1. Identificar a empresa
        cursor.execute("SELECT id, name FROM companies WHERE id = ?", (COMPANY_ID,))
        company = cursor.fetchone()
        
        if not company:
            print(f"❌ Empresa {COMPANY_ID} não encontrada!")
            return
        
        print(f"✅ Empresa encontrada: {company[1]} (ID: {company[0]})")
        
        # 2. Identificar a filial do restaurante
        cursor.execute(
            "SELECT id, name, business_type FROM branches WHERE company_id = ? AND business_type = ? AND is_active = 1",
            (COMPANY_ID, BUSINESS_TYPE)
        )
        branch = cursor.fetchone()
        
        if not branch:
            print(f"❌ Filial do tipo '{BUSINESS_TYPE}' não encontrada para a empresa {COMPANY_ID}!")
            return
        
        print(f"✅ Filial encontrada: {branch[1]} (ID: {branch[0]}) | Tipo: {branch[2]}")
        
        # 3. Garantir categorias
        print("\n📁 Verificando categorias...")
        categories = {}
        
        default_categories = ["Entradas", "Pratos", "Bebidas", "Sobremesas", "Outros"]
        
        for cat_name in default_categories:
            cursor.execute(
                "SELECT id FROM product_categories WHERE company_id = ? AND business_type = ? AND name = ?",
                (COMPANY_ID, BUSINESS_TYPE, cat_name)
            )
            cat = cursor.fetchone()
            
            if not cat:
                cursor.execute(
                    "INSERT INTO product_categories (company_id, business_type, name) VALUES (?, ?, ?)",
                    (COMPANY_ID, BUSINESS_TYPE, cat_name)
                )
                cat_id = cursor.lastrowid
                print(f"   🆕 {cat_name} (ID: {cat_id})")
            else:
                cat_id = cat[0]
                print(f"   ✅ {cat_name} (ID: {cat_id})")
            
            categories[cat_name] = cat_id
        
        # 4. Garantir localização padrão
        print("\n📍 Verificando localização padrão...")
        
        cursor.execute(
            "SELECT id FROM stock_locations WHERE company_id = ? AND branch_id = ? AND type = 'store' AND is_default = 1",
            (COMPANY_ID, branch[0])
        )
        location = cursor.fetchone()
        
        if not location:
            cursor.execute(
                "INSERT INTO stock_locations (company_id, branch_id, type, name, is_default, is_active) VALUES (?, ?, ?, ?, ?, ?)",
                (COMPANY_ID, branch[0], "store", "Loja", 1, 1)
            )
            default_location_id = cursor.lastrowid
            print(f"   🆕 Localização criada: ID {default_location_id}")
        else:
            default_location_id = location[0]
            print(f"   ✅ Localização encontrada: ID {default_location_id}")
        
        # 5. Verificar produtos existentes
        cursor.execute(
            "SELECT COUNT(*) FROM products WHERE company_id = ? AND branch_id = ? AND business_type = ?",
            (COMPANY_ID, branch[0], BUSINESS_TYPE)
        )
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"\n⚠️  Já existem {existing_count} produtos na filial.")
            print("   Removendo produtos existentes...")
            
            # Remover stocks
            cursor.execute(
                "DELETE FROM product_stocks WHERE company_id = ? AND branch_id = ?",
                (COMPANY_ID, branch[0])
            )
            
            # Remover produtos
            cursor.execute(
                "DELETE FROM products WHERE company_id = ? AND branch_id = ? AND business_type = ?",
                (COMPANY_ID, branch[0], BUSINESS_TYPE)
            )
            
            print("✅ Produtos existentes removidos.")
        
        # 6. Criar produtos
        print(f"\n🚀 Criando {len(MUTXUTXU_PRODUCTS)} produtos...")
        
        success_count = 0
        error_count = 0
        
        for i, product_data in enumerate(MUTXUTXU_PRODUCTS, 1):
            try:
                # Mapear categoria
                category_name = product_data["category"]
                if category_name not in categories:
                    print(f"❌ {i:3d}. {product_data['name']} - Categoria '{category_name}' não encontrada")
                    error_count += 1
                    continue
                
                category_id = categories[category_name]
                
                # Inserir produto
                cursor.execute("""
                    INSERT INTO products (
                        company_id, branch_id, default_location_id, category_id, business_type,
                        name, sku, unit, price, cost, tax_rate, min_stock, track_stock, is_active,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """, (
                    COMPANY_ID, branch[0], default_location_id, category_id, BUSINESS_TYPE,
                    product_data["name"], f"RES-{COMPANY_ID}-{i:03d}", "un",
                    product_data["price"], product_data["price"] * 0.7, 0,
                    max(1, product_data["stock"] // 4), 1, 1
                ))
                
                product_id = cursor.lastrowid
                
                # Inserir estoque
                cursor.execute("""
                    INSERT INTO product_stocks (
                        company_id, branch_id, product_id, location_id, qty_on_hand,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """, (
                    COMPANY_ID, branch[0], product_id, default_location_id, product_data["stock"]
                ))
                
                print(f"✅ {i:3d}. {product_data['name']} - MZN {product_data['price']:7.2f} | {product_data['category']} | Estoque: {product_data['stock']}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ {i:3d}. {product_data['name']} - ERRO: {e}")
                error_count += 1
                conn.rollback()
                continue
        
        conn.commit()
        
        print(f"\n" + "=" * 60)
        print(f"🎉 SEED CONCLUÍDO!")
        print(f"✅ Sucesso: {success_count} produtos")
        print(f"❌ Erros: {error_count} produtos")
        print(f"📊 Total: {success_count + error_count} produtos")
        
        if success_count > 0:
            print(f"\n🌐 Os produtos do Mutxutxu estão prontos no banco local!")
            print(f"📦 Execute o backend local para testar.")
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
