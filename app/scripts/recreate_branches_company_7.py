#!/usr/bin/env python3
"""
Recriar as filiais da empresa 7 (VUCHADA) com base nos dados anteriores.
Este script deve ser executado após o reset para restaurar as filiais.
"""

from sqlalchemy import text
from app.database.connection import SessionLocal


def main():
    db = SessionLocal()
    try:
        company_id = 7

        # Buscar filiais existentes antes do reset (se houver backup ou logs)
        # Como não temos backup, vamos recriar as filiais com base nos usuários
        print("=== Recriando filiais com base nos usuários ===")

        # Verificar branch_ids dos usuários
        rows = db.execute(
            text(
                """
                SELECT DISTINCT branch_id, COUNT(*) as user_count
                FROM users
                WHERE company_id = :cid
                GROUP BY branch_id
                ORDER BY branch_id
                """
            ),
            {"cid": company_id},
        ).fetchall()

        if not rows:
            print("Nenhum branch_id encontrado nos usuários.")
            return

        print(f"Branch IDs encontrados: {[r.branch_id for r in rows]}")

        # Criar filiais baseadas nos branch_ids históricos
        # Mapeamento baseado nos dados que vimos anteriormente
        branch_mapping = {
            7: "Filial Restaurante",
            16: "Filial Retalho",
            19: "Filial Bar",
        }

        created_branches = {}
        business_type = "restaurant"  # padrão, pode ajustar

        for branch_id, user_count in rows:
            if branch_id is None:
                continue

            branch_name = branch_mapping.get(branch_id, f"Filial {branch_id}")
            
            print(f"Criando filial: {branch_name} (ID antigo: {branch_id})")

            # Inserir nova filial
            new_branch_id = db.execute(
                text(
                    """
                    INSERT INTO branches (company_id, name, business_type, is_active, public_menu_enabled)
                    VALUES (:cid, :name, :bt, TRUE, FALSE)
                    RETURNING id
                    """
                ),
                {"cid": company_id, "name": branch_name, "bt": business_type},
            ).scalar()

            created_branches[branch_id] = new_branch_id
            print(f"  -> Nova filial criada com ID: {new_branch_id}")

        db.commit()

        # Atualizar usuários para as novas filiais
        print("\n=== Atualizando usuários para novas filiais ===")
        users = db.execute(
            text(
                """
                SELECT id, name, email, branch_id
                FROM users
                WHERE company_id = :cid
                ORDER BY id
                """
            ),
            {"cid": company_id},
        ).fetchall()

        for user in users:
            old_branch_id = user.branch_id
            if old_branch_id in created_branches:
                new_branch_id = created_branches[old_branch_id]
                db.execute(
                    text("UPDATE users SET branch_id = :new_bid WHERE id = :uid"),
                    {"new_bid": new_branch_id, "uid": user.id},
                )
                print(f"  Usuário {user.name} -> Filial {new_branch_id}")

        db.commit()

        print("\n=== Filiais recriadas com sucesso ===")
        for old_id, new_id in created_branches.items():
            print(f"Branch antigo {old_id} -> Novo branch {new_id}")

        # Verificar resultado final
        final_branches = db.execute(
            text(
                """
                SELECT id, name, business_type, is_active
                FROM branches
                WHERE company_id = :cid
                ORDER BY id
                """
            ),
            {"cid": company_id},
        ).fetchall()

        print("\n=== Filiais atuais ===")
        for b in final_branches:
            print(f"[{b.id}] {b.name} ({b.business_type}) - {'Ativa' if b.is_active else 'Inativa'}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
