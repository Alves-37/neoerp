#!/usr/bin/env python3
"""
Reset company 7 (VUCHADA) safely, ignoring tables that don't exist.
"""

from sqlalchemy import text
from app.database.connection import SessionLocal


def main():
    db = SessionLocal()
    try:
        company_id = 7

        # Keep only admin/owner users
        rows = db.execute(
            text(
                """
                SELECT id FROM users
                WHERE company_id = :cid
                  AND lower(coalesce(role, '')) IN ('admin', 'owner')
                """
            ),
            {"cid": company_id},
        ).scalars().all()
        keep_ids = [int(x) for x in rows if x is not None]
        if not keep_ids:
            print("ERRO: Nenhum admin/owner encontrado para manter.")
            return
        print(f"Manter users: {keep_ids}")

        # Tables to delete (safe order)
        tables = [
            "debt_items",
            "debts",
            "sale_items",
            "sales",
            "fiscal_document_lines",
            "fiscal_documents",
            "quote_items",
            "quotes",
            "order_items",
            "orders",
            "restaurant_tables",
            "product_images",
            "product_stocks",
            "stock_movements",
            "stock_transfers",
            "stock_locations",
            "products",
            "product_categories",
            "customers",
            "suppliers",
            "supplier_purchases",
            "supplier_payments",
            "user_roles",
        ]

        for table in tables:
            try:
                r = db.execute(text(f"DELETE FROM {table} WHERE company_id = :cid"), {"cid": company_id})
                db.commit()
                if r.rowcount > 0:
                    print(f"Apagados {r.rowcount} registros de {table}")
            except Exception as e:
                db.rollback()
                if "does not exist" in str(e):
                    print(f"Tabela {table} não existe, ignorando.")
                else:
                    print(f"ERRO ao apagar {table}: {e}")
                    raise

        # Delete non-admin users
        r = db.execute(
            text(
                """
                DELETE FROM users
                WHERE company_id = :cid
                  AND NOT (id = ANY(:keep_ids))
                """
            ),
            {"cid": company_id, "keep_ids": keep_ids},
        )
        db.commit()
        print(f"Apagados {r.rowcount} usuários não-admin.")

        # Delete branches
        r = db.execute(text("DELETE FROM branches WHERE company_id = :cid"), {"cid": company_id})
        db.commit()
        print(f"Apagadas {r.rowcount} filiais.")

        # Recreate default branch
        bt = db.execute(text("SELECT business_type FROM companies WHERE id = :cid"), {"cid": company_id}).scalar()
        bt = bt or "retail"
        new_branch_id = db.execute(
            text(
                """
                INSERT INTO branches (company_id, name, business_type, is_active, public_menu_enabled)
                VALUES (:cid, 'Filial Principal', :bt, TRUE, FALSE)
                RETURNING id
                """
            ),
            {"cid": company_id, "bt": bt},
        ).scalar()
        db.commit()
        print(f"Recriada filial padrão com id {new_branch_id}.")

        # Update admins to new branch
        db.execute(
            text(
                """
                UPDATE users
                SET branch_id = :bid
                WHERE company_id = :cid
                  AND id = ANY(:keep_ids)
                """
            ),
            {"cid": company_id, "bid": new_branch_id, "keep_ids": keep_ids},
        )
        db.commit()
        print("Admins atualizados para nova filial.")

        print("\nReset concluído com sucesso.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
