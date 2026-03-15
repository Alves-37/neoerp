import argparse
from pathlib import Path
import mimetypes
import requests
import time

from app.database.connection import SessionLocal
from app.models.branch import Branch
from app.models.company import Company
from app.models.product import Product
from app.scripts.seed_branch_products import _product_name_from_image


def _product_name_from_image(image_path: Path) -> str:
    """
    Gera nome de produto a partir do nome do arquivo de imagem.
    Remove extensão e coloca em "Title Case" (apenas normaliza separadores).
    """
    name = image_path.stem.replace("-", " ").replace("_", " ").strip()
    clean = " ".join(name.split())
    # Title Case por palavra (preserva acentos)
    return " ".join((w[:1].upper() + w[1:].lower()) if w else "" for w in clean.split(" "))


def _find_product_by_name(db, company_id: int, branch_id: int, name: str) -> Product | None:
    """
    Procura um produto pelo nome (case-insensitive) na empresa e filial.
    """
    return db.scalar(
        select(Product)
        .where(Product.company_id == company_id)
        .where(Product.branch_id == branch_id)
        .where(Product.name.ilike(f"%{name}%"))
        .order_by(Product.name.asc())
        .limit(1)
    )


def upload_images_to_production(
    *,
    pic_dir: str,
    api_url: str,
    token: str,
    dry_run: bool = False,
) -> None:
    """
    Envia imagens da pasta pic_dir para o backend em produção via API.
    Associa imagens a produtos pelo nome do arquivo.
    """
    pic_path = Path(pic_dir).expanduser().resolve()
    if not pic_path.is_dir():
        raise ValueError(f"Pasta não encontrada: {pic_path}")

    exts = {".png", ".jpg", ".jpeg", ".webp"}
    image_files = sorted([f for f in pic_path.iterdir() if f.suffix.lower() in exts])

    if not image_files:
        print("Nenhuma imagem encontrada na pasta.")
        return

    print(f"Encontradas {len(image_files)} imagens em {pic_path}")

    # Buscar produtos em produção via API
    headers = {"Authorization": f"Bearer {token}"}
    products_resp = requests.get(f"{api_url.rstrip('/')}/products", headers=headers, timeout=15)
    products_resp.raise_for_status()
    products_data = products_resp.json()
    products_by_name = {p["name"]: p for p in products_data}

    uploaded = 0
    skipped = 0
    errors = 0

    for img_file in image_files:
        try:
            product_name = _product_name_from_image(img_file)
            print(f"\nImagem: {img_file.name} -> Produto esperado: '{product_name}'")

            # Procurar produto em produção
            product = None
            # Tenta match exato
            if product_name in products_by_name:
                product = products_by_name[product_name]
            else:
                # Tenta match parcial (case-insensitive)
                for p_name, p_data in products_by_name.items():
                    if product_name.lower() in p_name.lower() or p_name.lower() in product_name.lower():
                        product = p_data
                        break

            if not product:
                print(f"  -> Produto não encontrado. Pulando imagem.")
                skipped += 1
                continue

            product_id = product["id"]
            print(f"  -> Produto encontrado: ID {product_id} ('{product['name']}')")

            if dry_run:
                print(f"  [DRY-RUN] Enviaria {img_file.name} para produto ID {product_id}")
                uploaded += 1
                continue

            # Upload via multipart
            with open(img_file, "rb") as f:
                files = {"file": (img_file.name, f, mimetypes.guess_type(img_file)[0] or "image/jpeg")}
                upload_resp = requests.post(
                    f"{api_url.rstrip('/')}/products/{product_id}/images",
                    headers=headers,
                    files=files,
                    timeout=30,
                )
            if upload_resp.status_code == 200:
                print(f"  -> Upload OK: {upload_resp.json()}")
                uploaded += 1
            else:
                print(f"  -> Erro no upload: {upload_resp.status_code} {upload_resp.text}")
                errors += 1

            time.sleep(0.2)  # Gentileza
        except Exception as e:
            print(f"  -> Exceção: {e}")
            errors += 1

    print(f"\n--- Resumo ---")
    print(f"Enviados: {uploaded}")
    print(f"Pulados (produto não encontrado): {skipped}")
    print(f"Erros: {errors}")
    print(f"Total imagens: {len(image_files)}")


def main():
    parser = argparse.ArgumentParser(
        description="Envia imagens da pasta local para o backend em produção via API, associando por nome do produto."
    )
    parser.add_argument("--pic-dir", type=str, required=True, help="Pasta local com as imagens (ex: ../pic)")
    parser.add_argument(
        "--api-url",
        type=str,
        default="https://neoerp-production.up.railway.app",
        help="URL base da API em produção",
    )
    parser.add_argument("--token", type=str, required=True, help="JWT token (Bearer) para autenticação")
    parser.add_argument("--dry-run", action="store_true", help="Apenas simular, não enviar")
    args = parser.parse_args()

    upload_images_to_production(
        pic_dir=args.pic_dir,
        api_url=args.api_url,
        token=args.token,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
