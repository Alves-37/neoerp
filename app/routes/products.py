import os
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import delete, desc, func, or_, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.branch import Branch
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_image import ProductImage
from app.models.product_stock import ProductStock
from app.models.sale_item import SaleItem
from app.models.stock_movement import StockMovement
from app.models.stock_transfer import StockTransfer
from app.models.supplier import Supplier
from app.models.stock_location import StockLocation
from app.models.user import User
from app.schemas.products import ProductCreate, ProductImageOut, ProductOut, ProductUpdate
from app.settings import Settings

router = APIRouter()
settings = Settings()


def _get_or_create_stock_row(db: Session, company_id: int, branch_id: int, product_id: int, location_id: int) -> ProductStock:
    row = db.scalar(
        select(ProductStock)
        .where(ProductStock.company_id == company_id)
        .where(ProductStock.branch_id == int(branch_id))
        .where(ProductStock.product_id == product_id)
        .where(ProductStock.location_id == location_id)
        .with_for_update()
    )
    if row:
        return row

    row = ProductStock(
        company_id=company_id,
        branch_id=int(branch_id),
        product_id=product_id,
        location_id=location_id,
        qty_on_hand=0,
    )
    db.add(row)
    db.flush()

    row = db.scalar(
        select(ProductStock)
        .where(ProductStock.company_id == company_id)
        .where(ProductStock.branch_id == int(branch_id))
        .where(ProductStock.product_id == product_id)
        .where(ProductStock.location_id == location_id)
        .with_for_update()
    )
    return row


def _get_stock_qty(db: Session, company_id: int, branch_id: int, product: Product) -> float:
    try:
        location_id = int(getattr(product, "default_location_id", 0) or 0)
        if not location_id:
            return 0
        qty = db.scalar(
            select(func.coalesce(ProductStock.qty_on_hand, 0))
            .where(ProductStock.company_id == company_id)
            .where(ProductStock.branch_id == int(branch_id))
            .where(ProductStock.product_id == int(product.id))
            .where(ProductStock.location_id == location_id)
        )
        return float(qty or 0)
    except Exception:
        return 0


def _ensure_upload_dir():
    os.makedirs(settings.upload_dir, exist_ok=True)


@router.get("/", response_model=list[ProductOut])
@router.get("", response_model=list[ProductOut], include_in_schema=False)
def list_products(
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    branch_id: int | None = None,
    establishment_id: int | None = None,
    category_id: int | None = None,
    low_stock: bool = False,
    is_active: bool | None = None,
    in_stock: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    image_file_subq = (
        select(ProductImage.file_path)
        .where(ProductImage.company_id == current_user.company_id)
        .where(ProductImage.product_id == Product.id)
        .order_by(ProductImage.id.desc())
        .limit(1)
        .scalar_subquery()
    )

    qty_expr = func.coalesce(ProductStock.qty_on_hand, 0)
    stmt = (
        select(Product, image_file_subq.label("image_file_path"), qty_expr.label("stock_qty"))
        .select_from(Product)
        .outerjoin(
            ProductStock,
            (ProductStock.company_id == current_user.company_id)
            & (ProductStock.branch_id == Product.branch_id)
            & (ProductStock.product_id == Product.id)
            & (ProductStock.location_id == Product.default_location_id),
        )
        .where(Product.company_id == current_user.company_id)
    )

    # Default: always scope to the current user's branch for isolation.
    # Admins can explicitly choose another branch via branch_id.
    effective_branch_id = int(branch_id) if (is_admin and branch_id is not None) else int(current_user.branch_id)
    branch = db.get(Branch, effective_branch_id)
    if not branch or branch.company_id != current_user.company_id:
        raise HTTPException(status_code=400, detail="Filial inválida")
    business_type = branch.business_type or "retail"
    stmt = stmt.where(Product.branch_id == effective_branch_id).where(Product.business_type == business_type)

    # Scope by establishment (ponto)
    if is_admin:
        if establishment_id is not None:
            stmt = stmt.where(Product.establishment_id == int(establishment_id))
    else:
        if not getattr(current_user, "establishment_id", None):
            raise HTTPException(status_code=400, detail="Ponto inválido")
        stmt = stmt.where(Product.establishment_id == int(current_user.establishment_id))

    if low_stock:
        stmt = (
            stmt.where(Product.track_stock.is_(True))
            .where(Product.is_active.is_(True))
            .where(func.coalesce(Product.min_stock, 0) > 0)
            .where(qty_expr < func.coalesce(Product.min_stock, 0))
        )

    if in_stock:
        stmt = stmt.where(or_(Product.track_stock.is_(False), qty_expr > 0))

    if is_active is not None:
        stmt = stmt.where(Product.is_active.is_(bool(is_active)))

    if category_id is not None:
        stmt = stmt.where(Product.category_id == int(category_id))

    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q}%"))

    rows = db.execute(stmt.order_by(Product.name.asc(), Product.id.asc()).limit(limit).offset(offset)).all()
    out: list[ProductOut] = []
    for product, image_file_path, stock_qty in rows:
        p = ProductOut.model_validate(product)
        if image_file_path:
            p.image_url = f"/uploads/{image_file_path}"
        p.stock_qty = float(stock_qty or 0)
        out.append(p)
    return out


