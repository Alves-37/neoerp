#!/usr/bin/env python3
"""
Script para verificar tabelas no banco de dados
"""

import sqlite3

def check_tables():
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Listar todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("📊 TABELAS NO BANCO DE DADOS:")
        for table in tables:
            print(f"   📋 {table[0]}")
        
        # Verificar se existem users e branches
        table_names = [t[0] for t in tables]
        
        if 'users' in table_names:
            print("\n👥 USUÁRIOS:")
            cursor.execute("SELECT id, email, role, company_id, branch_id FROM users LIMIT 5")
            users = cursor.fetchall()
            for user in users:
                print(f"   👤 ID: {user[0]} | Email: {user[1]} | Role: {user[2]} | Company: {user[3]} | Branch: {user[4]}")
        
        if 'branches' in table_names:
            print("\n📍 BRANCHES:")
            cursor.execute("SELECT id, name, company_id FROM branches LIMIT 5")
            branches = cursor.fetchall()
            for branch in branches:
                print(f"   📍 ID: {branch[0]} | Nome: {branch[1]} | Company: {branch[2]}")
        
        if 'companies' in table_names:
            print("\n🏢 COMPANIES:")
            cursor.execute("SELECT id, name FROM companies LIMIT 5")
            companies = cursor.fetchall()
            for company in companies:
                print(f"   🏢 ID: {company[0]} | Nome: {company[1]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar tabelas: {e}")

if __name__ == "__main__":
    check_tables()
