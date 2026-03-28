#!/usr/bin/env python3
"""
Script para resetar dados da empresa Mutxutxu
Mantém apenas o usuário admin e estrutura básica
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.settings import Settings
from app.database.connection import engine, SessionLocal

def listar_empresas():
    """Lista todas as empresas para identificar a Mutxutxu"""
    session = SessionLocal()
    
    try:
        # Listar empresas
        companies = session.execute(text("""
            SELECT id, name, email, created_at 
            FROM companies 
            ORDER BY id
        """)).fetchall()
        
        print("🏢 EMPRESAS CADASTRADAS:")
        print("=" * 60)
        for company in companies:
            print(f"ID: {company.id} | Nome: {company.name} | Email: {company.email}")
        
        print("\n" + "=" * 60)
        company_id = input("Digite o ID da empresa que deseja resetar: ")
        
        if not company_id.isdigit():
            print("❌ ID inválido!")
            return None
            
        return int(company_id)
        
    finally:
        session.close()

def reset_empresa(company_id):
    """Reseta todos os dados da empresa, mantendo apenas admin"""
    session = SessionLocal()
    
    try:
        print(f"🔄 Iniciando reset da empresa ID: {company_id}")
        
        # 1. Listar usuário admin para manter
        admin_user = session.execute(text("""
            SELECT id, email, role 
            FROM users 
            WHERE company_id = :company_id AND role IN ('admin', 'owner')
            LIMIT 1
        """), {"company_id": company_id}).fetchone()
        
        if not admin_user:
            print("❌ Nenhum usuário admin encontrado!")
            return
            
        print(f"✅ Mantendo usuário admin: {admin_user.email} (ID: {admin_user.id})")
        
        # 2. Deletar em ordem correta (respeitando foreign keys)
        
        # Transações e dados financeiros
        print("🗑️ Deletando dados financeiros...")
        session.execute(text("DELETE FROM fiscal_documents WHERE company_id = :company_id"), {"company_id": company_id})
        session.execute(text("DELETE FROM sale_items WHERE sale_id IN (SELECT id FROM sales WHERE company_id = :company_id)"), {"company_id": company_id})
        session.execute(text("DELETE FROM sales WHERE company_id = :company_id"), {"company_id": company_id})
        session.execute(text("DELETE FROM expenses WHERE company_id = :company_id"), {"company_id": company_id})
        session.execute(text("DELETE FROM cash_sessions WHERE company_id = :company_id AND opened_by != :admin_id"), {"company_id": company_id, "admin_id": admin_user.id})
        
        # Pedidos e itens
        print("🗑️ Deletando pedidos...")
        session.execute(text("DELETE FROM order_item_options WHERE order_item_id IN (SELECT id FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE company_id = :company_id))"), {"company_id": company_id})
        session.execute(text("DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE company_id = :company_id)"), {"company_id": company_id})
        session.execute(text("DELETE FROM orders WHERE company_id = :company_id"), {"company_id": company_id})
        
        # Estoque e produtos
        print("🗑️ Deletando produtos e estoque...")
        session.execute(text("DELETE FROM product_stocks WHERE company_id = :company_id"), {"company_id": company_id})
        session.execute(text("DELETE FROM product_images WHERE product_id IN (SELECT id FROM products WHERE company_id = :company_id)"), {"company_id": company_id})
        session.execute(text("DELETE FROM recipe_items WHERE recipe_id IN (SELECT id FROM recipes WHERE company_id = :company_id)"), {"company_id": company_id})
        session.execute(text("DELETE FROM recipes WHERE company_id = :company_id"), {"company_id": company_id})
        session.execute(text("DELETE FROM products WHERE company_id = :company_id"), {"company_id": company_id})
        session.execute(text("DELETE FROM product_categories WHERE company_id = :company_id"), {"company_id": company_id})
        
        # Clientes
        print("🗑️ Deletando clientes...")
        session.execute(text("DELETE FROM customers WHERE company_id = :company_id"), {"company_id": company_id})
        
        # Mesas e configurações
        print("🗑️ Deletando configurações...")
        session.execute(text("DELETE FROM restaurant_tables WHERE company_id = :company_id"), {"company_id": company_id})
        
        # Outros usuários (menos admin)
        print("🗑️ Deletando outros usuários...")
        session.execute(text("DELETE FROM users WHERE company_id = :company_id AND id != :admin_id"), {"company_id": company_id, "admin_id": admin_user.id})
        
        # Branches (se houver mais de um)
        print("🗑️ Deletando filiais adicionais...")
        branches = session.execute(text("SELECT id FROM branches WHERE company_id = :company_id"), {"company_id": company_id}).fetchall()
        for branch in branches:
            # Manter apenas a primeira filial (onde o admin está)
            if branch.id != admin_user.id:  # Assumindo que admin está na branch principal
                session.execute(text("DELETE FROM branches WHERE id = :branch_id"), {"branch_id": branch.id})
        
        session.commit()
        print("✅ Reset concluído com sucesso!")
        print(f"✅ Empresa {company_id} resetada. Usuário admin mantido: {admin_user.email}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Erro durante o reset: {e}")
        raise
    finally:
        session.close()

def main():
    print("🔄 SCRIPT DE RESET DA EMPRESA MUTXUTXU")
    print("=" * 50)
    
    company_id = listar_empresas()
    if company_id:
        confirm = input(f"\n⚠️ TEM CERTEZA QUE DESEJA RESETAR A EMPRESA ID {company_id}? (digite 'SIM' para confirmar): ")
        if confirm.upper() == 'SIM':
            reset_empresa(company_id)
        else:
            print("❌ Operação cancelada.")

if __name__ == "__main__":
    main()
