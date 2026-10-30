from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.config import settings
from app.database import engine, Base, get_db
from app import schemas, crud
import app.models  # Import standard models so Base.metadata knows about all tables

from app.routers import platos, menu, pedidos, metricas, auth, caja, clientes

# Create database tables and sync POS catalog automatically
Base.metadata.create_all(bind=engine)
try:
    from app.fix_enum import fix
    fix()
except Exception as e:
    print(f"[!] Aviso en inicialización de esquema: {e}")

app = FastAPI(
    title=settings.APP_NAME,
    description="API REST modular para el Restaurante San Parrilla con autenticación por roles, control de principios, acompañamientos, métricas, pagos y cierres de caja.",
    version="1.0.0",
    debug=settings.DEBUG
)

# CORS configuration for Astro / Vite Frontend and Production deployments (Vercel, Netlify, Render)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4321",
    "http://127.0.0.1:4321",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir Routers Modulares
app.include_router(auth.router)
app.include_router(platos.router)
app.include_router(platos.platos_direct_router)
app.include_router(clientes.router)
app.include_router(menu.router)
app.include_router(pedidos.router)
app.include_router(caja.router)
app.include_router(metricas.router)


@app.get("/api/especiales-dia", response_model=schemas.DailySpecialsConfigOut, tags=["Especiales del Día"])
def obtener_especiales_dia(db: Session = Depends(get_db)):
    return crud.get_daily_specials_config(db)


@app.put("/api/especiales-dia", response_model=schemas.DailySpecialsConfigOut, tags=["Especiales del Día"])
@app.post("/api/especiales-dia", response_model=schemas.DailySpecialsConfigOut, tags=["Especiales del Día"])
def guardar_especiales_dia(
    payload: schemas.DailySpecialsConfigUpdate,
    db: Session = Depends(get_db),
):
    return crud.update_daily_specials_config(db, payload)


@app.get("/", tags=["Estado"])
def read_root():
    return {
        "message": "Bienvenido a la API del Restaurante San Parrilla!",
        "status": "online",
        "version": "1.0.0"
    }
