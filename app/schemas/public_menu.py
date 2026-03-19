from pydantic import BaseModel


class PublicMenuCategoryOut(BaseModel):
    id: int
    name: str


class PublicMenuProductOut(BaseModel):
    id: int
    name: str
    price: float
    is_daily_dish: bool = False
    promo_enabled: bool = False
    promo_price: float | None = None
    category_id: int | None = None
    image_url: str | None = None


class PublicMenuOut(BaseModel):
    branch_id: int
    branch_name: str
    categories: list[PublicMenuCategoryOut] = []
    products: list[PublicMenuProductOut] = []


class PublicMesaOut(BaseModel):
    id: int
    numero: int


class PublicOrderItemCreate(BaseModel):
    product_id: int
    qty: float = 1


class PublicOrderCreate(BaseModel):
    table_number: int
    seat_number: int
    items: list[PublicOrderItemCreate]


class PublicOrderCreatedOut(BaseModel):
    order_id: int
    status: str
