from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.branch import Branch
from app.models.company import Company
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.user import User
from app.schemas.product_categories import ProductCategoryCreate, ProductCategoryOut, ProductCategoryUpdate

router = APIRouter()


DEFAULT_CATEGORIES: dict[str, list[str]] = {
    "retail": ["Geral", "Bebidas", "Alimentos", "Higiene", "Outros"],
    "restaurant": ["Entradas", "Pratos", "Bebidas", "Sobremesas", "Outros"],
    "bar": ["Cervejas", "Refrigerantes", "Águas", "Cocktails", "Outros"],
    "butcher": ["Bovina", "Suína", "Aves", "Miúdos", "Outros"],
    "services": ["Consultoria", "Manutenção", "Instalação", "Suporte", "Outros"],
    "electronics": [
        "Celulares e Smartphones",
        "Capas, Películas e Protetores",
        "Carregadores e Fontes",
        "Cabos e Adaptadores",
        "Peças e Reposição (LCD, Visores, Baterias)",
        "Computadores e Notebooks",
        "Periféricos (Mouse, Teclado, Headset)",
        "Redes e Internet (Roteadores, Switches)",
        "Áudio e Som (Fones, Caixas, Microfones)",
        "Câmeras e Segurança (CFTV, DVR, Alarmes)",
    ],
    "hardware": [
        "Ferramentas Manuais",
        "Ferramentas Elétricas",
        "Acessórios p/ Ferramentas (Brocas, Discos, Lixas)",
        "Parafusos, Porcas e Arruelas",
        "Pregos, Rebites e Fixadores",
        "Dobradiças, Corrediças e Ferragens p/ Móveis",
        "Fechaduras, Trancas e Cadeados",
        "Materiais Elétricos (Fios, Tomadas, Interruptores)",
        "Iluminação (Lâmpadas, Luminárias, Refletores)",
        "Hidráulica (Tubos, Conexões, Torneiras)",
        "Tintas, Vernizes e Solventes",
        "Acessórios de Pintura (Rolos, Pincéis, Fitas)",
        "Colas, Selantes e Silicone",
        "EPI e Segurança (Luvas, Óculos, Capacetes)",
        "Jardinagem (Mangueiras, Bicos, Ferramentas)",
        "Abrasivos e Corte",
        "Cordas, Correntes e Cabos de Aço",
        "Rodízios, Roldanas e Movimentação",
        "Solda e Acessórios (Eletrodos, Máscaras)",
        "Organização e Armazenamento (Caixas, Prateleiras)",
    ],
    "pharmacy": [
        "Medicamentos (Marca)",
        "Medicamentos (Genéricos)",
        "Analgésicos e Antitérmicos",
        "Antibióticos",
        "Anti-inflamatórios",
        "Anti-histamínicos / Alergias",
        "Gastrointestinais",
        "Vitaminas e Suplementos",
        "Dermocosméticos",
        "Higiene e Cuidado Pessoal",
        "Cuidados do Bebê",
        "Primeiros Socorros",
        "Dispositivos Médicos",
        "Testes e Diagnóstico",
        "Saúde Sexual e Planejamento Familiar",
        "Ortopedia e Mobilidade",
        "Outros",
    ],
    "reprography": ["Cópias", "Impressões", "Digitalização", "Encadernação", "Plastificação", "Design", "Papelaria", "Serviços"],
}


def _normalize_business_type(value: str | None) -> str:
    bt = (value or '').strip().lower()
    if not bt:
        return ''
    aliases = {
        'reprografia': 'reprography',
    }
    return aliases.get(bt, bt)


DEFAULT_CATEGORY_COLORS: dict[str, dict[str, str]] = {
    "reprography": {
        "cópias": "#3b82f6",
        "impressões": "#8b5cf6",
        "digitalização": "#06b6d4",
        "encadernação": "#f97316",
        "plastificação": "#22c55e",
        "design": "#ec4899",
        "papelaria": "#64748b",
        "serviços": "#eab308",
    }
}


