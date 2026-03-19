from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    business_type: Mapped[str] = mapped_column(String(50), nullable=False, default="restaurant", index=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open", index=True)

    # public tracking id for menu
    order_uuid: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # table|delivery
    order_type: Mapped[str] = mapped_column(String(20), nullable=False, default="table", index=True)

    # delivery metadata (optional)
    delivery_kind: Mapped[str | None] = mapped_column(String(20), nullable=True)  # entrega|retirada
    customer_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    customer_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    delivery_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    delivery_zone_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    delivery_fee: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    table_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    seat_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )
