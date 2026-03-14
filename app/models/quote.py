from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    cashier_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    series: Mapped[str] = mapped_column(String(20), nullable=False, default="A", index=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)  # open|converted|cancelled

    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_nuit: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)

    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="MZN")

    net_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    tax_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    gross_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    sale_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sales.id"), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
