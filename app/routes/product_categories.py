from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.company import Company
from app.models.product_category import ProductCategory
from app.models.user import User
from app.schemas.product_categories import ProductCategoryOut

router = APIRouter()


DEFAULT_CATEGORIES: dict[str, list[str]] = {
    "retail": ["Geral", "Bebidas", "Alimentos", "Higiene", "Outros"],
    "restaurant": ["Entradas", "Pratos", "Bebidas", "Sobremesas", "Outros"],
    "bar": ["Cervejas", "Refrigerantes", "Águas", "Cocktails", "Outros"],
    "butcher": ["Bovina", "Suína", "Aves", "Miúdos", "Outros"],
    "services": ["Consultoria", "Manutenção", "Instalação", "Suporte", "Outros"],
}


def _ensure_default_categories(db: Session, company_id: int, business_type: str):
    defaults = DEFAULT_CATEGORIES.get(business_type) or DEFAULT_CATEGORIES["retail"]
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
        if name.strip().lower() in existing:
            continue
        db.add(ProductCategory(company_id=company_id, business_type=business_type, name=name))
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
    company = db.get(Company, current_user.company_id)
    bt = business_type or (company.business_type if company else "retail")

    _ensure_default_categories(db, current_user.company_id, bt)

    rows = db.scalars(
        select(ProductCategory)
        .where(ProductCategory.company_id == current_user.company_id)
        .where(ProductCategory.business_type == bt)
        .order_by(ProductCategory.name.asc())
    ).all()
    return rows
