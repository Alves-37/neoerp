#!/usr/bin/env python3
"""Listar pontos (establishments) e impressoras (reprography) da empresa Nelson Multi-Service.

- Lista todas as filiais da empresa 9.
- Para cada filial, lista todos os pontos.
- Para pontos de filiais de reprografia (business_type == reprography/reprografia), lista as impressoras cadastradas.

Uso:
  python -m app.scripts.list_establishments_and_printers_company_9

Observação: este script é somente leitura.
"""

from __future__ import annotations

from sqlalchemy import text

from app.database.connection import SessionLocal


COMPANY_ID = 9


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

        print("=" * 80)
        print(f"EMPRESA {company.id}: {company.name}")
        print("=" * 80)

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

        if not branches:
            print("Nenhuma filial encontrada.")
            return

        for b in branches:
            bt = _norm_bt(b.business_type)
            status = "Ativa" if b.is_active else "Inativa"
            print(f"\n--- Filial [{b.id}] {b.name} ({bt}) — {status} ---")

            points = db.execute(
                text(
                    """
                    SELECT id, name, is_active
                    FROM establishments
                    WHERE company_id = :cid AND branch_id = :bid
                    ORDER BY id
                    """
                ),
                {"cid": COMPANY_ID, "bid": int(b.id)},
            ).fetchall()

            if not points:
                print("  (sem pontos)")
                continue

            for p in points:
                pstatus = "Ativo" if p.is_active else "Inativo"
                print(f"  Ponto [{p.id}] {p.name} — {pstatus}")

                if bt != "reprography":
                    continue

                printers = db.execute(
                    text(
                        """
                        SELECT id, serial_number, brand, model, is_active
                        FROM printers
                        WHERE company_id = :cid AND branch_id = :bid AND establishment_id = :eid
                        ORDER BY serial_number, id
                        """
                    ),
                    {"cid": COMPANY_ID, "bid": int(b.id), "eid": int(p.id)},
                ).fetchall()

                if not printers:
                    print("    Impressoras: (nenhuma)")
                    continue

                print("    Impressoras:")
                for pr in printers:
                    prstatus = "Ativa" if pr.is_active else "Inativa"
                    brand = (pr.brand or "").strip()
                    model = (pr.model or "").strip()
                    details = " ".join(x for x in [brand, model] if x)
                    details = f" — {details}" if details else ""
                    print(f"      - [{pr.id}] {pr.serial_number}{details} — {prstatus}")

        print("\n" + "=" * 80)
        print("IMPRESSORAS (todas) — onde estão cadastradas")
        print("=" * 80)

        all_printers = db.execute(
            text(
                """
                SELECT
                    p.id,
                    p.serial_number,
                    p.brand,
                    p.model,
                    p.is_active,
                    p.branch_id,
                    b.name AS branch_name,
                    p.establishment_id,
                    e.name AS establishment_name
                FROM printers p
                LEFT JOIN branches b ON b.id = p.branch_id
                LEFT JOIN establishments e ON e.id = p.establishment_id
                WHERE p.company_id = :cid
                ORDER BY p.branch_id, p.establishment_id, p.serial_number, p.id
                """
            ),
            {"cid": COMPANY_ID},
        ).fetchall()

        if not all_printers:
            print("(nenhuma impressora encontrada)")
        else:
            for pr in all_printers:
                prstatus = "Ativa" if pr.is_active else "Inativa"
                brand = (pr.brand or "").strip()
                model = (pr.model or "").strip()
                details = " ".join(x for x in [brand, model] if x)
                details = f" — {details}" if details else ""
                branch_label = f"[{pr.branch_id}] {pr.branch_name}" if pr.branch_id else "(sem filial)"
                est_label = (
                    f"[{pr.establishment_id}] {pr.establishment_name}"
                    if pr.establishment_id
                    else "(sem ponto)"
                )
                print(f"- [{pr.id}] {pr.serial_number}{details} — {prstatus} | Filial: {branch_label} | Ponto: {est_label}")

        print("\n=" * 40)
        print("Fim.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
