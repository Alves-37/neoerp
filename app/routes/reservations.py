from datetime import datetime, time, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.database import get_db
from app.models.reservations import Reservation
from app.models.user import User
from app.schemas.reservation import (
    ReservationCreate,
    ReservationUpdate,
    ReservationResponse,
    ReservationListResponse
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/reservations", tags=["reservations"])

@router.get("/", response_model=ReservationListResponse)
async def list_reservations(
    date: Optional[str] = Query(None, description="Data no formato YYYY-MM-DD"),
    status: Optional[str] = Query(None, description="Status da reserva"),
    table_id: Optional[int] = Query(None, description="ID da mesa"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Listar reservas com filtros"""
    query = db.query(Reservation).filter(
        Reservation.company_id == current_user.company_id,
        Reservation.branch_id == current_user.branch_id
    )
    
    # Filtros
    if date:
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d").date()
            next_day = filter_date + timedelta(days=1)
            query = query.filter(
                and_(
                    Reservation.reservation_date >= filter_date,
                    Reservation.reservation_date < next_day
                )
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Data inválida. Use formato YYYY-MM-DD")
    
    if status:
        query = query.filter(Reservation.status == status)
    
    if table_id:
        query = query.filter(Reservation.table_id == table_id)
    
    # Ordenação
    query = query.order_by(Reservation.reservation_date, Reservation.time_slot)
    
    # Paginação
    total = query.count()
    reservations = query.offset(offset).limit(limit).all()
    
    return ReservationListResponse(
        reservations=reservations,
        total=total,
        offset=offset,
        limit=limit
    )

@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obter detalhes de uma reserva"""
    reservation = db.query(Reservation).filter(
        and_(
            Reservation.id == reservation_id,
            Reservation.company_id == current_user.company_id,
            Reservation.branch_id == current_user.branch_id
        )
    ).first()
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Reserva não encontrada")
    
    return reservation

@router.post("/", response_model=ReservationResponse)
async def create_reservation(
    reservation: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Criar nova reserva"""
    
    # Verificar se a mesa está disponível no horário
    existing = db.query(Reservation).filter(
        and_(
            Reservation.table_id == reservation.table_id,
            Reservation.reservation_date == reservation.reservation_date,
            Reservation.time_slot == reservation.time_slot,
            Reservation.status.in_(['pending_payment', 'confirmed', 'completed']),
            Reservation.company_id == current_user.company_id,
            Reservation.branch_id == current_user.branch_id
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409, 
            detail=f"Mesa já reservada para este horário. Reserva existente: {existing.customer_name}"
        )
    
    # Calcular valor do depósito se não informado
    deposit_amount = reservation.deposit_amount
    if deposit_amount is None and reservation.estimated_amount and reservation.deposit_percentage:
        deposit_amount = reservation.estimated_amount * (reservation.deposit_percentage / 100)
    
    # Criar reserva
    db_reservation = Reservation(
        company_id=current_user.company_id,
        branch_id=current_user.branch_id,
        establishment_id=getattr(current_user, 'establishment_id', None),
        customer_name=reservation.customer_name,
        customer_phone=reservation.customer_phone,
        customer_email=reservation.customer_email,
        customer_nuit=reservation.customer_nuit,
        table_id=reservation.table_id,
        reservation_date=reservation.reservation_date,
        time_slot=reservation.time_slot,
        people_count=reservation.people_count,
        estimated_amount=reservation.estimated_amount,
        deposit_percentage=reservation.deposit_percentage,
        deposit_amount=deposit_amount,
        payment_method=reservation.payment_method,
        payment_status='paid' if reservation.payment_method else 'pending',
        payment_reference=reservation.payment_reference,
        paid_at=datetime.now() if reservation.payment_method else None,
        status='confirmed' if reservation.payment_method else 'pending_payment',
        notes=reservation.notes,
        special_requests=reservation.special_requests,
        created_by=current_user.id
    )
    
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    
    return db_reservation

@router.put("/{reservation_id}", response_model=ReservationResponse)
async def update_reservation(
    reservation_id: int,
    reservation_update: ReservationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualizar reserva"""
    reservation = db.query(Reservation).filter(
        and_(
            Reservation.id == reservation_id,
            Reservation.company_id == current_user.company_id,
            Reservation.branch_id == current_user.branch_id
        )
    ).first()
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Reserva não encontrada")
    
    # Verificar se mudou de mesa/horário e se está disponível
    if (reservation_update.table_id and reservation_update.table_id != reservation.table_id) or \
       (reservation_update.reservation_date and reservation_update.reservation_date != reservation.reservation_date) or \
       (reservation_update.time_slot and reservation_update.time_slot != reservation.time_slot):
        
        new_table_id = reservation_update.table_id or reservation.table_id
        new_date = reservation_update.reservation_date or reservation.reservation_date
        new_time_slot = reservation_update.time_slot or reservation.time_slot
        
        existing = db.query(Reservation).filter(
            and_(
                Reservation.table_id == new_table_id,
                Reservation.reservation_date == new_date,
                Reservation.time_slot == new_time_slot,
                Reservation.status.in_(['pending_payment', 'confirmed', 'completed']),
                Reservation.id != reservation_id,
                Reservation.company_id == current_user.company_id,
                Reservation.branch_id == current_user.branch_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Mesa já reservada para este horário. Reserva existente: {existing.customer_name}"
            )
    
    # Atualizar campos
    update_data = reservation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reservation, field, value)
    
    # Se adicionou pagamento, atualizar status
    if reservation_update.payment_method and reservation.payment_status == 'pending':
        reservation.payment_status = 'paid'
        reservation.paid_at = datetime.now()
        reservation.status = 'confirmed'
    
    db.commit()
    db.refresh(reservation)
    
    return reservation

@router.post("/{reservation_id}/cancel")
async def cancel_reservation(
    reservation_id: int,
    cancellation_reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancelar reserva"""
    reservation = db.query(Reservation).filter(
        and_(
            Reservation.id == reservation_id,
            Reservation.company_id == current_user.company_id,
            Reservation.branch_id == current_user.branch_id
        )
    ).first()
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Reserva não encontrada")
    
    if reservation.status in ['cancelled', 'completed']:
        raise HTTPException(status_code=400, detail="Reserva já foi cancelada ou concluída")
    
    reservation.status = 'cancelled'
    reservation.cancelled_at = datetime.now()
    reservation.cancelled_by = current_user.id
    reservation.cancellation_reason = cancellation_reason
    
    db.commit()
    
    return {"message": "Reserva cancelada com sucesso"}

@router.get("/tables/availability/{date}")
async def get_tables_availability(
    date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verificar disponibilidade de mesas para uma data"""
    try:
        filter_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Data inválida. Use formato YYYY-MM-DD")
    
    # Buscar reservas do dia
    reservations = db.query(Reservation).filter(
        and_(
            Reservation.reservation_date == filter_date,
            Reservation.status.in_(['pending_payment', 'confirmed', 'completed']),
            Reservation.company_id == current_user.company_id,
            Reservation.branch_id == current_user.branch_id
        )
    ).all()
    
    # Organizar por mesa e time_slot
    availability = {}
    for reservation in reservations:
        table_id = reservation.table_id
        time_slot = reservation.time_slot
        
        if table_id not in availability:
            availability[table_id] = {}
        
        availability[table_id][time_slot] = {
            "reservation_id": reservation.id,
            "customer_name": reservation.customer_name,
            "people_count": reservation.people_count,
            "status": reservation.status
        }
    
    return {"date": date, "availability": availability}
