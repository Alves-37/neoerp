#!/usr/bin/env python3
"""
Listar todas as filiais da empresa 1
"""

from sqlalchemy import text
from app.database.connection import SessionLocal


def main():
    db = SessionLocal()
    try:
        company_id = 1

        print(f"=== Filiais da Empresa {company_id} ===")
        
        branches = db.execute(
            text(
                """
                SELECT id, name, business_type, is_active, public_menu_enabled, 
                       public_menu_subdomain, public_menu_custom_domain
                FROM branches
                WHERE company_id = :cid
                ORDER BY id
                """
            ),
            {"cid": company_id},
        ).fetchall()

        if not branches:
            print("Nenhuma filial encontrada.")
            return

        for b in branches:
            print(f"[{b.id}] {b.name}")
            print(f"    Tipo: {b.business_type}")
            print(f"    Status: {'Ativa' if b.is_active else 'Inativa'}")
            if b.public_menu_enabled:
                print(f"    Menu público: Ativo")
                if b.public_menu_subdomain:
                    print(f"      Subdomínio: {b.public_menu_subdomain}")
                if b.public_menu_custom_domain:
                    print(f"      Domínio próprio: {b.public_menu_custom_domain}")
            else:
                print(f"    Menu público: Inativo")
            print()

    finally:
        db.close()


if __name__ == "__main__":
    main()
