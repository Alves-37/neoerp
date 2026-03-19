from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Printer(Base):
    __tablename__ = "printers"
    __table_args__ = (
        UniqueConstraint("company_id", "branch_id", "establishment_id", "serial_number", name="uq_printers_scope_serial"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    establishment_id: Mapped[int] = mapped_column(Integer, ForeignKey("establishments.id"), nullable=False, index=True)

    serial_number: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    brand: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # PDV3 compatibility
    initial_counter: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    installation_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PrinterSaleLine(Base):
    __tablename__ = "printer_sale_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    sale_id: Mapped[int] = mapped_column(Integer, ForeignKey("sales.id"), nullable=False, index=True)
    printer_id: Mapped[int] = mapped_column(Integer, ForeignKey("printers.id"), nullable=False, index=True)
    counter_type_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("printer_counter_types.id"),
        nullable=True,
        index=True,
    )

    copies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    line_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PrinterBillingRegistry(Base):
    __tablename__ = "printer_billing_registry"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "branch_id",
            "establishment_id",
            "printer_id",
            "year",
            "month",
            name="uq_printer_billing_registry_scope_unique",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    establishment_id: Mapped[int] = mapped_column(Integer, ForeignKey("establishments.id"), nullable=False, index=True)
    printer_id: Mapped[int] = mapped_column(Integer, ForeignKey("printers.id"), nullable=False, index=True)

    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    copies_to: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PrinterCounterType(Base):
    __tablename__ = "printer_counter_types"
    __table_args__ = (
        UniqueConstraint("company_id", "branch_id", "establishment_id", "code", name="uq_printer_counter_types_scope_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    establishment_id: Mapped[int] = mapped_column(Integer, ForeignKey("establishments.id"), nullable=False, index=True)

    # Examples: A4_PB, A4_COLOR, A3_PB, A3_COLOR
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PrinterContract(Base):
    __tablename__ = "printer_contracts"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "branch_id",
            "establishment_id",
            "printer_id",
            "counter_type_id",
            name="uq_printer_contracts_scope_printer_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    establishment_id: Mapped[int] = mapped_column(Integer, ForeignKey("establishments.id"), nullable=False, index=True)

    printer_id: Mapped[int] = mapped_column(Integer, ForeignKey("printers.id"), nullable=False, index=True)
    counter_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("printer_counter_types.id"), nullable=False, index=True)

    monthly_allowance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price_per_page: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PrinterReading(Base):
    __tablename__ = "printer_readings"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "branch_id",
            "establishment_id",
            "printer_id",
            "counter_type_id",
            "reading_date",
            name="uq_printer_readings_scope_unique",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    establishment_id: Mapped[int] = mapped_column(Integer, ForeignKey("establishments.id"), nullable=False, index=True)

    printer_id: Mapped[int] = mapped_column(Integer, ForeignKey("printers.id"), nullable=False, index=True)
    counter_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("printer_counter_types.id"), nullable=False, index=True)

    reading_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    counter_value: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
