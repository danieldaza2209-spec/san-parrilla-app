from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from app.database import get_db
from app import schemas, crud

router = APIRouter(prefix="/api/metricas", tags=["Métricas y Optimización"])


@router.get("/hoy", response_model=schemas.MetricasDiaOut)
def metricas_hoy(db: Session = Depends(get_db)):
    return crud.obtener_metricas_dia(db, date.today())


@router.get("/{fecha_str}", response_model=schemas.MetricasDiaOut)
def metricas_por_fecha(fecha_str: str, db: Session = Depends(get_db)):
    try:
        fecha_parsed = date.fromisoformat(fecha_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD")
    
    return crud.obtener_metricas_dia(db, fecha_parsed)
