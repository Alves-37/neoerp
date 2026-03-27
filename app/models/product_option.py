from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class ProductOption(Base):
    __tablename__ = "product_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    option_group_id: Mapped[int] = mapped_column(Integer, ForeignKey("product_option_groups.id"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)  # "Pequeno", "Grande", "Bacon Extra"
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    # Tipo lógico da opção
    option_type: Mapped[str] = mapped_column(String(20), nullable=False, default="addon")  # variant, addon, removal
    
    # Impacto no preço
    price_adjustment: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)  # +200 MT
    adjustment_type: Mapped[str] = mapped_column(String(10), nullable=False, default="fixed")  # fixed, percentage

    # Impacto na receita (ficha técnica)
    ingredient_impact: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # {"add": {"1": {"qty": 0.1, "unit": "kg"}}}
    ingredient_remove: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # {"remove": [45, 67]}
    ingredient_multiplier: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # {"multiply": {"1": 1.3}}

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
