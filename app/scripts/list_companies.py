from sqlalchemy import select

from app.database.connection import SessionLocal
from app.models.company import Company


def main():
    db = SessionLocal()
    try:
        rows = db.scalars(select(Company).order_by(Company.id)).all()
        if not rows:
            print("Nenhuma empresa encontrada")
            return

        print(f"Total de empresas: {len(rows)}")
        for c in rows:
            print(
                " | ".join(
                    [
                        f"id={c.id}",
                        f"name={c.name}",
                        f"business_type={c.business_type}",
                        f"nuit={c.nuit or ''}",
                        f"email={c.email or ''}",
                        f"phone={c.phone or ''}",
                    ]
                )
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
