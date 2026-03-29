#!/usr/bin/env python3
"""
Script para verificar reservas no banco de dados
"""

import sqlite3
from datetime import datetime

def check_reservations():
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Verificar todas as reservas
        cursor.execute('''
            SELECT id, company_id, branch_id, customer_name, table_id, 
                   reservation_date, time_slot, people_count, status, payment_status
            FROM reservations 
            ORDER BY reservation_date, time_slot
        ''')
        
        reservations = cursor.fetchall()
        
        if not reservations:
            print("❌ Nenhuma reserva encontrada no banco de dados!")
            return
        
        print(f"📋 Encontradas {len(reservations)} reservas no total:\n")
        
        for res in reservations:
            (id, company_id, branch_id, customer_name, table_id, 
             reservation_date, time_slot, people_count, status, payment_status) = res
            
            print(f"🔹 ID: {id}")
            print(f"   👤 Cliente: {customer_name}")
            print(f"   🏢 Company ID: {company_id}")
            print(f"   📍 Branch ID: {branch_id}")
            print(f"   🪑 Mesa: {table_id}")
            print(f"   📅 Data/Hora: {reservation_date}")
            print(f"   ⏰ Turno: {time_slot}")
            print(f"   👥 Pessoas: {people_count}")
            print(f"   📊 Status: {status}")
            print(f"   💳 Pagamento: {payment_status}")
            print("-" * 50)
        
        # Verificar também as empresas e branches
        print("\n🏢 EMPRESAS E BRANCHES:")
        cursor.execute("SELECT id, name FROM companies")
        companies = cursor.fetchall()
        for comp in companies:
            print(f"   Company {comp[0]}: {comp[1]}")
        
        cursor.execute("SELECT id, name, company_id FROM branches")
        branches = cursor.fetchall()
        for branch in branches:
            print(f"   Branch {branch[0]}: {branch[1]} (Company {branch[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar reservas: {e}")

if __name__ == "__main__":
    check_reservations()
