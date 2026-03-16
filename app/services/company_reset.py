from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import text

from app.database.connection import SessionLocal
from app.settings import Settings


def _now_utc() -> datetime:
    return datetime.utcnow()


def _set_job(db, job_id: int, status: str, progress: int, message: str | None = None, error: str | None = None):
    db.execute(
        text(
            """
            UPDATE company_reset_jobs
            SET status = :status,
                progress = :progress,
                message = :message,
                error = :error,
                updated_at = now()
            WHERE id = :id
            """
        ),
        {
            "id": int(job_id),
            "status": status,
            "progress": int(progress),
            "message": message,
            "error": error,
        },
    )
    db.commit()


def _collect_upload_paths(db, company_id: int) -> list[str]:
    rows = db.execute(
        text(
            """
            SELECT file_path FROM product_images
            WHERE company_id = :cid
            """
        ),
        {"cid": int(company_id)},
    ).all()
    out: list[str] = []
    for r in rows:
        fp = (r[0] if isinstance(r, (tuple, list)) else getattr(r, "file_path", None)) or ""
        fp = str(fp).strip()
        if fp:
            out.append(fp)
    logo = db.execute(
        text(
            """
            SELECT logo_url FROM companies
            WHERE id = :cid
            """
        ),
        {"cid": int(company_id)},
    ).scalar()
    if logo and str(logo).startswith("/uploads/"):
        out.append(str(logo).replace("/uploads/", "", 1))
    return out


def _safe_unlink_uploads(upload_dir: str, file_paths: list[str]):
    if not upload_dir:
        return
    for fp in file_paths:
        try:
            rel = str(fp).lstrip("/\\")
            disk = os.path.join(upload_dir, rel)
            if os.path.exists(disk) and os.path.isfile(disk):
                os.remove(disk)
        except Exception:
            continue


def run_company_reset(job_id: int, company_id: int):
    settings = Settings()
    db = SessionLocal()
    try:
        _set_job(db, job_id, "running", 1, "Preparando reset")

        keep_user_ids = db.execute(
            text(
                """
                SELECT id FROM users
                WHERE company_id = :cid
                  AND lower(coalesce(role, '')) IN ('admin', 'owner')
                """
            ),
            {"cid": int(company_id)},
        ).scalars().all()
        keep_user_ids = [int(x) for x in (keep_user_ids or []) if x is not None]
        if not keep_user_ids:
            raise RuntimeError("Nenhum admin/owner encontrado para manter")

        upload_paths = _collect_upload_paths(db, company_id)

        steps: list[tuple[str, str]] = [
            ("Limpando itens dependentes", "debt_items"),
            ("Limpando dívidas", "debts"),
            ("Limpando itens de venda", "sale_items"),
            ("Limpando vendas", "sales"),
            ("Limpando linhas fiscais", "fiscal_document_lines"),
            ("Limpando documentos fiscais", "fiscal_documents"),
            ("Limpando itens de orçamento", "quote_items"),
            ("Limpando orçamentos", "quotes"),
            ("Limpando itens de pedido", "order_items"),
            ("Limpando pedidos", "orders"),
            ("Limpando mesas", "restaurant_tables"),
            ("Limpando imagens de produto", "product_images"),
            ("Limpando stocks", "product_stocks"),
            ("Limpando movimentos de stock", "stock_movements"),
            ("Limpando transferências de stock", "stock_transfers"),
            ("Limpando locais de stock", "stock_locations"),
            ("Limpando produtos", "products"),
            ("Limpando categorias", "product_categories"),
            ("Limpando clientes", "customers"),
            ("Limpando compras de fornecedor", "supplier_purchases"),
            ("Limpando pagamentos de fornecedor", "supplier_payments"),
            ("Limpando fornecedores", "suppliers"),
            ("Limpando papéis", "user_roles"),
        ]

        total = len(steps) + 4
        done = 0

        def bump(msg: str):
            nonlocal done
            done += 1
            progress = int(round((done / total) * 90))
            progress = max(1, min(90, progress))
            _set_job(db, job_id, "running", progress, msg)

        # Delete dependent tables first (skip if table doesn't exist)
        for msg, table in steps:
            bump(msg)
            try:
                db.execute(text(f"DELETE FROM {table} WHERE company_id = :cid"), {"cid": int(company_id)})
                db.commit()
            except Exception as e:
                # Ignore errors for tables that don't exist
                if "does not exist" in str(e):
                    continue
                else:
                    raise

        bump("Apagando usuários não-admin")
        db.execute(
            text(
                """
                DELETE FROM users
                WHERE company_id = :cid
                  AND NOT (id = ANY(:keep_ids))
                """
            ),
            {"cid": int(company_id), "keep_ids": keep_user_ids},
        )
        db.commit()

        bump("Apagando filiais")
        db.execute(text("DELETE FROM branches WHERE company_id = :cid"), {"cid": int(company_id)})
        db.commit()

        bump("Recriando filial padrão")
        bt = db.execute(text("SELECT business_type FROM companies WHERE id = :cid"), {"cid": int(company_id)}).scalar()
        bt = (bt or "retail").strip() or "retail"
        new_branch_id = db.execute(
            text(
                """
                INSERT INTO branches (company_id, name, business_type, is_active, public_menu_enabled)
                VALUES (:cid, 'Filial Principal', :bt, TRUE, FALSE)
                RETURNING id
                """
            ),
            {"cid": int(company_id), "bt": bt},
        ).scalar()
        if not new_branch_id:
            raise RuntimeError("Falha ao recriar filial")

        bump("Ajustando filial dos admins")
        db.execute(
            text(
                """
                UPDATE users
                SET branch_id = :bid
                WHERE company_id = :cid
                  AND id = ANY(:keep_ids)
                """
            ),
            {"cid": int(company_id), "bid": int(new_branch_id), "keep_ids": keep_user_ids},
        )
        db.commit()

        bump("Removendo uploads")
        _safe_unlink_uploads(settings.upload_dir, upload_paths)

        _set_job(db, job_id, "done", 100, "Concluído")
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        _set_job(db, job_id, "error", 100, "Erro", error=str(e))
    finally:
        try:
            db.close()
        except Exception:
            pass
