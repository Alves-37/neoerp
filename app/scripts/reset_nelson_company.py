#!/usr/bin/env python3
"""
Script para resetar a empresa Nelson Multservice (ID: 9).
Mantém o usuário Admin (Nelson Alfredo, owner) e apaga todos os outros dados.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database.connection import SessionLocal

COMPANY_ID = 9
ADMIN_USER_ID = 12  # Nelson Alfredo - owner


def table_exists(db, table_name):
    """Verifica se uma tabela existe no banco de dados."""
    result = db.execute(
        text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = :table
            )
        """),
        {"table": table_name}
    ).scalar()
    return result


def safe_delete(db, description, sql, params):
    """Executa DELETE com tratamento de erro usando savepoint."""
    # Criar savepoint para isolar erros
    db.execute(text("SAVEPOINT sp_delete"))
    try:
        result = db.execute(text(sql), params)
        db.execute(text("RELEASE SAVEPOINT sp_delete"))
        print(f"   {result.rowcount} registros apagados")
        return result.rowcount
    except Exception as e:
        # Rollback para o savepoint em caso de erro
        db.execute(text("ROLLBACK TO SAVEPOINT sp_delete"))
        error_msg = str(e).lower()
        if "does not exist" in error_msg or "undefinedtable" in error_msg or "undefined table" in error_msg:
            print(f"   Tabela não existe, pulando...")
            return 0
        raise


