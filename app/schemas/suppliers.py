from datetime import date, datetime

from pydantic import BaseModel


class SupplierBase(BaseModel):
    name: str
    nuit: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: str | None = None
    nuit: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None


class SupplierOut(SupplierBase):
    id: int
    company_id: int
    branch_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SupplierPurchaseBase(BaseModel):
    supplier_id: int
    doc_ref: str | None = None
    purchase_date: date | None = None
    currency: str = "MZN"
    total: float = 0
    status: str = "open"
    notes: str | None = None


class SupplierPurchaseCreate(SupplierPurchaseBase):
    pass


class SupplierPurchaseUpdate(BaseModel):
    doc_ref: str | None = None
    purchase_date: date | None = None
    currency: str | None = None
    total: float | None = None
    status: str | None = None
    notes: str | None = None


class SupplierPurchaseOut(SupplierPurchaseBase):
    id: int
    company_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SupplierPaymentBase(BaseModel):
    supplier_id: int
    purchase_id: int | None = None
    payment_date: date | None = None
    method: str = "cash"
    amount: float = 0
    reference: str | None = None
    notes: str | None = None


class SupplierPaymentCreate(SupplierPaymentBase):
    pass


class SupplierPaymentUpdate(BaseModel):
    purchase_id: int | None = None
    payment_date: date | None = None
    method: str | None = None
    amount: float | None = None
    reference: str | None = None
    notes: str | None = None


class SupplierPaymentOut(SupplierPaymentBase):
    id: int
    company_id: int
    created_at: datetime

    class Config:
        from_attributes = True
