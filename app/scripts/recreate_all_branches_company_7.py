#!/usr/bin/env python3
"""
Recriar todas as filiais da empresa 7 (VUCHADA) que existiam antes do reset.
Baseado nos dados que vimos: Filial Principal, Filial Restaurante, Filial Retalho, Filial Bar
"""

from sqlalchemy import text
from app.database.connection import SessionLocal


def main():
    db = SessionLocal()
    try:
        company_id = 7

        print("=== Recriando todas as filiais da empresa 7 ===")

        # Definir as filiais que existiam antes
        branches_to_create = [
            {"name": "Filial Principal", "business_type": "retail"},
            {"name": "Filial Restaurante", "business_type": "restaurant"},
            {"name": "Filial Retalho", "business_type": "retail"},
            {"name": "Filial Bar", "business_type": "bar"},
            {"name": "Filial Mercadoria", "business_type": "retail"},
        ]

        # Verificar filiais atuais para não duplicar
        existing = db.execute(
            text("SELECT name FROM branches WHERE company_id = :cid"),
            {"cid": company_id},
        ).fetchall()
        existing_names = {row.name for row in existing}

        created_branches = []
        for branch in branches_to_create:
            if branch["name"] in existing_names:
                print(f"Filial '{branch['name']}' já existe, pulando.")
                continue

            print(f"Criando filial: {branch['name']} ({branch['business_type']})")
            
            new_branch_id = db.execute(
                text(
                    """
                    INSERT INTO branches (company_id, name, business_type, is_active, public_menu_enabled)
                    VALUES (:cid, :name, :bt, TRUE, FALSE)
                    RETURNING id
                    """
                ),
                {"cid": company_id, "name": branch["name"], "bt": branch["business_type"]},
            ).scalar()

            created_branches.append({"id": new_branch_id, "name": branch["name"], "business_type": branch["business_type"]})
            print(f"  -> Criada com ID: {new_branch_id}")

        db.commit()

        # Distribuir usuários pelas filiais
        print("\n=== Distribuindo usuários pelas filiais ===")
        
        # Buscar todas as filiais atuais
        all_branches = db.execute(
            text(
                """
                SELECT id, name, business_type
                FROM branches
                WHERE company_id = :cid
                ORDER BY id
                """
            ),
            {"cid": company_id},
        ).fetchall()

        # Buscar usuários
        users = db.execute(
            text(
                """
                SELECT id, name, email, role
                FROM users
                WHERE company_id = :cid
                ORDER BY id
                """
            ),
            {"cid": company_id},
        ).fetchall()

        # Lógica de distribuição:
        # Owner -> Filial Principal
        # Outros -> distribuir equilibradamente
        
        principal_branch = next((b for b in all_branches if "Principal" in b.name), all_branches[0])
        other_branches = [b for b in all_branches if b.id != principal_branch.id]

        user_idx = 0
        for user in users:
            if user.role and user.role.lower() == "owner":
                # Owner vai para a filial principal
                target_branch = principal_branch
            else:
                # Outros usuários distribuídos pelas outras filiais
                if other_branches:
                    target_branch = other_branches[user_idx % len(other_branches)]
                    user_idx += 1
                else:
                    target_branch = principal_branch

            db.execute(
                text("UPDATE users SET branch_id = :bid WHERE id = :uid"),
                {"bid": target_branch.id, "uid": user.id},
            )
            print(f"  {user.name} ({user.role}) -> {target_branch.name}")

        db.commit()

        print("\n=== Resumo final ===")
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

        print("Filiais criadas/atualizadas:")
        for b in final_branches:
            print(f"  [{b.id}] {b.name} ({b.business_type}) - {'Ativa' if b.is_active else 'Inativa'}")

        print("\nUsuários por filial:")
        for b in final_branches:
            users_in_branch = db.execute(
                text(
                    """
                    SELECT name, role
                    FROM users
                    WHERE company_id = :cid AND branch_id = :bid
                    ORDER BY name
                    """
                ),
                {"cid": company_id, "bid": b.id},
            ).fetchall()
            
            if users_in_branch:
                print(f"\n  {b.name}:")
                for u in users_in_branch:
                    print(f"    - {u.name} ({u.role})")

    finally:
        db.close()


if __name__ == "__main__":
    main()
