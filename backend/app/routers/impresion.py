from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app import schemas, models

router = APIRouter(prefix="/api/impresion", tags=["Impresión Térmica SAT Q22"])


def formatear_comanda_texto(pedido: models.Pedido, items: List[schemas.ItemImpresionOut], tipo_label: str) -> str:
    """
    Genera el texto limpio para comanda térmica de 80mm (aprox. 42-48 columnas).
    """
    fecha_str = pedido.fecha_hora.strftime("%d/%m/%Y %H:%M") if pedido.fecha_hora else datetime.now().strftime("%d/%m/%Y %H:%M")
    sep = "=" * 42
    subsep = "-" * 42

    lineas = [
        sep,
        "       RESTAURANTE SAN PARRILLA",
        "           COMANDA DE COCINA",
        sep,
        f"PEDIDO: {pedido.codigo_pedido} (ID: #{pedido.id})",
        f"FECHA : {fecha_str}",
        f"TIPO  : {tipo_label.upper()}",
    ]

    if pedido.mesa:
        lineas.append(f"MESA  : {pedido.mesa}")
    if pedido.cliente_nombre and pedido.cliente_nombre.lower() != "cliente":
        cli = pedido.cliente_nombre
        if pedido.cliente_telefono:
            cli += f" - Tel: {pedido.cliente_telefono}"
        lineas.append(f"CLIENTE: {cli}")
    if pedido.creado_por:
        lineas.append(f"MESERO/CAJERO: {pedido.creado_por}")

    lineas.append(subsep)
    lineas.append("CANT  DESCRIPCION / DETALLE")
    lineas.append(subsep)

    for item in items:
        lineas.append(f"{item.cantidad}x   {item.plato_nombre.upper()}")
        if item.sopa:
            lineas.append(f"      [SOPA: {item.sopa}]")
        if item.principio:
            lineas.append(f"      [PRINCIPIO: {item.principio}]")
        if item.acompanamiento:
            lineas.append(f"      [ACOMP: {item.acompanamiento}]")
        if item.notas_item:
            lineas.append(f"      * NOTA: {item.notas_item}")

    lineas.append(subsep)

    if pedido.notas and pedido.notas.strip():
        lineas.append("OBSERVACIONES GENERALES:")
        lineas.append(f"  {pedido.notas.strip()}")
        lineas.append(subsep)

    lineas.append(f"TOTAL COMANDA: ${pedido.total:,.0f}")
    lineas.append(sep)
    lineas.append("\n\n")

    return "\n".join(lineas)


