from sqlalchemy import text
from app.database.connection import SessionLocal

def create_product_options_tables():
    """Cria as tabelas de opções de produtos para restaurantes"""
    db = SessionLocal()
    try:
        # Tabela de grupos de opções
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS product_option_groups (
                id SERIAL PRIMARY KEY,
                company_id INTEGER NOT NULL REFERENCES companies(id),
                branch_id INTEGER NOT NULL REFERENCES branches(id),
                product_id INTEGER NOT NULL REFERENCES products(id),
                name VARCHAR(100) NOT NULL,
                display_type VARCHAR(20) NOT NULL DEFAULT 'radio',
                is_required BOOLEAN NOT NULL DEFAULT FALSE,
                min_selections INTEGER NOT NULL DEFAULT 0,
                max_selections INTEGER NOT NULL DEFAULT 1,
                sort_order INTEGER NOT NULL DEFAULT 0,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """))

        # Tabela de opções
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS product_options (
                id SERIAL PRIMARY KEY,
                company_id INTEGER NOT NULL REFERENCES companies(id),
                branch_id INTEGER NOT NULL REFERENCES branches(id),
                option_group_id INTEGER NOT NULL REFERENCES product_option_groups(id),
                name VARCHAR(100) NOT NULL,
                description VARCHAR(200),
                price_adjustment NUMERIC(10,2) NOT NULL DEFAULT 0,
                adjustment_type VARCHAR(10) NOT NULL DEFAULT 'fixed',
                ingredient_impact JSONB NOT NULL DEFAULT '{}',
                sort_order INTEGER NOT NULL DEFAULT 0,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """))

        # Tabela de opções de itens de venda
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS sale_item_options (
                id SERIAL PRIMARY KEY,
                company_id INTEGER NOT NULL REFERENCES companies(id),
                branch_id INTEGER NOT NULL REFERENCES branches(id),
                sale_item_id INTEGER NOT NULL REFERENCES sale_items(id),
                option_group_id INTEGER NOT NULL REFERENCES product_option_groups(id),
                option_id INTEGER NOT NULL REFERENCES product_options(id),
                option_name VARCHAR(100) NOT NULL,
                price_adjustment NUMERIC(10,2) NOT NULL DEFAULT 0,
                ingredient_impact JSONB NOT NULL DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """))

        # Índices
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_product_option_groups_company_id ON product_option_groups(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_product_option_groups_branch_id ON product_option_groups(branch_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_product_option_groups_product_id ON product_option_groups(product_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_product_option_groups_is_active ON product_option_groups(is_active)"))

        db.execute(text("CREATE INDEX IF NOT EXISTS ix_product_options_company_id ON product_options(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_product_options_branch_id ON product_options(branch_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_product_options_option_group_id ON product_options(option_group_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_product_options_is_active ON product_options(is_active)"))

        db.execute(text("CREATE INDEX IF NOT EXISTS ix_sale_item_options_company_id ON sale_item_options(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_sale_item_options_branch_id ON sale_item_options(branch_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_sale_item_options_sale_item_id ON sale_item_options(sale_item_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_sale_item_options_option_group_id ON sale_item_options(option_group_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_sale_item_options_option_id ON sale_item_options(option_id)"))

        db.commit()
        print("✅ Tabelas de opções de produtos criadas com sucesso!")

    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao criar tabelas: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_product_options_tables()
