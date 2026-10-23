from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

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
