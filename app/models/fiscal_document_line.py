from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class FiscalDocumentLine(Base):
    __tablename__ = "fiscal_document_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    fiscal_document_id: Mapped[int] = mapped_column(Integer, ForeignKey("fiscal_documents.id"), nullable=False, index=True)

    product_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)

    qty: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    line_net: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    tax_rate: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    line_tax: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    line_gross: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
