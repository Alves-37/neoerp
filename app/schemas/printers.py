from datetime import datetime

from pydantic import BaseModel


class PrinterBase(BaseModel):
    serial_number: str
    brand: str | None = None
    model: str | None = None
    is_active: bool = True


class PrinterCreate(PrinterBase):
    establishment_id: int | None = None


class PrinterUpdate(BaseModel):
    serial_number: str | None = None
    brand: str | None = None
    model: str | None = None
    is_active: bool | None = None


class PrinterOut(PrinterBase):
    id: int
    company_id: int
    branch_id: int
    establishment_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PrinterCounterTypeBase(BaseModel):
    code: str
    name: str
    is_active: bool = True


class PrinterCounterTypeCreate(PrinterCounterTypeBase):
    establishment_id: int | None = None


class PrinterCounterTypeUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    is_active: bool | None = None


class PrinterCounterTypeOut(PrinterCounterTypeBase):
    id: int
    company_id: int
    branch_id: int
    establishment_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PrinterContractBase(BaseModel):
    printer_id: int
    counter_type_id: int
    monthly_allowance: int = 0
    price_per_page: float = 0
    is_active: bool = True


class PrinterContractCreate(PrinterContractBase):
    establishment_id: int | None = None


class PrinterContractUpdate(BaseModel):
    monthly_allowance: int | None = None
    price_per_page: float | None = None
    is_active: bool | None = None


class PrinterContractOut(PrinterContractBase):
    id: int
    company_id: int
    branch_id: int
    establishment_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PrinterReadingBase(BaseModel):
    printer_id: int
    counter_type_id: int
    reading_date: datetime
    counter_value: int


class PrinterReadingCreate(PrinterReadingBase):
    establishment_id: int | None = None


class PrinterReadingOut(PrinterReadingBase):
    id: int
    company_id: int
    branch_id: int
    establishment_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
