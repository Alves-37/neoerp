#!/usr/bin/env python3
"""Listar os produtos que o PDV efetivamente busca (mesma lógica do endpoint /products).

Objetivo
- Comparar o total de produtos existentes na reprografia (company 9) vs os que o PDV consegue buscar.

Como o PDV busca hoje
- Chama GET /products com:
  - is_active=true
  - q (opcional)
  - establishment_id (para admin, o PDV manda o establishment atual; para não-admin, o backend força o establishment do usuário)
  - NÃO manda branch_id (logo o backend usa current_user.branch_id)
  - (limit default = 50, se não for passado)

Este script replica a query do backend (routes/products.py) com:
- branch = filial reprografia da empresa 9
- establishment = ponto default da filial reprografia
- is_active=true
- limit/offset iguais ao endpoint (por padrão limit=50) para demonstrar a limitação

Uso:
  python -m app.scripts.list_products_company_9_reprography_pdv_query

Observação: script somente leitura.
"""

from __future__ import annotations

import json

from sqlalchemy import text

from app.database.connection import SessionLocal


COMPANY_ID = 9
BUSINESS_TYPE = "reprography"
ESTABLISHMENT_SCOPE = True
IS_ACTIVE_ONLY = True
LIMIT = 50
OFFSET = 0
OUTPUT_FORMAT = "jsonl"  # jsonl | pretty


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

        branches = db.execute(
            text(
                """
                SELECT id, name, business_type, is_active
                FROM branches
                WHERE company_id = :cid
                ORDER BY id
                """
            ),
            {"cid": COMPANY_ID},
        ).fetchall()

        repro = None
        for b in branches:
            if _norm_bt(getattr(b, "business_type", None)) == BUSINESS_TYPE:
                repro = b
                break

        if not repro:
            print(f"Nenhuma filial de reprografia encontrada para a empresa {COMPANY_ID}.")
            return

        points = db.execute(
            text(
                """
                SELECT id, name, is_active, is_default
                FROM establishments
                WHERE company_id = :cid AND branch_id = :bid
                ORDER BY id
                """
            ),
            {"cid": COMPANY_ID, "bid": int(repro.id)},
        ).fetchall()

        if not points:
            print(f"Filial reprografia [{repro.id}] não tem pontos (establishments).")
            return

        target = None
        for p in points:
            if bool(getattr(p, "is_default", False)):
                target = p
                break
        if not target:
            for p in points:
                if bool(getattr(p, "is_active", False)):
                    target = p
                    break
        if not target:
            target = points[0]

        print("=" * 80)
        print(f"EMPRESA [{company.id}] {company.name}")
        print(f"FILIAL REPROGRAFIA [{repro.id}] {repro.name} ({_norm_bt(repro.business_type)})")
        print(
            f"PONTO ALVO [{target.id}] {target.name} | ativo={bool(target.is_active)} | default={bool(target.is_default)}"
        )
        print(f"PARAMS: is_active={IS_ACTIVE_ONLY} establishment_scope={ESTABLISHMENT_SCOPE} limit={LIMIT} offset={OFFSET}")
        print("=" * 80)

        where_est = "AND p.establishment_id = :eid" if ESTABLISHMENT_SCOPE else ""
        where_active = "AND p.is_active = true" if IS_ACTIVE_ONLY else ""

        rows = db.execute(
            text(
                f"""
                SELECT
                    p.id,
                    p.name,
                    p.sku,
                    p.barcode,
                    p.track_stock,
                    p.is_service,
                    p.is_active,
                    p.min_stock,
                    p.default_location_id,
                    COALESCE(ps.qty_on_hand, 0) AS stock_qty_default_location
                FROM products p
                LEFT JOIN product_stocks ps ON ps.company_id = p.company_id
                    AND ps.branch_id = p.branch_id
                    AND ps.product_id = p.id
                    AND ps.location_id = p.default_location_id
                WHERE p.company_id = :cid
                  AND p.branch_id = :bid
                  AND p.business_type = :bt
                  {where_active}
                  {where_est}
                ORDER BY p.name ASC, p.id ASC
                LIMIT :lim OFFSET :off
                """
            ),
            {
                "cid": COMPANY_ID,
                "bid": int(repro.id),
                "bt": BUSINESS_TYPE,
                "eid": int(target.id),
                "lim": int(LIMIT),
                "off": int(OFFSET),
            },
        ).fetchall()

        print(f"Total retornado (simulando PDV/back-end com paginação): {len(rows)}")

        if OUTPUT_FORMAT == "pretty":
            for r in rows:
                print(json.dumps(dict(r._mapping), ensure_ascii=False, default=str, indent=2))
        else:
            for r in rows:
                print(json.dumps(dict(r._mapping), ensure_ascii=False, default=str))

        print("=" * 80)
        print("Fim.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
