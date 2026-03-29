#!/usr/bin/env python3
"""
Script para importar produtos do Mutxutxu usando a estrutura correta do sistema
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
from datetime import datetime

# Dados extraídos do PDF lista_produtos_4.pdf
products_data = [
    {"name": "2M garrafa", "price": 80.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "2M lata", "price": 90.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Agua Pequena", "price": 50.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Agua Tonica", "price": 60.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Agua grande", "price": 100.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Amarula", "price": 1400.00, "stock": 100, "category": "Outos"},
    {"name": "Azinhas", "price": 300.00, "stock": 104, "category": "Outos"},
    {"name": "Bife Completo", "price": 800.00, "stock": 10, "category": "Congelados"},
    {"name": "Bull dog", "price": 3300.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "C double burger", "price": 500.00, "stock": 10, "category": "Bolos e salgados"},
    {"name": "Cabeca de Peixe", "price": 200.00, "stock": 10, "category": "Outos"},
    {"name": "Cabeca de Vaca", "price": 200.00, "stock": 10, "category": "Outos"},
    {"name": "Caldo verde", "price": 150.00, "stock": 10, "category": "Azeites"},
    {"name": "Cappy", "price": 80.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Carne de porco", "price": 800.00, "stock": 10, "category": "Congelados"},
    {"name": "Ceres", "price": 200.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Champanhe Anabela", "price": 1300.00, "stock": 100, "category": "Outos"},
    {"name": "Champanhe JS", "price": 1200.00, "stock": 100, "category": "Outos"},
    {"name": "Champanhe Martini Rose", "price": 1200.00, "stock": 100, "category": "Outos"},
    {"name": "Champanhe Toste", "price": 1500.00, "stock": 100, "category": "Outos"},
    {"name": "Chamussas", "price": 25.00, "stock": 10, "category": "Outos"},
    {"name": "Chourico", "price": 300.00, "stock": 10, "category": "Outos"},
    {"name": "Cochinhas", "price": 30.00, "stock": 9, "category": "Outos"},
    {"name": "Compal", "price": 200.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Dobrada", "price": 200.00, "stock": 10, "category": "Outos"},
    {"name": "Dry Lemon", "price": 150.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Escape Vodka", "price": 1000.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Four Causin Grade", "price": 1600.00, "stock": 100, "category": "Outos"},
    {"name": "Frango 1 quarto", "price": 300.00, "stock": 10, "category": "Congelados"},
    {"name": "Frango a Passarinho", "price": 1250.00, "stock": 10, "category": "Congelados"},
    {"name": "Frango assado 1", "price": 1200.00, "stock": 10, "category": "Congelados"},
    {"name": "Frango assado meio", "price": 600.00, "stock": 10, "category": "Congelados"},
    {"name": "Galinha Fumado", "price": 1500.00, "stock": 10, "category": "Congelados"},
    {"name": "Galo Dourado", "price": 1100.00, "stock": 100, "category": "Outos"},
    {"name": "Gatao", "price": 1500.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Gordon", "price": 1100.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Grants", "price": 1800.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "HENICKER", "price": 100.00, "stock": 500, "category": "Outos"},
    {"name": "Hamburger Completo", "price": 300.00, "stock": 8, "category": "Bolos e salgados"},
    {"name": "Hanked Bannister", "price": 1100.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Havelock", "price": 1100.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Humburger S", "price": 250.00, "stock": 10, "category": "Bolos e salgados"},
    {"name": "Joh walker red", "price": 1800.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "John Walker black", "price": 3500.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Maicgregor", "price": 1500.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Martine", "price": 1400.00, "stock": 100, "category": "Outos"},
    {"name": "Mutxutxu de galinha", "price": 200.00, "stock": 110, "category": "Outos"},
    {"name": "Pizza 4 estacoes", "price": 100.00, "stock": 10, "category": "pizzas"},
    {"name": "Pizza de atum", "price": 700.00, "stock": 10, "category": "pizzas"},
    {"name": "Pizza de frango", "price": 800.00, "stock": 10, "category": "pizzas"},
    {"name": "Pizza vegetariana", "price": 700.00, "stock": 10, "category": "pizzas"},
    {"name": "Quinta da bolota", "price": 1200.00, "stock": 100, "category": "Outos"},
    {"name": "Red Bull", "price": 150.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Refresco em lata", "price": 60.00, "stock": 97, "category": "Sumos, agua e refrescos"},
    {"name": "Rose Grande", "price": 1600.00, "stock": 100, "category": "Outos"},
    {"name": "Rusian", "price": 1000.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Silk spice", "price": 1800.00, "stock": 100, "category": "Outos"},
    {"name": "Sopa de Feijao", "price": 150.00, "stock": 10, "category": "Azeites"},
    {"name": "Sopa de legumes", "price": 150.00, "stock": 10, "category": "Azeites"},
    {"name": "Takeaway", "price": 30.00, "stock": 100, "category": "Outos"},
    {"name": "Tbone", "price": 800.00, "stock": 10, "category": "Congelados"},
    {"name": "Tostas com batata frita", "price": 300.00, "stock": 10, "category": "Outos"},
    {"name": "Worce", "price": 300.00, "stock": 10, "category": "Outos"},
    {"name": "altum", "price": 800.00, "stock": 10, "category": "Outos"},
    {"name": "bermine", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "bife trinchado", "price": 700.00, "stock": 101, "category": "Outos"},
    {"name": "brizer", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "brutal", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "budweiser", "price": 100.00, "stock": 10, "category": "Outos"},
    {"name": "cape ruby", "price": 1100.00, "stock": 10, "category": "Outos"},
    {"name": "casal garcia", "price": 1200.00, "stock": 10, "category": "Outos"},
    {"name": "castle lite", "price": 100.00, "stock": 10, "category": "Outos"},
    {"name": "celler cast", "price": 1100.00, "stock": 100, "category": "Outos"},
    {"name": "chima", "price": 100.00, "stock": 10, "category": "Bolachas,doces"},
    {"name": "dose de arroz", "price": 100.00, "stock": 10, "category": "Bolachas,doces"},
    {"name": "dose de batata", "price": 100.00, "stock": 10, "category": "Bolachas,doces"},
    {"name": "drosdy hof", "price": 800.00, "stock": 10, "category": "Outos"},
    {"name": "duas quintas", "price": 1100.00, "stock": 10, "category": "Outos"},
    {"name": "filetes", "price": 800.00, "stock": 10, "category": "Temperos"},
    {"name": "gazela", "price": 1100.00, "stock": 10, "category": "Outos"},
    {"name": "hunters dray", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "hunters gold", "price": 100.00, "stock": 10, "category": "Outos"},
    {"name": "jamson", "price": 1500.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "lemone", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "lulas", "price": 800.00, "stock": 10, "category": "Temperos"},
    {"name": "mao de vaca", "price": 200.00, "stock": 9, "category": "Outos"},
    {"name": "pandora", "price": 1100.00, "stock": 10, "category": "Outos"},
    {"name": "peixe chambo grande", "price": 1000.00, "stock": 10, "category": "Temperos"},
    {"name": "peixe chambo medio", "price": 800.00, "stock": 10, "category": "Temperos"},
    {"name": "peixe chambo pequeno", "price": 600.00, "stock": 10, "category": "Temperos"},
    {"name": "prego no pao", "price": 300.00, "stock": 10, "category": "Bolos e salgados"},
    {"name": "prego no prato", "price": 450.00, "stock": 10, "category": "Bolos e salgados"},
    {"name": "preta grande", "price": 80.00, "stock": 10, "category": "Outos"},
    {"name": "preta lata", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "preta pequena", "price": 100.00, "stock": 10, "category": "Outos"},
    {"name": "saladas", "price": 75.00, "stock": 10, "category": "Bolachas,doces"},
    {"name": "sande de ovo", "price": 200.00, "stock": 10, "category": "Bolos e salgados"},
    {"name": "segredo sao miguel", "price": 1200.00, "stock": 10, "category": "Outos"},
    {"name": "spin", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "super bock", "price": 80.00, "stock": 10, "category": "Outos"},
    {"name": "vinho cabriz", "price": 1200.00, "stock": 10, "category": "Outos"},
    {"name": "vinho portada", "price": 1200.00, "stock": 10, "category": "Outos"}
]

def create_correct_tables():
    """Cria tabelas com a estrutura correta do sistema"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        print("🏗️ CRIANDO TABELAS COM ESTRUTURA CORRETA...")
        
        # Apagar tabelas antigas se existirem
        cursor.execute("DROP TABLE IF EXISTS product_stocks")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS product_categories")
        
        # Criar tabela de categorias de produtos (com business_type)
        cursor.execute('''
            CREATE TABLE product_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                company_id INTEGER NOT NULL,
                business_type VARCHAR(50),
                color VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Criar tabela de produtos (estrutura completa)
        cursor.execute('''
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(500) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                cost DECIMAL(10,2),
                company_id INTEGER NOT NULL,
                branch_id INTEGER,
                category_id INTEGER,
                default_location_id INTEGER,
                business_type VARCHAR(50),
                sku VARCHAR(200),
                barcode VARCHAR(200),
                unit VARCHAR(50),
                tax_rate DECIMAL(5,2) DEFAULT 0,
                min_stock INTEGER DEFAULT 0,
                max_stock INTEGER,
                track_stock BOOLEAN DEFAULT 1,
                is_active BOOLEAN DEFAULT 1,
                attributes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES product_categories(id)
            )
        ''')
        
        # Criar tabela de stock de produtos
        cursor.execute('''
            CREATE TABLE product_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                branch_id INTEGER,
                product_id INTEGER NOT NULL,
                location_id INTEGER,
                qty_on_hand INTEGER DEFAULT 0,
                min_quantity INTEGER DEFAULT 0,
                max_quantity INTEGER,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        # Criar índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_company_id ON products(company_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_branch_id ON products(branch_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_categories_company_id ON product_categories(company_id)')
        
        conn.commit()
        conn.close()
        
        print("✅ Tabelas criadas com estrutura correta!")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")

