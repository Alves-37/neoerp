from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, nullable=False, index=True)
    branch_id = Column(Integer, nullable=False, index=True)
    establishment_id = Column(Integer, nullable=True, index=True)
    
    # Cliente
    customer_name = Column(String(200), nullable=False)
    customer_phone = Column(String(50), nullable=True)
    customer_email = Column(String(200), nullable=True)
    customer_nuit = Column(String(50), nullable=True)
    
    # Reserva
    table_id = Column(Integer, nullable=False, index=True)
    reservation_date = Column(DateTime, nullable=False, index=True)
    time_slot = Column(String(50), nullable=False)  # 'almoço' ou 'jantar'
    people_count = Column(Integer, nullable=False)
    
    # Valores
    estimated_amount = Column(Numeric(10, 2), nullable=True)
    deposit_percentage = Column(Numeric(5, 2), nullable=True)  # Ex: 50.00 para 50%
    deposit_amount = Column(Numeric(10, 2), nullable=True)
    
    # Pagamento
    payment_method = Column(String(50), nullable=True)  # 'mpesa', 'cash', etc.
    payment_status = Column(String(50), nullable=False, default='pending')  # 'pending', 'paid', 'refunded'
    payment_reference = Column(String(200), nullable=True)
    paid_at = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(50), nullable=False, default='pending_payment')  # 'pending_payment', 'confirmed', 'cancelled', 'completed', 'no_show'
    
    # Informações adicionais
    notes = Column(Text, nullable=True)
    special_requests = Column(Text, nullable=True)
    
    # Controle
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by = Column(Integer, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    # Relacionamentos
    # table = relationship("RestaurantTable", back_populates="reservations")
    
    def __repr__(self):
        return f"<Reservation(id={self.id}, customer={self.customer_name}, date={self.reservation_date}, status={self.status})>"
