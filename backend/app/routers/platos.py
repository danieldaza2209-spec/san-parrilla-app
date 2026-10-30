from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app import schemas, crud

router = APIRouter(prefix="/api/catalogo", tags=["Catálogos del Menú"])
platos_direct_router = APIRouter(prefix="/api/platos", tags=["Gestor de Platos y Precios en Tiempo Real"])


@router.get("/categorias", response_model=List[schemas.CategoriaOut])
def listar_categorias(db: Session = Depends(get_db)):
    return crud.get_categorias(db)


@router.get("/platos", response_model=List[schemas.PlatoOut])
def listar_platos_catalogo(
    categoria_id: Optional[int] = Query(None),
    solo_activos: bool = Query(False),
    db: Session = Depends(get_db),
):
    return crud.get_platos(db, categoria_id=categoria_id, solo_activos=solo_activos)


@router.get("/sopas", response_model=List[schemas.SopaOut])
def listar_sopas(db: Session = Depends(get_db)):
    return crud.get_sopas(db)


@router.get("/principios", response_model=List[schemas.PrincipioOut])
def listar_principios(db: Session = Depends(get_db)):
    return crud.get_principios(db)


@router.get("/acompanamientos", response_model=List[schemas.AcompanamientoOut])
def listar_acompanamientos(db: Session = Depends(get_db)):
    return crud.get_acompanamientos(db)


# --- ENDPOINTS DIRECTOS /api/platos PARA GESTOR DE PRECIOS Y AGOTADOS ---

@platos_direct_router.get("/", response_model=List[schemas.PlatoOut])
@platos_direct_router.get("", response_model=List[schemas.PlatoOut], include_in_schema=False)
def obtener_todos_los_platos(
    categoria_id: Optional[int] = Query(None),
    solo_activos: bool = Query(False),
    db: Session = Depends(get_db),
):
    return crud.get_platos(db, categoria_id=categoria_id, solo_activos=solo_activos)


@platos_direct_router.put("/bulk-price", response_model=List[schemas.PlatoOut])
@platos_direct_router.post("/bulk-price", response_model=List[schemas.PlatoOut])
@router.put("/platos/bulk-price", response_model=List[schemas.PlatoOut])
@router.post("/platos/bulk-price", response_model=List[schemas.PlatoOut])
def actualizar_precios_en_bloque(
    payload: schemas.PlatoBulkPriceUpdate,
    db: Session = Depends(get_db),
):
    try:
        return crud.bulk_update_plato_prices(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@platos_direct_router.put("/by-name", response_model=schemas.PlatoOut)
@platos_direct_router.post("/by-name", response_model=schemas.PlatoOut)
@router.put("/platos/by-name", response_model=schemas.PlatoOut)
@router.post("/platos/by-name", response_model=schemas.PlatoOut)
def actualizar_plato_por_nombre(
    payload: schemas.PlatoUpdate,
    nombre: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    target_name = nombre or payload.nombre
    if not target_name:
        raise HTTPException(status_code=400, detail="Debe proporcionar el nombre del plato.")
    try:
        return crud.update_plato_by_name(db, target_name, payload)
    except (LookupError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@platos_direct_router.put("/{plato_id}", response_model=schemas.PlatoOut)
@platos_direct_router.patch("/{plato_id}", response_model=schemas.PlatoOut)
@router.put("/platos/{plato_id}", response_model=schemas.PlatoOut)
@router.patch("/platos/{plato_id}", response_model=schemas.PlatoOut)
def actualizar_plato_individual(
    plato_id: int,
    payload: schemas.PlatoUpdate,
    db: Session = Depends(get_db),
):
    try:
        return crud.update_plato(db, plato_id, payload)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