def import_mutxutu_products():
    """Importa produtos para o Restaurante Mutxutxu"""
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        print(f"🍽️ IMPORTANDO PRODUTOS PARA RESTAURANTE MUTXUTXU")
        print(f"📊 Total de produtos: {len(products_data)}")
        print("=" * 60)
        
        # Company ID do Mutxutxu
        company_id = 10
        branch_id = 1
        business_type = 'restaurant'
        
        # Obter categorias existentes ou criar novas
        cursor.execute("SELECT id, name FROM product_categories WHERE company_id = ?", (company_id,))
        existing_categories = {row[1]: row[0] for row in cursor.fetchall()}
        
        # Mapeamento de categorias
        category_mapping = {}
        
        for product in products_data:
            category_name = product['category']
            
            # Se categoria não existe, criar
            if category_name not in existing_categories:
                cursor.execute('''
                    INSERT INTO product_categories (name, company_id, business_type, created_at, updated_at)
                    VALUES (?, ?, ?, datetime('now'), datetime('now'))
                ''', (category_name, company_id, business_type))
                
                category_id = cursor.lastrowid
                existing_categories[category_name] = category_id
                print(f"📁 Categoria criada: {category_name} (ID: {category_id})")
            
            category_mapping[category_name] = existing_categories[category_name]
        
        print(f"\n✅ Categorias prontas: {len(category_mapping)} categorias")
        
        # Importar produtos
        imported_count = 0
        skipped_count = 0
        
        for i, product in enumerate(products_data, 1):
            try:
                # Verificar se produto já existe
                cursor.execute('''
                    SELECT id FROM products 
                    WHERE name = ? AND company_id = ?
                ''', (product['name'], company_id))
                
                if cursor.fetchone():
                    print(f"⚠️  {i:3d}. {product['name']} - JÁ EXISTE")
                    skipped_count += 1
                    continue
                
                # Inserir produto
                cursor.execute('''
                    INSERT INTO products (
                        name, price, cost, company_id, branch_id, category_id,
                        business_type, sku, unit, min_stock, track_stock, is_active,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                ''', (
                    product['name'],
                    product['price'],
                    product['price'] * 0.7,  # Cost estimado 70% do preço
                    company_id,
                    branch_id,
                    category_mapping[product['category']],
                    business_type,
                    f"RES-{company_id}-{i:03d}",  # SKU
                    "un",  # Unit
                    max(1, product['stock'] // 4),  # Min stock
                    1,  # Track stock
                    1  # Is active
                ))
                
                product_id = cursor.lastrowid
                
                # Inserir registro de stock
                cursor.execute('''
                    INSERT INTO product_stocks (
                        company_id, branch_id, product_id, qty_on_hand, 
                        min_quantity, last_updated
                    ) VALUES (?, ?, ?, ?, ?, datetime('now'))
                ''', (
                    company_id,
                    branch_id,
                    product_id,
                    product['stock'],
                    max(1, product['stock'] // 4)
                ))
                
                print(f"✅ {i:3d}. {product['name']} - MZN {product['price']:7.2f} | Estoque: {product['stock']:3d} | {product['category']}")
                imported_count += 1
                
            except Exception as e:
                print(f"❌ {i:3d}. {product['name']} - ERRO: {e}")
        
        # Commit das alterações
        conn.commit()
        conn.close()
        
        print("\n" + "=" * 60)
        print(f"🎉 IMPORTAÇÃO CONCLUÍDA!")
        print(f"✅ Produtos importados: {imported_count}")
        print(f"⚠️  Produtos pulados: {skipped_count}")
        print(f"📊 Total processado: {imported_count + skipped_count}")
        print(f"🏢 Empresa: Restaurante Mutxutxu (ID: {company_id})")
        print(f"📋 Estrutura: Tabelas corretas do sistema")
        
    except Exception as e:
        print(f"❌ Erro na importação: {e}")

if __name__ == "__main__":
    create_correct_tables()
    import_mutxutu_products()
