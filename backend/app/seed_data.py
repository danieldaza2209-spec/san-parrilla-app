import sys
import os
from datetime import date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal, Base
from app import models, crud, schemas


def seed():
    print("[+] Inicializando tablas en la base de datos San Parrilla...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Solo poblar si el catálogo está vacío
        if db.query(models.Categoria).count() == 0:
            print("[+] Poblando categorías reales de San Parrilla...")
            cat_165 = models.Categoria(nombre="Platos Fuertes $16.500", descripcion="Plato fuerte + Sopa + Principio + Acompañamiento", orden=1)
            cat_175 = models.Categoria(nombre="Platos Fuertes $17.500", descripcion="Plato fuerte + Sopa + Principio + Acompañamiento", orden=2)
            cat_180 = models.Categoria(nombre="Platos Fuertes $18.000", descripcion="Plato fuerte + Sopa + Principio + Acompañamiento", orden=3)
            cat_210 = models.Categoria(nombre="Especialidades $21.000", descripcion="Plato fuerte + Sopa + Principio + Acompañamiento", orden=4)
            cat_220 = models.Categoria(nombre="Pescados & Mariscos $22.000", descripcion="Plato fuerte + Sopa + Principio + Acompañamiento", orden=5)
            cat_230 = models.Categoria(nombre="Cortes & Gratinados $23.000", descripcion="Plato fuerte + Sopa + Principio + Acompañamiento", orden=6)
            cat_275 = models.Categoria(nombre="Parrilla Premium $27.500", descripcion="Plato fuerte + Sopa + Principio + Acompañamiento", orden=7)
            cat_330 = models.Categoria(nombre="Mariscos & Especiales $33.000", descripcion="Plato fuerte + Sopa + Principio + Acompañamiento", orden=8)

            db.add_all([cat_165, cat_175, cat_180, cat_210, cat_220, cat_230, cat_275, cat_330])
            db.commit()

            print("[+] Poblando platos reales de San Parrilla...")
            platos = [
                # $16.500
                models.Plato(nombre="Milanesa de Pollo", descripcion="Pechuga apanada dorada crujiente.", precio=16500.0, imagen_emoji="🍗", categoria_id=cat_165.id),
                models.Plato(nombre="Nuggets de Pollo", descripcion="Porción de nuggets crocantes de pechuga.", precio=16500.0, imagen_emoji="🧆", categoria_id=cat_165.id),
                models.Plato(nombre="Pernil Frito", descripcion="Pernil de pollo jugoso y dorado a la sartén.", precio=16500.0, imagen_emoji="🍗", categoria_id=cat_165.id),
                models.Plato(nombre="Pernil BBQ", descripcion="Pernil de pollo jugoso bañado en salsa BBQ de la casa.", precio=16500.0, imagen_emoji="🍗", categoria_id=cat_165.id),
                models.Plato(nombre="Lomo de Cerdo a la Plancha", descripcion="Lomo magro a la plancha en sal marina.", precio=16500.0, imagen_emoji="🥩", categoria_id=cat_165.id),
                models.Plato(nombre="Hígado en Bistec", descripcion="Hígado tierno con cebolla y tomate en guiso.", precio=16500.0, imagen_emoji="🍳", categoria_id=cat_165.id),
                models.Plato(nombre="Chuleta de Cerdo", descripcion="Chuleta de cerdo sazonada a la plancha.", precio=16500.0, imagen_emoji="🥩", categoria_id=cat_165.id),

                # $17.500
                models.Plato(nombre="Carne a la plancha", descripcion="Corte de res tierno sazonado a la brasa.", precio=17500.0, imagen_emoji="🥩", categoria_id=cat_175.id),
                models.Plato(nombre="Carne en bistec", descripcion="Corte de res jugoso en guiso suave de tomate y cebolla.", precio=17500.0, imagen_emoji="🥩", categoria_id=cat_175.id),
                models.Plato(nombre="Carne bbq", descripcion="Jugosa carne de res bañada en salsa BBQ de la casa.", precio=17500.0, imagen_emoji="🥩", categoria_id=cat_175.id),
                models.Plato(nombre="Pechuga a la plancha", descripcion="Pechuga de pollo a la plancha sazonada a la parrilla.", precio=17500.0, imagen_emoji="🍗", categoria_id=cat_175.id),
                models.Plato(nombre="Pechuga en salsa criolla", descripcion="Pechuga de pollo bañada en tradicional salsa criolla.", precio=17500.0, imagen_emoji="🍗", categoria_id=cat_175.id),
                models.Plato(nombre="Pechuga apanada", descripcion="Pechuga de pollo empanada crocante y dorada.", precio=17500.0, imagen_emoji="🍗", categoria_id=cat_175.id),
                models.Plato(nombre="Pechuga bbq", descripcion="Pechuga de pollo a la parrilla bañada en salsa BBQ.", precio=17500.0, imagen_emoji="🍗", categoria_id=cat_175.id),
                models.Plato(nombre="Pernil hawaiano", descripcion="Pernil de pollo con salsa agridulce de piña y queso.", precio=17500.0, imagen_emoji="🍍", categoria_id=cat_175.id),
                models.Plato(nombre="Lomo de cerdo a la bbq", descripcion="Lomo magro de cerdo bañado en salsa barbacoa.", precio=17500.0, imagen_emoji="🥩", categoria_id=cat_175.id),
                models.Plato(nombre="Lomo de cerdo al ajillo", descripcion="Lomo de cerdo salteado en fina salsa al ajillo.", precio=17500.0, imagen_emoji="🧄", categoria_id=cat_175.id),
                models.Plato(nombre="Chuleta de cerdo al ajillo", descripcion="Chuleta de cerdo bañada en apetitosa salsa al ajillo.", precio=17500.0, imagen_emoji="🥩", categoria_id=cat_175.id),
                models.Plato(nombre="Chuleta de cerdo a la bbq", descripcion="Chuleta de cerdo dorada a la parrilla con salsa BBQ.", precio=17500.0, imagen_emoji="🥩", categoria_id=cat_175.id),

                # $18.000
                models.Plato(nombre="Bandeja paisa", descripcion="Bandeja paisa tradicional con carne, frijoles, arroz, chicharrón, huevo y tajada.", precio=18000.0, imagen_emoji="🍲", categoria_id=cat_180.id),
                models.Plato(nombre="Alitas bbq", descripcion="Alitas de pollo crocantes bañadas en nuestra salsa BBQ artesanal.", precio=18000.0, imagen_emoji="🍗", categoria_id=cat_180.id),
                models.Plato(nombre="Creps de pollo", descripcion="Delicadas crepas rellenas de pollo desmechado en salsa cremosa.", precio=18000.0, imagen_emoji="🥞", categoria_id=cat_180.id),
                models.Plato(nombre="Bistec a caballo", descripcion="Jugoso corte de res bañado en guiso criollo con huevo frito encima.", precio=18000.0, imagen_emoji="🍳", categoria_id=cat_180.id),
                models.Plato(nombre="Pechuga hawaiana", descripcion="Pechuga de pollo a la plancha cubierta con piña, jamón y queso fundido.", precio=18000.0, imagen_emoji="🍍", categoria_id=cat_180.id),
                models.Plato(nombre="Combo Personal", descripcion="Combo individual especial con plato fuerte, acompañamiento y bebida.", precio=18000.0, imagen_emoji="🍱", categoria_id=cat_180.id),
                models.Plato(nombre="Sancocho de gallina", descripcion="Tradicional sancocho de gallina criolla con plátano, yuca y mazorca.", precio=18000.0, imagen_emoji="🍲", categoria_id=cat_180.id),
                models.Plato(nombre="Espaguetis con pollo", descripcion="Pasta en salsa suave con generosos trozos de pechuga de pollo.", precio=18000.0, imagen_emoji="🍝", categoria_id=cat_180.id),
                models.Plato(nombre="Espaguetis boloñesa", descripcion="Espaguetis en clásica salsa boloñesa con carne molida sazonada.", precio=18000.0, imagen_emoji="🍝", categoria_id=cat_180.id),
                models.Plato(nombre="Arroz con pollo", descripcion="Arroz amarillo sazonado con desmechado de pechuga y verduras frescas.", precio=18000.0, imagen_emoji="🍚", categoria_id=cat_180.id),
                models.Plato(nombre="Arroz campesino", descripcion="Arroz salteado estilo campesino con carnes mixtas, maíz dulce y plátano.", precio=18000.0, imagen_emoji="🍚", categoria_id=cat_180.id),

                # $21.000
                models.Plato(nombre="Sobrebarriga dorada", descripcion="Sobrebarriga tierna dorada al horno con especias.", precio=21000.0, imagen_emoji="🥩", categoria_id=cat_210.id),
                models.Plato(nombre="Bagre frito", descripcion="Posta de bagre fresco dorada y crocante.", precio=21000.0, imagen_emoji="🐟", categoria_id=cat_210.id),
                models.Plato(nombre="Bagre al ajillo", descripcion="Posta de bagre salteada en rica salsa de ajo y mantequilla.", precio=21000.0, imagen_emoji="🧄", categoria_id=cat_210.id),
                models.Plato(nombre="Róbalo apanado", descripcion="Filete de róbalo empanado doradito y crujiente.", precio=21000.0, imagen_emoji="🐠", categoria_id=cat_210.id),
                models.Plato(nombre="Róbalo al ajillo", descripcion="Filete de róbalo en delicada salsa al ajillo de la casa.", precio=21000.0, imagen_emoji="🐠", categoria_id=cat_210.id),

                # $22.000
                models.Plato(nombre="Bagre sudado", descripcion="Posta de bagre en sabroso guiso criollo con plátano y yuca.", precio=22000.0, imagen_emoji="🐟", categoria_id=cat_220.id),
                models.Plato(nombre="Bagre frito sudado", descripcion="Posta de bagre frita y luego guisada en salsa criolla.", precio=22000.0, imagen_emoji="🐟", categoria_id=cat_220.id),
                models.Plato(nombre="Mojarra frita", descripcion="Mojarra entera frita crocante servida con limón.", precio=22000.0, imagen_emoji="🐟", categoria_id=cat_220.id),
                models.Plato(nombre="Mojarra sudada", descripcion="Mojarra entera guisada en tradicional salsa criolla.", precio=22000.0, imagen_emoji="🐟", categoria_id=cat_220.id),
                models.Plato(nombre="Mojarra frita sudada", descripcion="Mojarra entera frita y pasada por apetitoso guiso criollo.", precio=22000.0, imagen_emoji="🐟", categoria_id=cat_220.id),
                models.Plato(nombre="Mini cazuela de mariscos", descripcion="Cremosa mini cazuela cargada de mariscos mixtos y camarones.", precio=22000.0, imagen_emoji="🥘", categoria_id=cat_220.id),

                # $23.000
                models.Plato(nombre="Costillas bbq", descripcion="Tiernas costillas de cerdo bañadas en salsa BBQ ahumada.", precio=23000.0, imagen_emoji="🥓", categoria_id=cat_230.id),
                models.Plato(nombre="Pechuga con maíz gratinada", descripcion="Pechuga de pollo en salsa cremosa de maíz con queso gratinado.", precio=23000.0, imagen_emoji="🌽", categoria_id=cat_230.id),
                models.Plato(nombre="Pechuga en champiñones", descripcion="Pechuga de pollo en rica salsa cremosa con champiñones frescos.", precio=23000.0, imagen_emoji="🍄", categoria_id=cat_230.id),

                # $27.500
                models.Plato(nombre="Churrasco", descripcion="Corte de res jugoso a las brasas sazonado con sal marina.", precio=27500.0, imagen_emoji="🥩", categoria_id=cat_275.id),
                models.Plato(nombre="Parrillada", descripcion="Excelente combinación de res, pollo, chorizo y morcilla a la brasa.", precio=27500.0, imagen_emoji="🔥", categoria_id=cat_275.id),
                models.Plato(nombre="Pechuga con tocineta y champ.", descripcion="Pechuga a la plancha cubierta con tocineta crocante y salsa de champiñones.", precio=27500.0, imagen_emoji="🥓", categoria_id=cat_275.id),
                models.Plato(nombre="Pollo Santo domingo", descripcion="Especialidad con pechuga jugosa bañada en salsa especial Santo Domingo.", precio=27500.0, imagen_emoji="🍗", categoria_id=cat_275.id),
                models.Plato(nombre="Llanera mixta", descripcion="Exquisita carne a la llanera acompañada de chicharrón y chorizo artesanal.", precio=27500.0, imagen_emoji="🍖", categoria_id=cat_275.id),
                models.Plato(nombre="Parrilla mixta", descripcion="Selección especial de res, cerdo y pollo a la parrilla con sazón criollo.", precio=27500.0, imagen_emoji="🔥", categoria_id=cat_275.id),
                models.Plato(nombre="Carne grande", descripcion="Generosa porción doble de carne de res tierno a las brasas.", precio=27500.0, imagen_emoji="🥩", categoria_id=cat_275.id),
                models.Plato(nombre="Pechuga grande", descripcion="Generosa porción doble de pechuga de pollo a la parrilla.", precio=27500.0, imagen_emoji="🍗", categoria_id=cat_275.id),
                models.Plato(nombre="Mini cazuela de camarones", descripcion="Deliciosa mini cazuela concentrada con camarones frescos en crema.", precio=27500.0, imagen_emoji="🦐", categoria_id=cat_275.id),
                models.Plato(nombre="Mini cazuela de bagre", descripcion="Suculenta mini cazuela con trozos de bagre fresco en suave guiso.", precio=27500.0, imagen_emoji="🐟", categoria_id=cat_275.id),

                # $33.000
                models.Plato(nombre="Cazuela de mariscos", descripcion="Gran cazuela cremosa cargada con surtido premium de mariscos y camarones.", precio=33000.0, imagen_emoji="🥘", categoria_id=cat_330.id),
                models.Plato(nombre="Róbalo a la marinera", descripcion="Filete de róbalo bañado en abundante salsa marinera con mariscos.", precio=33000.0, imagen_emoji="🐠", categoria_id=cat_330.id),
                models.Plato(nombre="Bagre a la marinera", descripcion="Posta de bagre fresco salteada y cubierta en guiso mariscado especial.", precio=33000.0, imagen_emoji="🐟", categoria_id=cat_330.id),
                models.Plato(nombre="Róbalo con camarones", descripcion="Filete de róbalo jugoso cubierto con camarones al ajillo en crema.", precio=33000.0, imagen_emoji="🦐", categoria_id=cat_330.id),
            ]
            db.add_all(platos)
            db.commit()

            print("[+] Poblando sopas reales...")
            sopas = [
                models.Sopa(nombre="Sancocho Tradicional", descripcion="Sancocho criollo preparado hoy con plátano, yuca y mazorca")
            ]
            db.add_all(sopas)
            db.commit()

            print("[+] Poblando principios reales...")
            principios = [
                models.Principio(nombre="Frijoles Caseros", descripcion="Frijoles calados estilo tradicional"),
                models.Principio(nombre="Ensalada de Atún", descripcion="Ensalada fresca con trozos de atún y verduras"),
                models.Principio(nombre="Garbanzos Rancheros", descripcion="Garbanzos guisados con ahogado"),
                models.Principio(nombre="Lentejas con Maduro", descripcion="Lentejas caseras con plátano maduro")
            ]
            db.add_all(principios)
            db.commit()

            print("[+] Poblando acompañamientos reales del día...")
            acompanamientos = [
                models.Acompanamiento(nombre="Papa Francesa Casera", descripcion="Papas doradas a la francesa"),
                models.Acompanamiento(nombre="Maduro Pícaro", descripcion="Plátano maduro horneado agridulce"),
                models.Acompanamiento(nombre="Tajadas Maduras", descripcion="Tajadas de plátano maduro frito")
            ]
            db.add_all(acompanamientos)
            db.commit()

            # Configurar menú del día para hoy
            hoy = date.today()
            print(f"[+] Configurando stock del Menú del Día San Parrilla ({hoy})...")

            s_sancocho = db.query(models.Sopa).filter_by(nombre="Sancocho Tradicional").first()
            p_frijoles = db.query(models.Principio).filter_by(nombre="Frijoles Caseros").first()
            p_atun = db.query(models.Principio).filter_by(nombre="Ensalada de Atún").first()
            p_garbanzos = db.query(models.Principio).filter_by(nombre="Garbanzos Rancheros").first()
            a_francesa = db.query(models.Acompanamiento).filter_by(nombre="Papa Francesa Casera").first()
            a_maduro = db.query(models.Acompanamiento).filter_by(nombre="Maduro Pícaro").first()
            a_tajadas = db.query(models.Acompanamiento).filter_by(nombre="Tajadas Maduras").first()

            items = [
                schemas.MenuDiaItemCreate(tipo_item=models.TipoItemStock.SOPA, sopa_id=s_sancocho.id, cantidad_preparada=60),
                schemas.MenuDiaItemCreate(tipo_item=models.TipoItemStock.PRINCIPIO, principio_id=p_frijoles.id, cantidad_preparada=50),
                schemas.MenuDiaItemCreate(tipo_item=models.TipoItemStock.PRINCIPIO, principio_id=p_atun.id, cantidad_preparada=35),
                schemas.MenuDiaItemCreate(tipo_item=models.TipoItemStock.PRINCIPIO, principio_id=p_garbanzos.id, cantidad_preparada=30),
                schemas.MenuDiaItemCreate(tipo_item=models.TipoItemStock.ACOMPANAMIENTO, acompanamiento_id=a_francesa.id, cantidad_preparada=40),
                schemas.MenuDiaItemCreate(tipo_item=models.TipoItemStock.ACOMPANAMIENTO, acompanamiento_id=a_maduro.id, cantidad_preparada=35),
                schemas.MenuDiaItemCreate(tipo_item=models.TipoItemStock.ACOMPANAMIENTO, acompanamiento_id=a_tajadas.id, cantidad_preparada=30),
            ]

            menu_dto = schemas.MenuDiaCreate(
                fecha=hoy,
                notas="Menú oficial San Parrilla con Sopa del día única, Principios y Acompañamientos del día",
                items=items
            )
            crud.crear_o_actualizar_menu_dia(db, menu_dto)

        # Poblar usuarios si no existen
        if db.query(models.Usuario).count() == 0:
            print("[+] Creando usuarios por defecto con roles y contraseñas seguras...")
            from app.security import hash_password

            usuario_admin = models.Usuario(
                username="admin",
                nombre_completo="Administrador San Parrilla",
                hashed_password=hash_password("admin123"),
                rol=models.RolUsuario.ADMINISTRADOR,
                activo=True
            )
            usuario_mesero = models.Usuario(
                username="mesero1",
                nombre_completo="Carlos Mesero",
                hashed_password=hash_password("mesero123"),
                rol=models.RolUsuario.MESERO,
                activo=True
            )
            usuario_cocina = models.Usuario(
                username="cocina1",
                nombre_completo="Chef Don Pedro - Cocina",
                hashed_password=hash_password("cocina123"),
                rol=models.RolUsuario.COCINA,
                activo=True
            )
            db.add_all([usuario_admin, usuario_mesero, usuario_cocina])
            db.commit()

        print("[+] Base de datos de San Parrilla poblada con éxito!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
