from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Union
import traceback

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


@router.post("/mesa-append", response_model=schemas.PedidoOut)
def anexar_platos_a_mesa(
    pedido_in: schemas.PedidoCreate,
    db: Session = Depends(get_db)
):
    """
    Anexa nuevos platos al pedido abierto existente de una mesa o crea uno nuevo si la mesa está libre.
    """
    if not pedido_in.detalles:
        raise HTTPException(
            status_code=400,
            detail="Debe incluir al menos un detalle de plato para agregar a la mesa."
        )
    return crud.crear_pedido(db, pedido_in)


@router.get("/stats/dashboard", response_model=schemas.DashboardStatsOut)
def obtener_estadisticas_dashboard(db: Session = Depends(get_db)):
    """
    Devuelve las métricas consolidadas en tiempo real para /admin (ventas hoy/turno,
    efectivo vs digital, comandas pagadas, clientes y ranking de platos más vendidos).
    """
    return crud.obtener_estadisticas_dashboard(db)


@router.get("/especiales-dia", response_model=schemas.DailySpecialsConfigOut)
def obtener_especiales_dia_en_pedidos(db: Session = Depends(get_db)):
    return crud.get_daily_specials_config(db)


@router.put("/especiales-dia", response_model=schemas.DailySpecialsConfigOut)
@router.post("/especiales-dia", response_model=schemas.DailySpecialsConfigOut)
def actualizar_especiales_dia_en_pedidos(
    payload: schemas.DailySpecialsConfigUpdate,
    db: Session = Depends(get_db),
):
    return crud.update_daily_specials_config(db, payload)


@router.post("/liquidar-fiado")
def liquidar_fiado_en_pedidos(
    payload: schemas.LiquidarFiadoRequest,
    db: Session = Depends(get_db),
):
    try:
        return crud.liquidar_fiado_cliente(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[schemas.PedidoOut])
def listar_pedidos(
    limit: int = 200,
    estado: Optional[str] = None,
    tipo: Optional[str] = None,
    mesa: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Pedido)
    if estado is not None and estado.strip() != "":
        parts = [p.strip().upper() for p in estado.split(",") if p.strip()]
        if len(parts) == 1:
            try:
                estado_val = models.EstadoPedido(parts[0])
            except ValueError:
                estado_val = parts[0]
            query = query.filter(models.Pedido.estado == estado_val)
        elif len(parts) > 1:
            vals = []
            for p in parts:
                try:
                    vals.append(models.EstadoPedido(p))
                except ValueError:
                    vals.append(p)
            query = query.filter(models.Pedido.estado.in_(vals))

    if tipo is not None and tipo.strip() != "":
        clean_tipo = tipo.strip().upper()
        try:
            tipo_val = models.TipoPedido(clean_tipo)
        except ValueError:
            tipo_val = clean_tipo
        query = query.filter(models.Pedido.tipo == tipo_val)

    if mesa is not None and mesa.strip() != "":
        query = query.filter(models.Pedido.mesa == mesa.strip())

    pedidos = query.order_by(models.Pedido.fecha_hora.desc()).limit(limit).all()
    return pedidos


@router.get("/{pedido_id}", response_model=schemas.PedidoOut)
def obtener_pedido_por_id(
    pedido_id: int,
    db: Session = Depends(get_db)
):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")
    return pedido


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


