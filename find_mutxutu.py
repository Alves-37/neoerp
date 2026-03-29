#!/usr/bin/env python3
"""
Script para encontrar o restaurante Mutxutu
"""

import sqlite3

def find_mutxutu():
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Procurar por "mutxutu" em branches
        print("🔍 Procurando restaurante 'Mutxutu'...")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        if 'branches' in tables:
            cursor.execute("SELECT id, name, company_id FROM branches WHERE LOWER(name) LIKE '%mutxutu%'")
            branches = cursor.fetchall()
            
            if branches:
                print("✅ Restaurantes Mutxutu encontrados:")
                for branch in branches:
                    print(f"   📍 Branch ID: {branch[0]} | Nome: {branch[1]} | Company ID: {branch[2]}")
                return branches[0]  # Retornar o primeiro encontrado
        
        if 'companies' in tables:
            cursor.execute("SELECT id, name FROM companies WHERE LOWER(name) LIKE '%mutxutu%'")
            companies = cursor.fetchall()
            
            if companies:
                print("✅ Empresas Mutxutu encontradas:")
                for company in companies:
                    print(f"   🏢 Company ID: {company[0]} | Nome: {company[1]}")
                
                # Buscar branches desta company
                cursor.execute("SELECT id, name, company_id FROM branches WHERE company_id = ?", (companies[0][0],))
                branches = cursor.fetchall()
                if branches:
                    print("📍 Branches desta empresa:")
                    for branch in branches:
                        print(f"   📍 Branch ID: {branch[0]} | Nome: {branch[1]}")
                    return branches[0]
        
        print("❌ Nenhum restaurante 'Mutxutu' encontrado!")
        print("\n📋 Todos os branches encontrados:")
        
        if 'branches' in tables:
            cursor.execute("SELECT id, name, company_id FROM branches LIMIT 10")
            branches = cursor.fetchall()
            for branch in branches:
                print(f"   📍 ID: {branch[0]} | Nome: {branch[1]} | Company: {branch[2]}")
        
        conn.close()
        return None
        
    except Exception as e:
        print(f"❌ Erro ao procurar Mutxutu: {e}")
        return None

if __name__ == "__main__":
    result = find_mutxutu()
    if result:
        print(f"\n🎯 Usando Branch ID: {result[0]} para criar reservas")