@router.post("", response_model=ProductOut)
def create_product(payload: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    branch = db.get(Branch, int(current_user.branch_id))
    if not branch or branch.company_id != current_user.company_id:
        raise HTTPException(status_code=400, detail="Filial inválida")
    business_type = branch.business_type or "retail"

    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    effective_establishment_id: int | None = None
    if is_admin and getattr(payload, "establishment_id", None):
        effective_establishment_id = int(payload.establishment_id)
    else:
        effective_establishment_id = int(getattr(current_user, "establishment_id", 0) or 0)

    if not effective_establishment_id:
        raise HTTPException(status_code=400, detail="Ponto inválido")

    category_id = payload.category_id
    if payload.category_name and payload.category_name.strip():
        name = payload.category_name.strip()
        category = db.scalar(
            select(ProductCategory)
            .where(ProductCategory.company_id == current_user.company_id)
            .where(ProductCategory.business_type == business_type)
            .where(ProductCategory.name.ilike(name))
        )
        if not category:
            category = ProductCategory(company_id=current_user.company_id, business_type=business_type, name=name)
            db.add(category)
            db.commit()
            db.refresh(category)
        category_id = category.id

    if category_id is not None:
        category = db.get(ProductCategory, category_id)
        if not category or category.company_id != current_user.company_id or category.business_type != business_type:
            raise HTTPException(status_code=400, detail="Categoria inválida para este tipo de negócio")

    if payload.supplier_id is not None:
        supplier = db.get(Supplier, int(payload.supplier_id))
        if (
            not supplier
            or supplier.company_id != current_user.company_id
            or getattr(supplier, "branch_id", None) != int(current_user.branch_id)
        ):
            raise HTTPException(status_code=400, detail="Fornecedor inválido")

    location = db.get(StockLocation, int(payload.default_location_id))
    if not location or location.company_id != current_user.company_id or not location.is_active:
        raise HTTPException(status_code=400, detail="Local padrão inválido")
    if int(getattr(location, "branch_id", 0) or 0) != int(current_user.branch_id):
        raise HTTPException(status_code=400, detail="Local padrão inválido")

    is_service = bool(getattr(payload, "is_service", False))
    track_stock = bool(payload.track_stock)
    if is_service:
        track_stock = False

    product = Product(
        company_id=current_user.company_id,
        branch_id=int(current_user.branch_id),
        establishment_id=effective_establishment_id,
        category_id=category_id,
        supplier_id=payload.supplier_id,
        default_location_id=payload.default_location_id,
        business_type=business_type,
        name=payload.name,
        sku=payload.sku,
        barcode=payload.barcode,
        unit=payload.unit,
        price=payload.price,
        cost=0 if is_service else payload.cost,
        tax_rate=payload.tax_rate,
        min_stock=0 if is_service else float(getattr(payload, "min_stock", 0) or 0),
        track_stock=track_stock,
        is_service=is_service,
        is_active=payload.is_active,
        show_in_menu=True if (business_type or "").strip().lower() == "restaurant" else False,
        attributes=payload.attributes or {},
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    if (not is_service) and getattr(payload, "stock_qty", None) is not None:
        qty = float(payload.stock_qty or 0)
        if qty < 0:
            raise HTTPException(status_code=400, detail="Estoque inválido")
        stock = _get_or_create_stock_row(db, current_user.company_id, int(current_user.branch_id), product.id, int(product.default_location_id))
        before = float(stock.qty_on_hand or 0)
        delta = qty - before
        stock.qty_on_hand = qty
        mv = StockMovement(
            company_id=current_user.company_id,
            branch_id=int(current_user.branch_id),
            product_id=product.id,
            location_id=int(product.default_location_id),
            movement_type="initial",
            qty_delta=delta,
            reference_type="product",
            reference_id=product.id,
            notes="Estoque inicial",
            created_by=current_user.id,
        )
        db.add(mv)
        db.commit()

    out = ProductOut.model_validate(product)
    out.stock_qty = _get_stock_qty(db, current_user.company_id, int(current_user.branch_id), product)
    return out


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = db.get(Product, product_id)
    if not product or product.company_id != current_user.company_id or int(getattr(product, "branch_id", 0) or 0) != int(current_user.branch_id):
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    out = ProductOut.model_validate(product)
    out.stock_qty = _get_stock_qty(db, current_user.company_id, int(current_user.branch_id), product)
    return out


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int, payload: ProductUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    product = db.get(Product, product_id)
    if not product or product.company_id != current_user.company_id or int(getattr(product, "branch_id", 0) or 0) != int(current_user.branch_id):
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    data = payload.model_dump(exclude_unset=True)

    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}
    if (not is_admin) and ("establishment_id" in data):
        raise HTTPException(status_code=403, detail="Sem permissão para alterar o ponto do produto")

    is_service_next = bool(data.get("is_service", getattr(product, "is_service", False)))
    if is_service_next:
        # enforce service invariants
        data["track_stock"] = False
        data["min_stock"] = 0
        data["cost"] = 0

    if "supplier_id" in data and data["supplier_id"] is not None:
        supplier = db.get(Supplier, int(data["supplier_id"]))
        if not supplier or supplier.company_id != current_user.company_id:
            raise HTTPException(status_code=400, detail="Fornecedor inválido")

    if "default_location_id" in data and data["default_location_id"] is not None:
        location = db.get(StockLocation, int(data["default_location_id"]))
        if not location or location.company_id != current_user.company_id or not location.is_active:
            raise HTTPException(status_code=400, detail="Local padrão inválido")
        if int(getattr(location, "branch_id", 0) or 0) != int(current_user.branch_id):
            raise HTTPException(status_code=400, detail="Local padrão inválido")

    for k, v in data.items():
        if k == "stock_qty":
            continue
        setattr(product, k, v)

    db.add(product)
    db.commit()
    db.refresh(product)

    if (not is_service_next) and "stock_qty" in data and data["stock_qty"] is not None:
        qty = float(data["stock_qty"] or 0)
        if qty < 0:
            raise HTTPException(status_code=400, detail="Estoque inválido")
        stock = _get_or_create_stock_row(db, current_user.company_id, int(current_user.branch_id), product.id, int(product.default_location_id))
        before = float(stock.qty_on_hand or 0)
        delta = qty - before
        stock.qty_on_hand = qty
        mv = StockMovement(
            company_id=current_user.company_id,
            branch_id=int(current_user.branch_id),
            product_id=product.id,
            location_id=int(product.default_location_id),
            movement_type="adjustment",
            qty_delta=delta,
            reference_type="product",
            reference_id=product.id,
            notes="Ajuste via produto",
            created_by=current_user.id,
        )
        db.add(mv)
        db.commit()

    out = ProductOut.model_validate(product)
    out.stock_qty = _get_stock_qty(db, current_user.company_id, int(current_user.branch_id), product)
    return out


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = db.get(Product, product_id)
    if not product or product.company_id != current_user.company_id or int(getattr(product, "branch_id", 0) or 0) != int(current_user.branch_id):
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    # If product was used in sales, keep history: do not allow hard-delete.
    used_in_sales = db.scalar(
        select(func.count(SaleItem.id))
        .where(SaleItem.company_id == current_user.company_id)
        .where(SaleItem.product_id == product.id)
    )
    if int(used_in_sales or 0) > 0:
        product.is_active = False
        db.add(product)
        db.commit()
        return {"status": "deactivated"}

    # Remove related images first (FK constraint)
    imgs = db.scalars(
        select(ProductImage)
        .where(ProductImage.company_id == current_user.company_id)
        .where(ProductImage.product_id == product.id)
    ).all()
    for img in imgs:
        try:
            if getattr(img, "file_path", None):
                disk_path = os.path.join(settings.upload_dir, img.file_path)
                if os.path.exists(disk_path):
                    os.remove(disk_path)
        except Exception:
            # ignore disk delete errors; DB delete still proceeds
            pass
        db.delete(img)

    # Ensure image deletions are applied before deleting the product (avoid FK violations)
    db.flush()

    # Remove stock dependencies (safe to delete when product has no sales history)
    db.execute(
        delete(ProductStock)
        .where(ProductStock.company_id == current_user.company_id)
        .where(ProductStock.branch_id == int(current_user.branch_id))
        .where(ProductStock.product_id == product.id)
    )
    db.execute(
        delete(StockMovement)
        .where(StockMovement.company_id == current_user.company_id)
        .where(StockMovement.branch_id == int(current_user.branch_id))
        .where(StockMovement.product_id == product.id)
    )
    db.execute(
        delete(StockTransfer)
        .where(StockTransfer.company_id == current_user.company_id)
        .where(StockTransfer.branch_id == int(current_user.branch_id))
        .where(StockTransfer.product_id == product.id)
    )
    db.flush()

    try:
        db.delete(product)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Não foi possível apagar o produto. Verifique se há vendas/estoque vinculados.",
        )
    return {"status": "deleted"}


