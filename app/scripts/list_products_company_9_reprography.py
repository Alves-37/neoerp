#!/usr/bin/env python3
"""Listar todos os produtos da empresa Nelson (company_id=9) na filial de Reprografia.

- Resolve a filial (branches.business_type = reprography/reprografia) da empresa 9.
- Resolve o ponto (establishment) alvo:
  - Se existir um ponto default (is_default = true), usa ele.
  - Senão usa o primeiro ponto ativo.
  - Senão usa o primeiro ponto.
- Lista todos os produtos desta filial (e, opcionalmente, filtrando por ponto) com todos os campos.
- Inclui stock calculado para o default_location_id (product_stocks).

Uso:
  python -m app.scripts.list_products_company_9_reprography

Observação: script somente leitura.
"""

from __future__ import annotations

import json

from sqlalchemy import text

from app.database.connection import SessionLocal


COMPANY_ID = 9
BUSINESS_TYPE = "reprography"
FILTER_BY_ESTABLISHMENT = True
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

        branch = db.execute(
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
        for b in branch:
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
        print("=" * 80)

        params = {
            "cid": COMPANY_ID,
            "bid": int(repro.id),
            "eid": int(target.id),
        }

        where_est = "AND p.establishment_id = :eid" if FILTER_BY_ESTABLISHMENT else ""

        rows = db.execute(
            text(
                f"""
                SELECT
                    p.id,
                    p.company_id,
                    p.branch_id,
                    b.name AS branch_name,
                    b.business_type AS branch_business_type,
                    p.establishment_id,
                    e.name AS establishment_name,
                    p.category_id,
                    p.supplier_id,
                    p.default_location_id,
                    p.business_type,
                    p.name,
                    p.sku,
                    p.barcode,
                    p.unit,
                    p.price,
                    p.cost,
                    p.tax_rate,
                    p.min_stock,
                    p.track_stock,
                    p.is_service,
                    p.is_active,
                    p.show_in_menu,
                    p.attributes,
                    p.created_at,
                    p.updated_at,
                    COALESCE(ps.qty_on_hand, 0) AS stock_qty_default_location
                FROM products p
                JOIN branches b ON b.id = p.branch_id
                LEFT JOIN establishments e ON e.id = p.establishment_id
                LEFT JOIN product_stocks ps ON ps.company_id = p.company_id
                    AND ps.branch_id = p.branch_id
                    AND ps.product_id = p.id
                    AND ps.location_id = p.default_location_id
                WHERE p.company_id = :cid
                  AND p.branch_id = :bid
                  AND p.business_type = :bt
                  {where_est}
                ORDER BY p.name ASC, p.id ASC
                """
            ),
            {**params, "bt": BUSINESS_TYPE},
        ).fetchall()

        print(f"Total produtos: {len(rows)}")
        print("" if OUTPUT_FORMAT == "pretty" else "")

        if OUTPUT_FORMAT == "pretty":
            for r in rows:
                as_dict = dict(r._mapping)
                if isinstance(as_dict.get("attributes"), str):
                    try:
                        as_dict["attributes"] = json.loads(as_dict["attributes"])  # type: ignore[arg-type]
                    except Exception:
                        pass
                print(json.dumps(as_dict, ensure_ascii=False, default=str, indent=2))
        else:
            for r in rows:
                as_dict = dict(r._mapping)
                if isinstance(as_dict.get("attributes"), str):
                    try:
                        as_dict["attributes"] = json.loads(as_dict["attributes"])  # type: ignore[arg-type]
                    except Exception:
                        pass
                print(json.dumps(as_dict, ensure_ascii=False, default=str))

        print("=" * 80)
        print("Fim.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
