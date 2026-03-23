#!/usr/bin/env python3
"""Criar ponto na filial de Reprografia e mover impressoras existentes para ele.

Uso:
  python -m app.scripts.fix_reprography_printers_establishment

O script:
- Encontra a filial reprografia da empresa 9 (Nelson Multservice)
- Cria (se não existir) o ponto 'Gráfica e Papelaria Cidade Gurue'
- Move todas as impressoras da filial para este ponto (UPDATE printers.establishment_id)

Observação: este script altera a base de dados.
"""

from __future__ import annotations

from sqlalchemy import text

from app.database.connection import SessionLocal


COMPANY_ID = 9
BRANCH_BUSINESS_TYPE = "reprography"
TARGET_ESTABLISHMENT_NAME = "Gráfica e Papelaria Cidade Gurue"

# Safety: set to True to only print what would change.
DRY_RUN = False


def _norm_bt(bt: str | None) -> str:
    raw = (bt or "").strip().lower()
    if raw == "reprografia":
        return "reprography"
    return raw


def main() -> None:
    db = SessionLocal()
    try:
        company = db.execute(
            text(
                """
                SELECT id, name
                FROM companies
                WHERE id = :cid
                """
            ),
            {"cid": COMPANY_ID},
        ).fetchone()

        if not company:
            print(f"Empresa {COMPANY_ID} não encontrada.")
            return

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

        repro = None
        for b in branch:
            if _norm_bt(b.business_type) == BRANCH_BUSINESS_TYPE:
                repro = b
                break

        if not repro:
            print("Filial de reprografia não encontrada para a empresa.")
            return

        print(f"Empresa: [{company.id}] {company.name}")
        print(f"Filial Reprografia: [{repro.id}] {repro.name}")

        # Create or find target establishment
        est_id = db.execute(
            text(
                """
                SELECT id
                FROM establishments
                WHERE company_id = :cid
                  AND branch_id = :bid
                  AND lower(name) = lower(:name)
                LIMIT 1
                """
            ),
            {"cid": COMPANY_ID, "bid": int(repro.id), "name": TARGET_ESTABLISHMENT_NAME},
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
                {"cid": COMPANY_ID, "bid": int(repro.id), "name": TARGET_ESTABLISHMENT_NAME},
            ).scalar()
            print(f"Ponto criado: [{est_id}] {TARGET_ESTABLISHMENT_NAME}")
        else:
            print(f"Ponto já existe: [{est_id}] {TARGET_ESTABLISHMENT_NAME}")

        # Ensure target is the default for this branch.
        if not DRY_RUN:
            db.execute(
                text(
                    """
                    UPDATE establishments
                    SET is_default = CASE WHEN id = :eid THEN TRUE ELSE FALSE END
                    WHERE company_id = :cid AND branch_id = :bid
                    """
                ),
                {"eid": int(est_id), "cid": COMPANY_ID, "bid": int(repro.id)},
            )

        # Strategy A: migrate references from other establishments of this branch to the target,
        # preserving history, and then delete the old establishments.
        old_ids = db.execute(
            text(
                """
                SELECT id
                FROM establishments
                WHERE company_id = :cid
                  AND branch_id = :bid
                  AND id <> :eid
                ORDER BY id
                """
            ),
            {"cid": COMPANY_ID, "bid": int(repro.id), "eid": int(est_id)},
        ).scalars().all()

        print(f"Pontos antigos na filial reprografia para migrar/remover: {len(old_ids)}")
        if not old_ids:
            if not DRY_RUN:
                db.commit()
            print("Nada a fazer.")
            return

        def _bulk_update(table: str, extra_where: str = "") -> int:
            where_extra = f" AND {extra_where} " if extra_where.strip() else ""
            res = db.execute(
                text(
                    f"""
                    UPDATE {table}
                    SET establishment_id = :new_eid
                    WHERE company_id = :cid
                      AND branch_id = :bid
                      AND establishment_id = ANY(:old_ids)
                      {where_extra}
                    """
                ),
                {"new_eid": int(est_id), "cid": COMPANY_ID, "bid": int(repro.id), "old_ids": list(old_ids)},
            )
            return int(getattr(res, "rowcount", 0) or 0)

        def _bulk_update_no_branch(table: str) -> int:
            res = db.execute(
                text(
                    f"""
                    UPDATE {table}
                    SET establishment_id = :new_eid
                    WHERE company_id = :cid
                      AND establishment_id = ANY(:old_ids)
                    """
                ),
                {"new_eid": int(est_id), "cid": COMPANY_ID, "old_ids": list(old_ids)},
            )
            return int(getattr(res, "rowcount", 0) or 0)

        if DRY_RUN:
            print("DRY_RUN=True: nenhuma alteração será aplicada.")
            return

        # Core tables with establishment_id
        moved_users = _bulk_update_no_branch("users")
        moved_products = _bulk_update("products")
        moved_sales = _bulk_update("sales")
        moved_cash = _bulk_update("cash_sessions")
        moved_expenses = _bulk_update("expenses")

        # Reprography tables
        moved_printers = _bulk_update("printers")
        moved_ctypes = _bulk_update("printer_counter_types")
        moved_contracts = _bulk_update("printer_contracts")
        moved_readings = _bulk_update("printer_readings")
        moved_billing = _bulk_update("printer_billing_registry")

        # Delete old establishments (now hopefully unreferenced).
        deleted = db.execute(
            text(
                """
                DELETE FROM establishments
                WHERE company_id = :cid
                  AND branch_id = :bid
                  AND id = ANY(:old_ids)
                """
            ),
            {"cid": COMPANY_ID, "bid": int(repro.id), "old_ids": list(old_ids)},
        ).rowcount

        db.commit()

        print("Migração concluída.")
        print(f"- users: {moved_users}")
        print(f"- products: {moved_products}")
        print(f"- sales: {moved_sales}")
        print(f"- cash_sessions: {moved_cash}")
        print(f"- expenses: {moved_expenses}")
        print(f"- printers: {moved_printers}")
        print(f"- printer_counter_types: {moved_ctypes}")
        print(f"- printer_contracts: {moved_contracts}")
        print(f"- printer_readings: {moved_readings}")
        print(f"- printer_billing_registry: {moved_billing}")
        print(f"Pontos antigos apagados: {deleted}")
        print("OK")

    finally:
        db.close()


if __name__ == "__main__":
    main()
