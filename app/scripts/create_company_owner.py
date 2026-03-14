from sqlalchemy import select

from app.database.connection import SessionLocal
from app.models.branch import Branch
from app.models.company import Company
from app.models.user import User
from app.services.auth_service import hash_password
from app.services.default_branches import get_default_branches


def main():
    email = "vuchada@gmail.com"
    name = "Saide Adamo Marrapaz"
    username = "Marrapaz"
    password = "603684"

    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == email))
        if existing:
            raise RuntimeError(f"Já existe um usuário com este email: {email}")

        existing_u = db.scalar(select(User).where(User.username == username))
        if existing_u:
            raise RuntimeError(f"Já existe um usuário com este username: {username}")

        company = Company(name=name, business_type="retail")
        db.add(company)
        db.flush()

        branch_ids = {}
        for branch_name, bt in get_default_branches():
            b = Branch(company_id=company.id, name=branch_name, business_type=bt, is_active=True)
            db.add(b)
            db.flush()
            branch_ids[bt] = b.id

        retail_branch_id = branch_ids.get("retail")

        user = User(
            company_id=company.id,
            branch_id=retail_branch_id,
            name=name,
            username=username,
            email=email,
            password_hash=hash_password(password),
            role="owner",
            is_active=True,
        )
        db.add(user)

        company.owner_id = user.id
        db.add(company)

        db.commit()
        print("Company created successfully")
        print(f"company_id={company.id} branch_id={retail_branch_id} user_id={user.id}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
