#!/usr/bin/env python3
"""
Script to list existing companies and their reset jobs.
Useful for debugging company reset issues.
"""

import os
from sqlalchemy import text
from app.database.connection import SessionLocal


def main():
    db = SessionLocal()
    try:
        print("=== Empresas ===")
        rows = db.execute(
            text(
                """
                SELECT id, name, nuit, created_at
                FROM companies
                ORDER BY id
                """
            )
        ).fetchall()
        if not rows:
            print("Nenhuma empresa encontrada.")
        else:
            for r in rows:
                print(f"[{r.id}] {r.name} (NUIT: {r.nuit}) — criada em {r.created_at}")

        print("\n=== Reset Jobs (últimos por empresa) ===")
        rows = db.execute(
            text(
                """
                SELECT
                    cj.id,
                    cj.company_id,
                    c.name AS company_name,
                    cj.status,
                    cj.progress,
                    cj.message,
                    cj.error,
                    cj.created_at,
                    cj.updated_at
                FROM company_reset_jobs cj
                JOIN companies c ON c.id = cj.company_id
                ORDER BY cj.company_id, cj.id DESC
                """
            )
        ).fetchall()
        if not rows:
            print("Nenhum reset job encontrado.")
        else:
            current_company = None
            for r in rows:
                if current_company != r.company_id:
                    current_company = r.company_id
                    print(f"\n--- Company {r.company_id} ({r.company_name}) ---")
                print(
                    f"  Job {r.id}: status={r.status} progress={r.progress}% message={r.message or ''}"
                )
                if r.error:
                    print(f"    ERROR: {r.error}")
                print(f"    created: {r.created_at} | updated: {r.updated_at}")

        print("\n=== Users por empresa (role) ===")
        rows = db.execute(
            text(
                """
                SELECT
                    c.id AS company_id,
                    c.name AS company_name,
                    u.id AS user_id,
                    u.name AS user_name,
                    u.email,
                    u.role,
                    u.branch_id
                FROM companies c
                LEFT JOIN users u ON u.company_id = c.id
                ORDER BY c.id, u.id
                """
            )
        ).fetchall()
        current_company = None
        for r in rows:
            if current_company != r.company_id:
                current_company = r.company_id
                print(f"\n--- Company {r.company_id} ({r.company_name}) ---")
            if r.user_id:
                print(
                    f"  User {r.user_id}: {r.user_name} <{r.email}> role={r.role or '(null)'} branch_id={r.branch_id}"
                )
            else:
                print("  (sem usuários)")

    finally:
        db.close()


if __name__ == "__main__":
    main()
