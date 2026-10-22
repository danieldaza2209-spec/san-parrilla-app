from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List
from pydantic import BaseModel

from app.database import get_db
from app import schemas, crud
from app.services import reglas_menu

router = APIRouter(prefix="/api/menu-dia", tags=["Menú del Día y Stock"])


class GenerarMenuReglasRequest(BaseModel):
    fecha: Optional[str] = None
    sopa_id: int
    principios_ids: List[int]
    acompanamientos_ids: List[int]
    stock_preparado: Optional[int] = 50


@router.get("/reglas")
def obtener_reglas_menu():
    """
    Devuelve las reglas de negocio oficiales para la preparacion del menu diario.
    """
    return {
        "max_sopas": reglas_menu.MAX_SOPAS_POR_DIA,
        "max_principios": reglas_menu.MAX_PRINCIPIOS_POR_DIA,
        "max_acompanamientos": reglas_menu.MAX_ACOMPANAMIENTOS_POR_DIA,
        "principio_obligatorio": reglas_menu.NOMBRE_PRINCIPIO_OBLIGATORIO,
        "acompanamiento_obligatorio": reglas_menu.NOMBRE_ACOMPANAMIENTO_OBLIGATORIO,
        "descripcion": "Todos los dias se prepara exactamente 1 sopa, 3 principios (incluyendo Frijoles Caseros obligatoriamente) y 3 acompanamientos (incluyendo Tajadas Maduras obligatoriamente)."
    }


@router.get("/hoy", response_model=Optional[schemas.MenuDiaOut])
def obtener_menu_hoy(db: Session = Depends(get_db)):
    menu = crud.get_menu_dia_by_fecha(db, date.today())
    return menu


@router.get("/{fecha_str}", response_model=Optional[schemas.MenuDiaOut])
def obtener_menu_por_fecha(fecha_str: str, db: Session = Depends(get_db)):
    try:
        fecha_parsed = date.fromisoformat(fecha_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha invalido. Usa YYYY-MM-DD")
    
    return crud.get_menu_dia_by_fecha(db, fecha_parsed)


@router.post("/generar-con-reglas", response_model=schemas.MenuDiaOut)
def generar_menu_con_reglas(req: GenerarMenuReglasRequest, db: Session = Depends(get_db)):
    """
    Genera o actualiza el menú del día aplicando y validando las reglas de negocio de San Parrilla.
    """
    fecha_target = req.fecha or date.today().isoformat()
    try:
        menu = reglas_menu.auto_generar_menu_dia_segun_reglas(
            db=db,
            fecha_str=fecha_target,
            sopa_id=req.sopa_id,
            principios_ids=req.principios_ids,
            acompanamientos_ids=req.acompanamientos_ids,
            stock_preparado=req.stock_preparado or 50
        )
        return menu
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/", response_model=schemas.MenuDiaOut)
def guardar_menu_dia(menu_in: schemas.MenuDiaCreate, db: Session = Depends(get_db)):
    return crud.crear_o_actualizar_menu_dia(db, menu_in)
