from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import schemas, crud

router = APIRouter(prefix="/api/mensajeros", tags=["Mensajeros / Domiciliarios"])


@router.get("", response_model=List[schemas.MensajeroOut])
@router.get("/", response_model=List[schemas.MensajeroOut])
def listar_mensajeros(
    incluir_inactivos: bool = Query(default=False, description="Incluir mensajeros inactivos para panel de administración"),
    db: Session = Depends(get_db)
):
    """
    Lista todos los mensajeros registrados.
    Por defecto devuelve solo los activos. Con incluir_inactivos=true devuelve el catálogo completo.
    """
    return crud.list_mensajeros(db, incluir_inactivos=incluir_inactivos)


@router.post("", response_model=schemas.MensajeroOut, status_code=201)
@router.post("/", response_model=schemas.MensajeroOut, status_code=201)
def crear_mensajero(
    payload: schemas.MensajeroCreate,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo mensajero / domiciliario en el sistema.
    """
    try:
        return crud.create_mensajero(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{mensajero_id}/toggle", response_model=schemas.MensajeroOut)
def toggle_mensajero(
    mensajero_id: int,
    db: Session = Depends(get_db)
):
    """
    Alterna el estado activo/inactivo de un mensajero (activo = !activo).
    """
    try:
        return crud.toggle_mensajero(db, mensajero_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
