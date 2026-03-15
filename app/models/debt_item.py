from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class DebtItem(Base):
    __tablename__ = "debt_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    debt_id: Mapped[int] = mapped_column(Integer, ForeignKey("debts.id"), nullable=False, index=True)

    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    qty: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)

    price_at_debt: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    cost_at_debt: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    line_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
