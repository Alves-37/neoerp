import os
import random
import shutil
from argparse import ArgumentParser
from pathlib import Path
from uuid import uuid4

from sqlalchemy import func, select

from app.database.connection import SessionLocal
from app.models.company import Company
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_image import ProductImage
from app.settings import Settings


BUSINESS_TYPES = ["retail", "restaurant", "bar", "butcher", "services"]

DEFAULT_CATEGORIES: dict[str, list[str]] = {
    "retail": ["Geral", "Bebidas", "Alimentos", "Higiene", "Outros"],
    "restaurant": ["Entradas", "Pratos", "Bebidas", "Sobremesas", "Outros"],
    "bar": ["Cervejas", "Refrigerantes", "Águas", "Cocktails", "Outros"],
    "butcher": ["Bovina", "Suína", "Aves", "Miúdos", "Outros"],
    "services": ["Consultoria", "Manutenção", "Instalação", "Suporte", "Outros"],
}


def _ensure_upload_dir(upload_dir: str) -> Path:
    p = Path(upload_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _pick_image_files(images_dir: str | None) -> list[Path]:
    if not images_dir:
        return []

    root = Path(images_dir)
    if not root.exists() or not root.is_dir():
        return []

    exts = {".png", ".jpg", ".jpeg", ".webp"}
    files: list[Path] = []
    for f in root.iterdir():
        if f.is_file() and f.suffix.lower() in exts:
            files.append(f)
    return sorted(files)


def _demo_name(bt: str) -> str:
    if bt == "restaurant":
        return "Demo Restaurante"
    if bt == "bar":
        return "Demo Bar"
    if bt == "butcher":
        return "Demo Talho"
    if bt == "services":
        return "Demo Serviços"
    return "Demo Loja"


def _ensure_default_categories(db, *, company_id: int, business_type: str) -> list[ProductCategory]:
    defaults = DEFAULT_CATEGORIES.get(business_type) or DEFAULT_CATEGORIES["retail"]

    existing = {
        (r.name or "").strip().lower(): r
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
        cat = ProductCategory(company_id=company_id, business_type=business_type, name=name)
        db.add(cat)
        created_any = True

    if created_any:
        db.commit()

    rows = db.scalars(
        select(ProductCategory)
        .where(ProductCategory.company_id == company_id)
        .where(ProductCategory.business_type == business_type)
        .order_by(ProductCategory.name.asc())
    ).all()
    return list(rows or [])


def _product_name(bt: str, idx: int) -> str:
    if bt == "restaurant":
        options = [
            "Pizza",
            "Hambúrguer",
            "Frango",
            "Bife",
            "Salada",
            "Massa",
            "Sopa",
            "Sumo",
            "Água",
            "Sobremesa",
        ]
        return f"{random.choice(options)} {idx + 1}"
    if bt == "bar":
        options = ["Cerveja", "Cocktail", "Vinho", "Whisky", "Gin", "Vodka", "Refrigerante"]
        return f"{random.choice(options)} {idx + 1}"
    if bt == "butcher":
        options = ["Picanha", "Costela", "Frango", "Coxa", "Alcatra", "Carne Moída"]
        return f"{random.choice(options)} {idx + 1}"
    if bt == "services":
        options = ["Consultoria", "Instalação", "Manutenção", "Limpeza", "Treinamento"]
        return f"{random.choice(options)} {idx + 1}"

    options = ["Produto", "Item", "Acessório", "Peça", "Kit"]
    return f"{random.choice(options)} {idx + 1}"


def _product_unit(bt: str) -> str:
    if bt in {"restaurant", "bar"}:
        return random.choice(["un", "porção", "copo", "garrafa", "lata"])
    if bt == "butcher":
        return random.choice(["kg", "g", "un"])
    if bt == "services":
        return random.choice(["serv", "h", "un"])
    return random.choice(["un", "cx", "pct"])


def _product_price(bt: str) -> float:
    if bt == "restaurant":
        return round(random.uniform(50, 450), 2)
    if bt == "bar":
        return round(random.uniform(30, 400), 2)
    if bt == "butcher":
        return round(random.uniform(80, 900), 2)
    if bt == "services":
        return round(random.uniform(200, 5000), 2)
    return round(random.uniform(50, 2500), 2)


def _product_cost(price: float) -> float:
    ratio = random.uniform(0.45, 0.85)
    return round(price * ratio, 2)


def _seed_company_products(
    *,
    db,
    company: Company,
    per_company: int,
    force: bool,
    restaurant_images: list[Path],
    upload_dir: Path,
    images_per_product: int,
):
    bt = company.business_type or "retail"

    categories = _ensure_default_categories(db, company_id=company.id, business_type=bt)
    category_ids = [c.id for c in categories]

    existing_count = db.scalar(
        select(func.count(Product.id)).where(Product.company_id == company.id).where(Product.business_type == bt)
    )
    existing_count = int(existing_count or 0)

    if existing_count >= per_company and not force:
        print(f"[{company.id}] {company.name} ({bt}): já tem {existing_count} produtos, ignorando.")
        return

    to_create = per_company if force else max(0, per_company - existing_count)
    if to_create <= 0:
        print(f"[{company.id}] {company.name} ({bt}): nada a criar.")
        return

    print(f"[{company.id}] {company.name} ({bt}): criando {to_create} produtos...")

    start_idx = existing_count if not force else 0

    for i in range(to_create):
        idx = start_idx + i
        name = _product_name(bt, idx)
        price = _product_price(bt)
        cost = _product_cost(price)

        category_id = random.choice(category_ids) if category_ids else None

        product = Product(
            company_id=company.id,
            category_id=category_id,
            business_type=bt,
            name=name,
            sku=f"{bt[:3].upper()}-{company.id}-{idx + 1}",
            barcode=None,
            unit=_product_unit(bt),
            price=price,
            cost=cost,
            tax_rate=0,
            track_stock=(bt not in {"services"}),
            is_active=True,
            attributes={},
        )
        db.add(product)
        db.flush()

        if bt == "restaurant" and restaurant_images:
            n = max(1, images_per_product)
            chosen = [restaurant_images[(idx + j) % len(restaurant_images)] for j in range(n)]
            for img_src in chosen:
                ext = img_src.suffix.lower()
                filename = f"{uuid4().hex}{ext}"
                dest = upload_dir / filename
                shutil.copyfile(img_src, dest)

                db.add(
                    ProductImage(
                        company_id=company.id,
                        product_id=product.id,
                        file_path=filename,
                    )
                )

    db.commit()


def main():
    parser = ArgumentParser(description="Seed de produtos para todos os tipos de negócios")
    parser.add_argument("--per-company", type=int, default=50)
    parser.add_argument("--company-id", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--create-demo-companies", action="store_true")
    parser.add_argument("--no-create-missing-companies", action="store_true")
    parser.add_argument("--restaurant-images-dir", type=str, default=None)
    parser.add_argument("--images-per-product", type=int, default=1)
    args = parser.parse_args()

    settings = Settings()
    upload_dir = _ensure_upload_dir(settings.upload_dir)
    restaurant_images = _pick_image_files(args.restaurant_images_dir)

    if args.restaurant_images_dir and not restaurant_images:
        print(
            "Aviso: nenhuma imagem encontrada em --restaurant-images-dir. Restaurante será seeded sem fotos."
        )

    db = SessionLocal()
    try:
        # Importante: uma empresa só tem 1 business_type.
        # Para ter seed em "todos os tipos", garantimos que existam empresas para cada tipo.
        create_missing = args.create_demo_companies or (not args.no_create_missing_companies)
        if create_missing and not args.company_id:
            for bt in BUSINESS_TYPES:
                name = _demo_name(bt)
                company = db.scalar(select(Company).where(Company.name == name))
                if not company:
                    company = Company(name=name, business_type=bt, owner_id=None)
                    db.add(company)
                    db.commit()
                    db.refresh(company)

        stmt = select(Company)
        if args.company_id:
            stmt = stmt.where(Company.id == args.company_id)
        companies = db.scalars(stmt.order_by(Company.id)).all()

        if not companies:
            print("Nenhuma empresa encontrada para seed.")
            return

        for c in companies:
            _seed_company_products(
                db=db,
                company=c,
                per_company=args.per_company,
                force=args.force,
                restaurant_images=restaurant_images,
                upload_dir=upload_dir,
                images_per_product=args.images_per_product,
            )

        print("Seed concluído.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
