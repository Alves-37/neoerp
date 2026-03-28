from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class ReservationBase(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=200, description="Nome do cliente")
    customer_phone: Optional[str] = Field(None, max_length=50, description="Telefone do cliente")
    customer_email: Optional[str] = Field(None, max_length=200, description="Email do cliente")
    customer_nuit: Optional[str] = Field(None, max_length=50, description="NUIT do cliente")
    
    table_id: int = Field(..., description="ID da mesa")
    reservation_date: datetime = Field(..., description="Data e hora da reserva")
    time_slot: str = Field(..., pattern="^(manhã|almoço|lanche|jantar)$", description="Turno: manhã, almoço, lanche ou jantar")
    people_count: int = Field(..., ge=1, le=20, description="Número de pessoas")
    
    estimated_amount: Optional[float] = Field(None, ge=0, description="Valor estimado da conta")
    deposit_percentage: Optional[float] = Field(None, ge=0, le=100, description="Percentual de depósito")
    deposit_amount: Optional[float] = Field(None, ge=0, description="Valor do depósito")
    
    payment_method: Optional[str] = Field(None, description="Forma de pagamento do depósito")
    payment_reference: Optional[str] = Field(None, max_length=200, description="Referência do pagamento")
    
    notes: Optional[str] = Field(None, max_length=1000, description="Observações")
    special_requests: Optional[str] = Field(None, max_length=1000, description="Pedidos especiais")

class ReservationCreate(ReservationBase):
    pass

class ReservationUpdate(BaseModel):
    customer_name: Optional[str] = Field(None, min_length=1, max_length=200)
    customer_phone: Optional[str] = Field(None, max_length=50)
    customer_email: Optional[str] = Field(None, max_length=200)
    customer_nuit: Optional[str] = Field(None, max_length=50)
    
    table_id: Optional[int] = None
    reservation_date: Optional[datetime] = None
    time_slot: Optional[str] = Field(None, pattern="^(manhã|almoço|lanche|jantar)$")
    people_count: Optional[int] = Field(None, ge=1, le=20)
    
    estimated_amount: Optional[float] = Field(None, ge=0)
    deposit_percentage: Optional[float] = Field(None, ge=0, le=100)
    deposit_amount: Optional[float] = Field(None, ge=0)
    
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = Field(None, max_length=200)
    
    notes: Optional[str] = Field(None, max_length=1000)
    special_requests: Optional[str] = Field(None, max_length=1000)

class ReservationResponse(ReservationBase):
    id: int
    company_id: int
    branch_id: int
    establishment_id: Optional[int]
    
    payment_status: str
    paid_at: Optional[datetime]
    status: str
    
    created_by: int
    created_at: datetime
    updated_at: datetime
    cancelled_at: Optional[datetime]
    cancelled_by: Optional[int]
    cancellation_reason: Optional[str]
    
    class Config:
        from_attributes = True

class ReservationListResponse(BaseModel):
    reservations: List[ReservationResponse]
    total: int
    offset: int
    limit: int

class TableAvailability(BaseModel):
    reservation_id: int
    customer_name: str
    people_count: int
    status: str

class AvailabilityResponse(BaseModel):
    date: str
    availability: dict[int, dict[str, TableAvailability]]
