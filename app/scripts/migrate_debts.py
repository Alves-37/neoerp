#!/usr/bin/env python3
"""
Script para migrar/criar as tabelas de dívidas (debts e debt_items)
"""

from sqlalchemy import text
from app.database.connection import SessionLocal


def main():
    db = SessionLocal()
    try:
        print("=== Verificando e criando tabelas de dívidas ===")

        # Verificar se a tabela debts existe
        check_debts = db.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'debts'
                )
            """)
        ).scalar()

        if not check_debts:
            print("Criando tabela 'debts'...")
            db.execute(text("""
                CREATE TABLE debts (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    branch_id INTEGER NOT NULL REFERENCES branches(id),
                    cashier_id INTEGER NULL REFERENCES users(id),
                    customer_id INTEGER NULL REFERENCES customers(id),
                    customer_name VARCHAR(120) NULL,
                    customer_nuit VARCHAR(30) NULL,
                    currency VARCHAR(10) NOT NULL DEFAULT 'MZN',
                    total NUMERIC(12,2) NOT NULL DEFAULT 0,
                    net_total NUMERIC(12,2) NOT NULL DEFAULT 0,
                    tax_total NUMERIC(12,2) NOT NULL DEFAULT 0,
                    include_tax BOOLEAN NOT NULL DEFAULT TRUE,
                    status VARCHAR(20) NOT NULL DEFAULT 'open',
                    sale_id INTEGER NULL REFERENCES sales(id),
                    notes TEXT NULL,
                    due_date DATE NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    paid_at TIMESTAMPTZ NULL
                );
            """))
            print("Tabela 'debts' criada com sucesso.")
        else:
            print("Tabela 'debts' já existe.")

        # Verificar se a tabela debt_items existe
        check_debt_items = db.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'debt_items'
                )
            """)
        ).scalar()

        if not check_debt_items:
            print("Criando tabela 'debt_items'...")
            db.execute(text("""
                CREATE TABLE debt_items (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    branch_id INTEGER NOT NULL REFERENCES branches(id),
                    debt_id INTEGER NOT NULL REFERENCES debts(id) ON DELETE CASCADE,
                    product_id INTEGER NULL REFERENCES products(id),
                    description VARCHAR(255) NULL,
                    qty NUMERIC(10,3) NOT NULL DEFAULT 0,
                    price_at_debt NUMERIC(12,2) NOT NULL DEFAULT 0,
                    cost_at_debt NUMERIC(12,2) NOT NULL DEFAULT 0,
                    discount_percent NUMERIC(5,2) NOT NULL DEFAULT 0,
                    line_total NUMERIC(12,2) NOT NULL DEFAULT 0,
                    tax_rate NUMERIC(5,2) NOT NULL DEFAULT 0,
                    notes TEXT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
            """))
            print("Tabela 'debt_items' criada com sucesso.")
        else:
            print("Tabela 'debt_items' já existe.")

        # Criar índices para melhor performance
        print("\nCriando índices...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS ix_debts_company_id ON debts(company_id)",
            "CREATE INDEX IF NOT EXISTS ix_debts_branch_id ON debts(branch_id)",
            "CREATE INDEX IF NOT EXISTS ix_debts_customer_id ON debts(customer_id)",
            "CREATE INDEX IF NOT EXISTS ix_debts_status ON debts(status)",
            "CREATE INDEX IF NOT EXISTS ix_debts_created_at ON debts(created_at)",
            "CREATE INDEX IF NOT EXISTS ix_debts_due_date ON debts(due_date)",
            "CREATE INDEX IF NOT EXISTS ix_debt_items_company_id ON debt_items(company_id)",
            "CREATE INDEX IF NOT EXISTS ix_debt_items_branch_id ON debt_items(branch_id)",
            "CREATE INDEX IF NOT EXISTS ix_debt_items_debt_id ON debt_items(debt_id)",
            "CREATE INDEX IF NOT EXISTS ix_debt_items_product_id ON debt_items(product_id)",
        ]

        for idx in indexes:
            db.execute(text(idx))

        db.commit()

        # Verificar resultado final
        print("\n=== Verificação final ===")
        tables = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name IN ('debts', 'debt_items')
            ORDER BY table_name
        """)).fetchall()

        print("Tabelas criadas/verificadas:")
        for t in tables:
            print(f"  ✓ {t.table_name}")

        # Contar registros (se existirem)
        debts_count = db.execute(text("SELECT COUNT(*) FROM debts")).scalar()
        debt_items_count = db.execute(text("SELECT COUNT(*) FROM debt_items")).scalar()
        
        print(f"\nRegistros atuais:")
        print(f"  debts: {debts_count}")
        print(f"  debt_items: {debt_items_count}")

        print("\nMigração das tabelas de dívidas concluída com sucesso!")

    except Exception as e:
        print(f"ERRO durante migração: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
