from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.branch import Branch

router = APIRouter()


@router.get("/debug/branches")
def debug_branches(db: Session = Depends(get_db)):
    """Endpoint para listar todas as filiais e suas configurações de menu público"""
    branches = db.scalars(select(Branch)).all()
    
    result = []
    for branch in branches:
        result.append({
            "id": branch.id,
            "name": branch.name,
            "business_type": branch.business_type,
            "public_menu_enabled": branch.public_menu_enabled,
            "public_menu_subdomain": branch.public_menu_subdomain,
            "public_menu_custom_domain": branch.public_menu_custom_domain,
            "is_restaurant": (branch.business_type or "").strip().lower() == "restaurant"
        })
    
    return {"branches": result, "total": len(result)}


@router.post("/debug/setup-menu/{branch_id}")
def setup_public_menu(branch_id: int, db: Session = Depends(get_db)):
    """Endpoint para configurar automaticamente menu público para uma filial"""
    branch = db.scalar(select(Branch).where(Branch.id == branch_id))
    if not branch:
        raise HTTPException(status_code=404, detail="Filial não encontrada")
    
    # Configurar para menu.vuchada.com
    branch.public_menu_enabled = True
    branch.public_menu_custom_domain = "menu.vuchada.com"
    branch.public_menu_subdomain = None  # Limpar subdomínio se existir
    
    db.commit()
    db.refresh(branch)
    
    return {
        "success": True,
        "message": f"Menu público configurado para {branch.name}",
        "config": {
            "id": branch.id,
            "name": branch.name,
            "public_menu_enabled": branch.public_menu_enabled,
            "public_menu_custom_domain": branch.public_menu_custom_domain,
            "public_menu_subdomain": branch.public_menu_subdomain,
            "url": f"https://{branch.public_menu_custom_domain}"
        }
    }
