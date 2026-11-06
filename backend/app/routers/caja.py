from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, List, Optional, Union
import traceback

from app.database import get_db
from app import schemas, crud

router = APIRouter(prefix="/api/caja", tags=["Caja y Cierres (Cash Closures)"])


@router.post("/open", response_model=schemas.CashClosureOut)
def abrir_caja(
    open_in: schemas.CashClosureOpen,
    db: Session = Depends(get_db)
):
    """
    Abre una nueva sesión de caja en cash_closures con initial_cash,
    verificando que no exista otra caja en estado OPEN.
    """
    try:
        nueva_caja = crud.open_cash_closure(db, open_in)
        return crud.calcular_resumen_caja(db, nueva_caja)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/active", response_model=Optional[schemas.CashClosureOut])
def obtener_caja_activa(db: Session = Depends(get_db)):
    """
    Devuelve la sesión de caja OPEN actual junto con el resumen en tiempo real
    por método de pago (CASH, NEQUI, DAVIPLATA, CARD), subtotal (ventas restaurante),
    total_delivery_payouts (pagos en efectivo a domiciliarios) y
    expected_cash = initial_cash + total_cash_sales - total_delivery_payouts.
    """
    activa = crud.get_active_cash_closure(db)
    if not activa:
        return None
    resumen = crud.calcular_resumen_caja(db, activa)
    db.commit()
    return resumen


@router.patch("/active/initial-cash", response_model=schemas.CashClosureOut)
@router.post("/active/initial-cash", response_model=schemas.CashClosureOut)
def corregir_base_inicial(
    payload: schemas.CashClosureInitialCashUpdate,
    db: Session = Depends(get_db)
):
    """
    Corrige administrativamente la base inicial (initial_cash) de la caja activa (OPEN)
    y recalcula inmediatamente el expected_cash oficial:
    expected_cash = initial_cash + total_cash_sales - total_delivery_payouts - total_expenses
    """
    try:
        return crud.update_active_cash_closure_initial_cash(db, payload.initial_cash)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/close", response_model=schemas.CashClosureOut)
def cerrar_caja(
    close_in: schemas.CashClosureClose,
    db: Session = Depends(get_db)
):
    """
    Cierra la caja OPEN actual recibiendo counted_cash y notes.
    Calcula totales finales por método de pago,
    expected_cash = initial_cash + total_cash_sales - total_delivery_payouts,
    discrepancy = counted_cash - expected_cash, y cambia el estado a CLOSED.
    """
    try:
        return crud.close_cash_closure(db, close_in)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", response_model=List[schemas.CashClosureOut])
def listar_historial_cajas(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Lista el historial de sesiones/cierres de caja ordenados del más reciente al más antiguo.
    """
    return crud.list_cash_closures_history(db, limit=limit)


@router.post("/expenses", response_model=schemas.CashExpenseOut)
def registrar_gasto_caja(
    expense_in: schemas.CashExpenseCreate,
    db: Session = Depends(get_db)
):
    """
    Registra una salida de dinero en efectivo de la caja activa actual (ej. compra de verduras, agua, insumos).
    """
    activa = crud.get_active_cash_closure(db)
    if not activa:
        raise HTTPException(
            status_code=400,
            detail="No hay una caja abierta (OPEN) para registrar gastos. Abre caja primero."
        )
    gasto = crud.create_cash_expense(db, activa.id, expense_in)
    return gasto


@router.get("/expenses", response_model=List[schemas.CashExpenseOut])
def listar_gastos_caja_activa(db: Session = Depends(get_db)):
    """
    Lista los gastos en efectivo registrados en el turno de caja actual.
    """
    activa = crud.get_active_cash_closure(db)
    if not activa:
        return []
    return crud.get_cash_expenses(db, activa.id)


@router.post("/pay/{pedido_id}")
def pagar_pedido_en_caja(
    pedido_id: int,
    payload: Union[schemas.PedidoPayRequest, List[schemas.PaymentCreate], schemas.PaymentCreate, dict] = Body(...),
    db: Session = Depends(get_db),
):
    """
    Registra el pago de un pedido directamente en la caja activa (CASH, NEQUI, BANCOLOMBIA, DAVIPLATA, CARD, FIADO o mixto),
    vincula el pedido al cash_closure_id abierto, cambia su estado a ENTREGADO y estado_pago a PAGADO,
    libera formalmente la mesa y opcionalmente encola la tirilla de cliente en impresion.py.
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
        impreso_cocina_val = None

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
            if payload.impreso_cocina is not None:
                impreso_cocina_val = bool(payload.impreso_cocina)
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
            if "impreso_cocina" in payload and payload["impreso_cocina"] is not None:
                impreso_cocina_val = bool(payload["impreso_cocina"])
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
            impreso_cocina=impreso_cocina_val,
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


@router.patch("/payment-method/{pedido_id}", response_model=schemas.PedidoOut)
@router.post("/payment-method/{pedido_id}", response_model=schemas.PedidoOut)
def cambiar_metodo_pago_en_caja(
    pedido_id: int,
    payload: schemas.PedidoUpdatePaymentMethod,
    db: Session = Depends(get_db),
):
    """
    Actualiza el medio de pago de un pedido ya cobrado y recalcula inmediatamente la sesión de caja activa.
    """
    try:
        return crud.cambiar_metodo_pago_pedido(db, pedido_id, payload)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats", response_model=schemas.DashboardStatsOut)
def obtener_metricas_dashboard_caja(db: Session = Depends(get_db)):
    """
    Devuelve las métricas en tiempo real para el panel de Administración (/admin).
    """
    return crud.obtener_estadisticas_dashboard(db)
