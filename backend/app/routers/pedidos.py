from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Union

from app.database import get_db
from app import schemas, crud, models

router = APIRouter(prefix="/api/pedidos", tags=["Pedidos"])


@router.post("/", response_model=schemas.PedidoOut)
def registrar_pedido(
    pedido_in: schemas.PedidoCreate,
    es_borrador_web: Optional[bool] = Query(
        default=None,
        description="Si es True, crea el pedido en estado BORRADOR_WEB sin descontar stock."
    ),
    db: Session = Depends(get_db)
):
    if not pedido_in.detalles:
        raise HTTPException(
            status_code=400,
            detail="El pedido debe incluir al menos un detalle de plato."
        )

    if es_borrador_web is not None:
        pedido_in.es_borrador_web = es_borrador_web

    nuevo_pedido = crud.crear_pedido(db, pedido_in)
    return nuevo_pedido


@router.get("/", response_model=List[schemas.PedidoOut])
def listar_pedidos(
    limit: int = 50,
    estado: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Pedido)
    if estado is not None and estado.strip() != "":
        clean_estado = estado.strip().upper()
        try:
            estado_val = models.EstadoPedido(clean_estado)
        except ValueError:
            estado_val = clean_estado
        query = query.filter(models.Pedido.estado == estado_val)
    pedidos = query.order_by(models.Pedido.fecha_hora.desc()).limit(limit).all()
    return pedidos


@router.post("/{pedido_id}/aprobar", response_model=schemas.PedidoOut)
def aprobar_pedido_borrador(
    pedido_id: int,
    datos_aprobacion: Optional[schemas.PedidoApprove] = Body(default=None),
    db: Session = Depends(get_db)
):
    """
    Permite al cajero aprobar un pedido en estado BORRADOR_WEB (creado desde la carta web),
    actualizar opcionalmente datos como cliente_telefono, delivery_fee, notas o ítems,
    cambiar su estado a PENDIENTE y descontar en ese momento el stock en MenuDiaItem.
    """
    try:
        pedido = crud.aprobar_pedido_borrador(db, pedido_id, datos_aprobacion)
        return pedido
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{pedido_id}/pagar", response_model=schemas.PedidoOut)
def pagar_pedido(
    pedido_id: int,
    payload: Union[List[schemas.PaymentCreate], schemas.PedidoPayRequest],
    db: Session = Depends(get_db)
):
    """
    Registra uno o varios pagos (pago único o mixto, ej. CASH + NEQUI) para un pedido,
    verifica que exista una caja OPEN en cash_closures, vincula los pagos a dicha caja
    y cambia el estado del pedido a PAGADO.
    """
    pagos_lista = (
        payload.payments
        if isinstance(payload, schemas.PedidoPayRequest)
        else payload
    )
    try:
        pedido = crud.pagar_pedido(db, pedido_id, pagos_lista)
        return pedido
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{pedido_id}/estado", response_model=schemas.PedidoOut)
def cambiar_estado_pedido(
    pedido_id: int,
    nuevo_estado: models.EstadoPedido,
    db: Session = Depends(get_db)
):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")
    
    pedido.estado = nuevo_estado
    db.commit()
    db.refresh(pedido)
    return pedido
