from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app import schemas, crud

router = APIRouter(prefix="/api/catalogo", tags=["Catálogos del Menú"])


@router.get("/categorias", response_model=List[schemas.CategoriaOut])
def listar_categorias(db: Session = Depends(get_db)):
    return crud.get_categorias(db)


@router.get("/platos", response_model=List[schemas.PlatoOut])
def listar_platos(categoria_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    return crud.get_platos(db, categoria_id=categoria_id)


@router.get("/sopas", response_model=List[schemas.SopaOut])
def listar_sopas(db: Session = Depends(get_db)):
    return crud.get_sopas(db)


@router.get("/principios", response_model=List[schemas.PrincipioOut])

def listar_principios(db: Session = Depends(get_db)):
    return crud.get_principios(db)


@router.get("/acompanamientos", response_model=List[schemas.AcompanamientoOut])
def listar_acompanamientos(db: Session = Depends(get_db)):
    return crud.get_acompanamientos(db)
