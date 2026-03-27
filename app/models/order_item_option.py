from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class OrderItemOption(Base):
    __tablename__ = "order_item_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    order_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("order_items.id"), nullable=False, index=True)

    # Detalhes da opção selecionada
    option_group_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    option_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    option_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Impacto no preço e ingredientes
    price_adjustment: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    ingredient_impact: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
