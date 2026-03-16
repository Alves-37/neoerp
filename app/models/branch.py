from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    business_type: Mapped[str] = mapped_column(String(50), nullable=False, default="retail")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    public_menu_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    public_menu_subdomain: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    public_menu_custom_domain: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
