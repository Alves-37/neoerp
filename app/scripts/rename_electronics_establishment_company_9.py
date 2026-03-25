#!/usr/bin/env python3
"""Renomear o ponto da filial Eletrônica (electronics) da empresa 9 para 'Ponto Principal'.

Uso:
  python -m app.scripts.rename_electronics_establishment_company_9

O script:
- Encontra a filial electronics da empresa 9
- Escolhe o establishment principal atual (is_default=true, fallback menor id)
- Renomeia para 'Ponto Principal'

Observação: este script altera a base de dados.
"""

from __future__ import annotations

from sqlalchemy import text

from app.database.connection import SessionLocal


COMPANY_ID = 9
DEFAULT_NAME = "Ponto Principal"


def _norm_bt(bt: str | None) -> str:
    raw = (bt or "").strip().lower()
    return raw


def main() -> None:
    db = SessionLocal()
    try:
        branch = db.execute(
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

        electronics = None
        for b in branch:
            if _norm_bt(b.business_type) == "electronics":
                electronics = b
                break

        if not electronics:
            print("Filial electronics não encontrada.")
            return

        est_id = db.execute(
            text(
                """
                SELECT id
                FROM establishments
                WHERE company_id = :cid AND branch_id = :bid
                ORDER BY is_default DESC, id ASC
                LIMIT 1
                """
            ),
            {"cid": COMPANY_ID, "bid": int(electronics.id)},
        ).scalar()

        if not est_id:
            est_id = db.execute(
                text(
                    """
                    INSERT INTO establishments (company_id, branch_id, name, is_active, is_default)
                    VALUES (:cid, :bid, :name, true, true)
                    RETURNING id
                    """
                ),
                {"cid": COMPANY_ID, "bid": int(electronics.id), "name": DEFAULT_NAME},
            ).scalar()
            db.commit()
            print(f"Criado establishment [{est_id}] {DEFAULT_NAME} na filial electronics.")
            return

        current_name = db.execute(
            text("SELECT name FROM establishments WHERE id = :eid"),
            {"eid": int(est_id)},
        ).scalar()

        db.execute(
            text("UPDATE establishments SET name = :name WHERE id = :eid"),
            {"name": DEFAULT_NAME, "eid": int(est_id)},
        )
        db.commit()

        print(f"Filial electronics: [{electronics.id}] {electronics.name}")
        print(f"Establishment renomeado: [{est_id}] '{current_name}' -> '{DEFAULT_NAME}'")
        print("OK")

    finally:
        db.close()


if __name__ == "__main__":
    main()
