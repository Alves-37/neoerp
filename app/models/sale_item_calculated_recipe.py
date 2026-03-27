from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class SaleItemCalculatedRecipe(Base):
    __tablename__ = "sale_item_calculated_recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    sale_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("sale_items.id"), nullable=False, index=True)

    # Snapshot da receita final calculada (para auditoria e performance)
    base_recipe_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # ID da receita base
    final_recipe: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # Receita final após aplicar opções
    total_multiplier: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False, default=1.0)  # Multiplicador total aplicado
    
    # Valores calculados no momento da venda
    final_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    base_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    options_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    # Metadados para auditoria
    applied_options: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # Opções aplicadas
    calculation_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")  # Versão do algoritmo

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
