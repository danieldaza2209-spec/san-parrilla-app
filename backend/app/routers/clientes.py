from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app import schemas, crud

router = APIRouter(prefix="/api/clientes", tags=["Directorio de Clientes y Cuentas de Fiado"])


@router.get("/search", response_model=List[schemas.ClienteOut])
def buscar_clientes(
    q: Optional[str] = Query(default=None, description="Búsqueda por teléfono o nombre (insensible a mayúsculas/acentos)"),
    telefono: Optional[str] = Query(default=None),
    phone: Optional[str] = Query(default=None),
    limit: int = Query(default=30, le=200),
    db: Session = Depends(get_db),
):
    tel_param = telefono or phone
    return crud.search_clientes(db, q=q, telefono=tel_param, limit=limit)


@router.get("/", response_model=List[schemas.ClienteOut])
@router.get("", response_model=List[schemas.ClienteOut], include_in_schema=False)
def listar_o_buscar_clientes(
    q: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    telefono: Optional[str] = Query(default=None),
    phone: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
):
    query_val = q if q is not None else search
    tel_param = telefono or phone
    return crud.search_clientes(db, q=query_val, telefono=tel_param, limit=limit)


@router.post("/", response_model=schemas.ClienteOut)
@router.post("", response_model=schemas.ClienteOut, include_in_schema=False)
def crear_o_actualizar_cliente(
    payload: schemas.ClienteCreate,
    db: Session = Depends(get_db),
):
    nombre = payload.nombre or payload.name or ""
    telefono = payload.telefono or payload.phone or ""
    direccion = payload.direccion if payload.direccion is not None else payload.address
    barrio = payload.barrio
    notas = payload.notas if payload.notas is not None else payload.notes

    cliente = crud.upsert_cliente(
        db,
        nombre=nombre,
        telefono=telefono,
        direccion=direccion,
        barrio=barrio,
        notas=notas,
        allow_without_phone=True,
    )
    if not cliente:
        raise HTTPException(
            status_code=400,
            detail="Debe proporcionar al menos el teléfono o nombre válido del cliente.",
        )
    db.commit()
    db.refresh(cliente)
    return crud._enrich_cliente_out(db, cliente)


@router.put("/{cliente_id}", response_model=schemas.ClienteOut)
@router.patch("/{cliente_id}", response_model=schemas.ClienteOut)
def actualizar_cliente_por_id(
    cliente_id: int,
    payload: schemas.ClienteUpdate,
    db: Session = Depends(get_db),
):
    try:
        return crud.update_cliente(db, cliente_id, payload)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/liquidar-fiado")
def liquidar_cuenta_fiado(
    payload: schemas.LiquidarFiadoRequest,
    db: Session = Depends(get_db),
):
    try:
        return crud.liquidar_fiado_cliente(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
