#!/usr/bin/env python3
"""
Script simplificado para listar produtos do Restaurante Mutxutxu
"""

import sqlite3
from datetime import datetime

def list_mutxutu_products():
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        print("🍽️ RESTAURANTE MUTXUTXU - LISTA COMPLETA DE PRODUTOS")
        print("=" * 80)
        
        company_id = 10
        
        print(f"🏢 Empresa ID: {company_id} (Restaurante Mutxutxu)")
        print(f"📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Verificar categorias
        cursor.execute("""
            SELECT id, name, business_type 
            FROM product_categories 
            WHERE company_id = ? 
            ORDER BY name
        """, (company_id,))
        
        categories = cursor.fetchall()
        
        if not categories:
            print("❌ Nenhuma categoria encontrada!")
            return
        
        print(f"\n📁 CATEGORIAS ({len(categories)}):")
        for cat in categories:
            print(f"   ID: {cat[0]} | {cat[1]} | Type: {cat[2]}")
        
        print("\n" + "=" * 80)
        
        # Contar produtos por categoria
        cursor.execute("""
            SELECT pc.name, COUNT(p.id) as product_count, 
                   COALESCE(SUM(p.price), 0) as total_value,
                   COALESCE(SUM(ps.qty_on_hand), 0) as total_stock
            FROM product_categories pc
            LEFT JOIN products p ON pc.id = p.category_id AND p.company_id = ?
            LEFT JOIN product_stocks ps ON p.id = ps.product_id
            WHERE pc.company_id = ?
            GROUP BY pc.id, pc.name
            ORDER BY pc.name
        """, (company_id, company_id))
        
        category_stats = cursor.fetchall()
        
        print(f"\n📊 RESUMO POR CATEGORIA:")
        print("-" * 80)
        total_products = 0
        total_value = 0
        total_stock = 0
        
        for stats in category_stats:
            cat_name, count, value, stock = stats
            print(f"📁 {cat_name}:")
            print(f"   📦 Produtos: {count}")
            print(f"   💰 Valor total: MZN {value:,.2f}")
            print(f"   📊 Estoque total: {int(stock)} unidades")
            print()
            
            total_products += count
            total_value += value
            total_stock += stock
        
        print("=" * 80)
        print(f"🎯 RESUMO GERAL:")
        print(f"   📦 Total de produtos: {total_products}")
        print(f"   💰 Valor total do inventário: MZN {total_value:,.2f}")
        print(f"   📊 Estoque total: {int(total_stock)} unidades")
        print(f"   💰 Valor médio por produto: MZN {total_value/total_products if total_products > 0 else 0:.2f}")
        
        print("\n" + "=" * 80)
        print("📋 LISTA DETALHADA DE PRODUTOS:")
        print("=" * 80)
        
        # Listar todos os produtos
        cursor.execute("""
            SELECT p.id, p.name, p.price, p.sku, p.unit, p.is_active,
                   pc.name as category_name, ps.qty_on_hand as stock,
                   p.min_stock, p.created_at
            FROM products p
            LEFT JOIN product_categories pc ON p.category_id = pc.id
            LEFT JOIN product_stocks ps ON p.id = ps.product_id
            WHERE p.company_id = ?
            ORDER BY pc.name, p.name
        """, (company_id,))
        
        products = cursor.fetchall()
        
        if not products:
            print("❌ Nenhum produto encontrado!")
            return
        
        current_category = ""
        count = 0
        
        for product in products:
            (id, name, price, sku, unit, is_active, 
             category_name, stock, min_stock, created_at) = product
            
            count += 1
            
            # Nova categoria
            if category_name != current_category:
                current_category = category_name or "Sem categoria"
                print(f"\n🗂️  {current_category}:")
                print("-" * 60)
            
            # Status do produto
            status = "✅ Ativo" if is_active else "❌ Inativo"
            stock_info = f"{int(stock) if stock else 0} {unit}"
            
            # Status de estoque
            if stock and min_stock:
                if stock <= min_stock:
                    stock_status = "🔴 Baixo"
                elif stock <= min_stock * 1.5:
                    stock_status = "🟡 Médio"
                else:
                    stock_status = "🟢 Bom"
            else:
                stock_status = "⚪ N/A"
            
            print(f"{count:3d}. {status} {name}")
            print(f"     💰 Preço: MZN {price:7.2f} | 📦 Estoque: {stock_info} ({stock_status})")
            print(f"     🏷️  SKU: {sku} | 📅 Criado: {created_at}")
        
        print("\n" + "=" * 80)
        
        # Produtos com estoque baixo
        cursor.execute("""
            SELECT p.name, ps.qty_on_hand, p.min_stock, pc.name
            FROM products p
            JOIN product_stocks ps ON p.id = ps.product_id
            JOIN product_categories pc ON p.category_id = pc.id
            WHERE p.company_id = ? 
            AND ps.qty_on_hand <= p.min_stock
            AND p.is_active = 1
            ORDER BY ps.qty_on_hand ASC
        """, (company_id,))
        
        low_stock = cursor.fetchall()
        
        if low_stock:
            print(f"⚠️  PRODUTOS COM ESTOQUE BAIXO ({len(low_stock)}):")
            for item in low_stock:
                name, qty, min_qty, category = item
                print(f"   🔴 {name} ({category}): {int(qty)}/{int(min_qty)} unidades")
        else:
            print("✅ Nenhum produto com estoque baixo!")
        
        print("\n" + "=" * 80)
        print("🏷️  TOP 10 PRODUTOS MAIS CAROS:")
        print("-" * 80)
        
        cursor.execute("""
            SELECT p.name, p.price, pc.name
            FROM products p
            JOIN product_categories pc ON p.category_id = pc.id
            WHERE p.company_id = ? AND p.is_active = 1
            ORDER BY p.price DESC
            LIMIT 10
        """, (company_id,))
        
        expensive = cursor.fetchall()
        for i, (name, price, category) in enumerate(expensive, 1):
            print(f"{i:2d}. 💰 MZN {price:7.2f} - {name} ({category})")
        
        print("\n" + "=" * 80)
        print("📊 TOP 10 PRODUTOS COM MAIOR ESTOQUE:")
        print("-" * 80)
        
        cursor.execute("""
            SELECT p.name, ps.qty_on_hand, pc.name
            FROM products p
            JOIN product_stocks ps ON p.id = ps.product_id
            JOIN product_categories pc ON p.category_id = pc.id
            WHERE p.company_id = ? AND p.is_active = 1
            ORDER BY ps.qty_on_hand DESC
            LIMIT 10
        """, (company_id,))
        
        high_stock = cursor.fetchall()
        for i, (name, stock, category) in enumerate(high_stock, 1):
            print(f"{i:2d}. 📦 {int(stock):4d} und - {name} ({category})")
        
        conn.close()
        
        print(f"\n🎉 LISTAGEM CONCLUÍDA!")
        print(f"📊 Total analisado: {len(products)} produtos")
        
    except Exception as e:
        print(f"❌ Erro ao listar produtos: {e}")

if __name__ == "__main__":
    list_mutxutu_products()
