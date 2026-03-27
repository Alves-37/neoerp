from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_current_user
from app.models.branch import Branch
from app.models.product import Product
from app.models.product_option import ProductOption
from app.models.product_option_group import ProductOptionGroup
from app.models.sale_item import SaleItem
from app.models.sale_item_option import SaleItemOption
from app.models.user import User
from app.schemas.product_options import (
    ProductOptionCreate,
    ProductOptionGroupCreate,
    ProductOptionGroupOut,
    ProductOptionGroupUpdate,
    ProductOptionGroupWithOptionsOut,
    ProductOptionOut,
    ProductOptionUpdate,
)

router = APIRouter()


@router.get("/products/{product_id}/option-groups", response_model=list[ProductOptionGroupWithOptionsOut])
def list_product_option_groups(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista todos os grupos de opções de um produto"""
    # Verificar se o produto existe e pertence à empresa
    product = db.scalar(
        select(Product).where(
            Product.id == product_id,
            Product.company_id == current_user.company_id,
            Product.branch_id == current_user.branch_id,
        )
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    groups = db.scalars(
        select(ProductOptionGroup)
        .where(
            ProductOptionGroup.product_id == product_id,
            ProductOptionGroup.company_id == current_user.company_id,
            ProductOptionGroup.branch_id == current_user.branch_id,
            ProductOptionGroup.is_active == True,
        )
        .order_by(ProductOptionGroup.sort_order, ProductOptionGroup.name)
    ).all()

    result = []
    for group in groups:
        options = db.scalars(
            select(ProductOption)
            .where(
                ProductOption.option_group_id == group.id,
                ProductOption.is_active == True,
            )
            .order_by(ProductOption.sort_order, ProductOption.name)
        ).all()
        
        group_data = ProductOptionGroupWithOptionsOut.model_validate(group)
        group_data.options = [ProductOptionOut.model_validate(opt) for opt in options]
        result.append(group_data)

    return result


@router.post("/products/{product_id}/option-groups", response_model=ProductOptionGroupOut)
def create_product_option_group(
    product_id: int,
    payload: ProductOptionGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cria um novo grupo de opções para um produto"""
    # Verificar se o produto existe
    product = db.scalar(
        select(Product).where(
            Product.id == product_id,
            Product.company_id == current_user.company_id,
            Product.branch_id == current_user.branch_id,
        )
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Validar regras de seleção
    if payload.min_selections > payload.max_selections:
        raise HTTPException(status_code=400, detail="Min selections cannot be greater than max selections")

    group = ProductOptionGroup(
        company_id=current_user.company_id,
        branch_id=current_user.branch_id,
        product_id=product_id,
        **payload.model_dump(),
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@router.put("/option-groups/{group_id}", response_model=ProductOptionGroupOut)
def update_product_option_group(
    group_id: int,
    payload: ProductOptionGroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualiza um grupo de opções"""
    group = db.scalar(
        select(ProductOptionGroup).where(
            ProductOptionGroup.id == group_id,
            ProductOptionGroup.company_id == current_user.company_id,
            ProductOptionGroup.branch_id == current_user.branch_id,
        )
    )
    if not group:
        raise HTTPException(status_code=404, detail="Option group not found")

    # Validar regras de seleção
    if payload.min_selections > payload.max_selections:
        raise HTTPException(status_code=400, detail="Min selections cannot be greater than max selections")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(group, field, value)

    db.commit()
    db.refresh(group)
    return group


@router.delete("/option-groups/{group_id}")
def delete_product_option_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove (desativa) um grupo de opções"""
    group = db.scalar(
        select(ProductOptionGroup).where(
            ProductOptionGroup.id == group_id,
            ProductOptionGroup.company_id == current_user.company_id,
            ProductOptionGroup.branch_id == current_user.branch_id,
        )
    )
    if not group:
        raise HTTPException(status_code=404, detail="Option group not found")

    group.is_active = False
    db.commit()
    return {"message": "Option group deleted successfully"}


@router.post("/option-groups/{group_id}/options", response_model=ProductOptionOut)
def create_product_option(
    group_id: int,
    payload: ProductOptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cria uma nova opção em um grupo"""
    # Verificar se o grupo existe
    group = db.scalar(
        select(ProductOptionGroup).where(
            ProductOptionGroup.id == group_id,
            ProductOptionGroup.company_id == current_user.company_id,
            ProductOptionGroup.branch_id == current_user.branch_id,
        )
    )
    if not group:
        raise HTTPException(status_code=404, detail="Option group not found")

    option = ProductOption(
        company_id=current_user.company_id,
        branch_id=current_user.branch_id,
        option_group_id=group_id,
        **payload.model_dump(),
    )
    db.add(option)
    db.commit()
    db.refresh(option)
    return option


@router.put("/options/{option_id}", response_model=ProductOptionOut)
def update_product_option(
    option_id: int,
    payload: ProductOptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualiza uma opção"""
    option = db.scalar(
        select(ProductOption).where(
            ProductOption.id == option_id,
            ProductOption.company_id == current_user.company_id,
            ProductOption.branch_id == current_user.branch_id,
        )
    )
    if not option:
        raise HTTPException(status_code=404, detail="Option not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(option, field, value)

    db.commit()
    db.refresh(option)
    return option


@router.delete("/options/{option_id}")
def delete_product_option(
    option_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove (desativa) uma opção"""
    option = db.scalar(
        select(ProductOption).where(
            ProductOption.id == option_id,
            ProductOption.company_id == current_user.company_id,
            ProductOption.branch_id == current_user.branch_id,
        )
    )
    if not option:
        raise HTTPException(status_code=404, detail="Option not found")

    option.is_active = False
    db.commit()
    return {"message": "Option deleted successfully"}
