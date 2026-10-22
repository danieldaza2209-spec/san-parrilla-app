from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timezone
import uuid
from typing import List, Optional

from app import models, schemas


# --- CATÁLOGOS ---

def get_categorias(db: Session) -> List[models.Categoria]:
    return db.query(models.Categoria).order_by(models.Categoria.orden).all()

def get_platos(db: Session, categoria_id: Optional[int] = None) -> List[models.Plato]:
    query = db.query(models.Plato).filter(models.Plato.activo == True)
    if categoria_id:
        query = query.filter(models.Plato.categoria_id == categoria_id)
    return query.all()

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


def crear_pedido(db: Session, pedido_in: schemas.PedidoCreate) -> models.Pedido:
    hoy = date.today()
    menu_hoy = get_menu_dia_by_fecha(db, hoy)
    
    codigo = f"SP-{uuid.uuid4().hex[:6].upper()}"
    estado_inicial = (
        models.EstadoPedido.BORRADOR_WEB
        if pedido_in.es_borrador_web
        else models.EstadoPedido.PENDIENTE
    )
    delivery_fee = float(pedido_in.delivery_fee or 0.0)

    nuevo_pedido = models.Pedido(
        codigo_pedido=codigo,
        cliente_nombre=pedido_in.cliente_nombre,
        cliente_telefono=pedido_in.cliente_telefono,
        mesa=pedido_in.mesa,
        tipo=pedido_in.tipo,
        estado=estado_inicial,
        notas=pedido_in.notas,
        subtotal=0.0,
        delivery_fee=delivery_fee,
        total=0.0
    )
    db.add(nuevo_pedido)
    db.flush()

    subtotal_calculado = 0.0
    detalles_creados: List[models.DetallePedido] = []

    for det in pedido_in.detalles:
        plato = db.query(models.Plato).filter(models.Plato.id == det.plato_id).first()
        if not plato:
            continue
        
        subtotal_item = plato.precio * det.cantidad
        subtotal_calculado += subtotal_item

        detalle_db = models.DetallePedido(
            pedido_id=nuevo_pedido.id,
            plato_id=det.plato_id,
            sopa_id=det.sopa_id,
            principio_id=det.principio_id,
            acompanamiento_id=det.acompanamiento_id,
            cantidad=det.cantidad,
            precio_unitario=plato.precio,
            notas_item=det.notas_item
        )
        db.add(detalle_db)
        detalles_creados.append(detalle_db)

    # REGLA CRÍTICA DE STOCK:
    # Si es_borrador_web=True, queda en BORRADOR_WEB y NO descuenta stock todavía.
    if not pedido_in.es_borrador_web:
        _verificar_y_descontar_stock(db, detalles_creados, menu_hoy, verificar_disponibilidad=False)

    nuevo_pedido.subtotal = subtotal_calculado
    nuevo_pedido.total = subtotal_calculado + delivery_fee
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
        if datos_aprobacion.delivery_fee is not None:
            pedido.delivery_fee = float(datos_aprobacion.delivery_fee)
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
                plato = db.query(models.Plato).filter(models.Plato.id == det.plato_id).first()
                if not plato:
                    raise ValueError(f"Plato con id {det.plato_id} no encontrado.")
                nuevo_subtotal += plato.precio * det.cantidad
                detalle_db = models.DetallePedido(
                    pedido_id=pedido.id,
                    plato_id=det.plato_id,
                    sopa_id=det.sopa_id,
                    principio_id=det.principio_id,
                    acompanamiento_id=det.acompanamiento_id,
                    cantidad=det.cantidad,
                    precio_unitario=plato.precio,
                    notas_item=det.notas_item
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
    pedido.total = (pedido.subtotal or 0.0) + pedido.delivery_fee

    # Verificar disponibilidad y descontar stock en MenuDiaItem
    hoy = date.today()
    menu_hoy = get_menu_dia_by_fecha(db, hoy)
    _verificar_y_descontar_stock(db, pedido.detalles, menu_hoy, verificar_disponibilidad=True)

    pedido.estado = models.EstadoPedido.PENDIENTE
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
        .filter(models.Payment.cash_closure_id == closure.id)
        .all()
    )

    total_cash = sum(p.amount for p in pagos if p.method == models.PaymentMethod.CASH)
    total_nequi = sum(p.amount for p in pagos if p.method == models.PaymentMethod.NEQUI)
    total_daviplata = sum(p.amount for p in pagos if p.method == models.PaymentMethod.DAVIPLATA)
    total_card = sum(p.amount for p in pagos if p.method == models.PaymentMethod.CARD)

    pedido_ids = {p.pedido_id for p in pagos}
    if pedido_ids:
        pedidos_caja = (
            db.query(models.Pedido)
            .filter(models.Pedido.id.in_(pedido_ids))
            .all()
        )
    else:
        pedidos_caja = []

    total_delivery_payouts = sum(float(ped.delivery_fee or 0.0) for ped in pedidos_caja)
    total_delivery_fees = total_delivery_payouts
    subtotal_sales = sum(float(ped.subtotal or 0.0) for ped in pedidos_caja)
    total_sales = total_cash + total_nequi + total_daviplata + total_card
    expected_cash = float(closure.initial_cash or 0.0) + total_cash - total_delivery_payouts

    # Sincronizar campos acumulados en el modelo
    closure.total_cash_sales = total_cash
    closure.total_nequi_sales = total_nequi
    closure.total_daviplata_sales = total_daviplata
    closure.total_card_sales = total_card
    closure.total_delivery_fees = total_delivery_fees
    closure.total_delivery_payouts = total_delivery_payouts
    closure.expected_cash = expected_cash

    return schemas.CashClosureOut(
        id=closure.id,
        opened_at=closure.opened_at,
        closed_at=closure.closed_at,
        status=closure.status,
        initial_cash=closure.initial_cash,
        total_cash_sales=total_cash,
        total_nequi_sales=total_nequi,
        total_daviplata_sales=total_daviplata,
        total_card_sales=total_card,
        total_delivery_fees=total_delivery_fees,
        total_delivery_payouts=total_delivery_payouts,
        subtotal_sales=subtotal_sales,
        total_sales=total_sales,
        expected_cash=expected_cash,
        counted_cash=closure.counted_cash,
        discrepancy=closure.discrepancy,
        notes=closure.notes,
        payments=[schemas.PaymentOut.model_validate(p) for p in pagos]
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
        total_daviplata_sales=0.0,
        total_card_sales=0.0,
        total_delivery_fees=0.0,
        total_delivery_payouts=0.0,
        expected_cash=initial_cash,
        notes=open_in.notes
    )
    db.add(nueva_caja)
    db.commit()
    db.refresh(nueva_caja)
    return nueva_caja


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
