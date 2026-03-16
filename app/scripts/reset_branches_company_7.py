#!/usr/bin/env python3
"""
Resetar todas as filiais da empresa 7 (deixar apenas a Filial Principal)
"""

from sqlalchemy import text
from app.database.connection import SessionLocal


def main():
    db = SessionLocal()
    try:
        company_id = 7

        print("=== Resetando filiais da empresa 7 ===")

        # Listar filiais atuais
        current = db.execute(
            text("SELECT id, name FROM branches WHERE company_id = :cid ORDER BY id"),
            {"cid": company_id},
        ).fetchall()

        print("Filiais atuais:")
        for b in current:
            print(f"  [{b.id}] {b.name}")

        # Apagar todas as filiais exceto a primeira (que será a Principal)
        if len(current) > 1:
            to_delete = current[1:]  # Manter apenas a primeira
            print(f"\nApagando {len(to_delete)} filiais...")
            for b in to_delete:
                db.execute(
                    text("DELETE FROM branches WHERE id = :bid"),
                    {"bid": b.id},
                )
                print(f"  Apagada: {b.name}")
        
        # Renomear a primeira para "Filial Principal" se não for já
        principal = current[0] if current else None
        if principal and principal.name != "Filial Principal":
            db.execute(
                text("UPDATE branches SET name = :name WHERE id = :bid"),
                {"name": "Filial Principal", "bid": principal.id},
            )
            print(f"\nRenomeada para: Filial Principal")

        # Atualizar todos os usuários para a filial principal
        db.execute(
            text("UPDATE users SET branch_id = :bid WHERE company_id = :cid"),
            {"bid": principal.id if principal else None, "cid": company_id},
        )

        db.commit()

        print("\n=== Resumo após reset ===")
        final = db.execute(
            text("SELECT id, name, business_type FROM branches WHERE company_id = :cid ORDER BY id"),
            {"cid": company_id},
        ).fetchall()

        for b in final:
            print(f"[{b.id}] {b.name} ({b.business_type})")

        print("\nTodos os usuários foram movidos para a Filial Principal.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
