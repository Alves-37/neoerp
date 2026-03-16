#!/usr/bin/env python3

from sqlalchemy import text

from app.database.connection import SessionLocal


def main():
    db = SessionLocal()
    try:
        exists = db.execute(
            text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'branches')")
        ).scalar()
        print(f"branches_table_exists: {bool(exists)}")

        companies_count = db.execute(text("SELECT COUNT(*) FROM companies")).scalar() or 0
        print(f"companies_count: {int(companies_count)}")

        users_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
        users_null_branch = db.execute(text("SELECT COUNT(*) FROM users WHERE branch_id IS NULL")).scalar() or 0
        print(f"users_count: {int(users_count)}")
        print(f"users_null_branch_id: {int(users_null_branch)}")

        if not exists:
            return

        branches_count = db.execute(text("SELECT COUNT(*) FROM branches")).scalar() or 0
        print(f"branches_count: {int(branches_count)}")

        per_company = db.execute(
            text(
                """
                SELECT c.id, c.name, COUNT(b.id) AS branches
                FROM companies c
                LEFT JOIN branches b ON b.company_id = c.id
                GROUP BY c.id, c.name
                ORDER BY c.id
                """
            )
        ).fetchall()

        print("\nbranches_by_company:")
        for r in per_company:
            print(f"  company_id={r.id} name={r.name} branches={int(r.branches or 0)}")

        sample = db.execute(
            text(
                """
                SELECT id, company_id, name, business_type, is_active
                FROM branches
                ORDER BY company_id, id
                LIMIT 50
                """
            )
        ).fetchall()

        print("\nbranches_sample:")
        for r in sample:
            print(
                f"  id={r.id} company_id={r.company_id} name={r.name} business_type={r.business_type} active={r.is_active}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()
