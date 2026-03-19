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
    capacity: int | None = None
    occupied_seats: int = 0


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


class PublicDistanceCheckoutItemCreate(BaseModel):
    produto_id: str
    quantidade: float = 1
    observacao: str | None = None


class PublicDistanceCheckoutCreate(BaseModel):
    tipo: str  # entrega|retirada
    cliente_nome: str
    cliente_telefone: str
    endereco_entrega: str | None = None
    taxa_entrega: float = 0
    bairro: str | None = None
    provider: str | None = None
    phone: str | None = None
    itens: list[PublicDistanceCheckoutItemCreate]


class PublicDistanceCheckoutOut(BaseModel):
    pedido_id: int
    pedido_uuid: str
    status: str


class PublicPedidoItemCreate(BaseModel):
    produto_id: str
    quantidade: float = 1
    observacao: str | None = None


class PublicPedidoCreate(BaseModel):
    mesa_id: int
    lugar_numero: int = 1
    observacao_cozinha: str | None = None
    payment_mode: str | None = None
    itens: list[PublicPedidoItemCreate]


class PublicPedidoCreatedOut(BaseModel):
    pedido_id: int
    pedido_uuid: str
    status: str


class PublicPedidoTrackItemOut(BaseModel):
    produto_nome: str | None = None
    quantidade: float
    subtotal: float


class PublicPedidoTrackOut(BaseModel):
    pedido_id: int
    pedido_uuid: str
    status: str
    updated_at: str | None = None
    valor_total: float = 0
    itens: list[PublicPedidoTrackItemOut] = []
