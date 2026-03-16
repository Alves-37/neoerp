from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.branch import Branch

router = APIRouter()


@router.post("/debug/disable-menu/{branch_id}")
def disable_public_menu(branch_id: int, db: Session = Depends(get_db)):
    """Endpoint para desativar menu público de uma filial"""
    branch = db.scalar(select(Branch).where(Branch.id == branch_id))
    if not branch:
        raise HTTPException(status_code=404, detail="Filial não encontrada")
    
    # Desativar menu público
    branch.public_menu_enabled = False
    branch.public_menu_custom_domain = None
    branch.public_menu_subdomain = None
    
    db.commit()
    db.refresh(branch)
    
    return {
        "success": True,
        "message": f"Menu público desativado para {branch.name}",
        "config": {
            "id": branch.id,
            "name": branch.name,
            "public_menu_enabled": branch.public_menu_enabled,
            "public_menu_custom_domain": branch.public_menu_custom_domain,
            "public_menu_subdomain": branch.public_menu_subdomain
        }
    }
