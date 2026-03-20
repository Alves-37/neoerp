from argparse import ArgumentParser

from sqlalchemy import select

from app.database.connection import SessionLocal
from app.models.branch import Branch
from app.models.company import Company
from app.models.product_category import ProductCategory


def _ensure_branch(db, *, company_id: int, name: str, business_type: str) -> Branch:
    existing = db.scalar(
        select(Branch)
        .where(Branch.company_id == company_id)
        .where(Branch.name == name)
    )
    if existing:
        changed = False
        if (existing.business_type or '').strip().lower() != (business_type or '').strip().lower():
            existing.business_type = business_type
            changed = True
        if not getattr(existing, 'is_active', True):
            existing.is_active = True
            changed = True
        if changed:
            db.add(existing)
            db.commit()
            db.refresh(existing)
        return existing

    row = Branch(company_id=company_id, name=name, business_type=business_type, is_active=True)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _ensure_categories(db, *, company_id: int, business_type: str, names: list[str]) -> None:
    existing = {
        (r.name or '').strip().lower()
        for r in db.scalars(
            select(ProductCategory)
            .where(ProductCategory.company_id == company_id)
            .where(ProductCategory.business_type == business_type)
        ).all()
    }

    created_any = False
    for name in names:
        nm = (name or '').strip()
        if not nm:
            continue
        key = nm.lower()
        if key in existing:
            continue
        db.add(ProductCategory(company_id=company_id, business_type=business_type, name=nm))
        created_any = True

    if created_any:
        db.commit()


def main():
    parser = ArgumentParser(description='Seed: cria filiais padrão (Eletrônica/Ferragem) e categorias iniciais')
    parser.add_argument('--company-id', type=int, default=None)
    args = parser.parse_args()

    electronics_categories = [
        'Celulares e Smartphones',
        'Capas, Películas e Protetores',
        'Carregadores e Fontes',
        'Cabos e Adaptadores',
        'Peças e Reposição (LCD, Visores, Baterias)',
        'Computadores e Notebooks',
        'Periféricos (Mouse, Teclado, Headset)',
        'Redes e Internet (Roteadores, Switches)',
        'Áudio e Som (Fones, Caixas, Microfones)',
        'Câmeras e Segurança (CFTV, DVR, Alarmes)',
    ]
    hardware_categories = [
        'Ferramentas Manuais',
        'Ferramentas Elétricas',
        'Acessórios p/ Ferramentas (Brocas, Discos, Lixas)',
        'Parafusos, Porcas e Arruelas',
        'Pregos, Rebites e Fixadores',
        'Dobradiças, Corrediças e Ferragens p/ Móveis',
        'Fechaduras, Trancas e Cadeados',
        'Materiais Elétricos (Fios, Tomadas, Interruptores)',
        'Iluminação (Lâmpadas, Luminárias, Refletores)',
        'Hidráulica (Tubos, Conexões, Torneiras)',
        'Tintas, Vernizes e Solventes',
        'Acessórios de Pintura (Rolos, Pincéis, Fitas)',
        'Colas, Selantes e Silicone',
        'EPI e Segurança (Luvas, Óculos, Capacetes)',
        'Jardinagem (Mangueiras, Bicos, Ferramentas)',
        'Abrasivos e Corte',
        'Cordas, Correntes e Cabos de Aço',
        'Rodízios, Roldanas e Movimentação',
        'Solda e Acessórios (Eletrodos, Máscaras)',
        'Organização e Armazenamento (Caixas, Prateleiras)',
    ]

    db = SessionLocal()
    try:
        stmt = select(Company)
        if args.company_id:
            stmt = stmt.where(Company.id == args.company_id)
        companies = db.scalars(stmt.order_by(Company.id.asc())).all()
        if not companies:
            print('Nenhuma empresa encontrada.')
            return

        for c in companies:
            b1 = _ensure_branch(db, company_id=c.id, name='Eletrônica', business_type='electronics')
            b2 = _ensure_branch(db, company_id=c.id, name='Ferragem', business_type='hardware')

            _ensure_categories(db, company_id=c.id, business_type='electronics', names=electronics_categories)
            _ensure_categories(db, company_id=c.id, business_type='hardware', names=hardware_categories)

            print(f'[{c.id}] OK: filiais={b1.id},{b2.id} categorias electronics={len(electronics_categories)} hardware={len(hardware_categories)}')

        print('Seed concluído.')
    finally:
        db.close()


if __name__ == '__main__':
    main()
