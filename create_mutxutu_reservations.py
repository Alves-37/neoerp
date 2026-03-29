#!/usr/bin/env python3
"""
Script para criar reservas para o restaurante Mutxutu
"""

import sqlite3
from datetime import datetime, timedelta

def create_mutxutu_reservations():
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Data de hoje
        today = datetime.now().date()
        
        # Reservas para o restaurante Mutxutu (vamos usar IDs genéricos que devem funcionar)
        mutxutu_reservations = [
            {
                'customer_name': 'Família Mutxutu - Almoço Especial',
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
                'notes': 'Reserva no restaurante Mutxutu',
                'special_requests': 'Mesa próxima à cozinha, cadeira infantil',
                'company_id': 1,
                'branch_id': 1,
                'created_by': 1
            },
            {
                'customer_name': 'Casal Mutxutu - Jantar Romântico',
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
                'notes': 'Jantar romântico no Mutxutu',
                'special_requests': 'Mesa isolada, ambiente romântico',
                'company_id': 1,
                'branch_id': 1,
                'created_by': 1
            },
            {
                'customer_name': 'Amigos Mutxutu - Lanche da Tarde',
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
                'notes': 'Lanche com amigos no Mutxutu',
                'special_requests': 'Área externa se possível',
                'company_id': 1,
                'branch_id': 1,
                'created_by': 1
            },
            {
                'customer_name': 'Empresa Mutxutu - Reunião de Negócios',
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
                'notes': 'Reunião de negócios no Mutxutu',
                'special_requests': 'Espaço para apresentação, projetor',
                'company_id': 1,
                'branch_id': 1,
                'created_by': 1
            },
            {
                'customer_name': 'Aniversário Mutxutu - Grande Grupo',
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
                'notes': 'Festa de aniversário no Mutxutu',
                'special_requests': 'Mesa grande, bolo permitido, decoração simples',
                'company_id': 1,
                'branch_id': 1,
                'created_by': 1
            },
            {
                'customer_name': 'Cliente Mutxutu - Manhã Tranquila',
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
                'notes': 'Café da manhã no Mutxutu',
                'special_requests': 'Café forte, jornal disponível',
                'company_id': 1,
                'branch_id': 1,
                'created_by': 1
            }
        ]
        
        # Limpar reservas existentes para evitar duplicatas
        cursor.execute("DELETE FROM reservations")
        print("🗑️  Reservas anteriores limpas.")
        
        # Inserir novas reservas
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
                reservation['company_id'],
                reservation['branch_id'],
                reservation['created_by']
            ))
        
        # Commit e fechar conexão
        conn.commit()
        conn.close()
        
        print(f"✅ {len(mutxutu_reservations)} reservas criadas para o restaurante Mutxutu!")
        print(f"\n📅 Data das reservas: {today}")
        print("\n🍽️ RESERVAS CRIADAS:")
        
        for i, res in enumerate(mutxutu_reservations, 1):
            emoji = "🌅" if res['time_slot'] == 'manhã' else "☀️" if res['time_slot'] == 'almoço' else "🌤️" if res['time_slot'] == 'lanche' else "🌙"
            print(f"  {i}. {emoji} {res['customer_name']}")
            print(f"     🪑 Mesa {res['table_id']} | 👥 {res['people_count']} pessoas | 💰 {res['estimated_amount']:.2f} MZN")
            print(f"     ⏰ {res['time_slot']} | 📊 {res['status']} | 💳 {res['payment_status']}")
            print(f"     📝 {res['notes']}")
            print("-" * 60)
        
        print(f"\n🎯 INFORMAÇÕES IMPORTANTES:")
        print(f"   • Company ID: {mutxutu_reservations[0]['company_id']}")
        print(f"   • Branch ID: {mutxutu_reservations[0]['branch_id']}")
        print(f"   • Data: {today}")
        print(f"   • Total de reservas: {len(mutxutu_reservations)}")
        
        print(f"\n💡 PARA VER AS RESERVAS:")
        print(f"   1. Faça login no sistema")
        print(f"   2. Vá para 'Reservas' no menu")
        print(f"   3. Selecione a data de hoje: {today}")
        print(f"   4. As reservas devem aparecer na lista")
        
    except Exception as e:
        print(f"❌ Erro ao criar reservas Mutxutu: {e}")

if __name__ == "__main__":
    create_mutxutu_reservations()
