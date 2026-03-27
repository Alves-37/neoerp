from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class RestaurantTable(Base):
    __tablename__ = "restaurant_tables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Status da mesa
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="available")  # available, occupied, reserved
    current_order_id: Mapped[int] = mapped_column(Integer, nullable=True)  # ID do pedido atual
    customer_name: Mapped[str] = mapped_column(String(100), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
