#!/usr/bin/env python3
"""
Script para corrigir as reservas do Mutxutxu para a company_id correta
"""

import sqlite3
from datetime import datetime

def fix_mutxutu_reservations():
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Data de hoje
        today = datetime.now().date()
        
        # Reservas corrigidas para o restaurante Mutxutxu (Company ID: 10)
        mutxutu_reservations = [
            {
                'customer_name': 'Família Mutxutxu - Almoço Especial',
                'customer_phone': '+258 84 111 2222',
                'table_id': 1,
                'reservation_date': f'{today} 12:30:00',
                'time_slot': 'almoço',
                'people_count': 6,
                'estimated_amount': 1800.00,
                'deposit_percentage': 50.0,
                'deposit_amount': 900.00,
                'payment_method': 'mpesa',
                'payment_reference': 'MUTXU001',
                'status': 'confirmed',
                'payment_status': 'paid',
                'notes': 'Reserva no restaurante Mutxutxu',
                'special_requests': 'Mesa próxima à cozinha, cadeira infantil',
                'company_id': 10,  # CORRIGIDO!
                'branch_id': 1,    # Manter branch 1 por enquanto
                'created_by': 17   # Usuário Mutxutxu (owner)
            },
            {
                'customer_name': 'Casal Mutxutxu - Jantar Romântico',
                'customer_phone': '+258 85 333 4444',
                'table_id': 2,
                'reservation_date': f'{today} 20:00:00',
                'time_slot': 'jantar',
                'people_count': 2,
                'estimated_amount': 900.00,
                'deposit_percentage': 30.0,
                'deposit_amount': 270.00,
                'payment_method': 'cash',
                'payment_reference': '',
                'status': 'confirmed',
                'payment_status': 'paid',
                'notes': 'Jantar romântico no Mutxutxu',
                'special_requests': 'Mesa isolada, ambiente romântico',
                'company_id': 10,  # CORRIGIDO!
                'branch_id': 1,    # Manter branch 1 por enquanto
                'created_by': 17   # Usuário Mutxutxu (owner)
            },
            {
                'customer_name': 'Amigos Mutxutxu - Lanche da Tarde',
                'customer_phone': '+258 86 555 6666',
                'table_id': 3,
                'reservation_date': f'{today} 16:00:00',
                'time_slot': 'lanche',
                'people_count': 4,
                'estimated_amount': 600.00,
                'deposit_percentage': 0.0,
                'deposit_amount': 0.00,
                'payment_method': None,
                'payment_reference': None,
                'status': 'pending_payment',
                'payment_status': 'pending',
                'notes': 'Lanche com amigos no Mutxutxu',
                'special_requests': 'Área externa se possível',
                'company_id': 10,  # CORRIGIDO!
                'branch_id': 1,    # Manter branch 1 por enquanto
                'created_by': 17   # Usuário Mutxutxu (owner)
            },
            {
                'customer_name': 'Empresa Mutxutxu - Reunião de Negócios',
                'customer_phone': '+258 87 777 8888',
                'table_id': 4,
                'reservation_date': f'{today} 13:00:00',
                'time_slot': 'almoço',
                'people_count': 8,
                'estimated_amount': 2400.00,
                'deposit_percentage': 100.0,
                'deposit_amount': 2400.00,
                'payment_method': 'transfer',
                'payment_reference': 'MUTXU_BUSINESS',
                'status': 'confirmed',
                'payment_status': 'paid',
                'notes': 'Reunião de negócios no Mutxutxu',
                'special_requests': 'Espaço para apresentação, projetor',
                'company_id': 10,  # CORRIGIDO!
                'branch_id': 1,    # Manter branch 1 por enquanto
                'created_by': 17   # Usuário Mutxutxu (owner)
            },
            {
                'customer_name': 'Aniversário Mutxutxu - Grande Grupo',
                'customer_phone': '+258 88 999 0000',
                'table_id': 5,
                'reservation_date': f'{today} 19:30:00',
                'time_slot': 'jantar',
                'people_count': 10,
                'estimated_amount': 3000.00,
                'deposit_percentage': 50.0,
                'deposit_amount': 1500.00,
                'payment_method': 'mpesa',
                'payment_reference': 'MUTXU_PARTY',
                'status': 'confirmed',
                'payment_status': 'paid',
                'notes': 'Festa de aniversário no Mutxutxu',
                'special_requests': 'Mesa grande, bolo permitido, decoração simples',
                'company_id': 10,  # CORRIGIDO!
                'branch_id': 1,    # Manter branch 1 por enquanto
                'created_by': 17   # Usuário Mutxutxu (owner)
            },
            {
                'customer_name': 'Cliente Mutxutxu - Manhã Tranquila',
                'customer_phone': '+258 82 123 4567',
                'table_id': 6,
                'reservation_date': f'{today} 09:00:00',
                'time_slot': 'manhã',
                'people_count': 2,
                'estimated_amount': 400.00,
                'deposit_percentage': 25.0,
                'deposit_amount': 100.00,
                'payment_method': 'emola',
                'payment_reference': 'MUTXU_MORNING',
                'status': 'confirmed',
                'payment_status': 'paid',
                'notes': 'Café da manhã no Mutxutxu',
                'special_requests': 'Café forte, jornal disponível',
                'company_id': 10,  # CORRIGIDO!
                'branch_id': 1,    # Manter branch 1 por enquanto
                'created_by': 17   # Usuário Mutxutxu (owner)
            }
        ]
        
        # Limpar reservas existentes
        cursor.execute("DELETE FROM reservations")
        print("🗑️  Reservas anteriores limpas.")
        
        # Inserir novas reservas com company_id correta
        for reservation in mutxutu_reservations:
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
                reservation['company_id'],  # AGORA É 10!
                reservation['branch_id'],
                reservation['created_by']
            ))
        
        # Commit e fechar conexão
        conn.commit()
        conn.close()
        
        print(f"✅ {len(mutxutu_reservations)} reservas criadas para o RESTAURANTE MUTXUTXU!")
        print(f"\n🎯 INFORMAÇÕES CORRIGIDAS:")
        print(f"   • Company ID: {mutxutu_reservations[0]['company_id']} (Restaurante Mutxutxu)")
        print(f"   • Branch ID: {mutxutu_reservations[0]['branch_id']}")
        print(f"   • Created by: {mutxutu_reservations[0]['created_by']} (Mutxutxu - owner)")
        print(f"   • Data: {today}")
        
        print(f"\n👥 PARA ACESSAR:")
        print(f"   1. Faça login com: mutxutxu@gmail.com (owner)")
        print(f"   2. Ou com: abiude@gmail.com (cashier)")
        print(f"   3. Vá para 'Reservas' no menu")
        print(f"   4. Selecione a data: {today}")
        print(f"   5. As reservas devem aparecer!")
        
    except Exception as e:
        print(f"❌ Erro ao corrigir reservas Mutxutxu: {e}")

if __name__ == "__main__":
    fix_mutxutu_reservations()
