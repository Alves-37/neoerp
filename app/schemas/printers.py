from datetime import date, datetime

from pydantic import BaseModel


class PrinterBase(BaseModel):
    serial_number: str
    brand: str | None = None
    model: str | None = None
    initial_counter: int = 0
    installation_date: date | None = None
    is_active: bool = True


class PrinterCreate(PrinterBase):
    establishment_id: int | None = None


class PrinterUpdate(BaseModel):
    serial_number: str | None = None
    brand: str | None = None
    model: str | None = None
    initial_counter: int | None = None
    installation_date: date | None = None
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


class PrinterBillingLineOut(BaseModel):
    printer_id: int
    counter_type_id: int
    counter_type_code: str | None = None
    counter_type_name: str | None = None

    start_reading_date: datetime | None = None
    start_counter_value: int | None = None
    end_reading_date: datetime | None = None
    end_counter_value: int | None = None

    pages_used: int = 0
    monthly_allowance: int = 0
    excess_pages: int = 0
    price_per_page: float = 0
    excess_total: float = 0


class PrinterBillingPrinterOut(BaseModel):
    printer_id: int
    serial_number: str | None = None
    brand: str | None = None
    model: str | None = None
    lines: list[PrinterBillingLineOut] = []
    total_excess_pages: int = 0
    total_excess_amount: float = 0


class PrinterBillingOut(BaseModel):
    year: int
    month: int
    company_id: int
    branch_id: int
    establishment_id: int
    printers: list[PrinterBillingPrinterOut] = []
    total_excess_pages: int = 0
    total_excess_amount: float = 0


class PrinterBillingGenerateLaunchPayload(BaseModel):
    year: int
    month: int
    establishment_id: int | None = None
    include_zero: bool = False


class PrinterBillingGenerateLaunchOut(BaseModel):
    ok: bool = True
    sale_id: int
    total: float


# PDV3-like billing (single-counter, delta from registry)
class PrinterPdv3BillingRowOut(BaseModel):
    printer_id: int
    serial_number: str
    brand: str | None = None
    model: str | None = None
    month: int
    year: int
    month_year: str
    copies_total: int = 0
    copies_billed_to: int = 0
    copies_new: int = 0
    has_launch: bool = False


class PrinterPdv3BillingOut(BaseModel):
    month: int
    year: int
    company_id: int
    branch_id: int
    establishment_id: int
    rows: list[PrinterPdv3BillingRowOut] = []
    total_copies: int = 0
    total_printers: int = 0


class PrinterPdv3GenerateLaunchPayload(BaseModel):
    printer_id: int
    month: int
    year: int
    establishment_id: int | None = None
    price_per_copy: float
    cost_per_copy: float = 0


class PrinterPdv3GenerateLaunchOut(BaseModel):
    ok: bool = True
    sale_id: int
    total: float
    copies_new: int
    copies_billed_to: int


class PrinterPdv3ReadingCreate(BaseModel):
    printer_id: int
    reading_date: datetime
    counter_value: int
    establishment_id: int | None = None


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
