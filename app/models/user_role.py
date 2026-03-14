from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base

class UserRole(Base):
    __tablename__ = 'user_roles'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    name = Column(String(100), nullable=False)  # admin, manager, cashier, waiter, etc.
    display_name = Column(String(100), nullable=False)  # Administrador, Gerente, Caixa, Garçom
    permissions = Column(String, nullable=True)  # JSON string com lista de permissões
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship('Company')
