import sys
import os
from sqlalchemy import func

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
import app.models as models

COMIDAS_RAPIDAS_DATA = [
    # Categoría: Hamburguesas
    ("Hamburguesas", "Hamburguesas artesanales y clásicas al carbón", 20, [
        ("Hamburguesa Clásica", 15500.0, "🍔"),
        ("Hamburguesa Chicken", 18000.0, "🍔"),
        ("Choriburguer", 20000.0, "🍔"),
        ("Hamburguesa Space", 20500.0, "🍔"),
        ("Hamburguesa Tentación", 22500.0, "🍔"),
        ("Big Burguer", 23500.0, "🍔"),
        ("Hamburguesa Crunch Master", 26000.0, "🍔"),
        ("Hamburguesa Berraca", 26000.0, "🍔"),
    ]),
    # Categoría: Perros Calientes
    ("Perros Calientes", "Perros calientes tradicionales y especiales", 21, [
        ("Perro Americano", 15500.0, "🌭"),
        ("Choriperro", 16000.0, "🌭"),
        ("Perro Hawaiano (Carne)", 17500.0, "🌭"),
        ("Perro Hawaiano (Pollo)", 17500.0, "🌭"),
        ("Perro Loco", 18500.0, "🌭"),
        ("Perro Especial", 19500.0, "🌭"),
        ("Perro Extra-Largo", 30000.0, "🌭"),
    ]),
    # Categoría: Salchipapas y Papas Locas
    ("Salchipapas y Papas Locas", "Salchipapas y papas cargadas de queso y carnes", 22, [
        ("Salchipapa Clásica", 15500.0, "🍟"),
        ("Salchipapa Especial de Carne", 22000.0, "🍟"),
        ("Salchipapa Especial de Pollo", 22000.0, "🍟"),
        ("Papas Locas Clásicas (Carne)", 17000.0, "🍟"),
        ("Papas Locas Clásicas (Pollo)", 17000.0, "🍟"),
        ("Papas Locas Mixtas", 22000.0, "🍟"),
        ("Papas Locas San Parrilla", 24000.0, "🍟"),
    ]),
    # Categoría: Patacones
    ("Patacones", "Patacones pisados con carnes y queso", 23, [
        ("Patacón Clásico (Carne)", 15500.0, "🫓"),
        ("Patacón Clásico (Pollo)", 15500.0, "🫓"),
        ("Patacón Porky", 17000.0, "🫓"),
        ("Patacón Mixto", 19500.0, "🫓"),
        ("Patacón San Parrilla", 21000.0, "🫓"),
    ]),
    # Categoría: Sándwich
    ("Sándwich", "Sándwiches artesanales calientes", 24, [
        ("Sándwich Clásico (Carne)", 15500.0, "🥪"),
        ("Sándwich Clásico (Pollo)", 15500.0, "🥪"),
        ("Sándwich Granjero", 16500.0, "🥪"),
        ("Sándwich Porky", 19500.0, "🥪"),
        ("Sándwich San Parrilla", 21000.0, "🥪"),
    ]),
    # Categoría: Picadas Noche
    ("Picadas Noche", "Picadas nocturnas para compartir", 25, [
        ("Picada Personal", 27500.0, "🥩"),
        ("Picada Dúo", 50000.0, "🥩"),
        ("Picada Trío", 66000.0, "🥩"),
        ("Picada Berraca", 55000.0, "🥩"),
    ]),
    # Categoría: Especiales Noche
    ("Especiales Noche", "Bandejas y especialidades del turno noche", 26, [
        ("Bandeja San Parrilla (Carne a la plancha)", 21000.0, "🔥"),
        ("Bandeja San Parrilla (Pechuga a la plancha)", 21000.0, "🔥"),
        ("Bandeja San Parrilla (Lomo a la plancha)", 21000.0, "🔥"),
        ("Bandeja San Parrilla (Chuleta a la plancha)", 21000.0, "🔥"),
        ("Alitas BBQ", 22000.0, "🍗"),
        ("Alitas Apanadas", 22000.0, "🍗"),
        ("Costillitas BBQ", 23000.0, "🥓"),
    ]),
    # Categoría: Granizados y Jugos
    ("Granizados y Jugos", "Jugos naturales y granizados refrescantes", 27, [
        ("Jugo / Granizado en Agua", 8000.0, "🥤"),
        ("Jugo / Granizado en Leche", 9500.0, "🥤"),
        ("Limonada Cerezada", 10000.0, "🥤"),
    ]),
    # Categoría: Bebidas
    ("Bebidas", "Bebidas frías y gaseosas", 28, [
        ("Agua", 3000.0, "💧"),
        ("Soda", 4000.0, "🥤"),
        ("Gaseosa P400", 4000.0, "🥤"),
        ("Gaseosa 1.5L", 8000.0, "🥤"),
        ("Gaseosa Mega", 13500.0, "🥤"),
        ("Cerveza", 4500.0, "🍺"),
    ])
]


def seed_rapidas():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        cats_created = 0
        prods_created = 0
        prods_updated = 0

        for cat_name, cat_desc, cat_order, products in COMIDAS_RAPIDAS_DATA:
            cat = (
                db.query(models.Categoria)
                .filter(func.lower(models.Categoria.nombre) == cat_name.lower())
                .first()
            )
            if not cat:
                cat = models.Categoria(
                    nombre=cat_name,
                    descripcion=cat_desc,
                    orden=cat_order
                )
                db.add(cat)
                db.commit()
                db.refresh(cat)
                cats_created += 1

            for prod_name, price, emoji in products:
                # Buscar plato dentro de esta categoría específica
                plato = (
                    db.query(models.Plato)
                    .filter(
                        models.Plato.categoria_id == cat.id,
                        func.lower(models.Plato.nombre) == prod_name.lower()
                    )
                    .first()
                )

                if not plato:
                    # Si no existe en esta categoría, verificar si existe en la categoría general
                    plato_global = (
                        db.query(models.Plato)
                        .filter(func.lower(models.Plato.nombre) == prod_name.lower())
                        .first()
                    )
                    # Si ya existe globalmente pero en otra categoría (por ej. Bebidas o Almuerzos), 
                    # si es la categoría de Bebidas o Picadas podemos moverlo/actualizarlo o crearlo en su categoría propia
                    if plato_global and cat_name in ("Bebidas", "Granizados y Jugos"):
                        plato_global.categoria_id = cat.id
                        plato_global.precio = price
                        plato_global.activo = True
                        plato_global.imagen_emoji = emoji
                        prods_updated += 1
                        continue

                    nuevo_plato = models.Plato(
                        categoria_id=cat.id,
                        nombre=prod_name,
                        precio=price,
                        imagen_emoji=emoji,
                        activo=True,
                        descripcion=f"Comidas Rápidas San Parrilla - {cat_name}"
                    )
                    db.add(nuevo_plato)
                    prods_created += 1
                else:
                    plato.precio = price
                    plato.activo = True
                    plato.imagen_emoji = emoji
                    prods_updated += 1

        db.commit()
        print(f"[+] Comidas Rápidas sincronizadas con éxito en Neon:")
        print(f"    - Categorías nuevas: {cats_created}")
        print(f"    - Productos creados: {prods_created}")
        print(f"    - Productos actualizados: {prods_updated}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_rapidas()
