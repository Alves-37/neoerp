from sqlalchemy import text

from app.database.connection import SessionLocal


def main():
    db = SessionLocal()
    try:
        # companies.business_type
        db.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS business_type VARCHAR(50) NOT NULL DEFAULT 'retail'"))

        # branches (filiais/estabelecimentos)
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS branches (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    name VARCHAR(120) NOT NULL,
                    business_type VARCHAR(50) NOT NULL DEFAULT 'retail',
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    public_menu_enabled BOOLEAN NOT NULL DEFAULT FALSE,
                    public_menu_subdomain VARCHAR(120) NULL,
                    public_menu_custom_domain VARCHAR(255) NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
        )
        db.execute(text("ALTER TABLE branches ADD COLUMN IF NOT EXISTS public_menu_enabled BOOLEAN NOT NULL DEFAULT FALSE"))
        db.execute(text("ALTER TABLE branches ADD COLUMN IF NOT EXISTS public_menu_subdomain VARCHAR(120) NULL"))
        db.execute(text("ALTER TABLE branches ADD COLUMN IF NOT EXISTS public_menu_custom_domain VARCHAR(255) NULL"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_branches_company_id ON branches(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_branches_business_type ON branches(business_type)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_branches_is_active ON branches(is_active)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_branches_public_menu_enabled ON branches(public_menu_enabled)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_branches_public_menu_subdomain ON branches(public_menu_subdomain)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_branches_public_menu_custom_domain ON branches(public_menu_custom_domain)"))

        # ensure users.branch_id exists
        db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_users_branch_id ON users(branch_id)"))

        # establishments (pontos dentro da filial)
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS establishments (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    branch_id INTEGER NOT NULL REFERENCES branches(id),
                    name VARCHAR(120) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
        )
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_establishments_company_id ON establishments(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_establishments_branch_id ON establishments(branch_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_establishments_is_active ON establishments(is_active)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_establishments_name ON establishments(name)"))

        # ensure establishment_id columns exist
        db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS establishment_id INTEGER NULL REFERENCES establishments(id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_users_establishment_id ON users(establishment_id)"))

        db.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS establishment_id INTEGER NULL REFERENCES establishments(id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_products_establishment_id ON products(establishment_id)"))

        db.execute(text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS establishment_id INTEGER NULL REFERENCES establishments(id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_sales_establishment_id ON sales(establishment_id)"))

        # create a default establishment per branch if none exists
        db.execute(
            text(
                """
                INSERT INTO establishments (company_id, branch_id, name, is_active)
                SELECT b.company_id, b.id, 'Ponto Principal', TRUE
                FROM branches b
                WHERE NOT EXISTS (
                    SELECT 1 FROM establishments e WHERE e.branch_id = b.id
                );
                """
            )
        )

        # backfill users.establishment_id using the branch default establishment
        db.execute(
            text(
                """
                UPDATE users u
                SET establishment_id = e.id
                FROM (
                    SELECT branch_id, MIN(id) AS id
                    FROM establishments
                    GROUP BY branch_id
                ) e
                WHERE u.establishment_id IS NULL
                  AND u.branch_id IS NOT NULL
                  AND u.branch_id = e.branch_id;
                """
            )
        )

        # backfill products.establishment_id using the branch default establishment
        db.execute(
            text(
                """
                UPDATE products p
                SET establishment_id = e.id
                FROM (
                    SELECT branch_id, MIN(id) AS id
                    FROM establishments
                    GROUP BY branch_id
                ) e
                WHERE p.establishment_id IS NULL
                  AND p.branch_id IS NOT NULL
                  AND p.branch_id = e.branch_id;
                """
            )
        )

        # backfill sales.establishment_id using the cashier's current establishment_id (fallback to branch default)
        db.execute(
            text(
                """
                UPDATE sales s
                SET establishment_id = u.establishment_id
                FROM users u
                WHERE s.establishment_id IS NULL
                  AND s.cashier_id IS NOT NULL
                  AND u.id = s.cashier_id
                  AND u.establishment_id IS NOT NULL;
                """
            )
        )
        db.execute(
            text(
                """
                UPDATE sales s
                SET establishment_id = e.id
                FROM (
                    SELECT branch_id, MIN(id) AS id
                    FROM establishments
                    GROUP BY branch_id
                ) e
                WHERE s.establishment_id IS NULL
                  AND s.branch_id IS NOT NULL
                  AND s.branch_id = e.branch_id;
                """
            )
        )

        # cash sessions (abertura/fecho de caixa)
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS cash_sessions (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    branch_id INTEGER NOT NULL REFERENCES branches(id),
                    establishment_id INTEGER NULL REFERENCES establishments(id),
                    opened_by INTEGER NOT NULL REFERENCES users(id),
                    opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    opening_balance NUMERIC(12,2) NOT NULL DEFAULT 0,
                    status VARCHAR(20) NOT NULL DEFAULT 'open',
                    closed_at TIMESTAMPTZ NULL,
                    closed_by INTEGER NULL REFERENCES users(id),
                    closing_balance_expected NUMERIC(12,2) NOT NULL DEFAULT 0,
                    closing_balance_counted NUMERIC(12,2) NOT NULL DEFAULT 0,
                    difference NUMERIC(12,2) NOT NULL DEFAULT 0,
                    notes VARCHAR(255) NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
        )
        db.execute(text("ALTER TABLE cash_sessions ADD COLUMN IF NOT EXISTS establishment_id INTEGER NULL REFERENCES establishments(id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_cash_sessions_establishment_id ON cash_sessions(establishment_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_cash_sessions_company_id ON cash_sessions(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_cash_sessions_branch_id ON cash_sessions(branch_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_cash_sessions_opened_by ON cash_sessions(opened_by)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_cash_sessions_status ON cash_sessions(status)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_cash_sessions_opened_at ON cash_sessions(opened_at)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_cash_sessions_closed_at ON cash_sessions(closed_at)"))

        # backfill cash_sessions.establishment_id using the opened_by user's establishment_id (fallback to branch default)
        db.execute(
            text(
                """
                UPDATE cash_sessions cs
                SET establishment_id = u.establishment_id
                FROM users u
                WHERE cs.establishment_id IS NULL
                  AND cs.opened_by IS NOT NULL
                  AND u.id = cs.opened_by
                  AND u.establishment_id IS NOT NULL;
                """
            )
        )
        db.execute(
            text(
                """
                UPDATE cash_sessions cs
                SET establishment_id = e.id
                FROM (
                    SELECT branch_id, MIN(id) AS id
                    FROM establishments
                    GROUP BY branch_id
                ) e
                WHERE cs.establishment_id IS NULL
                  AND cs.branch_id IS NOT NULL
                  AND cs.branch_id = e.branch_id;
                """
            )
        )

        # user preference: visible branches in header
        db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS visible_branch_ids JSONB NULL"))

        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS company_reset_jobs (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    created_by INTEGER NULL REFERENCES users(id),
                    status VARCHAR(30) NOT NULL DEFAULT 'pending',
                    progress INTEGER NOT NULL DEFAULT 0,
                    message VARCHAR(255) NULL,
                    error TEXT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
        )
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_company_reset_jobs_company_id ON company_reset_jobs(company_id)"))

        # create a default branch for each company if none exists
        db.execute(
            text(
                """
                INSERT INTO branches (company_id, name, business_type, is_active)
                SELECT c.id, 'Filial Principal', COALESCE(NULLIF(c.business_type, ''), 'retail'), TRUE
                FROM companies c
                WHERE NOT EXISTS (
                    SELECT 1 FROM branches b WHERE b.company_id = c.id
                );
                """
            )
        )

        # backfill users.branch_id to the company's default (lowest id) branch
        db.execute(
            text(
                """
                UPDATE users u
                SET branch_id = b.id
                FROM (
                    SELECT company_id, MIN(id) AS id
                    FROM branches
                    GROUP BY company_id
                ) b
                WHERE u.branch_id IS NULL
                  AND u.company_id = b.company_id;
                """
            )
        )

        # branch_id columns for core business tables (isolation by filial)
        db.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_products_branch_id ON products(branch_id)"))

        # products.is_service (serviços sem stock/custo)
        db.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS is_service BOOLEAN NOT NULL DEFAULT FALSE"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_products_is_service ON products(is_service)"))

        db.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_customers_branch_id ON customers(branch_id)"))

        db.execute(text("ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_suppliers_branch_id ON suppliers(branch_id)"))

        db.execute(text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_sales_branch_id ON sales(branch_id)"))

        db.execute(text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS cash_session_id INTEGER NULL REFERENCES cash_sessions(id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_sales_cash_session_id ON sales(cash_session_id)"))

        # sales VAT fields
        db.execute(text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS include_tax BOOLEAN NOT NULL DEFAULT TRUE"))
        db.execute(text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS net_total NUMERIC(12,2) NOT NULL DEFAULT 0"))
        db.execute(text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS tax_total NUMERIC(12,2) NOT NULL DEFAULT 0"))

        # sales void/return metadata
        db.execute(text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS voided_at TIMESTAMPTZ NULL"))
        db.execute(text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS voided_by INTEGER NULL REFERENCES users(id)"))
        db.execute(text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS void_reason VARCHAR(255) NULL"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_sales_voided_at ON sales(voided_at)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_sales_voided_by ON sales(voided_by)"))

        db.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_branch_id ON orders(branch_id)"))

        db.execute(text("ALTER TABLE order_items ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_order_items_branch_id ON order_items(branch_id)"))

        db.execute(text("ALTER TABLE restaurant_tables ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_restaurant_tables_branch_id ON restaurant_tables(branch_id)"))

        db.execute(text("ALTER TABLE stock_locations ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_locations_branch_id ON stock_locations(branch_id)"))

        db.execute(text("ALTER TABLE product_stocks ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_product_stocks_branch_id ON product_stocks(branch_id)"))

        db.execute(text("ALTER TABLE stock_movements ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_movements_branch_id ON stock_movements(branch_id)"))

        db.execute(text("ALTER TABLE stock_transfers ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_transfers_branch_id ON stock_transfers(branch_id)"))

        db.execute(text("ALTER TABLE fiscal_documents ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_fiscal_documents_branch_id ON fiscal_documents(branch_id)"))

        db.execute(text("ALTER TABLE sale_items ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_sale_items_branch_id ON sale_items(branch_id)"))

        # backfill branch_id using the company's default (lowest id) branch
        db.execute(
            text(
                """
                UPDATE products t
                SET branch_id = b.id
                FROM (
                    SELECT company_id, MIN(id) AS id
                    FROM branches
                    GROUP BY company_id
                ) b
                WHERE t.branch_id IS NULL
                  AND t.company_id = b.company_id;
                """
            )
        )
        db.execute(
            text(
                """
                UPDATE customers t
                SET branch_id = b.id
                FROM (
                    SELECT company_id, MIN(id) AS id
                    FROM branches
                    GROUP BY company_id
                ) b
                WHERE t.branch_id IS NULL
                  AND t.company_id = b.company_id;
                """
            )
        )

        db.execute(
            text(
                """
                UPDATE suppliers t
                SET branch_id = b.id
                FROM (
                    SELECT company_id, MIN(id) AS id
                    FROM branches
                    GROUP BY company_id
                ) b
                WHERE t.branch_id IS NULL
                  AND t.company_id = b.company_id;
                """
            )
        )
        db.execute(
            text(
                """
                UPDATE sales t
                SET branch_id = b.id
                FROM (
                    SELECT company_id, MIN(id) AS id
                    FROM branches
                    GROUP BY company_id
                ) b
                WHERE t.branch_id IS NULL
                  AND t.company_id = b.company_id;
                """
            )
        )

        db.execute(
            text(
                """
                UPDATE sale_items si
                SET branch_id = s.branch_id
                FROM sales s
                WHERE si.branch_id IS NULL
                  AND s.id = si.sale_id;
                """
            )
        )

        db.execute(
            text(
                """
                UPDATE fiscal_documents fd
                SET branch_id = s.branch_id
                FROM sales s
                WHERE fd.branch_id IS NULL
                  AND fd.sale_id IS NOT NULL
                  AND s.id = fd.sale_id;
                """
            )
        )
        db.execute(
            text(
                """
                UPDATE orders t
                SET branch_id = b.id
                FROM (
                    SELECT company_id, MIN(id) AS id
                    FROM branches
                    GROUP BY company_id
                ) b
                WHERE t.branch_id IS NULL
                  AND t.company_id = b.company_id;
                """
            )
        )

        db.execute(
            text(
                """
                UPDATE restaurant_tables rt
                SET branch_id = b.id
                FROM (
                    SELECT company_id, MIN(id) AS id
                    FROM branches
                    GROUP BY company_id
                ) b
                WHERE rt.branch_id IS NULL
                  AND rt.company_id = b.company_id;
                """
            )
        )

        db.execute(
            text(
                """
                UPDATE order_items oi
                SET branch_id = o.branch_id
                FROM orders o
                WHERE oi.branch_id IS NULL
                  AND o.id = oi.order_id;
                """
            )
        )
        db.execute(
            text(
                """
                UPDATE stock_locations t
                SET branch_id = b.id
                FROM (
                    SELECT company_id, MIN(id) AS id
                    FROM branches
                    GROUP BY company_id
                ) b
                WHERE t.branch_id IS NULL
                  AND t.company_id = b.company_id;
                """
            )
        )

        db.execute(
            text(
                """
                UPDATE product_stocks ps
                SET branch_id = sl.branch_id
                FROM stock_locations sl
                WHERE ps.branch_id IS NULL
                  AND sl.id = ps.location_id;
                """
            )
        )

        db.execute(
            text(
                """
                UPDATE stock_movements sm
                SET branch_id = sl.branch_id
                FROM stock_locations sl
                WHERE sm.branch_id IS NULL
                  AND sl.id = sm.location_id;
                """
            )
        )

        db.execute(
            text(
                """
                UPDATE stock_transfers st
                SET branch_id = sl.branch_id
                FROM stock_locations sl
                WHERE st.branch_id IS NULL
                  AND sl.id = st.from_location_id;
                """
            )
        )

        # companies (Moçambique / dados cadastrais)
        db.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS nuit VARCHAR(30)"))
        db.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS email VARCHAR(255)"))
        db.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS phone VARCHAR(50)"))
        db.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS province VARCHAR(100)"))
        db.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS city VARCHAR(100)"))
        db.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS address VARCHAR(255)"))
        db.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS logo_url VARCHAR(500)"))

        # users.username
        db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(50)"))
        db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)"))

        # users.is_active
        db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE"))
        db.execute(text("UPDATE users SET is_active = TRUE WHERE is_active IS NULL"))

        # Backfill username for existing users if NULL
        db.execute(text("UPDATE users SET username = CONCAT('user_', id) WHERE username IS NULL"))
        db.execute(text("ALTER TABLE users ALTER COLUMN username SET NOT NULL"))

        # products
        db.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS business_type VARCHAR(50) NOT NULL DEFAULT 'retail'"))
        db.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS min_stock NUMERIC(12,3) NOT NULL DEFAULT 0"))
        db.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS show_in_menu BOOLEAN NOT NULL DEFAULT FALSE"))
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    category_id INTEGER NULL,
                    supplier_id INTEGER NULL REFERENCES suppliers(id),
                    business_type VARCHAR(50) NOT NULL DEFAULT 'retail',
                    name VARCHAR(255) NOT NULL,
                    sku VARCHAR(100) NULL,
                    barcode VARCHAR(100) NULL,
                    unit VARCHAR(30) NOT NULL DEFAULT 'un',
                    price NUMERIC(12,2) NOT NULL DEFAULT 0,
                    cost NUMERIC(12,2) NOT NULL DEFAULT 0,
                    tax_rate NUMERIC(6,2) NOT NULL DEFAULT 0,
                    min_stock NUMERIC(12,3) NOT NULL DEFAULT 0,
                    track_stock BOOLEAN NOT NULL DEFAULT TRUE,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    show_in_menu BOOLEAN NOT NULL DEFAULT FALSE,
                    attributes JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
        )

        db.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS supplier_id INTEGER REFERENCES suppliers(id)"))
        db.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS default_location_id INTEGER"))

        # sales.cashier_id (vincula venda ao usuário/caixa)
        db.execute(text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS cashier_id INTEGER REFERENCES users(id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_sales_cashier_id ON sales(cashier_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_products_company_id ON products(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_products_business_type ON products(business_type)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_products_name ON products(name)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_products_sku ON products(sku)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_products_barcode ON products(barcode)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_products_supplier_id ON products(supplier_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_products_default_location_id ON products(default_location_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_products_show_in_menu ON products(show_in_menu)"))

        # Auto-publish existing restaurant products (idempotent)
        db.execute(text("UPDATE products SET show_in_menu = TRUE WHERE business_type = 'restaurant' AND show_in_menu = FALSE"))

        # stock locations (warehouse / store)
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS stock_locations (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    type VARCHAR(30) NOT NULL,
                    name VARCHAR(120) NOT NULL,
                    is_default BOOLEAN NOT NULL DEFAULT FALSE,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
        )
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_locations_company_id ON stock_locations(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_locations_type ON stock_locations(type)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_locations_name ON stock_locations(name)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_locations_is_default ON stock_locations(is_default)"))

        # stock movements (history)
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS stock_movements (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    product_id INTEGER NOT NULL REFERENCES products(id),
                    location_id INTEGER NOT NULL REFERENCES stock_locations(id),
                    movement_type VARCHAR(30) NOT NULL,
                    qty_delta NUMERIC(12,3) NOT NULL,
                    reference_type VARCHAR(40) NULL,
                    reference_id INTEGER NULL,
                    notes VARCHAR(255) NULL,
                    created_by INTEGER NULL REFERENCES users(id),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
        )
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_movements_company_id ON stock_movements(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_movements_product_id ON stock_movements(product_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_movements_location_id ON stock_movements(location_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_movements_created_at ON stock_movements(created_at)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_movements_movement_type ON stock_movements(movement_type)"))

        # inventory balances per product/location
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS product_stocks (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    product_id INTEGER NOT NULL REFERENCES products(id),
                    location_id INTEGER NOT NULL REFERENCES stock_locations(id),
                    qty_on_hand NUMERIC(12,3) NOT NULL DEFAULT 0,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    CONSTRAINT uq_product_stocks_company_product_location UNIQUE(company_id, product_id, location_id)
                );
                """
            )
        )
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_product_stocks_company_id ON product_stocks(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_product_stocks_product_id ON product_stocks(product_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_product_stocks_location_id ON product_stocks(location_id)"))

        # stock transfers
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS stock_transfers (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    product_id INTEGER NOT NULL REFERENCES products(id),
                    from_location_id INTEGER NOT NULL REFERENCES stock_locations(id),
                    to_location_id INTEGER NOT NULL REFERENCES stock_locations(id),
                    qty NUMERIC(12,3) NOT NULL,
                    notes VARCHAR(255) NULL,
                    created_by INTEGER NULL REFERENCES users(id),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
        )
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_transfers_company_id ON stock_transfers(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_transfers_product_id ON stock_transfers(product_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_transfers_from_location_id ON stock_transfers(from_location_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_transfers_to_location_id ON stock_transfers(to_location_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_transfers_created_at ON stock_transfers(created_at)"))

        # create default locations for existing companies (Loja Principal + Armazém)
        db.execute(
            text(
                """
                INSERT INTO stock_locations (company_id, type, name, is_default, is_active)
                SELECT c.id, 'store', 'Loja Principal', TRUE, TRUE
                FROM companies c
                WHERE NOT EXISTS (
                    SELECT 1 FROM stock_locations sl WHERE sl.company_id = c.id
                );
                """
            )
        )
        db.execute(
            text(
                """
                INSERT INTO stock_locations (company_id, type, name, is_default, is_active)
                SELECT c.id, 'warehouse', 'Armazém', FALSE, TRUE
                FROM companies c
                WHERE NOT EXISTS (
                    SELECT 1 FROM stock_locations sl WHERE sl.company_id = c.id AND sl.type = 'warehouse'
                );
                """
            )
        )

        # backfill product default_location_id
        db.execute(
            text(
                """
                UPDATE products p
                SET default_location_id = sl.id
                FROM stock_locations sl
                WHERE p.default_location_id IS NULL
                  AND sl.company_id = p.company_id
                  AND sl.is_default = TRUE;
                """
            )
        )

        # product_categories
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS product_categories (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    business_type VARCHAR(50) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    color VARCHAR(32) NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    CONSTRAINT uq_product_categories_company_business_name UNIQUE(company_id, business_type, name)
                );
                """
            )
        )
        db.execute(text("ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS color VARCHAR(32) NULL"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_product_categories_company_id ON product_categories(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_product_categories_business_type ON product_categories(business_type)"))

        # reprography: printers
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS printers (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    branch_id INTEGER NOT NULL REFERENCES branches(id),
                    establishment_id INTEGER NOT NULL REFERENCES establishments(id),
                    serial_number VARCHAR(120) NOT NULL,
                    brand VARCHAR(120) NULL,
                    model VARCHAR(120) NULL,
                    initial_counter INTEGER NOT NULL DEFAULT 0,
                    installation_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    CONSTRAINT uq_printers_scope_serial UNIQUE(company_id, branch_id, establishment_id, serial_number)
                );
                """
            )
        )
        db.execute(text("ALTER TABLE printers ADD COLUMN IF NOT EXISTS company_id INTEGER"))
        db.execute(text("ALTER TABLE printers ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
        db.execute(text("ALTER TABLE printers ADD COLUMN IF NOT EXISTS establishment_id INTEGER"))
        db.execute(text("ALTER TABLE printers ADD COLUMN IF NOT EXISTS serial_number VARCHAR(120)"))
        db.execute(text("ALTER TABLE printers ADD COLUMN IF NOT EXISTS brand VARCHAR(120) NULL"))
        db.execute(text("ALTER TABLE printers ADD COLUMN IF NOT EXISTS model VARCHAR(120) NULL"))
        db.execute(text("ALTER TABLE printers ADD COLUMN IF NOT EXISTS initial_counter INTEGER NOT NULL DEFAULT 0"))
        db.execute(text("ALTER TABLE printers ADD COLUMN IF NOT EXISTS installation_date DATE NOT NULL DEFAULT CURRENT_DATE"))
        db.execute(text("ALTER TABLE printers ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE"))
        db.execute(text("ALTER TABLE printers ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now()"))
        db.execute(text("ALTER TABLE printers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printers_company_id ON printers(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printers_branch_id ON printers(branch_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printers_establishment_id ON printers(establishment_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printers_serial_number ON printers(serial_number)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printers_installation_date ON printers(installation_date)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printers_is_active ON printers(is_active)"))

        # reprography: billing registry (PDV3 faturamentos_reg equivalent)
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS printer_billing_registry (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    branch_id INTEGER NOT NULL REFERENCES branches(id),
                    establishment_id INTEGER NOT NULL REFERENCES establishments(id),
                    printer_id INTEGER NOT NULL REFERENCES printers(id),
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    copies_to INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    CONSTRAINT uq_printer_billing_registry_scope_unique UNIQUE(company_id, branch_id, establishment_id, printer_id, year, month)
                );
                """
            )
        )
        db.execute(text("ALTER TABLE printer_billing_registry ADD COLUMN IF NOT EXISTS company_id INTEGER"))
        db.execute(text("ALTER TABLE printer_billing_registry ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
        db.execute(text("ALTER TABLE printer_billing_registry ADD COLUMN IF NOT EXISTS establishment_id INTEGER"))
        db.execute(text("ALTER TABLE printer_billing_registry ADD COLUMN IF NOT EXISTS printer_id INTEGER"))
        db.execute(text("ALTER TABLE printer_billing_registry ADD COLUMN IF NOT EXISTS year INTEGER"))
        db.execute(text("ALTER TABLE printer_billing_registry ADD COLUMN IF NOT EXISTS month INTEGER"))
        db.execute(text("ALTER TABLE printer_billing_registry ADD COLUMN IF NOT EXISTS copies_to INTEGER NOT NULL DEFAULT 0"))
        db.execute(text("ALTER TABLE printer_billing_registry ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now()"))
        db.execute(text("ALTER TABLE printer_billing_registry ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_billing_registry_company_id ON printer_billing_registry(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_billing_registry_branch_id ON printer_billing_registry(branch_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_billing_registry_establishment_id ON printer_billing_registry(establishment_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_billing_registry_printer_id ON printer_billing_registry(printer_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_billing_registry_year_month ON printer_billing_registry(year, month)"))

        # reprography: printer counter types
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS printer_counter_types (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    branch_id INTEGER NOT NULL REFERENCES branches(id),
                    establishment_id INTEGER NOT NULL REFERENCES establishments(id),
                    code VARCHAR(50) NOT NULL,
                    name VARCHAR(120) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    CONSTRAINT uq_printer_counter_types_scope_code UNIQUE(company_id, branch_id, establishment_id, code)
                );
                """
            )
        )
        db.execute(text("ALTER TABLE printer_counter_types ADD COLUMN IF NOT EXISTS company_id INTEGER"))
        db.execute(text("ALTER TABLE printer_counter_types ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
        db.execute(text("ALTER TABLE printer_counter_types ADD COLUMN IF NOT EXISTS establishment_id INTEGER"))
        db.execute(text("ALTER TABLE printer_counter_types ADD COLUMN IF NOT EXISTS code VARCHAR(50)"))
        db.execute(text("ALTER TABLE printer_counter_types ADD COLUMN IF NOT EXISTS name VARCHAR(120)"))
        db.execute(text("ALTER TABLE printer_counter_types ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE"))
        db.execute(text("ALTER TABLE printer_counter_types ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now()"))
        db.execute(text("ALTER TABLE printer_counter_types ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_counter_types_company_id ON printer_counter_types(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_counter_types_branch_id ON printer_counter_types(branch_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_counter_types_establishment_id ON printer_counter_types(establishment_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_counter_types_code ON printer_counter_types(code)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_counter_types_is_active ON printer_counter_types(is_active)"))

        # reprography: printer contracts (allowance + price per page)
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS printer_contracts (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    branch_id INTEGER NOT NULL REFERENCES branches(id),
                    establishment_id INTEGER NOT NULL REFERENCES establishments(id),
                    printer_id INTEGER NOT NULL REFERENCES printers(id),
                    counter_type_id INTEGER NOT NULL REFERENCES printer_counter_types(id),
                    monthly_allowance INTEGER NOT NULL DEFAULT 0,
                    price_per_page NUMERIC(12,4) NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    CONSTRAINT uq_printer_contracts_scope_printer_type UNIQUE(company_id, branch_id, establishment_id, printer_id, counter_type_id)
                );
                """
            )
        )
        db.execute(text("ALTER TABLE printer_contracts ADD COLUMN IF NOT EXISTS company_id INTEGER"))
        db.execute(text("ALTER TABLE printer_contracts ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
        db.execute(text("ALTER TABLE printer_contracts ADD COLUMN IF NOT EXISTS establishment_id INTEGER"))
        db.execute(text("ALTER TABLE printer_contracts ADD COLUMN IF NOT EXISTS printer_id INTEGER"))
        db.execute(text("ALTER TABLE printer_contracts ADD COLUMN IF NOT EXISTS counter_type_id INTEGER"))
        db.execute(text("ALTER TABLE printer_contracts ADD COLUMN IF NOT EXISTS monthly_allowance INTEGER NOT NULL DEFAULT 0"))
        db.execute(text("ALTER TABLE printer_contracts ADD COLUMN IF NOT EXISTS price_per_page NUMERIC(12,4) NOT NULL DEFAULT 0"))
        db.execute(text("ALTER TABLE printer_contracts ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE"))
        db.execute(text("ALTER TABLE printer_contracts ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now()"))
        db.execute(text("ALTER TABLE printer_contracts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_contracts_company_id ON printer_contracts(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_contracts_branch_id ON printer_contracts(branch_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_contracts_establishment_id ON printer_contracts(establishment_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_contracts_printer_id ON printer_contracts(printer_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_contracts_counter_type_id ON printer_contracts(counter_type_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_contracts_is_active ON printer_contracts(is_active)"))

        # reprography: printer readings
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS printer_readings (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    branch_id INTEGER NOT NULL REFERENCES branches(id),
                    establishment_id INTEGER NOT NULL REFERENCES establishments(id),
                    printer_id INTEGER NOT NULL REFERENCES printers(id),
                    counter_type_id INTEGER NOT NULL REFERENCES printer_counter_types(id),
                    reading_date TIMESTAMPTZ NOT NULL,
                    counter_value INTEGER NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    CONSTRAINT uq_printer_readings_scope_unique UNIQUE(company_id, branch_id, establishment_id, printer_id, counter_type_id, reading_date)
                );
                """
            )
        )
        db.execute(text("ALTER TABLE printer_readings ADD COLUMN IF NOT EXISTS company_id INTEGER"))
        db.execute(text("ALTER TABLE printer_readings ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
        db.execute(text("ALTER TABLE printer_readings ADD COLUMN IF NOT EXISTS establishment_id INTEGER"))
        db.execute(text("ALTER TABLE printer_readings ADD COLUMN IF NOT EXISTS printer_id INTEGER"))
        db.execute(text("ALTER TABLE printer_readings ADD COLUMN IF NOT EXISTS counter_type_id INTEGER"))
        db.execute(text("ALTER TABLE printer_readings ADD COLUMN IF NOT EXISTS reading_date TIMESTAMPTZ"))
        db.execute(text("ALTER TABLE printer_readings ADD COLUMN IF NOT EXISTS counter_value INTEGER"))
        db.execute(text("ALTER TABLE printer_readings ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now()"))
        db.execute(text("ALTER TABLE printer_readings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_readings_company_id ON printer_readings(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_readings_branch_id ON printer_readings(branch_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_readings_establishment_id ON printer_readings(establishment_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_readings_printer_id ON printer_readings(printer_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_readings_counter_type_id ON printer_readings(counter_type_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_printer_readings_reading_date ON printer_readings(reading_date)"))

        # product_images
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS product_images (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    product_id INTEGER NOT NULL REFERENCES products(id),
                    file_path VARCHAR(500) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
        )

        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS order_items (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    order_id INTEGER NOT NULL REFERENCES orders(id),
                    product_id INTEGER NOT NULL REFERENCES products(id),
                    qty NUMERIC(12,3) NOT NULL DEFAULT 1,
                    price_at_order NUMERIC(12,2) NOT NULL DEFAULT 0,
                    cost_at_order NUMERIC(12,2) NOT NULL DEFAULT 0,
                    line_total NUMERIC(12,2) NOT NULL DEFAULT 0,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
        )
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_order_items_company_id ON order_items(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_order_items_order_id ON order_items(order_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_order_items_product_id ON order_items(product_id)"))

        # customers
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    name VARCHAR(255) NOT NULL,
                    nuit VARCHAR(30) NULL,
                    email VARCHAR(255) NULL,
                    phone VARCHAR(50) NULL,
                    address VARCHAR(255) NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
        )
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_customers_company_id ON customers(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_customers_name ON customers(name)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_customers_nuit ON customers(nuit)"))

        # fiscal_documents
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS fiscal_documents (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    sale_id INTEGER NULL REFERENCES sales(id),
                    cashier_id INTEGER NULL REFERENCES users(id),
                    document_type VARCHAR(30) NOT NULL,
                    series VARCHAR(20) NOT NULL DEFAULT 'A',
                    number INTEGER NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'issued',
                    customer_id INTEGER NULL REFERENCES customers(id),
                    customer_name VARCHAR(255) NULL,
                    customer_nuit VARCHAR(30) NULL,
                    currency VARCHAR(10) NOT NULL DEFAULT 'MZN',
                    net_total NUMERIC(12,2) NOT NULL DEFAULT 0,
                    tax_total NUMERIC(12,2) NOT NULL DEFAULT 0,
                    gross_total NUMERIC(12,2) NOT NULL DEFAULT 0,
                    issued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    cancelled_at TIMESTAMPTZ NULL,
                    cancelled_by INTEGER NULL REFERENCES users(id),
                    cancel_reason VARCHAR(255) NULL
                );
                """
            )
        )
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_fiscal_documents_company_id ON fiscal_documents(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_fiscal_documents_sale_id ON fiscal_documents(sale_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_fiscal_documents_cashier_id ON fiscal_documents(cashier_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_fiscal_documents_type_series_number ON fiscal_documents(document_type, series, number)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_fiscal_documents_status ON fiscal_documents(status)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_fiscal_documents_issued_at ON fiscal_documents(issued_at)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_fiscal_documents_customer_nuit ON fiscal_documents(customer_nuit)"))

        # fiscal_document_lines
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS fiscal_document_lines (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    fiscal_document_id INTEGER NOT NULL REFERENCES fiscal_documents(id),
                    product_id INTEGER NULL REFERENCES products(id),
                    description VARCHAR(255) NOT NULL,
                    qty NUMERIC(12,3) NOT NULL DEFAULT 1,
                    unit_price NUMERIC(12,2) NOT NULL DEFAULT 0,
                    line_net NUMERIC(12,2) NOT NULL DEFAULT 0,
                    tax_rate NUMERIC(6,2) NOT NULL DEFAULT 0,
                    line_tax NUMERIC(12,2) NOT NULL DEFAULT 0,
                    line_gross NUMERIC(12,2) NOT NULL DEFAULT 0
                );
                """
            )
        )
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_fiscal_document_lines_company_id ON fiscal_document_lines(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_fiscal_document_lines_doc_id ON fiscal_document_lines(fiscal_document_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_fiscal_document_lines_product_id ON fiscal_document_lines(product_id)"))

        # quotes (cotações / proformas)
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS quotes (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    cashier_id INTEGER NULL REFERENCES users(id),
                    series VARCHAR(20) NOT NULL DEFAULT 'A',
                    number INTEGER NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'open',
                    customer_name VARCHAR(255) NULL,
                    customer_nuit VARCHAR(30) NULL,
                    currency VARCHAR(10) NOT NULL DEFAULT 'MZN',
                    net_total NUMERIC(12,2) NOT NULL DEFAULT 0,
                    tax_total NUMERIC(12,2) NOT NULL DEFAULT 0,
                    gross_total NUMERIC(12,2) NOT NULL DEFAULT 0,
                    sale_id INTEGER NULL REFERENCES sales(id),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    CONSTRAINT uq_quotes_company_series_number UNIQUE(company_id, series, number)
                );
                """
            )
        )
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_quotes_company_id ON quotes(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_quotes_cashier_id ON quotes(cashier_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_quotes_status ON quotes(status)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_quotes_series_number ON quotes(series, number)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_quotes_customer_nuit ON quotes(customer_nuit)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_quotes_created_at ON quotes(created_at)"))

        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS quote_items (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    quote_id INTEGER NOT NULL REFERENCES quotes(id),
                    product_id INTEGER NULL REFERENCES products(id),
                    product_name VARCHAR(255) NOT NULL,
                    qty NUMERIC(12,3) NOT NULL DEFAULT 1,
                    unit_price NUMERIC(12,2) NOT NULL DEFAULT 0,
                    line_net NUMERIC(12,2) NOT NULL DEFAULT 0,
                    tax_rate NUMERIC(6,2) NOT NULL DEFAULT 0,
                    line_tax NUMERIC(12,2) NOT NULL DEFAULT 0,
                    line_gross NUMERIC(12,2) NOT NULL DEFAULT 0
                );
                """
            )
        )
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_quote_items_company_id ON quote_items(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_quote_items_quote_id ON quote_items(quote_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_quote_items_product_id ON quote_items(product_id)"))

        # suppliers
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS suppliers (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    name VARCHAR(255) NOT NULL,
                    nuit VARCHAR(30) NULL,
                    email VARCHAR(255) NULL,
                    phone VARCHAR(50) NULL,
                    address VARCHAR(255) NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
        )
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_suppliers_company_id ON suppliers(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_suppliers_name ON suppliers(name)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_suppliers_nuit ON suppliers(nuit)"))

        # supplier_purchases
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS supplier_purchases (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
                    doc_ref VARCHAR(100) NULL,
                    purchase_date DATE NULL,
                    currency VARCHAR(10) NOT NULL DEFAULT 'MZN',
                    total NUMERIC(12,2) NOT NULL DEFAULT 0,
                    status VARCHAR(20) NOT NULL DEFAULT 'open',
                    notes VARCHAR(255) NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
        )
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_supplier_purchases_company_id ON supplier_purchases(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_supplier_purchases_supplier_id ON supplier_purchases(supplier_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_supplier_purchases_status ON supplier_purchases(status)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_supplier_purchases_purchase_date ON supplier_purchases(purchase_date)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_supplier_purchases_doc_ref ON supplier_purchases(doc_ref)"))

        # supplier_payments
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS supplier_payments (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
                    purchase_id INTEGER NULL REFERENCES supplier_purchases(id),
                    payment_date DATE NULL,
                    method VARCHAR(30) NOT NULL DEFAULT 'cash',
                    amount NUMERIC(12,2) NOT NULL DEFAULT 0,
                    reference VARCHAR(120) NULL,
                    notes VARCHAR(255) NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
        )
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_supplier_payments_company_id ON supplier_payments(company_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_supplier_payments_supplier_id ON supplier_payments(supplier_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_supplier_payments_purchase_id ON supplier_payments(purchase_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_supplier_payments_payment_date ON supplier_payments(payment_date)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS ix_supplier_payments_reference ON supplier_payments(reference)"))

        db.commit()
        print('Migration completed successfully.')
    finally:
        db.close()


if __name__ == '__main__':
    main()
