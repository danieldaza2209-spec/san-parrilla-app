import sys
import os
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
import app.models


def fix():
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        statements = [
            "ALTER TYPE tipoitemstock ADD VALUE IF NOT EXISTS 'SOPA';",
            "ALTER TYPE estadopedido ADD VALUE IF NOT EXISTS 'BORRADOR_WEB';",
            "ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS cliente_telefono VARCHAR(20);",
            "ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS subtotal DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS delivery_fee DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS packaging_fee DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE cash_closures ADD COLUMN IF NOT EXISTS total_delivery_payouts DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE cash_closures ADD COLUMN IF NOT EXISTS total_expenses DOUBLE PRECISION DEFAULT 0.0;",
            """
            CREATE TABLE IF NOT EXISTS cash_expenses (
                id SERIAL PRIMARY KEY,
                cash_closure_id INTEGER NOT NULL REFERENCES cash_closures(id) ON DELETE CASCADE,
                description VARCHAR(255) NOT NULL,
                category VARCHAR(50) DEFAULT 'INSUMOS',
                amount DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            "CREATE INDEX IF NOT EXISTS ix_cash_expenses_id ON cash_expenses (id);",
            "CREATE INDEX IF NOT EXISTS ix_cash_expenses_closure ON cash_expenses (cash_closure_id);",
        ]
        for stmt in statements:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"[!] Info ({stmt}): {e}")
        print("[+] Esquema PostgreSQL y Enums actualizados correctamente.")

    # Sincronizar todos los platos del catálogo POS en la tabla `platos` de Neon DB
    from app.database import SessionLocal
    from sqlalchemy import func
    db = SessionLocal()
    try:
        cat = db.query(app.models.Categoria).order_by(app.models.Categoria.orden.asc()).first()
        if not cat:
            cat = app.models.Categoria(nombre="Menú San Parrilla", descripcion="Catálogo general", orden=1)
            db.add(cat)
            db.commit()
            db.refresh(cat)

        catalogo_pos = [
            ("🔥 Combo Prueba Impresión SAT Q22", 1000.0),
            ("Milanesa de pollo", 16500.0),
            ("Nuggets de pollo", 16500.0),
            ("Pernil frito", 16500.0),
            ("Pernil bbq", 16500.0),
            ("Lomo de cerdo a la plancha", 16500.0),
            ("Hígado en bistec", 16500.0),
            ("Chuleta de cerdo", 16500.0),
            ("Hígado al ajillo", 16500.0),
            ("Desgranado de carne", 16500.0),
            ("Carne a la plancha", 17500.0),
            ("Carne en bistec", 17500.0),
            ("Carne bbq", 17500.0),
            ("Pechuga a la plancha", 17500.0),
            ("Pechuga en salsa criolla", 17500.0),
            ("Pechuga apanada", 17500.0),
            ("Pechuga bbq", 17500.0),
            ("Pechuga al ajillo", 17500.0),
            ("Pernil hawaiano", 17500.0),
            ("Lomo de cerdo a la bbq", 17500.0),
            ("Lomo de cerdo al ajillo", 17500.0),
            ("Chuleta de cerdo al ajillo", 17500.0),
            ("Chuleta de cerdo a la bbq", 17500.0),
            ("Bandeja paisa", 18000.0),
            ("Alitas bbq", 18000.0),
            ("Creps de pollo", 18000.0),
            ("Bistec a caballo", 18000.0),
            ("Pechuga hawaiana", 18000.0),
            ("Pechuga en salsa bechamel", 18000.0),
            ("Combo Personal", 18000.0),
            ("Arroz ranchero", 18000.0),
            ("Sobrebarriga dorada", 21000.0),
            ("Bagre frito", 21000.0),
            ("Bagre al ajillo", 21000.0),
            ("Róbalo apanado", 21000.0),
            ("Róbalo al ajillo", 21000.0),
            ("Bagre sudado", 22000.0),
            ("Bagre frito sudado", 22000.0),
            ("Mojarra frita", 22000.0),
            ("Mojarra sudada", 22000.0),
            ("Mojarra frita sudada", 22000.0),
            ("Mini cazuela de mariscos", 22000.0),
            ("Costillas bbq", 23000.0),
            ("Pechuga con maíz gratinada", 23000.0),
            ("Pechuga en champiñones", 23000.0),
            ("Churrasco", 27500.0),
            ("Parrillada", 27500.0),
            ("Pechuga con tocineta y champ.", 27500.0),
            ("Pollo Santo domingo", 27500.0),
            ("Llanera mixta", 27500.0),
            ("Parrilla mixta", 27500.0),
            ("Carne grande", 27500.0),
            ("Pechuga grande", 27500.0),
            ("Mini cazuela de camarones", 27500.0),
            ("Mini cazuela de bagre", 27500.0),
            ("Cazuela de mariscos", 33000.0),
            ("Róbalo a la marinera", 33000.0),
            ("Bagre a la marinera", 33000.0),
            ("Róbalo con camarones", 33000.0),
            ("Picada x 1", 19500.0),
            ("Picada x 2", 30000.0),
            ("Picada x 3", 44000.0),
            ("Picada Berraca", 55000.0),
            ("Gaseosa 400ml", 4000.0),
            ("Gaseosa 1.5L", 8000.0),
            ("Jugo Natural en Agua", 6000.0),
            ("Jugo Natural en Leche", 7500.0),
            ("Cerveza Club Colombia / Águila", 5500.0),
            ("Porción de Papas a la Francesa", 6000.0),
            ("Porción de Patacón con Hogao", 6500.0),
        ]
        creados = 0
        for nombre, precio in catalogo_pos:
            existente = (
                db.query(app.models.Plato)
                .filter(func.lower(app.models.Plato.nombre) == nombre.lower())
                .first()
            )
            if not existente:
                db.add(app.models.Plato(
                    nombre=nombre,
                    descripcion="Catálogo POS San Parrilla",
                    precio=precio,
                    activo=True,
                    categoria_id=cat.id,
                ))
                creados += 1
            elif existente.precio != precio:
                existente.precio = precio
        db.commit()
        print(f"[+] Catálogo POS sincronizado en Neon DB ({creados} platos nuevos agregados).")
    finally:
        db.close()


if __name__ == "__main__":
    fix()
