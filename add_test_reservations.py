#!/usr/bin/env python3
"""
Script para adicionar reservas de teste no banco de dados
"""

import sqlite3
from datetime import datetime, timedelta
import sys

def add_test_reservations():
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Reservas de teste para hoje
        today = datetime.now().date()
        
        test_reservations = [
            {
                'customer_name': 'João Silva - Grupo Família',
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
                'notes': 'Reserva de aniversário familiar',
                'special_requests': 'Mesa próxima à janela, cadeira para criança',
                'company_id': 1,
                'branch_id': 1,
                'created_by': 1
            },
            {
                'customer_name': 'Maria Santos - Casal',
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
                'notes': 'Comemoração de aniversário de namoro',
                'special_requests': 'Mesa romântica, canto tranquilo',
                'company_id': 1,
                'branch_id': 1,
                'created_by': 1
            },
            {
                'customer_name': 'Empresa ABC - Reunião',
                'customer_phone': '+258 86 555 4444',
                'table_id': 3,
                'reservation_date': f'{today} 13:00:00',
                'time_slot': 'almoço',
                'people_count': 6,
                'estimated_amount': 1800.00,
                'deposit_percentage': 100.0,
                'deposit_amount': 1800.00,
                'payment_method': 'transfer',
                'payment_reference': 'TRF789012',
                'status': 'confirmed',
                'payment_status': 'paid',
                'notes': 'Reunião de negócios',
                'special_requests': 'Espaço para notebook, WiFi',
                'company_id': 1,
                'branch_id': 1,
                'created_by': 1
            },
            {
                'customer_name': 'Pedro Costa - Amigos',
                'customer_phone': '+258 87 222 3333',
                'table_id': 4,
                'reservation_date': f'{today} 20:30:00',
                'time_slot': 'jantar',
                'people_count': 4,
                'estimated_amount': 1200.00,
                'deposit_percentage': 0.0,
                'deposit_amount': 0.00,
                'payment_method': None,
                'payment_reference': None,
                'status': 'pending_payment',
                'payment_status': 'pending',
                'notes': 'Encontro de amigos',
                'special_requests': 'Mesa central',
                'company_id': 1,
                'branch_id': 1,
                'created_by': 1
            },
            {
                'customer_name': 'Ana Oliveira - Almoço',
                'customer_phone': '+258 88 777 8888',
                'table_id': 5,
                'reservation_date': f'{today} 12:30:00',
                'time_slot': 'almoço',
                'people_count': 3,
                'estimated_amount': 600.00,
                'deposit_percentage': 25.0,
                'deposit_amount': 150.00,
                'payment_method': 'emola',
                'payment_reference': 'EML345678',
                'status': 'confirmed',
                'payment_status': 'paid',
                'notes': 'Almoço de trabalho',
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
        
        print(f"✅ {len(test_reservations)} reservas de teste adicionadas com sucesso!")
        print("\n📋 Reservas criadas:")
        for i, res in enumerate(test_reservations, 1):
            print(f"  {i}. {res['customer_name']} - Mesa {res['table_id']} - {res['time_slot']} - {res['people_count']} pessoas")
        
    except Exception as e:
        print(f"❌ Erro ao adicionar reservas: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_test_reservations()
