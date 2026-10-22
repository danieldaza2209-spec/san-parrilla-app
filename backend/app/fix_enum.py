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
            "ALTER TABLE cash_closures ADD COLUMN IF NOT EXISTS total_delivery_payouts DOUBLE PRECISION DEFAULT 0.0;",
        ]
        for stmt in statements:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"[!] Info ({stmt}): {e}")
        print("[+] Esquema PostgreSQL y Enums actualizados correctamente.")


if __name__ == "__main__":
    fix()
