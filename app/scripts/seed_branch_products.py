import random
import shutil
from argparse import ArgumentParser
from pathlib import Path
from uuid import uuid4
import time
import requests

from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError

from app.database.connection import SessionLocal
from app.models.branch import Branch
from app.models.company import Company
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_image import ProductImage
from app.models.product_stock import ProductStock
from app.models.supplier import Supplier
from app.models.stock_location import StockLocation
from app.settings import Settings

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


def _download_food_images(target_dir: Path, count: int = 50) -> list[Path]:
    """
    Download food images from Unsplash API (client_id is public for demo).
    Falls back to a curated list of URLs if API fails.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = []

    # Public Unsplash access key for demo purposes only.
    # In production, you should use your own key or host images locally.
    unsplash_access_key = "YOUR_UNSPLASH_ACCESS_KEY"  # Replace if you have one

    # Fallback curated URLs (CC0/public domain food photos)
    fallback_urls = [
        "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1473093295043-c5128e3e85a7?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1473093295043-c5128e3e85a7?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1473093295043-c5128e3e85a7?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1473093295043-c5128e3e85a7?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1473093295043-c5128e3e85a7?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800&q=80&format=jpg",
        "https://images.unsplash.com/photo-1473093295043-c5128e3e85a7?w=800&q=80&format=jpg",
    ]

    urls_to_use = fallback_urls[:count]

    for i, url in enumerate(urls_to_use):
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            ext = ".jpg"
            filename = f"food_{i+1:03d}{ext}"
            dest = target_dir / filename
            with open(dest, "wb") as f:
                f.write(resp.content)
            downloaded.append(dest)
            time.sleep(0.2)  # Be gentle to the host
        except Exception as e:
            print(f"Erro ao baixar imagem {url}: {e}")
            continue

    print(f"Downloaded {len(downloaded)} food images to {target_dir}")
    return downloaded


def _pick_image_files(images_dir: str | None, target_download_dir: Path | None = None, required: int = 50) -> list[Path]:
    if not images_dir:
        return []

    root = Path(images_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    files: list[Path] = []
    for f in root.rglob("*"):
        if not (f.is_file() and f.suffix.lower() in exts):
            continue
        # Ignorar imagens baixadas automaticamente em tentativas antigas (não têm nomes reais)
        if f.stem.lower().startswith("food_"):
            continue
        files.append(f)

    # If we still have fewer images than required, do NOT download; just use what we have
    if len(files) < required and target_download_dir:
        print(f"Imagens locais insuficientes ({len(files)} < {required}). Usando apenas as imagens disponíveis.")
        # Do NOT download; just proceed with available images

    return sorted(files)


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


def _ensure_default_locations(db, *, company_id: int, branch_id: int) -> None:
    existing = db.scalars(
        select(StockLocation)
        .where(StockLocation.company_id == company_id)
        .where(StockLocation.branch_id == branch_id)
    ).all()
    if existing:
        return

    loja = StockLocation(
        company_id=company_id,
        branch_id=branch_id,
        type="store",
        name="Loja Principal",
        is_default=True,
        is_active=True,
    )
    armazem = StockLocation(
        company_id=company_id,
        branch_id=branch_id,
        type="warehouse",
        name="Armazém",
        is_default=False,
        is_active=True,
    )
    db.add(loja)
    db.add(armazem)
    db.commit()


def _get_default_store_location_id(db, *, company_id: int, branch_id: int) -> int:
    _ensure_default_locations(db, company_id=company_id, branch_id=branch_id)

    loc_id = db.scalar(
        select(StockLocation.id)
        .where(StockLocation.company_id == company_id)
        .where(StockLocation.branch_id == branch_id)
        .where(StockLocation.type == "store")
        .where(StockLocation.is_default.is_(True))
        .where(StockLocation.is_active.is_(True))
        .limit(1)
    )
    if not loc_id:
        raise RuntimeError(f"Sem local padrão (store) para company_id={company_id} branch_id={branch_id}")
    return int(loc_id)


def _product_name_from_image(image_path: Path) -> str:
    """
    Gera nome de produto a partir do nome do arquivo de imagem.
    Remove extensão e coloca em "Title Case" (apenas normaliza separadores).
    """
    name = image_path.stem.replace("-", " ").replace("_", " ").strip()
    clean = " ".join(name.split())
    # Title Case por palavra (preserva acentos)
    return " ".join((w[:1].upper() + w[1:].lower()) if w else "" for w in clean.split(" "))


def _product_description_from_name(name: str) -> str:
    """
    Gera uma descrição simples para o produto baseada no nome.
    """
    key = (name or "").strip().lower()
    desc_map = {
        "arroz": "Arroz branco solto, acompanhamento perfeito para pratos principais.",
        "cachorro": "Cachorro-quente tradicional com molho e mostarda.",
        "café": "Café fresco e aromático, escolha entre expresso ou americano.",
        "chá": "Chá quente selections de ervas, ideal para relaxar.",
        "combo": "Combo especial com acompanhamentos e bebida.",
        "combos": "Combos variados com pratos principais e bebidas.",
        "hamburguer": "Hambúrguer suculento com queijo, alface e tomate.",
        "pizza": "Pizza tradicional com molho, queijo e ingredientes frescos.",
        "refresco": "Refresco gelado de varios sabores, perfeito para hidratar.",
        "salda": "Salada fresca com vegetais crocantes e molho leve.",
        "sandes": "Sandes fofa com recheio generoso e acompanhamentos.",
        "xima": "Xima tradicional, acompanhamento tipico moçambicano.",
    }
    return desc_map.get(key, f"{name} fresco e delicioso, preparado com ingredientes de alta qualidade.")


def _product_name(bt: str, idx: int) -> str:
    if bt == "restaurant":
        options = ["Pizza", "Hambúrguer", "Frango", "Bife", "Salada", "Massa", "Sopa", "Sumo", "Água", "Sobremesa"]
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


def _product_min_stock(bt: str) -> float:
    if bt == "restaurant":
        return round(random.uniform(5, 20), 0)
    if bt == "bar":
        return round(random.uniform(10, 30), 0)
    if bt == "butcher":
        return round(random.uniform(15, 40), 0)
    if bt == "services":
        return 0
    return round(random.uniform(8, 25), 0)


def _product_initial_stock(bt: str, min_stock: float) -> float:
    if bt == "services":
        return 0
    # Ensure initial stock >= min_stock + some buffer
    buffer_factor = random.uniform(1.5, 3.0)
    qty = round(min_stock * buffer_factor, 0)
    return max(qty, min_stock + 5)


def _product_cost(price: float) -> float:
    ratio = random.uniform(0.45, 0.85)
    return round(price * ratio, 2)


def _seed_branch_products(
    *,
    db,
    company: Company,
    branch: Branch,
    per_branch: int,
    force: bool,
    restaurant_images: list[Path],
    upload_dir: Path,
    per_branch_target: int,
) -> None:
    bt = (branch.business_type or company.business_type or "retail").strip().lower()

    categories = _ensure_default_categories(db, company_id=company.id, business_type=bt)
    category_ids = [c.id for c in categories]

    default_location_id = _get_default_store_location_id(db, company_id=company.id, branch_id=branch.id)

    existing_count = db.scalar(
        select(func.count(Product.id))
        .where(Product.company_id == company.id)
        .where(Product.branch_id == branch.id)
    )
    existing_count = int(existing_count or 0)

    if existing_count >= per_branch and not force:
        print(f"[{company.id}:{branch.id}] {company.name} / {branch.name} ({bt}): já tem {existing_count} produtos, ignorando.")
        return

    to_create = per_branch if force else max(0, per_branch - existing_count)
    if to_create <= 0:
        print(f"[{company.id}:{branch.id}] {company.name} / {branch.name} ({bt}): nada a criar.")
        return

    if bt == "restaurant":
        if not restaurant_images:
            raise RuntimeError(
                "Restaurante exige fotos. Passe --restaurant-images-dir com pelo menos 50 imagens por filial."
            )
        # Limit number of products to available images for restaurants
    if branch.business_type == "restaurant" and restaurant_images:
        to_create = min(to_create, len(restaurant_images))
        if to_create < per_branch_target:
            print(f"Limitando criação de produtos para restaurante a {to_create} (imagens disponíveis).")

    print(f"[{company.id}:{branch.id}] {company.name} / {branch.name} ({bt}): criando {to_create} produtos...")

    start_idx = existing_count if not force else 0
    created_product_ids: list[int] = []
    copied_files: list[Path] = []

    try:
        for i in range(to_create):
            idx = start_idx + i
            attempts = 0
            while True:
                attempts += 1
                product_copied_files: list[Path] = []
                try:
                    # Para restaurante, usar nome da imagem; para outros, usar nome gerado
                    if bt == "restaurant" and restaurant_images:
                        img_path = restaurant_images[i]
                        name = _product_name_from_image(img_path)
                        description = _product_description_from_name(name)
                    else:
                        name = _product_name(bt, idx)
                        description = None

                    price = _product_price(bt)
                    cost = _product_cost(price)
                    min_stock = _product_min_stock(bt)
                    initial_stock = _product_initial_stock(bt, min_stock)

                    category_id = random.choice(category_ids) if category_ids else None

                    product = Product(
                        company_id=company.id,
                        branch_id=branch.id,
                        default_location_id=default_location_id,
                        category_id=category_id,
                        business_type=bt,
                        name=name,
                        sku=f"{bt[:3].upper()}-{company.id}-{branch.id}-{idx + 1}",
                        barcode=None,
                        unit=_product_unit(bt),
                        price=price,
                        cost=cost,
                        tax_rate=0,
                        min_stock=min_stock,
                        track_stock=(bt not in {"services"}),
                        is_active=True,
                        attributes={"description": description} if description else {},
                    )
                    db.add(product)
                    db.flush()
                    created_product_ids.append(int(product.id))

                    # Create stock record for the default location
                    if product.track_stock and initial_stock > 0:
                        stock = ProductStock(
                            company_id=company.id,
                            branch_id=branch.id,
                            product_id=product.id,
                            location_id=default_location_id,
                            qty_on_hand=initial_stock,
                        )
                        db.add(stock)

                    if bt == "restaurant":
                        img_src = restaurant_images[i]
                        ext = img_src.suffix.lower()
                        filename = f"{uuid4().hex}{ext}"
                        dest = upload_dir / filename
                        shutil.copyfile(img_src, dest)
                        copied_files.append(dest)
                        product_copied_files.append(dest)

                        db.add(
                            ProductImage(
                                company_id=company.id,
                                product_id=product.id,
                                file_path=filename,
                            )
                        )

                    db.commit()
                    break
                except OperationalError as e:
                    db.rollback()
                    # Limpar ficheiros copiados desta iteração
                    for f in product_copied_files:
                        try:
                            if f.exists():
                                f.unlink()
                        except Exception:
                            pass
                    if attempts >= 5:
                        raise
                    print(f"Aviso: falha de conex\u00e3o com BD durante seed (tentativa {attempts}/5). Repetindo em 2s... ({e})")
                    time.sleep(2)
                except Exception:
                    db.rollback()
                    for f in product_copied_files:
                        try:
                            if f.exists():
                                f.unlink()
                        except Exception:
                            pass
                    raise

        if bt == "restaurant" and created_product_ids:
            img_count = db.scalar(
                select(func.count(ProductImage.id))
                .where(ProductImage.company_id == company.id)
                .where(ProductImage.product_id.in_(created_product_ids))
            )
            img_count = int(img_count or 0)
            if img_count != len(created_product_ids):
                raise RuntimeError(
                    f"Falha ao garantir imagens do restaurante: produtos={len(created_product_ids)} imagens={img_count}"
                )

    except Exception:
        db.rollback()
        for f in copied_files:
            try:
                if f.exists():
                    f.unlink()
            except Exception:
                pass
        raise


def main():
    parser = ArgumentParser(description="Seed: cria 50 produtos por filial (branch) para empresas existentes")
    parser.add_argument("--per-branch", type=int, default=50)
    parser.add_argument("--company-id", type=int, default=None)
    parser.add_argument("--branch-id", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--restaurant-images-dir",
        type=str,
        default=None,
        help="Diretório com imagens (png/jpg/jpeg/webp) para usar nos produtos do restaurante. Se houver menos imagens que produtos, serão criados apenas produtos com imagens disponíveis.",
    )
    args = parser.parse_args()

    settings = Settings()
    upload_dir = _ensure_upload_dir(settings.upload_dir)
    # Resolve the target download directory for auto-download if needed
    target_download_dir = None
    if args.restaurant_images_dir:
        target_download_dir = Path(args.restaurant_images_dir).expanduser().resolve()
    restaurant_images = _pick_image_files(args.restaurant_images_dir, target_download_dir=target_download_dir, required=50)

    if args.restaurant_images_dir:
        images_root = Path(args.restaurant_images_dir).expanduser().resolve()
        print(f"restaurant-images-dir={images_root} | imagens_encontradas={len(restaurant_images)}")

    db = SessionLocal()
    try:
        companies_stmt = select(Company)
        if args.company_id:
            companies_stmt = companies_stmt.where(Company.id == args.company_id)
        companies = db.scalars(companies_stmt.order_by(Company.id)).all()
        if not companies:
            print("Nenhuma empresa encontrada.")
            return

        for c in companies:
            branches_stmt = select(Branch).where(Branch.company_id == c.id).where(Branch.is_active.is_(True))
            if args.branch_id:
                branches_stmt = branches_stmt.where(Branch.id == args.branch_id)
            branches = db.scalars(branches_stmt.order_by(Branch.id)).all()
            if not branches:
                print(f"[{c.id}] {c.name}: nenhuma filial encontrada.")
                continue

            for b in branches:
                _seed_branch_products(
                    db=db,
                    company=c,
                    branch=b,
                    per_branch=args.per_branch,
                    force=args.force,
                    restaurant_images=restaurant_images,
                    upload_dir=upload_dir,
                    per_branch_target=args.per_branch,
                )

        print("Seed por filial concluído.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
