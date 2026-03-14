from datetime import datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class SupplierPurchase(Base):
    __tablename__ = "supplier_purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)

    doc_ref: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    purchase_date: Mapped[datetime | None] = mapped_column(Date, nullable=True, index=True)

    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="MZN")
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)

    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
