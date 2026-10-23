from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class TipoPedido(str, enum.Enum):
    EN_MESA = "EN_MESA"
    PARA_LLEVAR = "PARA_LLEVAR"
    DOMICILIO = "DOMICILIO"


class EstadoPedido(str, enum.Enum):
    BORRADOR_WEB = "BORRADOR_WEB"
    PENDIENTE = "PENDIENTE"
    EN_PREPARACION = "EN_PREPARACION"
    SERVIDO = "SERVIDO"
    PAGADO = "PAGADO"
    CANCELADO = "CANCELADO"


class CashClosureStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    NEQUI = "NEQUI"
    DAVIPLATA = "DAVIPLATA"
    CARD = "CARD"


class TipoItemStock(str, enum.Enum):
    SOPA = "SOPA"
    PRINCIPIO = "PRINCIPIO"
    ACOMPANAMIENTO = "ACOMPANAMIENTO"


class RolUsuario(str, enum.Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    MESERO = "MESERO"
    COCINA = "COCINA"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    nombre_completo = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    rol = Column(SQLEnum(RolUsuario), nullable=False, default=RolUsuario.MESERO)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True)
    orden = Column(Integer, default=0)

    platos = relationship("Plato", back_populates="categoria", cascade="all, delete-orphan")


class Plato(Base):
    __tablename__ = "platos"

    id = Column(Integer, primary_key=True, index=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    precio = Column(Float, nullable=False)
    imagen_emoji = Column(String(10), default="🥩")
    activo = Column(Boolean, default=True)

    categoria = relationship("Categoria", back_populates="platos")
    detalles_pedido = relationship("DetallePedido", back_populates="plato")


class Sopa(Base):
    __tablename__ = "sopas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True)
    activo = Column(Boolean, default=True)

    items_menu = relationship("MenuDiaItem", back_populates="sopa")
    detalles_pedido = relationship("DetallePedido", back_populates="sopa")


class Principio(Base):
    __tablename__ = "principios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True)
    activo = Column(Boolean, default=True)

    items_menu = relationship("MenuDiaItem", back_populates="principio")
    detalles_pedido = relationship("DetallePedido", back_populates="principio")


class Acompanamiento(Base):
    __tablename__ = "acompanamientos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True)
    activo = Column(Boolean, default=True)

    items_menu = relationship("MenuDiaItem", back_populates="acompanamiento")
    detalles_pedido = relationship("DetallePedido", back_populates="acompanamiento")


class MenuDia(Base):
    __tablename__ = "menu_dia"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, unique=True, index=True)
    notas = Column(String(255), nullable=True)
    activo = Column(Boolean, default=True)

    items = relationship("MenuDiaItem", back_populates="menu_dia", cascade="all, delete-orphan")


class MenuDiaItem(Base):
    __tablename__ = "menu_dia_items"

    id = Column(Integer, primary_key=True, index=True)
    menu_dia_id = Column(Integer, ForeignKey("menu_dia.id"), nullable=False)
    tipo_item = Column(SQLEnum(TipoItemStock), nullable=False)
    sopa_id = Column(Integer, ForeignKey("sopas.id"), nullable=True)
    principio_id = Column(Integer, ForeignKey("principios.id"), nullable=True)
    acompanamiento_id = Column(Integer, ForeignKey("acompanamientos.id"), nullable=True)
    cantidad_preparada = Column(Integer, default=0, nullable=False)
    cantidad_vendida = Column(Integer, default=0, nullable=False)

    menu_dia = relationship("MenuDia", back_populates="items")
    sopa = relationship("Sopa", back_populates="items_menu")
    principio = relationship("Principio", back_populates="items_menu")
    acompanamiento = relationship("Acompanamiento", back_populates="items_menu")

    @property
    def disponible(self) -> int:
        return max(0, (self.cantidad_preparada or 0) - (self.cantidad_vendida or 0))


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    codigo_pedido = Column(String(20), nullable=False, unique=True, index=True)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    cliente_nombre = Column(String(100), default="Cliente")
    cliente_telefono = Column(String(20), nullable=True)
    mesa = Column(String(20), nullable=True)
    tipo = Column(SQLEnum(TipoPedido), default=TipoPedido.EN_MESA)
    estado = Column(SQLEnum(EstadoPedido), default=EstadoPedido.PENDIENTE)
    subtotal = Column(Float, default=0.0)
    delivery_fee = Column(Float, default=0.0)
    packaging_fee = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    notas = Column(Text, nullable=True)

    detalles = relationship("DetallePedido", back_populates="pedido", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="pedido", cascade="all, delete-orphan")


class DetallePedido(Base):
    __tablename__ = "detalles_pedido"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    plato_id = Column(Integer, ForeignKey("platos.id"), nullable=False)
    sopa_id = Column(Integer, ForeignKey("sopas.id"), nullable=True)
    principio_id = Column(Integer, ForeignKey("principios.id"), nullable=True)
    acompanamiento_id = Column(Integer, ForeignKey("acompanamientos.id"), nullable=True)
    cantidad = Column(Integer, default=1, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    notas_item = Column(String(255), nullable=True)

    pedido = relationship("Pedido", back_populates="detalles")
    plato = relationship("Plato", back_populates="detalles_pedido")
    sopa = relationship("Sopa", back_populates="detalles_pedido")
    principio = relationship("Principio", back_populates="detalles_pedido")
    acompanamiento = relationship("Acompanamiento", back_populates="detalles_pedido")


class CashClosure(Base):
    __tablename__ = "cash_closures"

    id = Column(Integer, primary_key=True, index=True)
    opened_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(SQLEnum(CashClosureStatus), default=CashClosureStatus.OPEN, nullable=False)
    initial_cash = Column(Float, default=0.0, nullable=False)
    total_cash_sales = Column(Float, default=0.0)
    total_nequi_sales = Column(Float, default=0.0)
    total_daviplata_sales = Column(Float, default=0.0)
    total_card_sales = Column(Float, default=0.0)
    total_delivery_fees = Column(Float, default=0.0)
    total_delivery_payouts = Column(Float, default=0.0)
    total_expenses = Column(Float, default=0.0)
    expected_cash = Column(Float, default=0.0)
    counted_cash = Column(Float, nullable=True)
    discrepancy = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    payments = relationship("Payment", back_populates="cash_closure", cascade="all, delete-orphan")
    expenses = relationship("CashExpense", back_populates="cash_closure", cascade="all, delete-orphan")


class CashExpense(Base):
    __tablename__ = "cash_expenses"

    id = Column(Integer, primary_key=True, index=True)
    cash_closure_id = Column(Integer, ForeignKey("cash_closures.id"), nullable=False)
    description = Column(String(255), nullable=False)
    category = Column(String(50), default="INSUMOS", nullable=True)
    amount = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cash_closure = relationship("CashClosure", back_populates="expenses")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    cash_closure_id = Column(Integer, ForeignKey("cash_closures.id"), nullable=False)
    method = Column(SQLEnum(PaymentMethod), nullable=False)
    amount = Column(Float, nullable=False)
    change_given = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    pedido = relationship("Pedido", back_populates="payments")
    cash_closure = relationship("CashClosure", back_populates="payments")
