from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class SaleItemOption(Base):
    __tablename__ = "sale_item_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    sale_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("sale_items.id"), nullable=False, index=True)
    option_group_id: Mapped[int] = mapped_column(Integer, ForeignKey("product_option_groups.id"), nullable=False, index=True)
    option_id: Mapped[int] = mapped_column(Integer, ForeignKey("product_options.id"), nullable=False, index=True)

    # Valores no momento da venda (para auditoria)
    option_name: Mapped[str] = mapped_column(String(100), nullable=False)
    price_adjustment: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    ingredient_impact: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
