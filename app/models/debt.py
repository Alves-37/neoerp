from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Debt(Base):
    __tablename__ = "debts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    cashier_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    customer_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_nuit: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)

    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="MZN")

    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    net_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    tax_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    include_tax: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open", index=True)  # open|paid|cancelled

    sale_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sales.id"), nullable=True, index=True)

    # Origem (ex.: faturamento de impressoras / PDV3)
    origin_source: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    origin_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    origin_meta: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
