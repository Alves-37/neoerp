from sqlalchemy import select

from app.database.connection import SessionLocal
from app.models.branch import Branch
from app.models.company import Company
from app.services.default_branches import get_default_branches


def main():
    db = SessionLocal()
    try:
        companies = db.scalars(select(Company).order_by(Company.id.asc())).all()
        created = 0
        for c in companies:
            existing = db.scalars(select(Branch).where(Branch.company_id == c.id)).all()
            existing_bt = {(b.business_type or '').strip().lower() for b in (existing or [])}

            for name, bt in get_default_branches():
                key = (bt or '').strip().lower()
                if not key or key in existing_bt:
                    continue
                db.add(Branch(company_id=c.id, name=name, business_type=bt, is_active=True))
                existing_bt.add(key)
                created += 1

        db.commit()
        print(f"Default branches ensured. Created {created} branches across {len(companies)} companies.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
