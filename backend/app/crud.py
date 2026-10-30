from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta, timezone
import unicodedata
import uuid
from typing import List, Optional

from app import models, schemas


def _normalizar_texto(texto: Optional[str]) -> str:
    if not texto:
        return ""
    s = unicodedata.normalize("NFD", str(texto).strip().lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


# --- CATÁLOGOS Y GESTIÓN DE PLATOS EN TIEMPO REAL ---

def get_categorias(db: Session) -> List[models.Categoria]:
    return db.query(models.Categoria).order_by(models.Categoria.orden).all()

def get_platos(
    db: Session,
    categoria_id: Optional[int] = None,
    solo_activos: bool = False,
) -> List[models.Plato]:
    query = db.query(models.Plato)
    if solo_activos:
        query = query.filter(models.Plato.activo == True)
    if categoria_id:
        query = query.filter(models.Plato.categoria_id == categoria_id)
    return query.order_by(models.Plato.categoria_id.asc(), models.Plato.id.asc()).all()


def update_plato(
    db: Session,
    plato_id: int,
    data: schemas.PlatoUpdate,
) -> models.Plato:
    plato = db.query(models.Plato).filter(models.Plato.id == plato_id).first()
    if not plato:
        raise LookupError(f"Plato con ID {plato_id} no encontrado.")

    if data.nombre is not None and data.nombre.strip():
        plato.nombre = data.nombre.strip()
    if data.descripcion is not None:
        plato.descripcion = data.descripcion.strip()
    if data.precio is not None and float(data.precio) >= 0:
        plato.precio = float(data.precio)
    if data.imagen_emoji is not None:
        plato.imagen_emoji = data.imagen_emoji
    if data.categoria_id is not None:
        plato.categoria_id = int(data.categoria_id)
    if data.disponible is not None:
        plato.disponible = bool(data.disponible)
        plato.activo = bool(data.disponible)
    elif data.activo is not None:
        plato.activo = bool(data.activo)
        plato.disponible = bool(data.activo)

    db.commit()
    db.refresh(plato)
    return plato


def update_plato_by_name(
    db: Session,
    nombre: str,
    data: schemas.PlatoUpdate,
) -> models.Plato:
    clean_name = (nombre or "").strip()
    if not clean_name:
        raise ValueError("El nombre del plato es obligatorio.")
    plato = (
        db.query(models.Plato)
        .filter(func.lower(models.Plato.nombre) == clean_name.lower())
        .first()
    )
    if not plato:
        norm_target = _normalizar_texto(clean_name)
        for p in db.query(models.Plato).all():
            if _normalizar_texto(p.nombre) == norm_target:
                plato = p
                break
    if not plato:
        plato = _resolver_o_crear_plato(db, None, clean_name, data.precio or 0.0)

    return update_plato(db, plato.id, data)


def bulk_update_plato_prices(
    db: Session,
    data: schemas.PlatoBulkPriceUpdate,
) -> List[models.Plato]:
    if data.nuevo_precio is None or float(data.nuevo_precio) <= 0:
        raise ValueError("El nuevo precio debe ser mayor a 0.")

    nuevo_precio = float(data.nuevo_precio)
    updated_platos: List[models.Plato] = []

    if data.plato_ids and len(data.plato_ids) > 0:
        platos = db.query(models.Plato).filter(models.Plato.id.in_(data.plato_ids)).all()
        for p in platos:
            p.precio = nuevo_precio
            updated_platos.append(p)
    elif data.nombres and len(data.nombres) > 0:
        norm_names = {_normalizar_texto(n) for n in data.nombres if n and n.strip()}
        all_platos = db.query(models.Plato).all()
        matched_norms = set()
        for p in all_platos:
            pn = _normalizar_texto(p.nombre)
            if pn in norm_names:
                p.precio = nuevo_precio
                updated_platos.append(p)
                matched_norms.add(pn)
        for raw_name in data.nombres:
            if raw_name and _normalizar_texto(raw_name) not in matched_norms:
                created = _resolver_o_crear_plato(db, None, raw_name.strip(), nuevo_precio)
                created.precio = nuevo_precio
                updated_platos.append(created)
    elif data.categoria_id is not None:
        query = db.query(models.Plato).filter(models.Plato.categoria_id == data.categoria_id)
        if data.precio_actual is not None:
            query = query.filter(models.Plato.precio == float(data.precio_actual))
        for p in query.all():
            p.precio = nuevo_precio
            updated_platos.append(p)
    elif data.precio_actual is not None:
        platos = db.query(models.Plato).filter(models.Plato.precio == float(data.precio_actual)).all()
        for p in platos:
            p.precio = nuevo_precio
            updated_platos.append(p)
    else:
        raise ValueError("Debe especificar plato_ids, nombres, categoria_id o precio_actual para actualizar en bloque.")

    db.commit()
    for p in updated_platos:
        db.refresh(p)
    return updated_platos


# --- DIRECTORIO DE CLIENTES Y CUENTAS DE FIADO ---

def _limpiar_telefono(telefono: Optional[str]) -> str:
    if not telefono:
        return ""
    raw = str(telefono).strip()
    digits = "".join(c for c in raw if c.isdigit())
    return digits or raw


def _extraer_direccion_y_barrio_de_notas(notas: Optional[str]):
    """Extrae dirección y barrio de las notas de un pedido si vienen embebidos."""
    if not notas:
        return None, None
    direccion = None
    barrio = None
    partes = [p.strip() for p in str(notas).split("|") if p.strip()]
    for p in partes:
        low = p.lower()
        if low.startswith("dirección:") or low.startswith("direccion:"):
            val = p.split(":", 1)[1].strip()
            if val:
                direccion = val
        elif low.startswith("barrio:") or low.startswith("indicaciones:"):
            val = p.split(":", 1)[1].strip()
            if val:
                barrio = val
    return direccion, barrio


def upsert_cliente(
    db: Session,
    nombre: Optional[str],
    telefono: Optional[str],
    direccion: Optional[str] = None,
    barrio: Optional[str] = None,
    notas: Optional[str] = None,
    allow_without_phone: bool = False,
) -> Optional[models.Cliente]:
    clean_phone = _limpiar_telefono(telefono)
    clean_name = (nombre or "").strip()

    GENERIC_NAMES = {
        "",
        "consumidor final",
        "cliente mostrador",
        "cliente",
        "mostrador",
        "mesa",
        "domicilio",
        "para llevar",
    }
    is_generic_name = _normalizar_texto(clean_name) in GENERIC_NAMES

    if not clean_phone:
        if not allow_without_phone or is_generic_name:
            return None
        existing_by_name = (
            db.query(models.Cliente)
            .filter(func.lower(models.Cliente.nombre) == clean_name.lower())
            .first()
        )
        if existing_by_name:
            if direccion and direccion.strip():
                existing_by_name.direccion = direccion.strip()
            if barrio and barrio.strip():
                existing_by_name.barrio = barrio.strip()
            if notas and notas.strip():
                existing_by_name.notas = notas.strip()
            db.flush()
            return existing_by_name

        synthetic_phone = f"SINTEL-{_normalizar_texto(clean_name)[:20].upper()}"
        existing_syn = db.query(models.Cliente).filter(models.Cliente.telefono == synthetic_phone).first()
        if existing_syn:
            return existing_syn
        nuevo = models.Cliente(
            nombre=clean_name,
            telefono=synthetic_phone,
            direccion=(direccion or "").strip() or None,
            barrio=(barrio or "").strip() or None,
            notas=(notas or "").strip() or None,
        )
        db.add(nuevo)
        db.flush()
        return nuevo

    cliente = db.query(models.Cliente).filter(models.Cliente.telefono == clean_phone).first()
    if not cliente and telefono and str(telefono).strip() != clean_phone:
        cliente = db.query(models.Cliente).filter(models.Cliente.telefono == str(telefono).strip()).first()

    if cliente:
        if clean_name and not is_generic_name:
            cliente.nombre = clean_name
        if clean_phone:
            cliente.telefono = clean_phone
        if direccion and direccion.strip():
            cliente.direccion = direccion.strip()
        if barrio and barrio.strip():
            cliente.barrio = barrio.strip()
        if notas and notas.strip():
            cliente.notas = notas.strip()
        db.flush()
        return cliente

    final_name = clean_name if (clean_name and not is_generic_name) else f"Cliente {clean_phone}"
    nuevo = models.Cliente(
        nombre=final_name,
        telefono=clean_phone,
        direccion=(direccion or "").strip() or None,
        barrio=(barrio or "").strip() or None,
        notas=(notas or "").strip() or None,
    )
    db.add(nuevo)
    db.flush()
    return nuevo


def _enrich_cliente_out(db: Session, c: models.Cliente, stats_map: Optional[dict] = None) -> schemas.ClienteOut:
    phone_key = _limpiar_telefono(c.telefono)
    st = (stats_map or {}).get(phone_key) or (stats_map or {}).get(c.id) or {}
    order_count = int(st.get("order_count", 0))
    total_fiado = float(st.get("total_fiado", 0.0))
    return schemas.ClienteOut(
        id=c.id,
        nombre=c.nombre,
        name=c.nombre,
        telefono=c.telefono,
        phone=c.telefono,
        direccion=c.direccion,
        address=c.direccion,
        barrio=c.barrio,
        notas=c.notas,
        notes=c.notas,
        created_at=c.created_at,
        total_pedidos=order_count,
        order_count=order_count,
        total_fiado=total_fiado,
    )


def search_clientes(
    db: Session,
    q: Optional[str] = None,
    telefono: Optional[str] = None,
    limit: int = 50,
) -> List[schemas.ClienteOut]:
    all_clientes = db.query(models.Cliente).order_by(models.Cliente.updated_at.desc(), models.Cliente.id.desc()).all()

    # Estadísticas rápidas por teléfono / cliente_id
    pedidos_activos = (
        db.query(models.Pedido)
        .filter(models.Pedido.estado != models.EstadoPedido.CANCELADO)
        .all()
    )
    stats_map = {}
    for ped in pedidos_activos:
        pk = _limpiar_telefono(ped.cliente_telefono)
        if pk:
            entry = stats_map.setdefault(pk, {"order_count": 0, "total_fiado": 0.0})
            entry["order_count"] += 1
            for pay in (ped.payments or []):
                if pay.method == models.PaymentMethod.FIADO:
                    entry["total_fiado"] += float(pay.amount or 0.0)
        if ped.cliente_id:
            entry_id = stats_map.setdefault(ped.cliente_id, {"order_count": 0, "total_fiado": 0.0})
            entry_id["order_count"] += 1
            for pay in (ped.payments or []):
                if pay.method == models.PaymentMethod.FIADO:
                    entry_id["total_fiado"] += float(pay.amount or 0.0)

    if telefono and str(telefono).strip():
        target_phone = _limpiar_telefono(telefono)
        matched = [
            c for c in all_clientes
            if _limpiar_telefono(c.telefono) == target_phone or str(c.telefono).strip() == str(telefono).strip()
        ]
        return [_enrich_cliente_out(db, c, stats_map) for c in matched[:limit]]

    query_str = (q or "").strip()
    if not query_str:
        return [_enrich_cliente_out(db, c, stats_map) for c in all_clientes[:limit]]

    norm_q = _normalizar_texto(query_str)
    digits_q = _limpiar_telefono(query_str)

    exact_matches = []
    partial_matches = []
    for c in all_clientes:
        c_phone = _limpiar_telefono(c.telefono)
        c_name = _normalizar_texto(c.nombre)
        c_dir = _normalizar_texto(c.direccion)
        c_barrio = _normalizar_texto(c.barrio)

        if (digits_q and c_phone == digits_q) or c_name == norm_q:
            exact_matches.append(c)
        elif (
            (digits_q and digits_q in c_phone)
            or (norm_q in c_name)
            or (norm_q in c_dir)
            or (norm_q in c_barrio)
        ):
            partial_matches.append(c)

    results = exact_matches + partial_matches
    return [_enrich_cliente_out(db, c, stats_map) for c in results[:limit]]


def update_cliente(
    db: Session,
    cliente_id: int,
    data: schemas.ClienteUpdate,
) -> schemas.ClienteOut:
    cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    if not cliente:
        raise LookupError(f"Cliente con ID {cliente_id} no encontrado.")

    if data.nombre is not None and data.nombre.strip():
        cliente.nombre = data.nombre.strip()
    if data.telefono is not None and data.telefono.strip():
        clean_p = _limpiar_telefono(data.telefono)
        other = (
            db.query(models.Cliente)
            .filter(models.Cliente.telefono == clean_p, models.Cliente.id != cliente.id)
            .first()
        )
        if not other:
            cliente.telefono = clean_p
    if data.direccion is not None:
        cliente.direccion = data.direccion.strip() or None
    if data.barrio is not None:
        cliente.barrio = data.barrio.strip() or None
    if data.notas is not None:
        cliente.notas = data.notas.strip() or None

    db.commit()
    db.refresh(cliente)
    return _enrich_cliente_out(db, cliente)


def liquidar_fiado_cliente(
    db: Session,
    data: schemas.LiquidarFiadoRequest,
) -> dict:
    """
    Marca como pagados todos los pedidos en FIADO seleccionados (o todos los pendientes de un cliente/teléfono),
    actualizando su método de pago a Efectivo (CASH), Nequi (NEQUI) o Bancolombia (BANCOLOMBIA) y dejando trazabilidad
    en las notas del pedido `[FIADO_PAGADO:METODO:FECHA]` para que sigan visibles en el filtro de 'Pagados' del módulo de Fiados.
    """
    target_method = data.payment_method or models.PaymentMethod.CASH
    if target_method == models.PaymentMethod.FIADO:
        raise ValueError("El método de liquidación debe ser Efectivo, Nequi, Bancolombia, Daviplata o Tarjeta.")

    query = (
        db.query(models.Pedido)
        .join(models.Payment, models.Payment.pedido_id == models.Pedido.id)
        .filter(
            models.Pedido.estado != models.EstadoPedido.CANCELADO,
            models.Payment.method == models.PaymentMethod.FIADO,
        )
    )

    if data.pedido_ids and len(data.pedido_ids) > 0:
        query = query.filter(models.Pedido.id.in_(data.pedido_ids))
    elif data.cliente_id:
        cliente = db.query(models.Cliente).filter(models.Cliente.id == data.cliente_id).first()
        if cliente:
            clean_p = _limpiar_telefono(cliente.telefono)
            query = query.filter(
                (models.Pedido.cliente_id == cliente.id)
                | (models.Pedido.cliente_telefono == clean_p)
                | (func.lower(models.Pedido.cliente_nombre) == cliente.nombre.lower())
            )
        else:
            query = query.filter(models.Pedido.cliente_id == data.cliente_id)
    elif data.cliente_telefono and data.cliente_telefono.strip():
        clean_p = _limpiar_telefono(data.cliente_telefono)
        query = query.filter(
            (models.Pedido.cliente_telefono == clean_p)
            | (models.Pedido.cliente_telefono == data.cliente_telefono.strip())
        )
    elif data.cliente_nombre and data.cliente_nombre.strip():
        clean_n = data.cliente_nombre.strip().lower()
        query = query.filter(func.lower(models.Pedido.cliente_nombre) == clean_n)
    else:
        raise ValueError("Debe especificar pedido_ids, cliente_id, cliente_telefono o cliente_nombre para liquidar el fiado.")

    pedidos_fiado = query.all()
    if not pedidos_fiado:
        return {"liquidados": 0, "monto_total": 0.0, "pedido_ids": []}

    tz_col = timezone(timedelta(hours=-5))
    fecha_liq = datetime.now(tz_col).strftime("%Y-%m-%d %H:%M")
    tag_liq = f"[FIADO_PAGADO:{target_method.value}:{fecha_liq}]"

    caja_activa = get_active_cash_closure(db)
    affected_closures = set()
    if caja_activa:
        affected_closures.add(caja_activa.id)

    monto_total = 0.0
    liquidados_ids = []

    for ped in pedidos_fiado:
        for pay in (ped.payments or []):
            if pay.method == models.PaymentMethod.FIADO:
                if pay.cash_closure_id:
                    affected_closures.add(pay.cash_closure_id)
                if caja_activa:
                    pay.cash_closure_id = caja_activa.id
                pay.method = target_method
                monto_total += float(pay.amount or 0.0)
        ped.estado = models.EstadoPedido.PAGADO
        cur_notas = ped.notas or ""
        if "[FIADO_PAGADO:" not in cur_notas:
            ped.notas = f"{cur_notas} | {tag_liq}".strip(" |") if cur_notas else tag_liq
        liquidados_ids.append(ped.id)

    db.flush()
    for cid in affected_closures:
        closure = db.query(models.CashClosure).filter(models.CashClosure.id == cid).first()
        if closure:
            calcular_resumen_caja(db, closure)

    db.commit()
    return {
        "liquidados": len(liquidados_ids),
        "monto_total": monto_total,
        "metodo_pago": target_method.value,
        "pedido_ids": liquidados_ids,
    }

def get_sopas(db: Session) -> List[models.Sopa]:
    return db.query(models.Sopa).filter(models.Sopa.activo == True).all()

def get_principios(db: Session) -> List[models.Principio]:
    return db.query(models.Principio).filter(models.Principio.activo == True).all()

def get_acompanamientos(db: Session) -> List[models.Acompanamiento]:
    return db.query(models.Acompanamiento).filter(models.Acompanamiento.activo == True).all()


# --- MENÚ DEL DÍA Y GESTIÓN DE STOCK ---

def get_menu_dia_by_fecha(db: Session, fecha_consulta: date) -> Optional[models.MenuDia]:
    return db.query(models.MenuDia).filter(models.MenuDia.fecha == fecha_consulta).first()

def crear_o_actualizar_menu_dia(db: Session, menu_in: schemas.MenuDiaCreate) -> models.MenuDia:
    menu = get_menu_dia_by_fecha(db, menu_in.fecha)
    if not menu:
        menu = models.MenuDia(fecha=menu_in.fecha, notas=menu_in.notas)
        db.add(menu)
        db.commit()
        db.refresh(menu)
    else:
        if menu_in.notas:
            menu.notas = menu_in.notas

    # Reemplazar o actualizar items
    db.query(models.MenuDiaItem).filter(models.MenuDiaItem.menu_dia_id == menu.id).delete()
    db.commit()

    for item in menu_in.items:
        db_item = models.MenuDiaItem(
            menu_dia_id=menu.id,
            tipo_item=item.tipo_item,
            sopa_id=item.sopa_id,
            principio_id=item.principio_id,
            acompanamiento_id=item.acompanamiento_id,
            cantidad_preparada=item.cantidad_preparada,
            cantidad_vendida=0
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(menu)

    return menu


# --- PEDIDOS, BORRADORES WEB Y DESCUENTO AUTOMÁTICO DE STOCK ---

def _verificar_y_descontar_stock(
    db: Session,
    detalles: List[models.DetallePedido],
    menu_hoy: Optional[models.MenuDia],
    verificar_disponibilidad: bool = False
) -> None:
    """
    Verifica opcionalmente que exista stock suficiente en MenuDiaItem y descuenta las unidades
    correspondientes a sopa, principio y acompañamiento del menú del día.
    """
    if not menu_hoy:
        return

    if verificar_disponibilidad:
        req_sopas = {}
        req_principios = {}
        req_acomp = {}
        for det in detalles:
            cant = det.cantidad or 1
            if det.sopa_id:
                req_sopas[det.sopa_id] = req_sopas.get(det.sopa_id, 0) + cant
            if det.principio_id:
                req_principios[det.principio_id] = req_principios.get(det.principio_id, 0) + cant
            if det.acompanamiento_id:
                req_acomp[det.acompanamiento_id] = req_acomp.get(det.acompanamiento_id, 0) + cant

        for sopa_id, cant_req in req_sopas.items():
            item_sopa = db.query(models.MenuDiaItem).filter(
                models.MenuDiaItem.menu_dia_id == menu_hoy.id,
                models.MenuDiaItem.sopa_id == sopa_id
            ).first()
            if item_sopa and item_sopa.disponible < cant_req:
                nombre = item_sopa.sopa.nombre if item_sopa.sopa else f"Sopa ID {sopa_id}"
                raise ValueError(f"Stock insuficiente para '{nombre}': disponible {item_sopa.disponible}, solicitado {cant_req}.")

        for principio_id, cant_req in req_principios.items():
            item_principio = db.query(models.MenuDiaItem).filter(
                models.MenuDiaItem.menu_dia_id == menu_hoy.id,
                models.MenuDiaItem.principio_id == principio_id
            ).first()
            if item_principio and item_principio.disponible < cant_req:
                nombre = item_principio.principio.nombre if item_principio.principio else f"Principio ID {principio_id}"
                raise ValueError(f"Stock insuficiente para '{nombre}': disponible {item_principio.disponible}, solicitado {cant_req}.")

        for acomp_id, cant_req in req_acomp.items():
            item_acomp = db.query(models.MenuDiaItem).filter(
                models.MenuDiaItem.menu_dia_id == menu_hoy.id,
                models.MenuDiaItem.acompanamiento_id == acomp_id
            ).first()
            if item_acomp and item_acomp.disponible < cant_req:
                nombre = item_acomp.acompanamiento.nombre if item_acomp.acompanamiento else f"Acompañamiento ID {acomp_id}"
                raise ValueError(f"Stock insuficiente para '{nombre}': disponible {item_acomp.disponible}, solicitado {cant_req}.")

    for det in detalles:
        if det.sopa_id:
            item_sopa = db.query(models.MenuDiaItem).filter(
                models.MenuDiaItem.menu_dia_id == menu_hoy.id,
                models.MenuDiaItem.sopa_id == det.sopa_id
            ).first()
            if item_sopa:
                item_sopa.cantidad_vendida += det.cantidad

        if det.principio_id:
            item_principio = db.query(models.MenuDiaItem).filter(
                models.MenuDiaItem.menu_dia_id == menu_hoy.id,
                models.MenuDiaItem.principio_id == det.principio_id
            ).first()
            if item_principio:
                item_principio.cantidad_vendida += det.cantidad

        if det.acompanamiento_id:
            item_acomp = db.query(models.MenuDiaItem).filter(
                models.MenuDiaItem.menu_dia_id == menu_hoy.id,
                models.MenuDiaItem.acompanamiento_id == det.acompanamiento_id
            ).first()
            if item_acomp:
                item_acomp.cantidad_vendida += det.cantidad


def _resolver_o_crear_plato(
    db: Session,
    plato_id: Optional[int],
    nombre_plato: Optional[str],
    precio_unitario: Optional[float],
) -> models.Plato:
    """
    Busca el plato por nombre exacto (case-insensitive) si se proporciona `nombre_plato`;
    si no existe en la tabla `platos`, lo crea automáticamente con su nombre y precio real.
    Si no viene `nombre_plato`, busca por `plato_id`.
    """
    clean_name = (nombre_plato or "").strip()
    if clean_name:
        plato = (
            db.query(models.Plato)
            .filter(func.lower(models.Plato.nombre) == clean_name.lower())
            .first()
        )
        if plato:
            return plato

        # Crear el plato automáticamente para mantener integridad referencial y métricas reales
        cat = db.query(models.Categoria).order_by(models.Categoria.orden.asc()).first()
        if not cat:
            cat = models.Categoria(
                nombre="Menú San Parrilla",
                descripcion="Platos generales del POS",
                orden=1,
            )
            db.add(cat)
            db.flush()

        nuevo_plato = models.Plato(
            nombre=clean_name,
            descripcion="Registrado desde POS",
            precio=float(precio_unitario or 0.0),
            imagen_emoji="🍽️",
            activo=True,
            categoria_id=cat.id,
        )
        db.add(nuevo_plato)
        db.flush()
        return nuevo_plato

    if plato_id is not None:
        plato = db.query(models.Plato).filter(models.Plato.id == plato_id).first()
        if plato:
            return plato

    # Fallback de seguridad al primer plato o creación de uno genérico
    plato = db.query(models.Plato).first()
    if plato:
        return plato

    cat = models.Categoria(nombre="General", descripcion="General", orden=1)
    db.add(cat)
    db.flush()
    plato = models.Plato(
        nombre="Plato POS",
        descripcion="Plato general",
        precio=float(precio_unitario or 0.0),
        activo=True,
        categoria_id=cat.id,
    )
    db.add(plato)
    db.flush()
    return plato


def crear_pedido(db: Session, pedido_in: schemas.PedidoCreate) -> models.Pedido:
    hoy = date.today()
    menu_hoy = get_menu_dia_by_fecha(db, hoy)
    
    codigo = f"SP-{uuid.uuid4().hex[:6].upper()}"
    if pedido_in.es_borrador_web:
        estado_inicial = models.EstadoPedido.BORRADOR_WEB
    elif pedido_in.estado is not None:
        estado_inicial = pedido_in.estado
    else:
        estado_inicial = models.EstadoPedido.PENDIENTE
    delivery_fee = float(pedido_in.delivery_fee or 0.0)
    packaging_fee = float(pedido_in.packaging_fee or 0.0)
    courier_name = (pedido_in.courier_name or "").strip() or None

    notas_pedido = pedido_in.notas or ""
    if pedido_in.direccion and pedido_in.direccion.strip():
        dir_str = pedido_in.direccion.strip()
        if dir_str not in notas_pedido:
            notas_pedido = f"Dirección: {dir_str}" + (f" | {notas_pedido}" if notas_pedido else "")
    if pedido_in.barrio and pedido_in.barrio.strip():
        barrio_str = pedido_in.barrio.strip()
        if barrio_str not in notas_pedido:
            notas_pedido = f"{notas_pedido} | Barrio: {barrio_str}".strip(" |")

    dir_extraida, barrio_extraido = _extraer_direccion_y_barrio_de_notas(notas_pedido)
    cliente_obj = upsert_cliente(
        db,
        nombre=pedido_in.cliente_nombre,
        telefono=pedido_in.cliente_telefono,
        direccion=pedido_in.direccion or dir_extraida,
        barrio=pedido_in.barrio or barrio_extraido,
        allow_without_phone=False,
    )

    nuevo_pedido = models.Pedido(
        codigo_pedido=codigo,
        cliente_id=cliente_obj.id if cliente_obj else pedido_in.cliente_id,
        cliente_nombre=pedido_in.cliente_nombre,
        cliente_telefono=pedido_in.cliente_telefono,
        mesa=pedido_in.mesa,
        tipo=pedido_in.tipo,
        estado=estado_inicial,
        courier_name=courier_name,
        notas=notas_pedido or None,
        subtotal=0.0,
        delivery_fee=delivery_fee,
        packaging_fee=packaging_fee,
        total=0.0
    )
    db.add(nuevo_pedido)
    db.flush()

    subtotal_calculado = 0.0
    detalles_creados: List[models.DetallePedido] = []

    for det in pedido_in.detalles:
        plato = _resolver_o_crear_plato(db, det.plato_id, det.nombre_plato, det.precio_unitario)
        if not plato:
            continue

        precio_item = (
            float(det.precio_unitario)
            if (det.precio_unitario is not None and det.precio_unitario > 0)
            else float(plato.precio)
        )
        subtotal_item = precio_item * det.cantidad
        subtotal_calculado += subtotal_item
        notas_item = det.notas_item if det.notas_item is not None else det.notas

        detalle_db = models.DetallePedido(
            pedido_id=nuevo_pedido.id,
            plato_id=plato.id,
            sopa_id=det.sopa_id,
            principio_id=det.principio_id,
            acompanamiento_id=det.acompanamiento_id,
            cantidad=det.cantidad,
            precio_unitario=precio_item,
            notas_item=notas_item
        )
        db.add(detalle_db)
        detalles_creados.append(detalle_db)

    # REGLA CRÍTICA DE STOCK:
    # Si es_borrador_web=True, queda en BORRADOR_WEB y NO descuenta stock todavía.
    if not pedido_in.es_borrador_web:
        _verificar_y_descontar_stock(db, detalles_creados, menu_hoy, verificar_disponibilidad=False)

    nuevo_pedido.subtotal = subtotal_calculado
    nuevo_pedido.packaging_fee = packaging_fee
    nuevo_pedido.total = subtotal_calculado + delivery_fee + packaging_fee
    db.commit()
    db.refresh(nuevo_pedido)
    return nuevo_pedido


def aprobar_pedido_borrador(
    db: Session,
    pedido_id: int,
    datos_aprobacion: Optional[schemas.PedidoApprove] = None
) -> models.Pedido:
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise LookupError("Pedido no encontrado.")

    if pedido.estado != models.EstadoPedido.BORRADOR_WEB:
        raise ValueError(
            f"El pedido no está en estado BORRADOR_WEB (estado actual: {pedido.estado.value})."
        )

    if datos_aprobacion:
        if datos_aprobacion.cliente_nombre is not None:
            pedido.cliente_nombre = datos_aprobacion.cliente_nombre
        if datos_aprobacion.cliente_telefono is not None:
            pedido.cliente_telefono = datos_aprobacion.cliente_telefono
        if datos_aprobacion.mesa is not None:
            pedido.mesa = datos_aprobacion.mesa
        if datos_aprobacion.tipo is not None:
            pedido.tipo = datos_aprobacion.tipo
        if datos_aprobacion.courier_name is not None:
            pedido.courier_name = datos_aprobacion.courier_name.strip() or None
        if datos_aprobacion.delivery_fee is not None:
            pedido.delivery_fee = float(datos_aprobacion.delivery_fee)
        if datos_aprobacion.packaging_fee is not None:
            pedido.packaging_fee = float(datos_aprobacion.packaging_fee)
        if datos_aprobacion.notas is not None:
            pedido.notas = datos_aprobacion.notas

        if datos_aprobacion.detalles is not None:
            if len(datos_aprobacion.detalles) == 0:
                raise ValueError("El pedido debe conservar al menos un ítem al aprobarse.")

            # Reemplazar los ítems del borrador con los actualizados por el cajero
            db.query(models.DetallePedido).filter(
                models.DetallePedido.pedido_id == pedido.id
            ).delete()
            db.flush()

            nuevo_subtotal = 0.0
            nuevos_detalles: List[models.DetallePedido] = []
            for det in datos_aprobacion.detalles:
                plato = _resolver_o_crear_plato(db, det.plato_id, det.nombre_plato, det.precio_unitario)
                if not plato:
                    raise ValueError(f"Plato con id {det.plato_id} no encontrado.")
                precio_item = (
                    float(det.precio_unitario)
                    if (det.precio_unitario is not None and det.precio_unitario > 0)
                    else float(plato.precio)
                )
                nuevo_subtotal += precio_item * det.cantidad
                notas_item = det.notas_item if det.notas_item is not None else det.notas
                detalle_db = models.DetallePedido(
                    pedido_id=pedido.id,
                    plato_id=plato.id,
                    sopa_id=det.sopa_id,
                    principio_id=det.principio_id,
                    acompanamiento_id=det.acompanamiento_id,
                    cantidad=det.cantidad,
                    precio_unitario=precio_item,
                    notas_item=notas_item
                )
                db.add(detalle_db)
                nuevos_detalles.append(detalle_db)

            db.flush()
            db.refresh(pedido)
            pedido.subtotal = nuevo_subtotal

    # Asegurar consistencia de subtotal y total
    if not pedido.subtotal and pedido.detalles:
        pedido.subtotal = sum(d.precio_unitario * d.cantidad for d in pedido.detalles)
    pedido.delivery_fee = float(pedido.delivery_fee or 0.0)
    pedido.packaging_fee = float(pedido.packaging_fee or 0.0)
    pedido.total = (pedido.subtotal or 0.0) + pedido.delivery_fee + pedido.packaging_fee

    # Verificar disponibilidad y descontar stock en MenuDiaItem
    hoy = date.today()
    menu_hoy = get_menu_dia_by_fecha(db, hoy)
    _verificar_y_descontar_stock(db, pedido.detalles, menu_hoy, verificar_disponibilidad=True)

    dir_extraida, barrio_extraido = _extraer_direccion_y_barrio_de_notas(pedido.notas)
    cliente_obj = upsert_cliente(
        db,
        nombre=pedido.cliente_nombre,
        telefono=pedido.cliente_telefono,
        direccion=dir_extraida,
        barrio=barrio_extraido,
        allow_without_phone=False,
    )
    if cliente_obj:
        pedido.cliente_id = cliente_obj.id

    pedido.estado = models.EstadoPedido.PENDIENTE
    db.commit()
    db.refresh(pedido)
    return pedido


def asignar_mensajero_pedido(
    db: Session,
    pedido_id: int,
    data: schemas.PedidoAssignCourier,
) -> models.Pedido:
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise LookupError("Pedido no encontrado.")

    if data.courier_name is not None:
        pedido.courier_name = data.courier_name.strip() or None
    if data.estado is not None:
        pedido.estado = data.estado

    db.commit()
    db.refresh(pedido)
    return pedido


def actualizar_pedido(
    db: Session,
    pedido_id: int,
    data: schemas.PedidoUpdate,
) -> models.Pedido:
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise LookupError("Pedido no encontrado.")

    if data.cliente_nombre is not None:
        pedido.cliente_nombre = data.cliente_nombre
    if data.cliente_telefono is not None:
        pedido.cliente_telefono = data.cliente_telefono
    if data.mesa is not None:
        pedido.mesa = data.mesa
    if data.tipo is not None:
        pedido.tipo = data.tipo
    if data.courier_name is not None:
        pedido.courier_name = data.courier_name.strip() or None
    if data.delivery_fee is not None:
        pedido.delivery_fee = float(data.delivery_fee)
    if data.packaging_fee is not None:
        pedido.packaging_fee = float(data.packaging_fee)
    if data.notas is not None:
        notas_str = data.notas
        if data.direccion and data.direccion.strip() and data.direccion.strip() not in notas_str:
            notas_str = f"Dirección: {data.direccion.strip()}" + (f" | {notas_str}" if notas_str else "")
        pedido.notas = notas_str or None
    elif data.direccion and data.direccion.strip():
        cur_notas = pedido.notas or ""
        if data.direccion.strip() not in cur_notas:
            pedido.notas = f"Dirección: {data.direccion.strip()}" + (f" | {cur_notas}" if cur_notas else "")

    if data.detalles is not None and len(data.detalles) > 0:
        db.query(models.DetallePedido).filter(
            models.DetallePedido.pedido_id == pedido.id
        ).delete()
        db.flush()

        nuevo_subtotal = 0.0
        for det in data.detalles:
            plato = _resolver_o_crear_plato(db, det.plato_id, det.nombre_plato, det.precio_unitario)
            if not plato:
                continue
            precio_item = (
                float(det.precio_unitario)
                if (det.precio_unitario is not None and det.precio_unitario > 0)
                else float(plato.precio)
            )
            nuevo_subtotal += precio_item * det.cantidad
            notas_item = det.notas_item if det.notas_item is not None else det.notas
            detalle_db = models.DetallePedido(
                pedido_id=pedido.id,
                plato_id=plato.id,
                sopa_id=det.sopa_id,
                principio_id=det.principio_id,
                acompanamiento_id=det.acompanamiento_id,
                cantidad=det.cantidad,
                precio_unitario=precio_item,
                notas_item=notas_item,
            )
            db.add(detalle_db)
        db.flush()
        pedido.subtotal = nuevo_subtotal

    pedido.delivery_fee = float(pedido.delivery_fee or 0.0)
    pedido.packaging_fee = float(pedido.packaging_fee or 0.0)
    if not pedido.subtotal and pedido.detalles:
        pedido.subtotal = sum(d.precio_unitario * d.cantidad for d in pedido.detalles)
    pedido.total = float(pedido.subtotal or 0.0) + pedido.delivery_fee + pedido.packaging_fee

    dir_extraida, barrio_extraido = _extraer_direccion_y_barrio_de_notas(pedido.notas)
    cliente_obj = upsert_cliente(
        db,
        nombre=pedido.cliente_nombre,
        telefono=pedido.cliente_telefono,
        direccion=data.direccion or dir_extraida,
        barrio=data.barrio or barrio_extraido,
        allow_without_phone=False,
    )
    if cliente_obj:
        pedido.cliente_id = cliente_obj.id
    elif data.cliente_id:
        pedido.cliente_id = data.cliente_id

    affected_closure_ids = {p.cash_closure_id for p in (pedido.payments or []) if p.cash_closure_id}
    if data.estado is not None:
        pedido.estado = data.estado
        if data.estado == models.EstadoPedido.CANCELADO:
            db.query(models.Payment).filter(models.Payment.pedido_id == pedido.id).delete()
            db.flush()
    elif pedido.payments and len(pedido.payments) == 1:
        pedido.payments[0].amount = float(pedido.total)
        db.flush()

    activa = get_active_cash_closure(db)
    if activa:
        affected_closure_ids.add(activa.id)

    for cid in affected_closure_ids:
        closure = db.query(models.CashClosure).filter(models.CashClosure.id == cid).first()
        if closure:
            calcular_resumen_caja(db, closure)

    db.commit()
    db.refresh(pedido)
    return pedido


def cambiar_metodo_pago_pedido(
    db: Session,
    pedido_id: int,
    data: schemas.PedidoUpdatePaymentMethod,
) -> models.Pedido:
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise LookupError("Pedido no encontrado.")

    if data.cliente_nombre is not None:
        pedido.cliente_nombre = data.cliente_nombre
    if data.cliente_telefono is not None:
        pedido.cliente_telefono = data.cliente_telefono
    if data.mesa is not None:
        pedido.mesa = data.mesa
    if data.courier_name is not None:
        pedido.courier_name = data.courier_name.strip() or None
    if data.delivery_fee is not None:
        pedido.delivery_fee = float(data.delivery_fee)
    if data.packaging_fee is not None:
        pedido.packaging_fee = float(data.packaging_fee)
    if data.notas is not None:
        pedido.notas = data.notas

    pedido.delivery_fee = float(pedido.delivery_fee or 0.0)
    pedido.packaging_fee = float(pedido.packaging_fee or 0.0)
    if not pedido.subtotal and pedido.detalles:
        pedido.subtotal = sum(d.precio_unitario * d.cantidad for d in pedido.detalles)
    pedido.total = float(pedido.subtotal or 0.0) + pedido.delivery_fee + pedido.packaging_fee

    pagos_existentes = (
        db.query(models.Payment)
        .filter(models.Payment.pedido_id == pedido.id)
        .order_by(models.Payment.id.asc())
        .all()
    )
    affected_closure_ids = {p.cash_closure_id for p in pagos_existentes if p.cash_closure_id}
    caja_activa = get_active_cash_closure(db)
    if caja_activa:
        affected_closure_ids.add(caja_activa.id)

    # Si el administrador decide ANULAR / CANCELAR el pedido
    if data.estado == models.EstadoPedido.CANCELADO:
        for p in pagos_existentes:
            db.delete(p)
        pedido.estado = models.EstadoPedido.CANCELADO
        db.flush()
        for cid in affected_closure_ids:
            closure = db.query(models.CashClosure).filter(models.CashClosure.id == cid).first()
            if closure:
                calcular_resumen_caja(db, closure)
        db.commit()
        db.refresh(pedido)
        return pedido

    target_method = data.method or data.payment_method
    has_fiado = (target_method == models.PaymentMethod.FIADO) or any(
        p.method == models.PaymentMethod.FIADO for p in (data.payments or [])
    )
    dir_extraida, barrio_extraido = _extraer_direccion_y_barrio_de_notas(pedido.notas)
    cliente_obj = upsert_cliente(
        db,
        nombre=pedido.cliente_nombre,
        telefono=pedido.cliente_telefono,
        direccion=dir_extraida,
        barrio=barrio_extraido,
        allow_without_phone=has_fiado,
    )
    if cliente_obj:
        pedido.cliente_id = cliente_obj.id

    target_closure_id = (
        pagos_existentes[0].cash_closure_id
        if pagos_existentes
        else (caja_activa.id if caja_activa else None)
    )
    if not target_closure_id:
        last_closure = (
            db.query(models.CashClosure)
            .order_by(models.CashClosure.opened_at.desc(), models.CashClosure.id.desc())
            .first()
        )
        if last_closure:
            target_closure_id = last_closure.id
            affected_closure_ids.add(last_closure.id)

    if data.payments and len(data.payments) > 0:
        if not target_closure_id:
            raise ValueError("No hay una sesión de caja disponible para vincular el pago.")
        for p in pagos_existentes:
            db.delete(p)
        db.flush()
        for p_in in data.payments:
            db.add(
                models.Payment(
                    pedido_id=pedido.id,
                    cash_closure_id=target_closure_id,
                    method=p_in.method,
                    amount=float(p_in.amount),
                    change_given=float(p_in.change_given or 0.0),
                )
            )
        pedido.estado = data.estado or models.EstadoPedido.PAGADO
    elif target_method is not None:
        if pagos_existentes:
            primary_payment = pagos_existentes[0]
            primary_payment.method = target_method
            primary_payment.amount = float(pedido.total or 0.0)
            if target_method != models.PaymentMethod.CASH:
                primary_payment.change_given = 0.0
            for extra_p in pagos_existentes[1:]:
                db.delete(extra_p)
        else:
            if not target_closure_id:
                raise ValueError("No hay una sesión de caja abierta para registrar este pago.")
            db.add(
                models.Payment(
                    pedido_id=pedido.id,
                    cash_closure_id=target_closure_id,
                    method=target_method,
                    amount=float(pedido.total or 0.0),
                    change_given=0.0,
                )
            )
        pedido.estado = data.estado or models.EstadoPedido.PAGADO
    else:
        # Si solo se actualizaron datos del pedido (ej. delivery_fee) y tiene 1 pago, ajustar su monto
        if len(pagos_existentes) == 1:
            pagos_existentes[0].amount = float(pedido.total or 0.0)
        if data.estado is not None:
            pedido.estado = data.estado

    db.flush()

    # CRÍTICO CONTABLE: Recalcular inmediatamente todas las cajas afectadas
    for cid in affected_closure_ids:
        closure = db.query(models.CashClosure).filter(models.CashClosure.id == cid).first()
        if closure:
            calcular_resumen_caja(db, closure)

    db.commit()
    db.refresh(pedido)
    return pedido


# --- CIERRES DE CAJA (CASH CLOSURES) Y PAGOS (PAYMENTS) ---

def get_active_cash_closure(db: Session) -> Optional[models.CashClosure]:
    return (
        db.query(models.CashClosure)
        .filter(models.CashClosure.status == models.CashClosureStatus.OPEN)
        .order_by(models.CashClosure.opened_at.desc())
        .first()
    )


def calcular_resumen_caja(db: Session, closure: models.CashClosure) -> schemas.CashClosureOut:
    """
    Calcula en tiempo real los totales de la caja a partir de sus pagos (payments)
    y los pedidos asociados, separando ventas de restaurante (subtotal) y domicilios (delivery_fee).
    """
    pagos = (
        db.query(models.Payment)
        .join(models.Pedido, models.Payment.pedido_id == models.Pedido.id)
        .filter(
            models.Payment.cash_closure_id == closure.id,
            models.Pedido.estado != models.EstadoPedido.CANCELADO,
        )
        .all()
    )

    total_cash = sum(p.amount for p in pagos if p.method == models.PaymentMethod.CASH)
    total_nequi = sum(p.amount for p in pagos if p.method == models.PaymentMethod.NEQUI)
    total_bancolombia = sum(p.amount for p in pagos if p.method == models.PaymentMethod.BANCOLOMBIA)
    total_daviplata = sum(p.amount for p in pagos if p.method == models.PaymentMethod.DAVIPLATA)
    total_transfer = total_nequi + total_bancolombia + total_daviplata
    total_card = sum(p.amount for p in pagos if p.method == models.PaymentMethod.CARD)
    # Regla Contable Crítica: FIADO NO suma a total_cash ni expected_cash, sino a total_credit_sales
    total_credit = sum(p.amount for p in pagos if p.method == models.PaymentMethod.FIADO)

    pedido_ids = {p.pedido_id for p in pagos}
    if pedido_ids:
        pedidos_caja = (
            db.query(models.Pedido)
            .filter(
                models.Pedido.id.in_(pedido_ids),
                models.Pedido.estado != models.EstadoPedido.CANCELADO,
            )
            .all()
        )
    else:
        pedidos_caja = []

    # Gastos de caja menor registrados en este turno
    gastos = (
        db.query(models.CashExpense)
        .filter(models.CashExpense.cash_closure_id == closure.id)
        .order_by(models.CashExpense.created_at.asc())
        .all()
    )
    total_expenses = sum(float(g.amount or 0.0) for g in gastos)

    total_delivery_payouts = sum(float(ped.delivery_fee or 0.0) for ped in pedidos_caja)
    total_delivery_fees = total_delivery_payouts
    subtotal_sales = sum(float(ped.subtotal or 0.0) + float(ped.packaging_fee or 0.0) for ped in pedidos_caja)
    total_sales = total_cash + total_transfer + total_card
    expected_cash = float(closure.initial_cash or 0.0) + total_cash - total_delivery_payouts - total_expenses

    # Sincronizar campos acumulados en el modelo
    closure.total_cash_sales = total_cash
    closure.total_nequi_sales = total_nequi
    closure.total_bancolombia_sales = total_bancolombia
    closure.total_daviplata_sales = total_daviplata
    closure.total_transfer_sales = total_transfer
    closure.total_card_sales = total_card
    closure.total_credit_sales = total_credit
    closure.total_delivery_fees = total_delivery_fees
    closure.total_delivery_payouts = total_delivery_payouts
    closure.total_expenses = total_expenses
    closure.expected_cash = expected_cash
    if closure.counted_cash is not None:
        closure.discrepancy = float(closure.counted_cash) - expected_cash

    return schemas.CashClosureOut(
        id=closure.id,
        opened_at=closure.opened_at,
        closed_at=closure.closed_at,
        status=closure.status,
        initial_cash=closure.initial_cash,
        total_cash_sales=total_cash,
        total_nequi_sales=total_nequi,
        total_bancolombia_sales=total_bancolombia,
        total_daviplata_sales=total_daviplata,
        total_transfer_sales=total_transfer,
        total_card_sales=total_card,
        total_credit_sales=total_credit,
        total_delivery_fees=total_delivery_fees,
        total_delivery_payouts=total_delivery_payouts,
        total_expenses=total_expenses,
        subtotal_sales=subtotal_sales,
        total_sales=total_sales,
        expected_cash=expected_cash,
        counted_cash=closure.counted_cash,
        discrepancy=closure.discrepancy,
        notes=closure.notes,
        payments=[schemas.PaymentOut.model_validate(p) for p in pagos],
        expenses=[schemas.CashExpenseOut.model_validate(g) for g in gastos]
    )


def open_cash_closure(db: Session, open_in: schemas.CashClosureOpen) -> models.CashClosure:
    activa = get_active_cash_closure(db)
    if activa:
        raise ValueError("Ya existe una caja abierta (OPEN). Debe cerrarla antes de abrir una nueva.")

    initial_cash = float(open_in.initial_cash or 0.0)
    nueva_caja = models.CashClosure(
        status=models.CashClosureStatus.OPEN,
        initial_cash=initial_cash,
        total_cash_sales=0.0,
        total_nequi_sales=0.0,
        total_bancolombia_sales=0.0,
        total_daviplata_sales=0.0,
        total_transfer_sales=0.0,
        total_card_sales=0.0,
        total_credit_sales=0.0,
        total_delivery_fees=0.0,
        total_delivery_payouts=0.0,
        total_expenses=0.0,
        expected_cash=initial_cash,
        notes=open_in.notes
    )
    db.add(nueva_caja)
    db.commit()
    db.refresh(nueva_caja)
    return nueva_caja


def create_cash_expense(db: Session, closure_id: int, expense_in: schemas.CashExpenseCreate) -> models.CashExpense:
    gasto = models.CashExpense(
        cash_closure_id=closure_id,
        description=expense_in.description.strip(),
        category=(expense_in.category or "INSUMOS").strip().upper(),
        amount=float(expense_in.amount),
    )
    db.add(gasto)
    db.commit()
    db.refresh(gasto)
    return gasto


def get_cash_expenses(db: Session, closure_id: int) -> List[models.CashExpense]:
    return (
        db.query(models.CashExpense)
        .filter(models.CashExpense.cash_closure_id == closure_id)
        .order_by(models.CashExpense.created_at.asc())
        .all()
    )


def close_cash_closure(db: Session, close_in: schemas.CashClosureClose) -> schemas.CashClosureOut:
    activa = get_active_cash_closure(db)
    if not activa:
        raise LookupError("No hay ninguna caja abierta (OPEN) para cerrar.")

    resumen = calcular_resumen_caja(db, activa)
    counted = float(close_in.counted_cash)
    expected = float(resumen.expected_cash)
    discrepancy = counted - expected

    activa.counted_cash = counted
    activa.expected_cash = expected
    activa.discrepancy = discrepancy
    activa.closed_at = datetime.now(timezone.utc)
    activa.status = models.CashClosureStatus.CLOSED
    if close_in.notes is not None:
        activa.notes = close_in.notes

    db.commit()
    db.refresh(activa)
    return calcular_resumen_caja(db, activa)


def list_cash_closures_history(db: Session, limit: int = 50) -> List[schemas.CashClosureOut]:
    closures = (
        db.query(models.CashClosure)
        .order_by(models.CashClosure.opened_at.desc(), models.CashClosure.id.desc())
        .limit(limit)
        .all()
    )
    return [calcular_resumen_caja(db, c) for c in closures]


def pagar_pedido(
    db: Session,
    pedido_id: int,
    pagos_in: List[schemas.PaymentCreate]
) -> models.Pedido:
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise LookupError("Pedido no encontrado.")

    if pedido.estado == models.EstadoPedido.CANCELADO:
        raise ValueError("No se puede pagar un pedido CANCELADO.")
    if pedido.estado == models.EstadoPedido.PAGADO:
        raise ValueError("El pedido ya se encuentra PAGADO.")
    if pedido.estado == models.EstadoPedido.BORRADOR_WEB:
        raise ValueError("El pedido está en BORRADOR_WEB. Debe ser aprobado antes de registrar el pago.")

    if not pagos_in:
        raise ValueError("Debe proporcionar al menos un pago.")

    caja_activa = get_active_cash_closure(db)
    if not caja_activa:
        raise ValueError("No hay una caja abierta (OPEN) en este momento. Abra caja antes de cobrar.")

    total_pagado = sum(float(p.amount) for p in pagos_in)
    if round(total_pagado, 2) < round(float(pedido.total or 0.0), 2):
        raise ValueError(
            f"El total de los pagos (${total_pagado:,.2f}) es menor al total del pedido (${pedido.total:,.2f})."
        )

    has_fiado = any(p_in.method == models.PaymentMethod.FIADO for p_in in pagos_in)
    dir_extraida, barrio_extraido = _extraer_direccion_y_barrio_de_notas(pedido.notas)
    cliente_obj = upsert_cliente(
        db,
        nombre=pedido.cliente_nombre,
        telefono=pedido.cliente_telefono,
        direccion=dir_extraida,
        barrio=barrio_extraido,
        allow_without_phone=has_fiado,
    )
    if cliente_obj:
        pedido.cliente_id = cliente_obj.id

    for p_in in pagos_in:
        nuevo_pago = models.Payment(
            pedido_id=pedido.id,
            cash_closure_id=caja_activa.id,
            method=p_in.method,
            amount=float(p_in.amount),
            change_given=float(p_in.change_given or 0.0)
        )
        db.add(nuevo_pago)

    pedido.estado = models.EstadoPedido.PAGADO
    db.flush()

    # Actualizar acumulados en la sesión de caja activa
    calcular_resumen_caja(db, caja_activa)

    db.commit()
    db.refresh(pedido)
    return pedido


# --- MÉTRICAS DE INVENTARIO Y DEPARTE ---

def obtener_metricas_dia(db: Session, fecha_consulta: date) -> schemas.MetricasDiaOut:
    menu = get_menu_dia_by_fecha(db, fecha_consulta)
    
    pedidos_hoy = db.query(models.Pedido).filter(
        func.date(models.Pedido.fecha_hora) == fecha_consulta,
        models.Pedido.estado.notin_([models.EstadoPedido.CANCELADO, models.EstadoPedido.BORRADOR_WEB])
    ).all()

    total_ventas = sum(p.total for p in pedidos_hoy)
    total_pedidos = len(pedidos_hoy)

    sopas_metricas = []
    principios_metricas = []
    acomp_metricas = []

    if menu:
        for item in menu.items:
            prep = item.cantidad_preparada
            vend = item.cantidad_vendida
            disp = max(0, prep - vend)
            pct = round((vend / prep * 100), 1) if prep > 0 else 0.0
            alerta = disp <= 3 and prep > 0

            if item.tipo_item == models.TipoItemStock.SOPA and item.sopa:
                sopas_metricas.append(schemas.MetricaItemStock(
                    id=item.sopa.id,
                    nombre=item.sopa.nombre,
                    tipo=models.TipoItemStock.SOPA,
                    preparado=prep,
                    vendido=vend,
                    disponible=disp,
                    porcentaje_consumido=pct,
                    alerta_agotamiento=alerta
                ))
            elif item.tipo_item == models.TipoItemStock.PRINCIPIO and item.principio:
                principios_metricas.append(schemas.MetricaItemStock(
                    id=item.principio.id,
                    nombre=item.principio.nombre,
                    tipo=models.TipoItemStock.PRINCIPIO,
                    preparado=prep,
                    vendido=vend,
                    disponible=disp,
                    porcentaje_consumido=pct,
                    alerta_agotamiento=alerta
                ))
            elif item.tipo_item == models.TipoItemStock.ACOMPANAMIENTO and item.acompanamiento:
                acomp_metricas.append(schemas.MetricaItemStock(
                    id=item.acompanamiento.id,
                    nombre=item.acompanamiento.nombre,
                    tipo=models.TipoItemStock.ACOMPANAMIENTO,
                    preparado=prep,
                    vendido=vend,
                    disponible=disp,
                    porcentaje_consumido=pct,
                    alerta_agotamiento=alerta
                ))

    # Encontrar plato más vendido
    plato_top = db.query(
        models.Plato.nombre, func.sum(models.DetallePedido.cantidad).label("total_cant")
    ).join(models.DetallePedido).join(models.Pedido).filter(
        func.date(models.Pedido.fecha_hora) == fecha_consulta,
        models.Pedido.estado.notin_([models.EstadoPedido.CANCELADO, models.EstadoPedido.BORRADOR_WEB])
    ).group_by(models.Plato.nombre).order_by(func.sum(models.DetallePedido.cantidad).desc()).first()

    plato_mas_vendido_nombre = plato_top[0] if plato_top else "Ninguno"

    return schemas.MetricasDiaOut(
        fecha=fecha_consulta,
        total_pedidos=total_pedidos,
        total_ventas=total_ventas,
        sopas_metricas=sopas_metricas,
        principios_metricas=principios_metricas,
        acompanamientos_metricas=acomp_metricas,
        plato_mas_vendido=plato_mas_vendido_nombre
    )


def obtener_estadisticas_dashboard(db: Session) -> schemas.DashboardStatsOut:
    """
    Calcula las métricas reales de Administración (/admin) desde Neon DB:
    - Ventas de Hoy / Turno Activo (separadas en Efectivo vs Medios Digitales)
    - Comandas Totales pagadas del día / turno
    - Clientes Guardados (teléfonos únicos en pedidos)
    - Ranking de Platos Más Vendidos reales (agrupados por plato, cantidad e ingresos)
    """
    # Hora actual en Colombia (UTC-5)
    tz_col = timezone(timedelta(hours=-5))
    ahora_col = datetime.now(tz_col)
    inicio_dia_col = datetime(ahora_col.year, ahora_col.month, ahora_col.day, 0, 0, 0, tzinfo=tz_col)
    inicio_dia_utc = inicio_dia_col.astimezone(timezone.utc)

    caja_activa = get_active_cash_closure(db)

    # Obtener pagos del día o del turno activo
    pagos_query = db.query(models.Payment).join(models.Pedido).filter(
        models.Pedido.estado == models.EstadoPedido.PAGADO
    )
    if caja_activa:
        pagos_hoy = pagos_query.filter(
            (models.Payment.cash_closure_id == caja_activa.id)
            | (models.Pedido.fecha_hora >= inicio_dia_utc)
        ).all()
    else:
        pagos_hoy = pagos_query.filter(
            models.Pedido.fecha_hora >= inicio_dia_utc
        ).all()

    cash_sales = sum(float(p.amount or 0.0) for p in pagos_hoy if p.method == models.PaymentMethod.CASH)
    nequi_sales = sum(float(p.amount or 0.0) for p in pagos_hoy if p.method == models.PaymentMethod.NEQUI)
    bancolombia_sales = sum(float(p.amount or 0.0) for p in pagos_hoy if p.method == models.PaymentMethod.BANCOLOMBIA)
    daviplata_sales = sum(float(p.amount or 0.0) for p in pagos_hoy if p.method == models.PaymentMethod.DAVIPLATA)
    card_sales = sum(float(p.amount or 0.0) for p in pagos_hoy if p.method == models.PaymentMethod.CARD)
    credit_sales = sum(float(p.amount or 0.0) for p in pagos_hoy if p.method == models.PaymentMethod.FIADO)
    transfer_sales = nequi_sales + bancolombia_sales + daviplata_sales
    digital_sales = transfer_sales + card_sales
    today_sales = cash_sales + digital_sales

    pedido_ids_hoy = {p.pedido_id for p in pagos_hoy}
    today_order_count = len(pedido_ids_hoy)

    # Clientes únicos registrados en directorio clientes o en pedidos
    total_clientes_tabla = db.query(func.count(models.Cliente.id)).scalar() or 0
    total_customers_pedidos = (
        db.query(func.count(func.distinct(models.Pedido.cliente_telefono)))
        .filter(
            models.Pedido.cliente_telefono.isnot(None),
            models.Pedido.cliente_telefono != "",
        )
        .scalar()
        or 0
    )
    total_customers = max(int(total_clientes_tabla), int(total_customers_pedidos))

    # Platos más vendidos reales en pedidos PAGADO (del turno/día actual, o histórico si hoy aún va en 0)
    top_rows = []
    if pedido_ids_hoy:
        top_rows = (
            db.query(
                models.Plato.nombre.label("product_name"),
                func.sum(models.DetallePedido.cantidad).label("sold_count"),
                func.sum(models.DetallePedido.cantidad * models.DetallePedido.precio_unitario).label("total_revenue"),
            )
            .join(models.DetallePedido, models.DetallePedido.plato_id == models.Plato.id)
            .filter(models.DetallePedido.pedido_id.in_(pedido_ids_hoy))
            .group_by(models.Plato.nombre)
            .order_by(
                func.sum(models.DetallePedido.cantidad).desc(),
                func.sum(models.DetallePedido.cantidad * models.DetallePedido.precio_unitario).desc(),
            )
            .limit(8)
            .all()
        )

    top_dishes = [
        schemas.TopPlatoOut(
            product_name=row.product_name,
            sold_count=int(row.sold_count or 0),
            total_revenue=float(row.total_revenue or 0.0),
        )
        for row in top_rows
    ]

    return schemas.DashboardStatsOut(
        todaySales=today_sales,
        cashSales=cash_sales,
        digitalSales=digital_sales,
        transferSales=transfer_sales,
        nequiSales=nequi_sales,
        bancolombiaSales=bancolombia_sales,
        daviplataSales=daviplata_sales,
        cardSales=card_sales,
        creditSales=credit_sales,
        todayOrderCount=today_order_count,
        totalCustomers=int(total_customers),
        topDishes=top_dishes,
    )


# --- CONFIGURACIÓN PERSISTENTE DE ESPECIALES DEL DÍA Y PLATOS ROTATIVOS ---

def _split_csv(val) -> List[str]:
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    if isinstance(val, str):
        return [x.strip() for x in val.split(",") if x.strip()]
    return []


def _format_daily_specials_out(row: models.DailySpecialsConfig) -> schemas.DailySpecialsConfigOut:
    principios_list = _split_csv(row.principios)
    acomp_list = _split_csv(row.acompanamientos)
    esp165_list = _split_csv(row.especiales_16500)
    return schemas.DailySpecialsConfigOut(
        id=row.id,
        sopa_dia=row.sopa_dia or "Campesina",
        sopa=row.sopa_dia or "Campesina",
        principios=principios_list,
        principios_str=", ".join(principios_list),
        acompanamientos=acomp_list,
        acompanamientos_str=", ".join(acomp_list),
        especiales_16500=esp165_list,
        especiales_16500_str=", ".join(esp165_list),
        especiales_16500_etiqueta=row.especiales_16500_etiqueta or "⭐ SOLO POR HOY",
        especial_arroz_nombre=row.especial_arroz_nombre or "Arroz ranchero",
        especial_arroz_etiqueta=row.especial_arroz_etiqueta or "⭐ SOLO LOS LUNES",
        especial_arroz_precio=float(row.especial_arroz_precio or 18000.0),
        updated_at=row.updated_at,
    )


def get_daily_specials_config(db: Session) -> schemas.DailySpecialsConfigOut:
    row = db.query(models.DailySpecialsConfig).order_by(models.DailySpecialsConfig.id.asc()).first()
    if not row:
        row = models.DailySpecialsConfig(
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
        db.add(row)
        db.commit()
        db.refresh(row)
    return _format_daily_specials_out(row)


def update_daily_specials_config(
    db: Session,
    data: schemas.DailySpecialsConfigUpdate,
) -> schemas.DailySpecialsConfigOut:
    row = db.query(models.DailySpecialsConfig).order_by(models.DailySpecialsConfig.id.asc()).first()
    if not row:
        row = models.DailySpecialsConfig(id=1)
        db.add(row)
        db.flush()

    sopa_val = data.sopa_dia if data.sopa_dia is not None else data.sopa
    if sopa_val is not None and sopa_val.strip():
        row.sopa_dia = sopa_val.strip()

    if data.principios is not None:
        p_list = _split_csv(data.principios)
        if p_list:
            row.principios = ", ".join(p_list)

    if data.acompanamientos is not None:
        a_list = _split_csv(data.acompanamientos)
        if a_list:
            row.acompanamientos = ", ".join(a_list)

    if data.especiales_16500 is not None:
        e_list = _split_csv(data.especiales_16500)
        if e_list:
            row.especiales_16500 = ", ".join(e_list)
            for dish_name in e_list:
                _resolver_o_crear_plato(db, None, dish_name, 16500.0)

    if data.especiales_16500_etiqueta is not None and data.especiales_16500_etiqueta.strip():
        row.especiales_16500_etiqueta = data.especiales_16500_etiqueta.strip()

    if data.especial_arroz_nombre is not None and data.especial_arroz_nombre.strip():
        row.especial_arroz_nombre = data.especial_arroz_nombre.strip()

    if data.especial_arroz_etiqueta is not None and data.especial_arroz_etiqueta.strip():
        row.especial_arroz_etiqueta = data.especial_arroz_etiqueta.strip()

    if data.especial_arroz_precio is not None and float(data.especial_arroz_precio) > 0:
        row.especial_arroz_precio = float(data.especial_arroz_precio)

    if row.especial_arroz_nombre:
        _resolver_o_crear_plato(db, None, row.especial_arroz_nombre, float(row.especial_arroz_precio or 18000.0))

    db.commit()
    db.refresh(row)
    return _format_daily_specials_out(row)