def _ensure_default_categories(db: Session, company_id: int, business_type: str):
    defaults = DEFAULT_CATEGORIES.get(business_type) or DEFAULT_CATEGORIES["retail"]
    default_colors = DEFAULT_CATEGORY_COLORS.get(business_type) or {}
    existing = {
        (r.name or "").strip().lower()
        for r in db.scalars(
            select(ProductCategory)
            .where(ProductCategory.company_id == company_id)
            .where(ProductCategory.business_type == business_type)
        ).all()
    }
    created_any = False
    for name in defaults:
        key = name.strip().lower()
        if key in existing:
            continue
        db.add(
            ProductCategory(
                company_id=company_id,
                business_type=business_type,
                name=name,
                color=default_colors.get(key),
            )
        )
        created_any = True
    if created_any:
        db.commit()


@router.get("", response_model=list[ProductCategoryOut])
@router.get("/", response_model=list[ProductCategoryOut], include_in_schema=False)
def list_product_categories(
    business_type: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bt = _get_effective_business_type(db, current_user, business_type)

    _ensure_default_categories(db, current_user.company_id, bt)

    rows = db.scalars(
        select(ProductCategory)
        .where(ProductCategory.company_id == current_user.company_id)
        .where(ProductCategory.business_type == bt)
        .order_by(ProductCategory.name.asc())
    ).all()
    return rows


def _get_effective_business_type(db: Session, current_user: User, business_type: str | None) -> str:
    bt = _normalize_business_type(business_type)
    if bt:
        return bt
    branch = db.get(Branch, int(current_user.branch_id))
    if branch and branch.company_id == current_user.company_id:
        return _normalize_business_type(branch.business_type) or 'retail'
    company = db.get(Company, current_user.company_id)
    return _normalize_business_type((company.business_type if company else 'retail') or 'retail') or 'retail'


def _ensure_admin(current_user: User):
    role = (getattr(current_user, 'role', '') or '').strip().lower()
    if role not in {'admin', 'owner'}:
        raise HTTPException(status_code=403, detail='Sem permissão')


@router.post('', response_model=ProductCategoryOut)
def create_product_category(
    payload: ProductCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    name = (payload.name or '').strip()
    if not name:
        raise HTTPException(status_code=400, detail='Nome inválido')
    bt = _get_effective_business_type(db, current_user, payload.business_type)

    exists = db.scalar(
        select(ProductCategory)
        .where(ProductCategory.company_id == current_user.company_id)
        .where(ProductCategory.business_type == bt)
        .where(func.lower(ProductCategory.name) == name.lower())
    )
    if exists:
        return exists

    row = ProductCategory(
        company_id=current_user.company_id,
        business_type=bt,
        name=name,
        color=(payload.color or '').strip() or None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put('/{category_id}', response_model=ProductCategoryOut)
def update_product_category(
    category_id: int,
    payload: ProductCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    row = db.get(ProductCategory, int(category_id))
    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail='Categoria não encontrada')

    name = (payload.name or '').strip()
    if not name:
        raise HTTPException(status_code=400, detail='Nome inválido')

    dup = db.scalar(
        select(ProductCategory)
        .where(ProductCategory.company_id == current_user.company_id)
        .where(ProductCategory.business_type == row.business_type)
        .where(func.lower(ProductCategory.name) == name.lower())
        .where(ProductCategory.id != row.id)
    )
    if dup:
        raise HTTPException(status_code=400, detail='Já existe uma categoria com este nome')

    row.name = name
    row.color = (payload.color or '').strip() or None
    db.commit()
    db.refresh(row)
    return row


@router.delete('/{category_id}')
def delete_product_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    row = db.get(ProductCategory, int(category_id))
    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail='Categoria não encontrada')

    in_use = db.scalar(
        select(Product.id)
        .where(Product.company_id == current_user.company_id)
        .where(Product.category_id == row.id)
        .limit(1)
    )
    if in_use:
        raise HTTPException(status_code=409, detail='Categoria em uso em produtos')

    db.delete(row)
    db.commit()
    return {'ok': True}
