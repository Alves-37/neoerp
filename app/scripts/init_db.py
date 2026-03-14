from sqlalchemy import select

from app.database.connection import Base, SessionLocal, engine
from app.models.branch import Branch
from app.models.company import Company
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.user import User
from app.services.auth_service import hash_password
from app.services.default_branches import get_default_branches


def main():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        company = db.scalar(select(Company).where(Company.name == "Neotrix Tecnologias"))
        if not company:
            company = Company(name="Neotrix Tecnologias", business_type="retail", owner_id=None)
            db.add(company)
            db.commit()
            db.refresh(company)

        branches = db.scalars(select(Branch).where(Branch.company_id == company.id)).all()
        if not branches:
            for name, bt in get_default_branches():
                db.add(Branch(company_id=company.id, name=name, business_type=bt, is_active=True))
            db.commit()
            branches = db.scalars(select(Branch).where(Branch.company_id == company.id)).all()

        retail_branch = next((b for b in branches if (b.business_type or "").lower() == "retail"), None)

        admin = db.scalar(select(User).where(User.email == "neotrix@gmail.com"))
        if not admin:
            admin = User(
                company_id=company.id,
                branch_id=retail_branch.id if retail_branch else None,
                name="Admin",
                username="Neotrix37",
                email="neotrix@gmail.com",
                password_hash=hash_password("842384"),
                role="admin",
            )
            db.add(admin)
            db.commit()

        print("DB initialized. Login: neotrix@gmail.com / 842384")
    finally:
        db.close()


if __name__ == "__main__":
    main()
