from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Optional
from datetime import date, datetime
from app.models import (
    TipoPedido,
    EstadoPedido,
    TipoItemStock,
    RolUsuario,
    CashClosureStatus,
    PaymentMethod,
)


# --- CATEGORÍAS & PLATOS ---

class CategoriaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    orden: int = 0

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaOut(CategoriaBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class PlatoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    imagen_emoji: str = "🥩"
    categoria_id: int
    activo: bool = True

class PlatoCreate(PlatoBase):
    pass

class PlatoOut(PlatoBase):
    id: int
    categoria: CategoriaOut
    model_config = ConfigDict(from_attributes=True)


# --- SOPAS, PRINCIPIOS Y ACOMPAÑAMIENTOS ---

class SopaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    activo: bool = True

class SopaOut(SopaBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class PrincipioBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    activo: bool = True

class PrincipioOut(PrincipioBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class AcompanamientoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    activo: bool = True

class AcompanamientoOut(AcompanamientoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# --- MENÚ DEL DÍA & CONTROL DE STOCK ---

class MenuDiaItemCreate(BaseModel):
    tipo_item: TipoItemStock
    sopa_id: Optional[int] = None
    principio_id: Optional[int] = None
    acompanamiento_id: Optional[int] = None
    cantidad_preparada: int = Field(ge=0, description="Cantidad inicial preparada")

class MenuDiaItemOut(BaseModel):
    id: int
    menu_dia_id: int
    tipo_item: TipoItemStock
    sopa_id: Optional[int] = None
    principio_id: Optional[int] = None
    acompanamiento_id: Optional[int] = None
    cantidad_preparada: int
    cantidad_vendida: int
    disponible: int
    sopa: Optional[SopaOut] = None
    principio: Optional[PrincipioOut] = None
    acompanamiento: Optional[AcompanamientoOut] = None

    model_config = ConfigDict(from_attributes=True)


class MenuDiaCreate(BaseModel):
    fecha: date
    notas: Optional[str] = None
    items: List[MenuDiaItemCreate] = []

class MenuDiaOut(BaseModel):
    id: int
    fecha: date
    notas: Optional[str] = None
    activo: bool
    items: List[MenuDiaItemOut] = []

    model_config = ConfigDict(from_attributes=True)


# --- PAGOS (PAYMENTS) ---

def _normalize_payment_method(v):
    if isinstance(v, str):
        val = v.strip().upper()
        if val in ("EFECTIVO", "CASH"):
            return PaymentMethod.CASH
        if val == "NEQUI":
            return PaymentMethod.NEQUI
        if val in ("BANCOLOMBIA", "QR", "AHORRO A LA MANO", "TRANSFERENCIA"):
            return PaymentMethod.BANCOLOMBIA
        if val == "DAVIPLATA":
            return PaymentMethod.DAVIPLATA
        if val in ("TARJETA", "DATAFONO", "DATÁFONO", "CARD"):
            return PaymentMethod.CARD
    return v


class PaymentCreate(BaseModel):
    method: PaymentMethod
    amount: float = Field(gt=0, description="Monto recibido en este método de pago")
    change_given: float = Field(default=0.0, ge=0, description="Vueltos entregados al cliente")

    @field_validator("method", mode="before")
    @classmethod
    def normalize_method(cls, v):
        return _normalize_payment_method(v)

class PaymentOut(BaseModel):
    id: int
    pedido_id: int
    cash_closure_id: int
    method: PaymentMethod
    amount: float
    change_given: float = 0.0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PedidoPayRequest(BaseModel):
    payments: List[PaymentCreate]


# --- PEDIDOS & DETALLES ---

class DetallePedidoCreate(BaseModel):
    plato_id: Optional[int] = 1
    nombre_plato: Optional[str] = None
    precio_unitario: Optional[float] = None
    sopa_id: Optional[int] = None
    principio_id: Optional[int] = None
    acompanamiento_id: Optional[int] = None
    cantidad: int = 1
    notas_item: Optional[str] = None
    notas: Optional[str] = None

class DetallePedidoOut(BaseModel):
    id: int
    plato_id: int
    sopa_id: Optional[int] = None
    principio_id: Optional[int] = None
    acompanamiento_id: Optional[int] = None
    cantidad: int
    precio_unitario: float
    notas_item: Optional[str] = None
    plato: PlatoOut
    sopa: Optional[SopaOut] = None
    principio: Optional[PrincipioOut] = None
    acompanamiento: Optional[AcompanamientoOut] = None

    model_config = ConfigDict(from_attributes=True)


class PedidoCreate(BaseModel):
    cliente_nombre: str = "Cliente"
    cliente_telefono: Optional[str] = None
    direccion: Optional[str] = None
    mesa: Optional[str] = None
    tipo: TipoPedido = TipoPedido.EN_MESA
    estado: Optional[EstadoPedido] = None
    courier_name: Optional[str] = None
    subtotal: Optional[float] = None
    delivery_fee: float = 0.0
    packaging_fee: float = 0.0
    total: Optional[float] = None
    es_borrador_web: bool = False
    notas: Optional[str] = None
    detalles: List[DetallePedidoCreate]

    @field_validator("tipo", mode="before")
    @classmethod
    def normalize_tipo(cls, v):
        if isinstance(v, str):
            val = v.strip().upper()
            if val in ("MESA", "EN_MESA"):
                return TipoPedido.EN_MESA
            if val in ("LLEVAR", "PARA_LLEVAR"):
                return TipoPedido.PARA_LLEVAR
            if val == "DOMICILIO":
                return TipoPedido.DOMICILIO
        return v


class PedidoApprove(BaseModel):
    cliente_nombre: Optional[str] = None
    cliente_telefono: Optional[str] = None
    mesa: Optional[str] = None
    tipo: Optional[TipoPedido] = None
    courier_name: Optional[str] = None
    delivery_fee: Optional[float] = None
    packaging_fee: Optional[float] = None
    notas: Optional[str] = None
    detalles: Optional[List[DetallePedidoCreate]] = None


class PedidoAssignCourier(BaseModel):
    courier_name: Optional[str] = None
    estado: Optional[EstadoPedido] = None


class PedidoUpdatePaymentMethod(BaseModel):
    method: Optional[PaymentMethod] = None
    payment_method: Optional[PaymentMethod] = None
    payments: Optional[List[PaymentCreate]] = None
    cliente_nombre: Optional[str] = None
    cliente_telefono: Optional[str] = None
    mesa: Optional[str] = None
    courier_name: Optional[str] = None
    delivery_fee: Optional[float] = None
    packaging_fee: Optional[float] = None
    notas: Optional[str] = None
    estado: Optional[EstadoPedido] = None

    @field_validator("method", "payment_method", mode="before")
    @classmethod
    def normalize_method(cls, v):
        if v is None or v == "":
            return None
        return _normalize_payment_method(v)


class PedidoUpdate(BaseModel):
    cliente_nombre: Optional[str] = None
    cliente_telefono: Optional[str] = None
    direccion: Optional[str] = None
    mesa: Optional[str] = None
    tipo: Optional[TipoPedido] = None
    estado: Optional[EstadoPedido] = None
    courier_name: Optional[str] = None
    subtotal: Optional[float] = None
    delivery_fee: Optional[float] = None
    packaging_fee: Optional[float] = None
    total: Optional[float] = None
    notas: Optional[str] = None
    detalles: Optional[List[DetallePedidoCreate]] = None


class PedidoOut(BaseModel):
    id: int
    codigo_pedido: str
    fecha_hora: datetime
    created_at: Optional[datetime] = None
    cliente_nombre: str
    cliente_telefono: Optional[str] = None
    mesa: Optional[str] = None
    tipo: TipoPedido
    estado: EstadoPedido
    courier_name: Optional[str] = None
    subtotal: float = 0.0
    delivery_fee: float = 0.0
    packaging_fee: float = 0.0
    total: float
    notas: Optional[str] = None
    detalles: List[DetallePedidoOut] = []
    payments: List[PaymentOut] = []

    model_config = ConfigDict(from_attributes=True)


# --- CIERRES DE CAJA (CASH CLOSURES) ---

class CashClosureOpen(BaseModel):
    initial_cash: float = Field(default=0.0, ge=0, description="Base de efectivo inicial al abrir caja")
    notes: Optional[str] = None

class CashExpenseCreate(BaseModel):
    description: str = Field(min_length=1, max_length=255, description="Concepto del gasto menor")
    amount: float = Field(gt=0, description="Monto en efectivo sacado de la caja")
    category: Optional[str] = Field(default="INSUMOS", max_length=50, description="Categoría opcional (INSUMOS, SERVICIOS, OTROS)")


class CashExpenseOut(BaseModel):
    id: int
    cash_closure_id: int
    description: str
    category: Optional[str] = "INSUMOS"
    amount: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CashClosureClose(BaseModel):
    counted_cash: float = Field(ge=0, description="Efectivo total contado físicamente en caja")
    notes: Optional[str] = None

class CashClosureOut(BaseModel):
    id: int
    opened_at: datetime
    closed_at: Optional[datetime] = None
    status: CashClosureStatus
    initial_cash: float
    total_cash_sales: float = 0.0
    total_nequi_sales: float = 0.0
    total_bancolombia_sales: float = 0.0
    total_daviplata_sales: float = 0.0
    total_transfer_sales: float = 0.0
    total_card_sales: float = 0.0
    total_delivery_fees: float = 0.0
    total_delivery_payouts: float = 0.0
    total_expenses: float = 0.0
    subtotal_sales: float = 0.0
    total_sales: float = 0.0
    expected_cash: float = 0.0
    counted_cash: Optional[float] = None
    discrepancy: Optional[float] = None
    notes: Optional[str] = None
    payments: List[PaymentOut] = []
    expenses: List[CashExpenseOut] = []

    model_config = ConfigDict(from_attributes=True)


# --- MÉTRICAS DE INVENTARIO Y DEPARTE DIARIO ---

class MetricaItemStock(BaseModel):
    id: int
    nombre: str
    tipo: TipoItemStock
    preparado: int
    vendido: int
    disponible: int
    porcentaje_consumido: float
    alerta_agotamiento: bool

class MetricasDiaOut(BaseModel):
    fecha: date
    total_pedidos: int
    total_ventas: float
    sopas_metricas: List[MetricaItemStock] = []
    principios_metricas: List[MetricaItemStock] = []
    acompanamientos_metricas: List[MetricaItemStock] = []
    plato_mas_vendido: Optional[str] = None


class TopPlatoOut(BaseModel):
    product_name: str
    sold_count: int
    total_revenue: float


class DashboardStatsOut(BaseModel):
    todaySales: float = 0.0
    cashSales: float = 0.0
    digitalSales: float = 0.0
    transferSales: float = 0.0
    nequiSales: float = 0.0
    bancolombiaSales: float = 0.0
    daviplataSales: float = 0.0
    cardSales: float = 0.0
    todayOrderCount: int = 0
    totalCustomers: int = 0
    topDishes: List[TopPlatoOut] = []


# --- USUARIOS & AUTENTICACIÓN ---

class UsuarioBase(BaseModel):
    username: str
    nombre_completo: str
    rol: RolUsuario = RolUsuario.MESERO

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioOut(UsuarioBase):
    id: int
    activo: bool
    fecha_creacion: datetime
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