def reset_company():
    db = SessionLocal()
    try:
        print("=" * 70)
        print("RESET DA EMPRESA NELSON MULTSERVICE")
        print("=" * 70)
        print(f"Company ID: {COMPANY_ID}")
        print(f"Admin a manter: User {ADMIN_USER_ID} (Nelson Alfredo)")
        print("=" * 70)
        
        # Verificar se a empresa existe
        company = db.execute(
            text("SELECT id, name FROM companies WHERE id = :cid"),
            {"cid": COMPANY_ID}
        ).fetchone()
        
        if not company:
            print(f"✗ Empresa {COMPANY_ID} não encontrada!")
            return False
        
        print(f"\n✓ Empresa encontrada: {company.name}")
        
        # Verificar usuários da empresa
        users = db.execute(
            text("SELECT id, name, email, role FROM users WHERE company_id = :cid"),
            {"cid": COMPANY_ID}
        ).fetchall()
        
        print(f"\nUsuários da empresa:")
        for u in users:
            marker = " ← ADMIN A MANTER" if u.id == ADMIN_USER_ID else ""
            print(f"  User {u.id}: {u.name} ({u.role}){marker}")
        
        # Iniciar transação
        print("\n" + "=" * 70)
        print("INICIANDO RESET...")
        print("=" * 70)
        
        # 1. Apagar itens de dívidas
        print("\n1. Apagando debt_items...")
        safe_delete(db, "debt_items", """
            DELETE FROM debt_items 
            WHERE debt_id IN (SELECT id FROM debts WHERE company_id = :cid)
        """, {"cid": COMPANY_ID})
        
        # 2. Apagar dívidas
        print("\n2. Apagando debts...")
        safe_delete(db, "debts", "DELETE FROM debts WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # 3. Apagar pagamentos
        print("\n3. Apagando payments...")
        safe_delete(db, "payments", "DELETE FROM payments WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # 4. Apagar linhas de documentos fiscais
        print("\n4. Apagando fiscal_document_lines...")
        safe_delete(db, "fiscal_document_lines", """
            DELETE FROM fiscal_document_lines 
            WHERE fiscal_document_id IN (
                SELECT id FROM fiscal_documents WHERE company_id = :cid
            )
        """, {"cid": COMPANY_ID})
        
        # 5. Apagar documentos fiscais
        print("\n5. Apagando fiscal_documents...")
        safe_delete(db, "fiscal_documents", "DELETE FROM fiscal_documents WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # 6. Apagar itens de vendas
        print("\n6. Apagando sale_items...")
        safe_delete(db, "sale_items", """
            DELETE FROM sale_items 
            WHERE sale_id IN (SELECT id FROM sales WHERE company_id = :cid)
        """, {"cid": COMPANY_ID})
        
        # 7. Apagar vendas
        print("\n7. Apagando sales...")
        safe_delete(db, "sales", "DELETE FROM sales WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # 8. Apagar despesas
        print("\n8. Apagando expenses...")
        safe_delete(db, "expenses", "DELETE FROM expenses WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # 9. Apagar sessões de caixa
        print("\n9. Apagando cash_sessions...")
        safe_delete(db, "cash_sessions", "DELETE FROM cash_sessions WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # 10. Apagar transferências de stock
        print("\n10. Apagando stock_transfers...")
        safe_delete(db, "stock_transfers", "DELETE FROM stock_transfers WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # 11. Apagar ajustes de stock
        print("\n11. Apagando stock_adjustments...")
        safe_delete(db, "stock_adjustments", "DELETE FROM stock_adjustments WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # 12. Apagar movimentações de stock
        print("\n12. Apagando stock_movements...")
        safe_delete(db, "stock_movements", "DELETE FROM stock_movements WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # 13. Apagar estoque
        print("\n13. Apagando stock...")
        safe_delete(db, "stock", "DELETE FROM stock WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # 14. Apagar estoque de produtos
        print("\n14. Apagando product_stocks...")
        safe_delete(db, "product_stocks", "DELETE FROM product_stocks WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # 15. Apagar itens de orçamentos
        print("\n15. Apagando quote_items...")
        safe_delete(db, "quote_items", """
            DELETE FROM quote_items 
            WHERE quote_id IN (SELECT id FROM quotes WHERE company_id = :cid)
        """, {"cid": COMPANY_ID})
        
        # 16. Apagar orçamentos
        print("\n16. Apagando quotes...")
        safe_delete(db, "quotes", "DELETE FROM quotes WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # 17. Apagar produtos
        print("\n17. Apagando products...")
        safe_delete(db, "products", "DELETE FROM products WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # 18. Apagar categorias
        print("\n18. Apagando categories...")
        safe_delete(db, "categories", "DELETE FROM categories WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # 19. Apagar fornecedores
        print("\n19. Apagando suppliers...")
        safe_delete(db, "suppliers", "DELETE FROM suppliers WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # 20. Apagar clientes
        print("\n20. Apagando customers...")
        safe_delete(db, "customers", "DELETE FROM customers WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # 21. Apagar usuários (exceto Admin)
        print("\n21. Apagando usuários (exceto Admin)...")
        result = db.execute(
            text("DELETE FROM users WHERE company_id = :cid AND id != :admin_id"),
            {"cid": COMPANY_ID, "admin_id": ADMIN_USER_ID}
        )
        print(f"   {result.rowcount} registros apagados")
        
        # Limpar establishment_id do Admin para poder apagar establishments
        print("\n22. Limpando establishment_id do Admin...")
        db.execute(
            text("UPDATE users SET establishment_id = NULL WHERE id = :admin_id"),
            {"admin_id": ADMIN_USER_ID}
        )
        print("   establishment_id limpo")
        
        # 23. Apagar leituras de impressoras
        print("\n23. Apagando printer_readings...")
        safe_delete(db, "printer_readings", """
            DELETE FROM printer_readings 
            WHERE printer_id IN (SELECT id FROM printers WHERE company_id = :cid)
        """, {"cid": COMPANY_ID})
        
        # 24. Apagar registro de faturação de impressoras
        print("\n24. Apagando printer_billing_registry...")
        safe_delete(db, "printer_billing_registry", """
            DELETE FROM printer_billing_registry 
            WHERE printer_id IN (SELECT id FROM printers WHERE company_id = :cid)
        """, {"cid": COMPANY_ID})
        
        # 25. Apagar impressoras (referenciam establishments)
        print("\n25. Apagando printers...")
        safe_delete(db, "printers", "DELETE FROM printers WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # 26. Apagar tipos de contadores de impressoras
        print("\n26. Apagando printer_counter_types...")
        safe_delete(db, "printer_counter_types", """
            DELETE FROM printer_counter_types 
            WHERE establishment_id IN (
                SELECT id FROM establishments 
                WHERE branch_id IN (SELECT id FROM branches WHERE company_id = :cid)
            )
        """, {"cid": COMPANY_ID})
        
        # 27. Apagar pontos de venda
        print("\n27. Apagando establishments...")
        safe_delete(db, "establishments", """
            DELETE FROM establishments 
            WHERE branch_id IN (SELECT id FROM branches WHERE company_id = :cid)
        """, {"cid": COMPANY_ID})
        
        # 28. Apagar categorias de despesas
        print("\n28. Apagando expense_categories...")
        safe_delete(db, "expense_categories", "DELETE FROM expense_categories WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # 29. Apagar filiais
        print("\n29. Apagando branches...")
        safe_delete(db, "branches", "DELETE FROM branches WHERE company_id = :cid", {"cid": COMPANY_ID})

        # Recriar 1 filial e 1 ponto padrão (para a empresa ficar utilizável após o reset)
        print("\n29.1. Recriando filial e ponto padrão...")
        company_bt = db.execute(
            text("SELECT business_type FROM companies WHERE id = :cid"),
            {"cid": COMPANY_ID},
        ).scalar()
        company_bt = (company_bt or "services").strip().lower()

        new_branch_id = db.execute(
            text(
                """
                INSERT INTO branches (company_id, name, business_type, is_active, public_menu_enabled)
                VALUES (:cid, :name, :bt, true, false)
                RETURNING id
                """
            ),
            {"cid": COMPANY_ID, "name": "Filial Principal", "bt": company_bt},
        ).scalar()

        new_establishment_id = db.execute(
            text(
                """
                INSERT INTO establishments (company_id, branch_id, name, is_active)
                VALUES (:cid, :bid, :name, true)
                RETURNING id
                """
            ),
            {"cid": COMPANY_ID, "bid": new_branch_id, "name": "Ponto Principal"},
        ).scalar()

        db.execute(
            text("UPDATE users SET establishment_id = :eid WHERE id = :admin_id"),
            {"eid": new_establishment_id, "admin_id": ADMIN_USER_ID},
        )

        db.execute(
            text("UPDATE users SET branch_id = :bid WHERE id = :admin_id"),
            {"bid": new_branch_id, "admin_id": ADMIN_USER_ID},
        )
        print(f"   Filial criada: {new_branch_id} | Ponto criado: {new_establishment_id}")
        
        # 30. Apagar configurações
        print("\n30. Apagando settings...")
        safe_delete(db, "settings", "DELETE FROM settings WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # 31. Apagar job de reset (se existir)
        print("\n31. Apagando company_reset_jobs...")
        safe_delete(db, "company_reset_jobs", "DELETE FROM company_reset_jobs WHERE company_id = :cid", {"cid": COMPANY_ID})
        
        # Verificar se Admin ainda existe
        admin = db.execute(
            text("SELECT id, name, email, role FROM users WHERE id = :uid"),
            {"uid": ADMIN_USER_ID}
        ).fetchone()
        
        print("\n" + "=" * 70)
        print("VERIFICAÇÃO FINAL")
        print("=" * 70)
        
        if admin:
            print(f"✓ Admin mantido: {admin.name} ({admin.email}) - {admin.role}")
        else:
            print("✗ ERRO: Admin não foi mantido!")
            db.rollback()
            return False
        
        # Commit
        db.commit()
        
        print("\n" + "=" * 70)
        print("✓ RESET CONCLUÍDO COM SUCESSO!")
        print("=" * 70)
        print(f"\nEmpresa {company.name} (ID: {COMPANY_ID}) foi resetada.")
        print(f"Apenas o Admin ({admin.name}) foi mantido.")
        print("\nA empresa está pronta para reconfiguração.")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    reset_company()
