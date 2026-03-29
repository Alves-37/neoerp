#!/usr/bin/env python3
"""
Script para verificar e criar tabelas necessárias
"""

import sqlite3

def check_and_create_tables():
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Listar tabelas existentes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print("📊 TABELAS EXISTENTES:")
        for table in existing_tables:
            print(f"   ✅ {table}")
        
        # Tabelas necessárias para produtos
        required_tables = ['products', 'product_categories', 'product_stocks']
        
        missing_tables = []
        for table in required_tables:
            if table not in existing_tables:
                missing_tables.append(table)
        
        if not missing_tables:
            print("\n✅ Todas as tabelas necessárias já existem!")
        else:
            print(f"\n❌ Tabelas faltando: {missing_tables}")
            print("💡 Execute as migrações completas do sistema primeiro.")
            print("   Use: python -m alembic upgrade head")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    check_and_create_tables()
