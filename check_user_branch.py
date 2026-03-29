#!/usr/bin/env python3
"""
Script para verificar users e branches
"""

import sqlite3

def check_users_and_branches():
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        print("👥 USUÁRIOS:")
        cursor.execute("SELECT id, email, role, company_id, branch_id FROM users")
        users = cursor.fetchall()
        
        if not users:
            print("   ❌ Nenhum usuário encontrado!")
        else:
            for user in users:
                print(f"   👤 ID: {user[0]} | Email: {user[1]} | Role: {user[2]} | Company: {user[3]} | Branch: {user[4]}")
        
        print("\n🏢 BRANCHES:")
        cursor.execute("SELECT id, name, company_id FROM branches")
        branches = cursor.fetchall()
        
        if not branches:
            print("   ❌ Nenhum branch encontrado!")
        else:
            for branch in branches:
                print(f"   📍 ID: {branch[0]} | Nome: {branch[1]} | Company: {branch[2]}")
        
        print("\n🏭 COMPANIES:")
        cursor.execute("SELECT id, name FROM companies")
        companies = cursor.fetchall()
        
        if not companies:
            print("   ❌ Nenhuma company encontrada!")
        else:
            for company in companies:
                print(f"   🏢 ID: {company[0]} | Nome: {company[1]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar: {e}")

if __name__ == "__main__":
    check_users_and_branches()
