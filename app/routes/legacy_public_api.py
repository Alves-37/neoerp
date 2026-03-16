from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.branch import Branch

router = APIRouter()


def _extract_effective_host(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-host")
    host = (forwarded or request.headers.get("host") or "").strip().lower()
    if not host:
        return host
    if "," in host:
        host = host.split(",", 1)[0].strip()
    if ":" in host:
        host = host.split(":", 1)[0]
    return host


def _resolve_branch_from_request(db: Session, request: Request) -> Branch:
    host = _extract_effective_host(request)
    if not host:
        raise HTTPException(status_code=400, detail="Host inválido")

    # Prefer custom domain mapping
    branch = db.scalar(select(Branch).where(Branch.public_menu_custom_domain == host))
    if branch:
        if not branch.public_menu_enabled:
            raise HTTPException(status_code=404, detail="Menu indisponível")
        return branch

    parts = host.split(".")
    if len(parts) < 3:
        raise HTTPException(status_code=404, detail="Menu não encontrado")

    subdomain = parts[0]
    if subdomain in {"www"}:
        raise HTTPException(status_code=404, detail="Menu não encontrado")

    branch = db.scalar(select(Branch).where(Branch.public_menu_subdomain == subdomain))
    if not branch or not branch.public_menu_enabled:
        raise HTTPException(status_code=404, detail="Menu não encontrado")

    return branch


@router.get("/app")
def get_app(request: Request, db: Session = Depends(get_db)):
    """Endpoint de compatibilidade para o menu público legado.

    Retorna informações mínimas do estabelecimento para o front-end estático.
    """

    branch = _resolve_branch_from_request(db, request)
    return {
        "id": branch.id,
        "name": branch.name,
        "business_type": branch.business_type,
        "updated_at": datetime.utcnow().isoformat(),
    }


@router.get("/restaurant-status")
def get_restaurant_status(request: Request, db: Session = Depends(get_db)):
    """Endpoint de compatibilidade esperado pelo index.html legado.

    Como ainda não temos um modelo de horários/disponibilidade, por enquanto:
    - Se menu público estiver habilitado na filial restaurante => aberto
    """

    branch = _resolve_branch_from_request(db, request)
    bt = (branch.business_type or "").strip().lower()
    if bt != "restaurant":
        return {
            "is_open": False,
            "status": "closed",
            "reason": "not_restaurant",
        }

    is_open = bool(branch.public_menu_enabled)
    return {
        "is_open": is_open,
        "status": "open" if is_open else "closed",
    }
