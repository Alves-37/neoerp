"""
Migration script para adicionar campos de status na tabela restaurant_tables
Execute: python -m app.scripts.add_table_status_fields
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.settings import Settings

settings = Settings()

def add_table_status_fields():
    """Adiciona campos de status à tabela restaurant_tables"""
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # Verificar se os campos já existem
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'restaurant_tables' 
            AND column_name IN ('status', 'current_order_id', 'customer_name', 'updated_at')
        """)).fetchall()
        
        existing_columns = [row[0] for row in result]
        
        # Adicionar campos que não existem
        if 'status' not in existing_columns:
            conn.execute(text("""
                ALTER TABLE restaurant_tables 
                ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'available'
            """))
            print("✅ Campo 'status' adicionado")
        
        if 'current_order_id' not in existing_columns:
            conn.execute(text("""
                ALTER TABLE restaurant_tables 
                ADD COLUMN current_order_id INTEGER NULL
            """))
            print("✅ Campo 'current_order_id' adicionado")
        
        if 'customer_name' not in existing_columns:
            conn.execute(text("""
                ALTER TABLE restaurant_tables 
                ADD COLUMN customer_name VARCHAR(100) NULL
            """))
            print("✅ Campo 'customer_name' adicionado")
        
        if 'updated_at' not in existing_columns:
            conn.execute(text("""
                ALTER TABLE restaurant_tables 
                ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            """))
            print("✅ Campo 'updated_at' adicionado")
            
            # Criar trigger para atualizar updated_at (PostgreSQL)
            try:
                conn.execute(text("""
                    CREATE OR REPLACE FUNCTION update_restaurant_tables_updated_at()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = CURRENT_TIMESTAMP;
                        RETURN NEW;
                    END;
                    $$ language 'plpgsql';
                """))
                
                conn.execute(text("""
                    CREATE TRIGGER update_restaurant_tables_updated_at_trigger
                        BEFORE UPDATE ON restaurant_tables
                        FOR EACH ROW
                        EXECUTE FUNCTION update_restaurant_tables_updated_at();
                """))
                print("✅ Trigger para updated_at criado")
            except Exception as e:
                print(f"⚠️  Trigger não criado (pode não ser PostgreSQL): {e}")
        
        conn.commit()
        print("🎉 Migration concluída com sucesso!")

if __name__ == "__main__":
    add_table_status_fields()
