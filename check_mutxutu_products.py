#!/usr/bin/env python3
"""
Script para verificar produtos do Restaurante Mutxutxu
"""

import sqlite3

def check_mutxutu_products():
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        print("🔍 VERIFICANDO PRODUTOS DO RESTAURANTE MUTXUTXU")
        print("=" * 60)
        
        company_id = 10
        
        # Verificar categorias
        cursor.execute("SELECT id, name, business_type FROM product_categories WHERE company_id = ?", (company_id,))
        categories = cursor.fetchall()
        
        print(f"📁 CATEGORIAS DA EMPRESA {company_id}:")
        if categories:
            for cat in categories:
                print(f"   ID: {cat[0]} | Nome: {cat[1]} | Type: {cat[2]}")
        else:
            print("   ❌ Nenhuma categoria encontrada!")
        
        print("\n" + "-" * 60)
        
        # Verificar produtos
        cursor.execute('''
            SELECT p.id, p.name, p.price, p.business_type, p.sku, p.unit, p.is_active,
                   pc.name as category_name, ps.qty_on_hand as stock
            FROM products p
            LEFT JOIN product_categories pc ON p.category_id = pc.id
            LEFT JOIN product_stocks ps ON p.id = ps.product_id
            WHERE p.company_id = ?
            ORDER BY pc.name, p.name
        ''', (company_id,))
        
        products = cursor.fetchall()
        
        print(f"📦 PRODUTOS DA EMPRESA {company_id}:")
        if products:
            print(f"   Total: {len(products)} produtos")
            print("\n📋 LISTA DE PRODUTOS:")
            
            current_category = ""
            for i, product in enumerate(products, 1):
                (id, name, price, business_type, sku, unit, is_active, category_name, stock) = product
                
                if category_name != current_category:
                    current_category = category_name
                    print(f"\n🗂️  {category_name or 'Sem categoria'}:")
                
                status = "✅" if is_active else "❌"
                stock_display = f"{stock or 0} und"
                
                print(f"   {i:3d}. {status} {name}")
                print(f"       💰 MZN {price:7.2f} | 📦 {stock_display} | 🏷️  {sku}")
            
            # Resumo por categoria
            print(f"\n📊 RESUMO POR CATEGORIA:")
            category_summary = {}
            for product in products:
                cat = product[7] or 'Sem categoria'
                if cat not in category_summary:
                    category_summary[cat] = {'count': 0, 'total_value': 0}
                category_summary[cat]['count'] += 1
                category_summary[cat]['total_value'] += product[2]
            
            for cat, data in category_summary.items():
                print(f"   📁 {cat}: {data['count']} produtos | Valor total: MZN {data['total_value']:.2f}")
                
        else:
            print("   ❌ Nenhum produto encontrado!")
        
        print("\n" + "-" * 60)
        
        # Verificar estrutura das tabelas
        print("🏗️ ESTRUTURA DAS TABELAS:")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%product%'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   📋 {table_name}: {count} registros")
        
        # Verificar se há produtos em outras empresas
        cursor.execute("SELECT company_id, COUNT(*) as count FROM products GROUP BY company_id")
        companies_with_products = cursor.fetchall()
        
        print(f"\n🏢 EMPRESAS COM PRODUTOS:")
        for comp in companies_with_products:
            print(f"   Company ID {comp[0]}: {comp[1]} produtos")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar produtos: {e}")

if __name__ == "__main__":
    check_mutxutu_products()