@router.post("/{product_id}/images", response_model=ProductImageOut)
def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.get(Product, product_id)
    if not product or product.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    _ensure_upload_dir()

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
        raise HTTPException(status_code=400, detail="Formato de imagem inválido")

    filename = f"{uuid4().hex}{ext}"
    disk_path = os.path.join(settings.upload_dir, filename)

    with open(disk_path, "wb") as f:
        f.write(file.file.read())

    img = ProductImage(
        company_id=current_user.company_id,
        product_id=product.id,
        file_path=filename,
    )
    db.add(img)
    db.commit()
    db.refresh(img)

    return ProductImageOut(
        id=img.id,
        product_id=img.product_id,
        company_id=img.company_id,
        file_path=img.file_path,
        url=f"/uploads/{img.file_path}",
        created_at=img.created_at,
    )


@router.get("/{product_id}/images", response_model=list[ProductImageOut])
def list_product_images(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.get(Product, product_id)
    if not product or product.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    rows = db.scalars(
        select(ProductImage)
        .where(ProductImage.company_id == current_user.company_id)
        .where(ProductImage.product_id == product.id)
        .order_by(desc(ProductImage.id))
    ).all()

    return [
        ProductImageOut(
            id=r.id,
            product_id=r.product_id,
            company_id=r.company_id,
            file_path=r.file_path,
            url=f"/uploads/{r.file_path}",
            created_at=r.created_at,
        )
        for r in rows
    ]
