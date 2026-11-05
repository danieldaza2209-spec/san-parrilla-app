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
            "ALTER TYPE estadopedido ADD VALUE IF NOT EXISTS 'EN_CAMINO';",
            "ALTER TYPE estadopedido ADD VALUE IF NOT EXISTS 'ENTREGADO';",
            "ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'BANCOLOMBIA';",
            "ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'FIADO';",
            "ALTER TYPE rolusuario ADD VALUE IF NOT EXISTS 'CAJERO';",
            """
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(120) NOT NULL,
                telefono VARCHAR(30) UNIQUE NOT NULL,
                direccion VARCHAR(255),
                barrio VARCHAR(150),
                notas TEXT,
                es_institucional BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS direccion VARCHAR(255);",
            "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS barrio VARCHAR(150);",
            "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS notas TEXT;",
            "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS es_institucional BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();",
            "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();",
            "CREATE INDEX IF NOT EXISTS ix_clientes_id ON clientes (id);",
            "CREATE INDEX IF NOT EXISTS ix_clientes_nombre ON clientes (nombre);",
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_clientes_telefono ON clientes (telefono);",
            "ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS cliente_id INTEGER REFERENCES clientes(id) ON DELETE SET NULL;",
            "CREATE INDEX IF NOT EXISTS ix_pedidos_cliente_id ON pedidos (cliente_id);",
            "ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS cliente_telefono VARCHAR(20);",
            "ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS creado_por VARCHAR(100);",
            "ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS cantidad_domicilios INTEGER DEFAULT 0;",
            "ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS subtotal DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS delivery_fee DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS packaging_fee DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS courier_name VARCHAR(100);",
            "ALTER TABLE platos ADD COLUMN IF NOT EXISTS disponible BOOLEAN NOT NULL DEFAULT TRUE;",
            "UPDATE platos SET disponible = activo WHERE disponible IS NULL;",
            "ALTER TABLE cash_closures ADD COLUMN IF NOT EXISTS total_bancolombia_sales DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE cash_closures ADD COLUMN IF NOT EXISTS total_transfer_sales DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE cash_closures ADD COLUMN IF NOT EXISTS total_credit_sales DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE cash_closures ADD COLUMN IF NOT EXISTS total_delivery_payouts DOUBLE PRECISION DEFAULT 0.0;",
            "ALTER TABLE cash_closures ADD COLUMN IF NOT EXISTS total_expenses DOUBLE PRECISION DEFAULT 0.0;",
            """
            CREATE TABLE IF NOT EXISTS daily_specials_config (
                id SERIAL PRIMARY KEY,
                sopa_dia VARCHAR(150) NOT NULL DEFAULT 'Campesina',
                principios TEXT NOT NULL DEFAULT 'Calabacín al huevo, Lentejas caseras, Frijoles caseros',
                acompanamientos TEXT NOT NULL DEFAULT 'Puré de ahuyama, Deditos, Tajadas maduras',
                especiales_16500 TEXT NOT NULL DEFAULT 'Hígado al ajillo, Desgranado de carne',
                especiales_16500_etiqueta VARCHAR(100) NOT NULL DEFAULT '⭐ SOLO POR HOY',
                especial_arroz_nombre VARCHAR(150) NOT NULL DEFAULT 'Arroz ranchero',
                especial_arroz_etiqueta VARCHAR(100) NOT NULL DEFAULT '⭐ SOLO LOS LUNES',
                especial_arroz_precio DOUBLE PRECISION NOT NULL DEFAULT 18000.0,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
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
    from app import crud
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
            ("Albóndigas napolitanas", 16500.0),
            ("Llanerita (lomo de cerdo y sobrebarriga)", 16500.0),
            ("Lomo de cerdo apanado", 16500.0),
            ("Lomo en salsa a la mostaza", 16500.0),
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
            ("Arroz mixto", 18000.0),
            ("Espagueti con pollo", 18000.0),
            ("Arroz con pollo", 18000.0),
            ("Arroz paisa", 18000.0),
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
                    disponible=True,
                    categoria_id=cat.id,
                ))
                creados += 1
        db.commit()
        print(f"[+] Catálogo POS sincronizado en Neon DB ({creados} platos nuevos agregados, respetando precios editados).")

        # Asegurar Categoría CONVENIOS_CLINICA y Platos de Dietas Hospitalarias + Convenios Corporativos
        cat_convenios = (
            db.query(app.models.Categoria)
            .filter(func.upper(app.models.Categoria.nombre) == "CONVENIOS_CLINICA")
            .first()
        )
        if not cat_convenios:
            cat_convenios = app.models.Categoria(
                nombre="CONVENIOS_CLINICA",
                descripcion="Menú Hospitalario Clínica Primero de Mayo y Convenios Corporativos",
                orden=30,
            )
            db.add(cat_convenios)
            db.commit()
            db.refresh(cat_convenios)

        dietas_clinica = [
            "Normal",
            "Hiposódica",
            "Hipoglúcida",
            "Hiposódica e Hipoglúcida",
            "Líquida",
            "Líquida Hiposódica",
            "Líquida Hipoglúcida",
        ]
        servicios_clinica = [
            ("Desayuno Clínica", 12000.0),
            ("Almuerzo Clínica", 16500.0),
            ("Cena Clínica", 15000.0),
        ]
        platos_convenios = []
        for serv_nombre, serv_precio in servicios_clinica:
            for dieta in dietas_clinica:
                es_hipo = ("hiposódica" in dieta.lower()) or ("hipoglúcida" in dieta.lower())
                desc = (
                    "Clínica Primero de Mayo (Pacientes) — Incluye Botella con Agua ($0)"
                    if es_hipo
                    else "Clínica Primero de Mayo (Pacientes) — Dieta Hospitalaria"
                )
                platos_convenios.append((f"{serv_nombre} - Dieta {dieta}", serv_precio, desc))

        platos_convenios.extend([
            ("Botella con Agua (Dieta Hipo Clínica)", 0.0, "Incluida automáticamente en dietas Hiposódicas e Hipoglúcidas ($0)"),
            ("Desayuno Tubo", 14000.0, "Convenio Corporativo TuboDrilling"),
            ("Almuerzo Especial Terpel", 16500.0, "Tarifa exclusiva pactada Convenio Terpel Aeropuerto"),
        ])

        creados_conv = 0
        for nombre_p, precio_p, desc_p in platos_convenios:
            existente_p = (
                db.query(app.models.Plato)
                .filter(func.lower(app.models.Plato.nombre) == nombre_p.lower())
                .first()
            )
            if not existente_p:
                db.add(app.models.Plato(
                    nombre=nombre_p,
                    descripcion=desc_p,
                    precio=precio_p,
                    activo=True,
                    disponible=True,
                    categoria_id=cat_convenios.id,
                ))
                creados_conv += 1
            else:
                existente_p.categoria_id = cat_convenios.id
        db.commit()
        print(f"[+] Platos CONVENIOS_CLINICA sincronizados en Neon DB ({creados_conv} nuevos creados).")

        # Asegurar los 6 Clientes Institucionales / Corporativos Fijos en la tabla `clientes`
        clientes_corporativos_fijos = [
            (
                "Clínica Primero de Mayo (Pacientes)",
                "CONV-CLINICA-PAC",
                "Clínica Primero de Mayo - Área Hospitalización",
                "Convenio Institucional Pacientes",
                "Dietas hospitalarias (Desayuno, Almuerzo, Cena) + Domicilios por turno",
            ),
            (
                "Clínica Primero de Mayo (Personal)",
                "CONV-CLINICA-PER",
                "Clínica Primero de Mayo - Personal Médico y Administrativo",
                "Convenio Institucional Personal",
                "Cuenta corporativa personal Clínica Primero de Mayo",
            ),
            (
                "Terpel Aeropuerto",
                "CONV-TERPEL",
                "Estación de Servicio Terpel Aeropuerto",
                "Convenio Corporativo",
                "Tarifa exclusiva Almuerzo Especial Terpel",
            ),
            (
                "Vanti",
                "CONV-VANTI",
                "Sede Corporativa Vanti",
                "Convenio Corporativo",
                "Cuenta corporativa Vanti",
            ),
            (
                "TuboDrilling",
                "CONV-TUBODRILLING",
                "Base Operativa TuboDrilling",
                "Convenio Corporativo",
                "Incluye Desayuno Tubo y almuerzos corporativos",
            ),
            (
                "Funeraria La Fe",
                "CONV-FUNERARIA-FE",
                "Funeraria La Fe",
                "Convenio Corporativo",
                "Cuenta corporativa Funeraria La Fe",
            ),
        ]
        corp_creados = 0
        for c_nombre, c_tel, c_dir, c_barrio, c_notas in clientes_corporativos_fijos:
            cli_corp = (
                db.query(app.models.Cliente)
                .filter(
                    (func.lower(app.models.Cliente.nombre) == c_nombre.lower())
                    | (app.models.Cliente.telefono == c_tel)
                )
                .first()
            )
            if not cli_corp:
                cli_corp = app.models.Cliente(
                    nombre=c_nombre,
                    telefono=c_tel,
                    direccion=c_dir,
                    barrio=c_barrio,
                    notas=c_notas,
                    es_institucional=True,
                )
                db.add(cli_corp)
                corp_creados += 1
            else:
                cli_corp.nombre = c_nombre
                cli_corp.es_institucional = True
                if not cli_corp.direccion:
                    cli_corp.direccion = c_dir
                if not cli_corp.barrio:
                    cli_corp.barrio = c_barrio
                if not cli_corp.notas:
                    cli_corp.notas = c_notas
        db.commit()
        print(f"[+] 6 Clientes Institucionales asegurados en Neon DB ({corp_creados} nuevos creados).")

        # Backfill de clientes existentes desde el historial de pedidos en Neon
        pedidos_con_cliente = (
            db.query(app.models.Pedido)
            .filter(app.models.Pedido.estado != app.models.EstadoPedido.CANCELADO)
            .order_by(app.models.Pedido.id.asc())
            .all()
        )
        clientes_sincronizados = 0
        for ped in pedidos_con_cliente:
            has_fiado = any(p.method == app.models.PaymentMethod.FIADO for p in (ped.payments or []))
            if (ped.cliente_telefono and ped.cliente_telefono.strip()) or has_fiado:
                dir_ext, barrio_ext = crud._extraer_direccion_y_barrio_de_notas(ped.notas)
                cli = crud.upsert_cliente(
                    db,
                    nombre=ped.cliente_nombre,
                    telefono=ped.cliente_telefono,
                    direccion=dir_ext,
                    barrio=barrio_ext,
                    allow_without_phone=has_fiado,
                )
                if cli and ped.cliente_id != cli.id:
                    ped.cliente_id = cli.id
                    clientes_sincronizados += 1
        db.commit()
        print(f"[+] Directorio de Clientes sincronizado con historial ({clientes_sincronizados} pedidos vinculados).")

        cfg = db.query(app.models.DailySpecialsConfig).order_by(app.models.DailySpecialsConfig.id.asc()).first()
        if not cfg:
            cfg = app.models.DailySpecialsConfig(
                id=1,
                sopa_dia="Campesina",
                principios="Calabacín al huevo, Lentejas caseras, Frijoles caseros",
                acompanamientos="Puré de ahuyama, Deditos, Tajadas maduras",
                especiales_16500="Hígado al ajillo, Desgranado de carne",
                especiales_16500_etiqueta="⭐ SOLO POR HOY",
                especial_arroz_nombre="Arroz ranchero",
                especial_arroz_etiqueta="⭐ SOLO LOS LUNES",
                especial_arroz_precio=18000.0,
            )
            db.add(cfg)
            db.commit()
            print("[+] Configuración inicial de Especiales del Día creada en Neon DB.")
    finally:
        db.close()

    try:
        from app.seed_rapidas import seed_rapidas
        seed_rapidas()
    except Exception as e:
        print(f"[!] Info (seed_rapidas): {e}")


if __name__ == "__main__":
    fix()
