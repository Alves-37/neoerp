from datetime import datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class SupplierPayment(Base):
    __tablename__ = "supplier_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)

    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    purchase_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("supplier_purchases.id"), nullable=True, index=True)

    payment_date: Mapped[datetime | None] = mapped_column(Date, nullable=True, index=True)
    method: Mapped[str] = mapped_column(String(30), nullable=False, default="cash")

    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    reference: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
