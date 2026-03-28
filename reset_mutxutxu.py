#!/usr/bin/env python3
"""
Script para resetar Restaurante Mutxutxu (Empresa ID: 10)
Mantém apenas o usuário owner (ID: 17)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database.connection import SessionLocal

def reset_mutxutxu():
    """Reseta todos os dados da empresa 10, mantendo apenas o owner"""
    session = SessionLocal()
    
    try:
        print("🔄 INICIANDO RESET DO RESTAURANTE MUTXUTXU")
        print("=" * 60)
        print("🏢 Empresa: Restaurante Mutxutxu (ID: 10)")
        print("👤 Mantendo: mutxutxu@gmail.com (Owner - ID: 17)")
        print("🗑️ Deletando: TODOS os outros dados")
        print("=" * 60)
        
        # 1. Deletar dados financeiros e transacionais (em ordem correta)
        print("\n📊 Deletando dados financeiros...")
        # Deletar linhas de documentos fiscais primeiro
        session.execute(text("DELETE FROM fiscal_document_lines WHERE fiscal_document_id IN (SELECT id FROM fiscal_documents WHERE company_id = 10)"))
        # Depois deletar os documentos fiscais
        session.execute(text("DELETE FROM fiscal_documents WHERE company_id = 10"))
        # Deletar itens de vendas
        session.execute(text("DELETE FROM sale_items WHERE sale_id IN (SELECT id FROM sales WHERE company_id = 10)"))
        # Deletar vendas
        session.execute(text("DELETE FROM sales WHERE company_id = 10"))
        # Deletar despesas
        session.execute(text("DELETE FROM expenses WHERE company_id = 10"))
        # Deletar sessões de caixa (manter apenas do owner)
        session.execute(text("DELETE FROM cash_sessions WHERE company_id = 10 AND opened_by != 17"))
        
        # 2. Deletar pedidos e itens
        print("🍽️ Deletando pedidos...")
        session.execute(text("DELETE FROM order_item_options WHERE order_item_id IN (SELECT id FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE company_id = 10))"))
        session.execute(text("DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE company_id = 10)"))
        session.execute(text("DELETE FROM orders WHERE company_id = 10"))
        
        # 3. Deletar produtos e estoque (em ordem correta)
        print("📦 Deletando produtos e estoque...")
        # Deletar movimentos de estoque primeiro
        session.execute(text("DELETE FROM stock_movements WHERE company_id = 10"))
        # Deletar estoque de produtos
        session.execute(text("DELETE FROM product_stocks WHERE company_id = 10"))
        # Deletar imagens de produtos
        session.execute(text("DELETE FROM product_images WHERE product_id IN (SELECT id FROM products WHERE company_id = 10)"))
        # Deletar itens de receitas
        session.execute(text("DELETE FROM recipe_items WHERE recipe_id IN (SELECT id FROM recipes WHERE company_id = 10)"))
        # Deletar receitas
        session.execute(text("DELETE FROM recipes WHERE company_id = 10"))
        # Agora deletar produtos
        session.execute(text("DELETE FROM products WHERE company_id = 10"))
        # Deletar categorias de produtos
        session.execute(text("DELETE FROM product_categories WHERE company_id = 10"))
        
        # 4. Deletar clientes
        print("👥 Deletando clientes...")
        session.execute(text("DELETE FROM customers WHERE company_id = 10"))
        
        # 5. Deletar configurações do restaurante
        print("🍽️ Deletando configurações do restaurante...")
        session.execute(text("DELETE FROM restaurant_tables WHERE company_id = 10"))
        
        # 6. Deletar outros usuários (manter apenas owner ID: 17)
        print("👤 Deletando outros usuários...")
        session.execute(text("DELETE FROM users WHERE company_id = 10 AND id != 17"))
        
        # 7. Verificar establishments, branches e categorias de despesa (manter apenas a principal)
        establishments = session.execute(text("SELECT id, name, branch_id FROM establishments WHERE company_id = 10")).fetchall()
        branches = session.execute(text("SELECT id, name FROM branches WHERE company_id = 10")).fetchall()
        
        if len(establishments) > 1 or len(branches) > 1:
            print("🏪 Mantendo apenas a branch principal...")
            
            # Deletar categorias de despesa de branches secundárias primeiro
            for branch in branches:
                if branch.id != 94:  # Assumindo que 94 é a branch principal
                    print(f"   Deletando categorias de despesa da branch: {branch.name} (ID: {branch.id})")
                    session.execute(text("DELETE FROM expense_categories WHERE branch_id = :branch_id"), {"branch_id": branch.id})
            
            # Deletar establishments secundários
            for establishment in establishments:
                if establishment.branch_id != 94:  # Assumindo que 94 é a branch principal
                    print(f"   Deletando establishment: {establishment.name} (ID: {establishment.id})")
                    session.execute(text("DELETE FROM establishments WHERE id = :establishment_id"), {"establishment_id": establishment.id})
            
            # Depois deletar branches secundárias
            for branch in branches:
                if branch.id != 94:  # Assumindo que 94 é a principal
                    print(f"   Deletando branch: {branch.name} (ID: {branch.id})")
                    session.execute(text("DELETE FROM branches WHERE id = :branch_id"), {"branch_id": branch.id})
        
        session.commit()
        
        print("\n" + "=" * 60)
        print("✅ RESET CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print("🏢 Restaurante Mutxutxu resetado")
        print("👤 Usuário mantido: mutxutxu@gmail.com (ID: 17)")
        print("🔐 Login disponível: mutxutxu@gmail.com")
        print("📱 Sistema limpo e pronto para novo uso!")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ ERRO DURANTE O RESET: {e}")
        raise
    finally:
        session.close()

def main():
    print("🔄 SCRIPT DE RESET - RESTAURANTE MUTXUTXU")
    print("=" * 50)
    
    confirm = input("\n⚠️ ESTE PROCESSO IRÁ DELETAR TODOS OS DADOS DO RESTAURANTE MUTXUTXU!")
    print("   - Vendas, pedidos, produtos")
    print("   - Clientes, estoque, configurações")
    print("   - Usuário cashier será deletado")
    print("   - Apenas o owner será mantido")
    print("\nDigite 'RESETAR MUTXUTXU' para confirmar: ")
    
    confirm = input("> ")
    
    if confirm.upper() == 'RESETAR MUTXUTXU':
        reset_mutxutxu()
    else:
        print("❌ Operação cancelada. Confirmação incorreta.")

if __name__ == "__main__":
    main()