@router.post("/{pedido_id}/pagar")
def pagar_pedido(
    pedido_id: int,
    payload: Union[schemas.PedidoPayRequest, List[schemas.PaymentCreate], schemas.PaymentCreate, dict] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Registra uno o varios pagos (pago único o mixto, ej. CASH, NEQUI, BANCOLOMBIA, DAVIPLATA, CARD, FIADO) para un pedido,
    vincula los pagos a la caja activa, actualiza estado_pago='PAGADO' y estado='ENTREGADO', libera la mesa
    y opcionalmente encola la tirilla de cliente en impresion.py.
    """
    try:
        pagos_lista = None
        creado_por_val = None
        cant_dom_val = None
        estado_val = None
        metodo_pago_val = None
        imprimir_recibo_val = False
        cliente_nombre_val = None
        cliente_telefono_val = None

        if isinstance(payload, schemas.PedidoPayRequest):
            pagos_lista = payload.payments
            creado_por_val = payload.creado_por
            cant_dom_val = payload.cantidad_domicilios
            estado_val = payload.estado
            raw_m = payload.metodo_pago or payload.payment_method or payload.method
            if raw_m:
                metodo_pago_val = str(raw_m).strip().upper()
            imprimir_recibo_val = bool(payload.imprimir_recibo)
            cliente_nombre_val = payload.cliente_nombre
            cliente_telefono_val = payload.cliente_telefono
        elif isinstance(payload, list):
            pagos_lista = payload
        elif isinstance(payload, schemas.PaymentCreate):
            pagos_lista = [payload]
            if payload.method:
                m_str = payload.method.value if hasattr(payload.method, "value") else str(payload.method)
                metodo_pago_val = m_str.strip().upper()
        elif isinstance(payload, dict):
            raw_m = payload.get("metodo_pago") or payload.get("payment_method") or payload.get("method")
            if raw_m:
                metodo_pago_val = str(raw_m).strip().upper()
            imprimir_recibo_val = bool(payload.get("imprimir_recibo", False))
            creado_por_val = payload.get("creado_por")
            cant_dom_val = payload.get("cantidad_domicilios")
            estado_val = payload.get("estado")
            cliente_nombre_val = payload.get("cliente_nombre")
            cliente_telefono_val = payload.get("cliente_telefono")
            if payload.get("payments"):
                pagos_lista = [
                    p if isinstance(p, schemas.PaymentCreate) else schemas.PaymentCreate(**p)
                    for p in payload["payments"]
                ]

        pedido = crud.pagar_pedido(
            db,
            pedido_id,
            pagos_lista,
            creado_por=creado_por_val,
            cantidad_domicilios=cant_dom_val,
            nuevo_estado=estado_val,
            metodo_pago=metodo_pago_val,
            imprimir_recibo=imprimir_recibo_val,
            cliente_nombre=cliente_nombre_val,
            cliente_telefono=cliente_telefono_val,
        )
        out_data = schemas.PedidoOut.model_validate(pedido).model_dump(mode="json")
        out_data["status"] = "success"
        out_data["pedido_id"] = pedido.id
        out_data["mesa_liberada"] = True
        return out_data
    except LookupError as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al procesar el cobro del pedido #{pedido_id}: {str(e)}")


@router.patch("/{pedido_id}/assign-courier", response_model=schemas.PedidoOut)
@router.post("/{pedido_id}/assign-courier", response_model=schemas.PedidoOut)
def asignar_mensajero_pedido(
    pedido_id: int,
    payload: schemas.PedidoAssignCourier,
    db: Session = Depends(get_db),
):
    """
    Permite asignar o cambiar el `courier_name` de un domicilio y opcionalmente
    actualizar su estado (ej. EN_PREPARACION -> EN_CAMINO / ENTREGADO).
    """
    try:
        return crud.asignar_mensajero_pedido(db, pedido_id, payload)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{pedido_id}/payment-method", response_model=schemas.PedidoOut)
@router.post("/{pedido_id}/payment-method", response_model=schemas.PedidoOut)
def cambiar_metodo_pago_pedido(
    pedido_id: int,
    payload: schemas.PedidoUpdatePaymentMethod,
    db: Session = Depends(get_db),
):
    """
    Permite al administrador cambiar el método de pago de un pedido (ej. CASH -> BANCOLOMBIA / NEQUI / CARD),
    editar datos del pedido o anularlo (estado=CANCELADO), recalculando de inmediato la sesión de caja activa.
    """
    try:
        return crud.cambiar_metodo_pago_pedido(db, pedido_id, payload)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{pedido_id}", response_model=schemas.PedidoOut)
@router.put("/{pedido_id}", response_model=schemas.PedidoOut)
def actualizar_pedido(
    pedido_id: int,
    payload: schemas.PedidoUpdate,
    db: Session = Depends(get_db),
):
    """
    Permite actualizar un pedido abierto (agregar/modificar platos de una mesa desde POS)
    o editar los datos de un pedido desde Administración.
    """
    try:
        return crud.actualizar_pedido(db, pedido_id, payload)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{pedido_id}/estado", response_model=schemas.PedidoOut)
@router.put("/{pedido_id}/estado", response_model=schemas.PedidoOut)
@router.post("/{pedido_id}/estado", response_model=schemas.PedidoOut)
def cambiar_estado_pedido(
    pedido_id: int,
    nuevo_estado: Optional[models.EstadoPedido] = Query(default=None),
    body_data: Optional[dict] = Body(default=None),
    db: Session = Depends(get_db)
):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")

    target_estado = nuevo_estado
    if target_estado is None and isinstance(body_data, dict):
        raw_est = body_data.get("nuevo_estado") or body_data.get("estado")
        if raw_est:
            target_estado = models.EstadoPedido(str(raw_est).strip().upper())

    if target_estado is None:
        raise HTTPException(status_code=400, detail="Debe especificar nuevo_estado.")

    pedido.estado = target_estado
    if target_estado == models.EstadoPedido.CANCELADO:
        pagos_exist = db.query(models.Payment).filter(models.Payment.pedido_id == pedido.id).all()
        closure_ids = {p.cash_closure_id for p in pagos_exist if p.cash_closure_id}
        for p in pagos_exist:
            db.delete(p)
        db.flush()
        activa = crud.get_active_cash_closure(db)
        if activa:
            closure_ids.add(activa.id)
        for cid in closure_ids:
            c = db.query(models.CashClosure).filter(models.CashClosure.id == cid).first()
            if c:
                crud.calcular_resumen_caja(db, c)

    db.commit()
    db.refresh(pedido)
    return pedido
