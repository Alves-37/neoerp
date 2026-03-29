#!/usr/bin/env python3
"""
Script para criar tabelas de produtos manualmente
"""

import sqlite3

def create_product_tables():
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        print("🏗️ CRIANDO TABELAS DE PRODUTOS...")
        
        # Criar tabela de categorias de produtos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                company_id INTEGER NOT NULL,
                color VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Criar tabela de produtos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(500) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                cost DECIMAL(10,2),
                company_id INTEGER NOT NULL,
                branch_id INTEGER,
                product_category_id INTEGER,
                stock INTEGER DEFAULT 0,
                min_stock INTEGER DEFAULT 0,
                max_stock INTEGER,
                barcode VARCHAR(200),
                sku VARCHAR(200),
                description TEXT,
                image_url VARCHAR(500),
                is_active BOOLEAN DEFAULT 1,
                is_tracked BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_category_id) REFERENCES product_categories(id)
            )
        ''')
        
        # Criar tabela de stock de produtos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                branch_id INTEGER,
                stock_location_id INTEGER,
                quantity INTEGER DEFAULT 0,
                min_quantity INTEGER DEFAULT 0,
                max_quantity INTEGER,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        # Criar índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_company_id ON products(company_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_branch_id ON products(branch_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(product_category_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_categories_company_id ON product_categories(company_id)')
        
        conn.commit()
        conn.close()
        
        print("✅ Tabelas criadas com sucesso!")
        print("📋 Tabelas criadas:")
        print("   - product_categories")
        print("   - products")
        print("   - product_stocks")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")

if __name__ == "__main__":
    create_product_tables()