@router.get("/pendientes", response_model=List[schemas.PedidoImpresionOut])
def obtener_pedidos_pendientes_impresion(
    tipo_filtro: Optional[str] = Query(default=None, description="Filtrar por tipo: EN_MESA, PARA_LLEVAR, DOMICILIO"),
    db: Session = Depends(get_db)
):
    """
    Retorna la lista de pedidos confirmados que no han sido impresos en cocina (impreso_cocina == False).
    Excluye borradores web no aprobados (BORRADOR_WEB) y pedidos cancelados (CANCELADO).
    """
    query = (
        db.query(models.Pedido)
        .filter(
            models.Pedido.impreso_cocina.is_(False),
            models.Pedido.estado.notin_([models.EstadoPedido.BORRADOR_WEB, models.EstadoPedido.CANCELADO]),
        )
        .order_by(models.Pedido.id.asc())
    )

    if tipo_filtro:
        query = query.filter(models.Pedido.tipo == tipo_filtro)

    pedidos = query.all()
    resultado: List[schemas.PedidoImpresionOut] = []

    for ped in pedidos:
        # Determinar etiqueta de tipo
        if ped.tipo == models.TipoPedido.EN_MESA:
            tipo_label = f"Mesa {ped.mesa or 'General'}"
        elif ped.tipo == models.TipoPedido.PARA_LLEVAR:
            tipo_label = "Para Llevar"
        elif ped.tipo == models.TipoPedido.DOMICILIO:
            tipo_label = "Domicilio"
        else:
            tipo_label = str(ped.tipo.value if hasattr(ped.tipo, 'value') else ped.tipo)

        # Mapear detalles de platos
        items_out: List[schemas.ItemImpresionOut] = []
        for det in ped.detalles:
            plato_nombre = det.plato.nombre if det.plato else "Plato"
            sopa_nom = det.sopa.nombre if det.sopa else None
            princ_nom = det.principio.nombre if det.principio else None
            acomp_nom = det.acompanamiento.nombre if det.acompanamiento else None
            pu = float(det.precio_unitario or 0.0)
            cant = int(det.cantidad or 1)

            items_out.append(
                schemas.ItemImpresionOut(
                    id=det.id,
                    cantidad=cant,
                    plato_nombre=plato_nombre,
                    precio_unitario=pu,
                    subtotal=pu * cant,
                    sopa=sopa_nom,
                    principio=princ_nom,
                    acompanamiento=acomp_nom,
                    notas_item=det.notas_item,
                )
            )

        texto_comanda = formatear_comanda_texto(ped, items_out, tipo_label)

        resultado.append(
            schemas.PedidoImpresionOut(
                id=ped.id,
                codigo_pedido=ped.codigo_pedido,
                fecha_hora=ped.fecha_hora,
                tipo=ped.tipo.value if hasattr(ped.tipo, 'value') else str(ped.tipo),
                tipo_label=tipo_label,
                mesa=ped.mesa,
                cliente_nombre=ped.cliente_nombre or "Cliente",
                cliente_telefono=ped.cliente_telefono,
                creado_por=ped.creado_por,
                notas=ped.notas,
                packaging_fee=float(ped.packaging_fee or 0.0),
                delivery_fee=float(ped.delivery_fee or 0.0),
                subtotal=float(ped.subtotal or 0.0),
                total=float(ped.total or 0.0),
                impreso_cocina=bool(ped.impreso_cocina),
                impreso_ticket=bool(ped.impreso_ticket),
                items=items_out,
                texto_comanda_sugerido=texto_comanda,
            )
        )

    return resultado


@router.post("/marcar-impreso/{pedido_id}")
def marcar_pedido_como_impreso(
    pedido_id: int,
    db: Session = Depends(get_db)
):
    """
    Actualiza impreso_cocina = True en la base de datos de Neon
    para indicar que la comanda ya fue impresa físicamente en la SAT Q22.
    """
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail=f"Pedido con ID #{pedido_id} no encontrado.")

    pedido.impreso_cocina = True
    db.commit()
    db.refresh(pedido)

    return {
        "success": True,
        "pedido_id": pedido.id,
        "codigo_pedido": pedido.codigo_pedido,
        "impreso_cocina": pedido.impreso_cocina,
    }


@router.post("/marcar-ticket/{pedido_id}")
def marcar_ticket_como_impreso(
    pedido_id: int,
    db: Session = Depends(get_db)
):
    """
    Actualiza impreso_ticket = True en Neon para indicar que la factura/ticket ya fue impreso.
    """
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail=f"Pedido con ID #{pedido_id} no encontrado.")

    pedido.impreso_ticket = True
    db.commit()
    db.refresh(pedido)

    return {
        "success": True,
        "pedido_id": pedido.id,
        "codigo_pedido": pedido.codigo_pedido,
        "impreso_ticket": pedido.impreso_ticket,
    }


@router.post("/reimprimir/{pedido_id}")
def habilitar_reimpresion_pedido(
    pedido_id: int,
    db: Session = Depends(get_db)
):
    """
    Restablece impreso_cocina = False para que el agente de impresión local vuelva a imprimir la comanda.
    """
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail=f"Pedido con ID #{pedido_id} no encontrado.")

    pedido.impreso_cocina = False
    db.commit()
    db.refresh(pedido)

    return {
        "success": True,
        "pedido_id": pedido.id,
        "codigo_pedido": pedido.codigo_pedido,
        "impreso_cocina": pedido.impreso_cocina,
        "mensaje": f"Pedido #{pedido.codigo_pedido} encolado nuevamente para impresión."
    }
