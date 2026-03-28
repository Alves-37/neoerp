#!/usr/bin/env python3
"""
Script simples para listar empresas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database.connection import SessionLocal

def listar_empresas():
    """Lista todas as empresas"""
    session = SessionLocal()
    
    try:
        # Listar empresas
        companies = session.execute(text("""
            SELECT id, name, email, created_at 
            FROM companies 
            ORDER BY id
        """)).fetchall()
        
        print("🏢 EMPRESAS CADASTRADAS:")
        print("=" * 80)
        
        for company in companies:
            marker = "👉" if company.id == 10 else "  "
            print(f"{marker} ID: {company.id} | Nome: {company.name} | Email: {company.email}")
        
        print("=" * 80)
        
        # Verificar se empresa 10 existe
        company_10 = session.execute(text("""
            SELECT id, name, email, created_at 
            FROM companies 
            WHERE id = 10
        """)).fetchone()
        
        if company_10:
            print(f"\n✅ Empresa ID 10 encontrada:")
            print(f"   Nome: {company_10.name}")
            print(f"   Email: {company_10.email}")
            print(f"   Criada em: {company_10.created_at}")
            
            # Listar usuários da empresa 10
            users = session.execute(text("""
                SELECT id, email, role, name 
                FROM users 
                WHERE company_id = 10
                ORDER BY role, id
            """)).fetchall()
            
            print(f"\n👥 Usuários da empresa 10:")
            for user in users:
                print(f"   ID: {user.id} | Email: {user.email} | Nome: {user.name} | Role: {user.role}")
        else:
            print("\n❌ Empresa ID 10 não encontrada!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    listar_empresas()
