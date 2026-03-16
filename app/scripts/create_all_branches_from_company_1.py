#!/usr/bin/env python3
"""
Criar todas as filiais da empresa 1 na empresa 7
"""

from sqlalchemy import text
from app.database.connection import SessionLocal


def main():
    db = SessionLocal()
    try:
        source_company_id = 1
        target_company_id = 7

        print("=== Copiando filiais da empresa 1 para empresa 7 ===")

        # Buscar filiais da empresa 1
        source_branches = db.execute(
            text(
                """
                SELECT name, business_type, is_active, public_menu_enabled,
                       public_menu_subdomain, public_menu_custom_domain
                FROM branches
                WHERE company_id = :cid
                ORDER BY id
                """
            ),
            {"cid": source_company_id},
        ).fetchall()

        if not source_branches:
            print("Nenhuma filial encontrada na empresa 1.")
            return

        print(f"Encontradas {len(source_branches)} filiais na empresa 1:")
        for b in source_branches:
            print(f"  - {b.name} ({b.business_type})")

        # Verificar filiais atuais na empresa 7
        existing = db.execute(
            text("SELECT name FROM branches WHERE company_id = :cid"),
            {"cid": target_company_id},
        ).fetchall()
        existing_names = {row.name for row in existing}

        created_branches = []
        for branch in source_branches:
            if branch.name in existing_names:
                print(f"\nFilial '{branch.name}' já existe na empresa 7, pulando.")
                continue

            print(f"\nCriando filial: {branch.name} ({branch.business_type})")
            
            new_branch_id = db.execute(
                text(
                    """
                    INSERT INTO branches (
                        company_id, name, business_type, is_active, 
                        public_menu_enabled, public_menu_subdomain, public_menu_custom_domain
                    )
                    VALUES (:cid, :name, :bt, :active, :menu_enabled, :subdomain, :custom_domain)
                    RETURNING id
                    """
                ),
                {
                    "cid": target_company_id,
                    "name": branch.name,
                    "bt": branch.business_type,
                    "active": branch.is_active,
                    "menu_enabled": branch.public_menu_enabled,
                    "subdomain": branch.public_menu_subdomain,
                    "custom_domain": branch.public_menu_custom_domain,
                },
            ).scalar()

            created_branches.append({
                "id": new_branch_id,
                "name": branch.name,
                "business_type": branch.business_type,
            })
            print(f"  -> Criada com ID: {new_branch_id}")

        db.commit()

        # Distribuir usuários pelas filiais
        print("\n=== Distribuindo usuários pelas filiais ===")
        
        # Buscar todas as filiais da empresa 7
        all_branches = db.execute(
            text(
                """
                SELECT id, name, business_type
                FROM branches
                WHERE company_id = :cid
                ORDER BY id
                """
            ),
            {"cid": target_company_id},
        ).fetchall()

        # Buscar usuários da empresa 7
        users = db.execute(
            text(
                """
                SELECT id, name, email, role
                FROM users
                WHERE company_id = :cid
                ORDER BY id
                """
            ),
            {"cid": target_company_id},
        ).fetchall()

        # Lógica de distribuição
        principal_branch = next((b for b in all_branches if "Principal" in b.name), all_branches[0])
        other_branches = [b for b in all_branches if b.id != principal_branch.id]

        user_idx = 0
        for user in users:
            if user.role and user.role.lower() in ["owner", "admin"]:
                # Owner/admin vai para a filial principal
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
            {"cid": target_company_id},
        ).fetchall()

        print(f"Total de filiais na empresa 7: {len(final_branches)}")
        for b in final_branches:
            status = "Ativa" if b.is_active else "Inativa"
            print(f"  [{b.id}] {b.name} ({b.business_type}) - {status}")

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
                {"cid": target_company_id, "bid": b.id},
            ).fetchall()
            
            if users_in_branch:
                print(f"\n  {b.name}:")
                for u in users_in_branch:
                    print(f"    - {u.name} ({u.role})")

    finally:
        db.close()


if __name__ == "__main__":
    main()
