from fastapi import APIRouter, HTTPException, Depends, Request
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


@router.post("/debug/setup-custom-domain/{branch_id}")
def setup_custom_domain(branch_id: int, domain: str, db: Session = Depends(get_db)):
    """Endpoint para configurar domínio customizado para qualquer filial"""
    branch = db.scalar(select(Branch).where(Branch.id == branch_id))
    if not branch:
        raise HTTPException(status_code=404, detail="Filial não encontrada")
    
    # Normalizar domínio
    domain = domain.strip().lower()
    if domain.startswith('http://') or domain.startswith('https://'):
        domain = domain.split('://', 1)[1]
    if '/' in domain:
        domain = domain.split('/', 1)[0]
    if ':' in domain:
        domain = domain.split(':', 1)[0]
    
    # Verificar se já está em uso
    existing = db.scalar(select(Branch).where(Branch.public_menu_custom_domain == domain))
    if existing and existing.id != branch_id:
        raise HTTPException(status_code=400, detail=f"Domínio {domain} já está em uso por {existing.name}")
    
    # Configurar
    branch.public_menu_enabled = True
    branch.public_menu_custom_domain = domain
    branch.public_menu_subdomain = None
    
    db.commit()
    db.refresh(branch)
    
    return {
        "success": True,
        "message": f"Menu público configurado para {branch.name} no domínio {domain}",
        "config": {
            "id": branch.id,
            "name": branch.name,
            "public_menu_enabled": branch.public_menu_enabled,
            "public_menu_custom_domain": branch.public_menu_custom_domain,
            "public_menu_subdomain": branch.public_menu_subdomain,
            "url": f"https://{domain}"
        },
        "dns_instructions": {
            "type": "CNAME",
            "host": domain,
            "target": "cname.vercel-dns.com",
            "note": "Configure este registro CNAME no seu provedor DNS (Hostinger)"
        }
    }


@router.post("/debug/setup-subdomain/{branch_id}")
def setup_subdomain(branch_id: int, subdomain: str, db: Session = Depends(get_db)):
    """Endpoint para configurar subdomínio para qualquer filial"""
    branch = db.scalar(select(Branch).where(Branch.id == branch_id))
    if not branch:
        raise HTTPException(status_code=404, detail="Filial não encontrada")
    
    # Normalizar subdomínio
    subdomain = subdomain.strip().lower()
    if subdomain in {"www", "mail", "ftp", "admin", "api"}:
        raise HTTPException(status_code=400, detail=f"Subdomínio {subdomain} não é permitido")
    
    # Verificar se já está em uso
    existing = db.scalar(select(Branch).where(Branch.public_menu_subdomain == subdomain))
    if existing and existing.id != branch_id:
        raise HTTPException(status_code=400, detail=f"Subdomínio {subdomain} já está em uso por {existing.name}")
    
    # Configurar
    branch.public_menu_enabled = True
    branch.public_menu_subdomain = subdomain
    branch.public_menu_custom_domain = None
    
    db.commit()
    db.refresh(branch)
    
    return {
        "success": True,
        "message": f"Menu público configurado para {branch.name} com subdomínio {subdomain}",
        "config": {
            "id": branch.id,
            "name": branch.name,
            "public_menu_enabled": branch.public_menu_enabled,
            "public_menu_custom_domain": branch.public_menu_custom_domain,
            "public_menu_subdomain": branch.public_menu_subdomain,
            "url": f"https://{subdomain}.vuchada.com"
        },
        "dns_instructions": {
            "type": "CNAME",
            "host": subdomain,
            "target": "cname.vercel-dns.com",
            "note": "Configure este registro CNAME no seu provedor DNS (Hostinger) ou use wildcard (*.vuchada.com)"
        }
    }


@router.get("/debug/host-resolution")
def debug_host_resolution(request: Request, db: Session = Depends(get_db)):
    """Endpoint para debugar resolução de host"""
    from app.routes.public_menu import _extract_effective_host, _resolve_branch_from_request
    
    try:
        host = _extract_effective_host(request)
        branch = _resolve_branch_from_request(db, request)
        
        return {
            "success": True,
            "headers": dict(request.headers),
            "extracted_host": host,
            "branch_found": {
                "id": branch.id,
                "name": branch.name,
                "public_menu_enabled": branch.public_menu_enabled,
                "public_menu_custom_domain": branch.public_menu_custom_domain,
                "public_menu_subdomain": branch.public_menu_subdomain
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "headers": dict(request.headers),
            "extracted_host": _extract_effective_host(request) if 'request' in locals() else None
        }
