#!/usr/bin/env python3
"""
Script para criar reservas com dados genéricos que funcionem em qualquer sistema
"""

import sqlite3
from datetime import datetime, timedelta

def create_reservations():
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Primeiro, verificar se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reservations'")
        if not cursor.fetchone():
            print("❌ Tabela 'reservations' não encontrada! Execute a migração primeiro.")
            return
        
        # Verificar se já existem reservas
        cursor.execute("SELECT COUNT(*) FROM reservations")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"⚠️  Já existem {count} reservas. Quer apagar e criar novas? (s/n)")
            # response = input().lower()
            # if response != 's':
            #     print("❌ Operação cancelada.")
            #     return
            
            # Apagar reservas existentes
            cursor.execute("DELETE FROM reservations")
            print("🗑️  Reservas existentes apagadas.")
        
        # Data de hoje
        today = datetime.now().date()
        
        # Reservas de teste genéricas
        test_reservations = [
            {
                'customer_name': 'Cliente Grande - Grupo Família',
                'customer_phone': '+258 84 123 4567',
                'table_id': 1,
                'reservation_date': f'{today} 12:00:00',
                'time_slot': 'almoço',
                'people_count': 8,
                'estimated_amount': 2500.00,
                'deposit_percentage': 50.0,
                'deposit_amount': 1250.00,
                'payment_method': 'mpesa',
                'payment_reference': 'REF123456',
                'status': 'confirmed',
                'payment_status': 'paid',
                'notes': 'Reserva de teste grande',
                'special_requests': 'Mesa para 8 pessoas',
                'company_id': 1,
                'branch_id': 1,
                'created_by': 1
            },
            {
                'customer_name': 'Cliente Médio - Casal Romântico',
                'customer_phone': '+258 85 987 6543',
                'table_id': 2,
                'reservation_date': f'{today} 19:00:00',
                'time_slot': 'jantar',
                'people_count': 2,
                'estimated_amount': 800.00,
                'deposit_percentage': 30.0,
                'deposit_amount': 240.00,
                'payment_method': 'cash',
                'payment_reference': '',
                'status': 'confirmed',
                'payment_status': 'paid',
                'notes': 'Reserva de casal',
                'special_requests': 'Mesa romântica',
                'company_id': 1,
                'branch_id': 1,
                'created_by': 1
            },
            {
                'customer_name': 'Cliente Pequeno - Almoço Rápido',
                'customer_phone': '+258 86 555 4444',
                'table_id': 3,
                'reservation_date': f'{today} 13:00:00',
                'time_slot': 'almoço',
                'people_count': 3,
                'estimated_amount': 600.00,
                'deposit_percentage': 0.0,
                'deposit_amount': 0.00,
                'payment_method': None,
                'payment_reference': None,
                'status': 'pending_payment',
                'payment_status': 'pending',
                'notes': 'Reserva de teste',
                'special_requests': 'Serviço rápido',
                'company_id': 1,
                'branch_id': 1,
                'created_by': 1
            }
        ]
        
        # Inserir reservas
        for reservation in test_reservations:
            cursor.execute('''
                INSERT INTO reservations (
                    customer_name, customer_phone, table_id, reservation_date, time_slot,
                    people_count, estimated_amount, deposit_percentage, deposit_amount,
                    payment_method, payment_reference, status, payment_status,
                    notes, special_requests, company_id, branch_id, created_by,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            ''', (
                reservation['customer_name'],
                reservation['customer_phone'],
                reservation['table_id'],
                reservation['reservation_date'],
                reservation['time_slot'],
                reservation['people_count'],
                reservation['estimated_amount'],
                reservation['deposit_percentage'],
                reservation['deposit_amount'],
                reservation['payment_method'],
                reservation['payment_reference'],
                reservation['status'],
                reservation['payment_status'],
                reservation['notes'],
                reservation['special_requests'],
                reservation['company_id'],
                reservation['branch_id'],
                reservation['created_by']
            ))
        
        # Commit e fechar conexão
        conn.commit()
        conn.close()
        
        print(f"✅ {len(test_reservations)} reservas criadas com sucesso!")
        print("\n📋 Reservas criadas:")
        for i, res in enumerate(test_reservations, 1):
            print(f"  {i}. {res['customer_name']} - Mesa {res['table_id']} - {res['time_slot']} - {res['people_count']} pessoas")
        
        print(f"\n🎯 DATA DAS RESERVAS: {today}")
        print("💡 Se você não vir as reservas, verifique:")
        print("   1. Se está logado na company/branch correta (ID: 1)")
        print("   2. Se está selecionando a data correta no calendário")
        print("   3. Se o backend está rodando e acessível")
        
    except Exception as e:
        print(f"❌ Erro ao criar reservas: {e}")

if __name__ == "__main__":
    create_reservations()
