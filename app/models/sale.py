from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    cashier_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    cash_session_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("cash_sessions.id"), nullable=True, index=True)
    business_type: Mapped[str] = mapped_column(String(50), nullable=False, default="retail", index=True)

    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    net_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    tax_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    include_tax: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    paid: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    change: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    payment_method: Mapped[str] = mapped_column(String(30), nullable=False, default="cash")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="paid", index=True)

    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    voided_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    void_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    sale_channel: Mapped[str] = mapped_column(String(20), nullable=False, default="counter", index=True)
    table_number: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    seat_number: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
