#!/usr/bin/env python3
"""Garantir que cada filial da empresa 9 tenha pelo menos 1 ponto e exatamente 1 ponto principal.

Uso:
  python -m app.scripts.ensure_one_default_establishment_per_branch_company_9

O script:
- Para cada branch da empresa 9:
  - Se não tiver establishments, cria 'Ponto Principal' (is_default=true)
  - Se tiver establishments:
    - Define exatamente 1 como principal (o menor id), e desmarca os outros

Observação: este script altera a base de dados.
"""

from __future__ import annotations

from sqlalchemy import text

from app.database.connection import SessionLocal


COMPANY_ID = 9
DEFAULT_NAME = "Ponto Principal"


def main() -> None:
    db = SessionLocal()
    try:
        branches = db.execute(
            text(
                """
                SELECT id, name, business_type
                FROM branches
                WHERE company_id = :cid
                ORDER BY id
                """
            ),
            {"cid": COMPANY_ID},
        ).fetchall()

        if not branches:
            print("Nenhuma filial encontrada.")
            return

        print(f"Empresa {COMPANY_ID}: garantindo 1 ponto principal por filial...")

        for b in branches:
            bid = int(b.id)
            count_points = db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM establishments
                    WHERE company_id = :cid AND branch_id = :bid
                    """
                ),
                {"cid": COMPANY_ID, "bid": bid},
            ).scalar()

            if int(count_points or 0) == 0:
                new_id = db.execute(
                    text(
                        """
                        INSERT INTO establishments (company_id, branch_id, name, is_active, is_default)
                        VALUES (:cid, :bid, :name, true, true)
                        RETURNING id
                        """
                    ),
                    {"cid": COMPANY_ID, "bid": bid, "name": DEFAULT_NAME},
                ).scalar()
                print(f"- Filial [{bid}] {b.name}: criado ponto principal [{new_id}] {DEFAULT_NAME}")
                continue

            # pick min(id) as default
            default_id = db.execute(
                text(
                    """
                    SELECT MIN(id)
                    FROM establishments
                    WHERE company_id = :cid AND branch_id = :bid
                    """
                ),
                {"cid": COMPANY_ID, "bid": bid},
            ).scalar()

            db.execute(
                text(
                    """
                    UPDATE establishments
                    SET is_default = CASE WHEN id = :did THEN TRUE ELSE FALSE END
                    WHERE company_id = :cid AND branch_id = :bid
                    """
                ),
                {"cid": COMPANY_ID, "bid": bid, "did": int(default_id)},
            )
            print(f"- Filial [{bid}] {b.name}: principal = [{int(default_id)}]")

        db.commit()
        print("OK")

    finally:
        db.close()


if __name__ == "__main__":
    main()
