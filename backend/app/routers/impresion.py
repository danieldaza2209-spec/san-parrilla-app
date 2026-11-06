from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Tuple
from datetime import datetime
import re

from app.database import get_db
from app import schemas, models

router = APIRouter(prefix="/api/impresion", tags=["Impresión Térmica SAT Q22"])

METODO_PAGO_LABELS = {
    "CASH": "EFECTIVO",
    "EFECTIVO": "EFECTIVO",
    "NEQUI": "NEQUI",
    "BANCOLOMBIA": "BANCOLOMBIA",
    "DAVIPLATA": "DAVIPLATA",
    "CARD": "TARJETA / DATAFONO",
    "TRANSFER": "TRANSFERENCIA",
    "FIADO": "FIADO / CARTERA",
    "CREDIT": "FIADO / CARTERA",
}


def _extraer_direccion_barrio(pedido: models.Pedido) -> Tuple[Optional[str], Optional[str]]:
    direccion = None
    barrio = None
    notas = pedido.notas or ""
    if notas:
        m_dir = re.search(r"Direcci[oó]n:\s*([^|]+)", notas, flags=re.IGNORECASE)
        if m_dir:
            direccion = m_dir.group(1).strip()
        m_barrio = re.search(r"Barrio:\s*([^|]+)", notas, flags=re.IGNORECASE)
        if m_barrio:
            barrio = m_barrio.group(1).strip()

    if not direccion and pedido.cliente and getattr(pedido.cliente, "direccion", None):
        direccion = pedido.cliente.direccion
    if not barrio and pedido.cliente and getattr(pedido.cliente, "barrio", None):
        barrio = pedido.cliente.barrio

    return direccion, barrio


def _extraer_metodo_pago(pedido: models.Pedido) -> str:
    if pedido.payments and len(pedido.payments) > 0:
        metodos = []
        for p in pedido.payments:
            m_val = p.method.value if hasattr(p.method, "value") else str(p.method)
            lbl = METODO_PAGO_LABELS.get(m_val.upper(), m_val.upper())
            if lbl not in metodos:
                metodos.append(lbl)
        return " / ".join(metodos)

    estado_str = pedido.estado.value if hasattr(pedido.estado, "value") else str(pedido.estado)
    if estado_str == "PAGADO":
        return "PAGADO"
    if pedido.tipo == models.TipoPedido.DOMICILIO:
        return "EFECTIVO (CONTRAENTREGA)"
    return "PENDIENTE POR COBRAR"


def _desglosar_notas_item(
    notas_raw: Optional[str],
    sopa_fk: Optional[str],
    principio_fk: Optional[str],
    acomp_fk: Optional[str],
):
    sopa = sopa_fk
    principio = principio_fk
    acomp = acomp_fk
    empaque = None
    ubicacion = None
    notas_limpias_partes = []

    if notas_raw:
        # Detectar ubicación hospitalaria explícita: Torre A, Torre B, Urgencias
        m_loc = re.search(r"(Torre\s*A|Torre\s*B|Urgencias)", notas_raw, flags=re.IGNORECASE)
        if m_loc:
            val_loc = m_loc.group(1).strip()
            if "torre" in val_loc.lower() and "a" in val_loc.lower():
                ubicacion = "Torre A"
            elif "torre" in val_loc.lower() and "b" in val_loc.lower():
                ubicacion = "Torre B"
            else:
                ubicacion = "Urgencias"

        segmentos = [s.strip() for s in notas_raw.split("|") if s.strip()]
        for seg in segmentos:
            low = seg.lower()
            if low.startswith("con sopa") or low == "sin sopa":
                if not sopa:
                    m_s = re.search(r"\(([^)]+)\)", seg)
                    sopa = m_s.group(1).strip() if m_s else seg
            elif low.startswith("sopa:"):
                if not sopa:
                    sopa = seg.split(":", 1)[1].strip()
            elif low.startswith("principio:"):
                if not principio:
                    principio = seg.split(":", 1)[1].strip()
            elif low.startswith("acomp:") or low.startswith("acompañamiento:"):
                if not acomp:
                    acomp = seg.split(":", 1)[1].strip()
            elif low.startswith("empaque:"):
                empaque = seg.split(":", 1)[1].strip()
            elif low.startswith("ubicación:") or low.startswith("ubicacion:"):
                if not ubicacion:
                    ubicacion = seg.split(":", 1)[1].strip()
            elif low.startswith("nota:"):
                notas_limpias_partes.append(seg.split(":", 1)[1].strip())
            elif re.match(r"^\[.*?(TORRE\s*A|TORRE\s*B|URGENCIAS).*?\]$", seg, flags=re.IGNORECASE):
                # Etiqueta hospitalaria ya capturada en ubicacion
                continue
            else:
                notas_limpias_partes.append(seg)

    notas_limpias = " | ".join(notas_limpias_partes) if notas_limpias_partes else None
    return sopa, principio, acomp, empaque, ubicacion, notas_limpias


def formatear_comanda_texto(pedido: models.Pedido, items: List[schemas.ItemImpresionOut], tipo_label: str) -> str:
    """
    Genera el texto limpio para comanda térmica de 80mm (40-42 columnas).
    """
    fecha_str = pedido.fecha_hora.strftime("%H:%M") if pedido.fecha_hora else datetime.now().strftime("%H:%M")
    sep = "=" * 40
    subsep = "-" * 40
    codigo = pedido.codigo_pedido if str(pedido.codigo_pedido).startswith("#") else f"#{pedido.codigo_pedido}"

    lineas = [
        sep,
        "        SAN PARRILLA - COCINA          ",
        f"Pedido: {codigo} | Tipo: {tipo_label.upper()}",
        f"Hora: {fecha_str}",
        subsep,
    ]

    for item in items:
        lineas.append(f"[{item.cantidad}] {item.plato_nombre.upper()}")
        if item.notas:
            lineas.append(f"  * Notas: {item.notas}")
        guarniciones = []
        if item.sopa:
            guarniciones.append(f"Sopa: {item.sopa}")
        if item.principios:
            guarniciones.append(f"Ppio: {item.principios}")
        if item.acompanamiento:
            guarniciones.append(f"Acomp: {item.acompanamiento}")
        if guarniciones:
            lineas.append("  * " + " | ".join(guarniciones))
        if item.ubicacion_hospitalaria:
            lineas.append(f"  * Ubicacion: {item.ubicacion_hospitalaria}")
        if item.empaque:
            lineas.append(f"  * Empaque: {item.empaque}")

    lineas.append(sep)
    return "\n".join(lineas)


@router.get("/pendientes", response_model=List[schemas.PedidoImpresionOut])
def obtener_pedidos_pendientes_impresion(
    tipo_filtro: Optional[str] = Query(default=None, description="Filtrar por tipo: EN_MESA, PARA_LLEVAR, DOMICILIO"),
    db: Session = Depends(get_db)
):
    """
    Consulta en Neon todos los pedidos con impreso_cocina == False ordenados por id ASC.
    Excluye borradores web no aprobados (BORRADOR_WEB) y pedidos cancelados (CANCELADO).
    """
    query = (
        db.query(models.Pedido)
        .filter(
            or_(
                models.Pedido.impreso_cocina.is_(False),
                models.Pedido.impreso_caja.is_(False),
            ),
            models.Pedido.estado.notin_([models.EstadoPedido.BORRADOR_WEB, models.EstadoPedido.CANCELADO]),
        )
        .order_by(models.Pedido.id.asc())
    )

    if tipo_filtro:
        query = query.filter(models.Pedido.tipo == tipo_filtro)

    pedidos = query.all()
    resultado: List[schemas.PedidoImpresionOut] = []

    for ped in pedidos:
        if ped.tipo == models.TipoPedido.EN_MESA:
            mesa_txt = (ped.mesa or "1").replace("Mesa", "").replace("MESA", "").strip()
            tipo_label = f"MESA {mesa_txt}"
        elif ped.tipo == models.TipoPedido.PARA_LLEVAR:
            tipo_label = "PARA LLEVAR"
        elif ped.tipo == models.TipoPedido.DOMICILIO:
            tipo_label = "DOMICILIO"
        else:
            tipo_label = str(ped.tipo.value if hasattr(ped.tipo, "value") else ped.tipo).upper()

        direccion, barrio = _extraer_direccion_barrio(ped)
        metodo_pago = _extraer_metodo_pago(ped)
        codigo_fmt = ped.codigo_pedido if str(ped.codigo_pedido).startswith("#") else f"#{ped.codigo_pedido}"

        items_out: List[schemas.ItemImpresionOut] = []
        for det in ped.detalles:
            plato_nombre = det.plato.nombre if det.plato else "Plato"
            sopa_fk = det.sopa.nombre if det.sopa else None
            princ_fk = det.principio.nombre if det.principio else None
            acomp_fk = det.acompanamiento.nombre if det.acompanamiento else None
            pu = float(det.precio_unitario or 0.0)
            cant = int(det.cantidad or 1)

            sopa, principio, acomp, empaque, ubicacion, notas_limpias = _desglosar_notas_item(
                det.notas_item, sopa_fk, princ_fk, acomp_fk
            )

            items_out.append(
                schemas.ItemImpresionOut(
                    id=det.id,
                    cantidad=cant,
                    nombre=plato_nombre,
                    plato_nombre=plato_nombre,
                    precio=pu,
                    precio_unitario=pu,
                    subtotal=pu * cant,
                    sopa=sopa,
                    principio=principio,
                    principios=principio,
                    acompanamiento=acomp,
                    empaque=empaque,
                    ubicacion_hospitalaria=ubicacion,
                    notas=notas_limpias,
                    notas_item=det.notas_item,
                )
            )

        texto_comanda = formatear_comanda_texto(ped, items_out, tipo_label)

        resultado.append(
            schemas.PedidoImpresionOut(
                id=ped.id,
                codigo=codigo_fmt,
                codigo_pedido=ped.codigo_pedido,
                fecha_hora=ped.fecha_hora,
                tipo=tipo_label,
                tipo_label=tipo_label,
                mesa=ped.mesa,
                cliente_nombre=ped.cliente_nombre or "Cliente",
                cliente_telefono=ped.cliente_telefono,
                direccion=direccion,
                barrio=barrio,
                courier_name=ped.courier_name,
                metodo_pago=metodo_pago,
                creado_por=ped.creado_por,
                notas=ped.notas,
                packaging_fee=float(ped.packaging_fee or 0.0),
                delivery_fee=float(ped.delivery_fee or 0.0),
                subtotal=float(ped.subtotal or 0.0),
                total=float(ped.total or 0.0),
                impreso_cocina=bool(ped.impreso_cocina),
                impreso_caja=bool(getattr(ped, "impreso_caja", False)),
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
    Actualiza impreso_cocina = True e impreso_caja = True en la base de datos de Neon
    para evitar impresiones duplicadas.
    """
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail=f"Pedido con ID #{pedido_id} no encontrado.")

    pedido.impreso_cocina = True
    pedido.impreso_caja = True
    pedido.impreso_ticket = True
    db.commit()
    db.refresh(pedido)

    return {
        "success": True,
        "pedido_id": pedido.id,
        "codigo": pedido.codigo_pedido,
        "codigo_pedido": pedido.codigo_pedido,
        "impreso_cocina": pedido.impreso_cocina,
        "impreso_caja": pedido.impreso_caja,
        "impreso_ticket": pedido.impreso_ticket,
    }


@router.post("/marcar-ticket/{pedido_id}")
def marcar_ticket_como_impreso(
    pedido_id: int,
    db: Session = Depends(get_db)
):
    """
    Actualiza impreso_ticket = True e impreso_caja = True en Neon.
    """
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail=f"Pedido con ID #{pedido_id} no encontrado.")

    pedido.impreso_caja = True
    pedido.impreso_ticket = True
    db.commit()
    db.refresh(pedido)

    return {
        "success": True,
        "pedido_id": pedido.id,
        "codigo_pedido": pedido.codigo_pedido,
        "impreso_caja": pedido.impreso_caja,
        "impreso_ticket": pedido.impreso_ticket,
    }


@router.post("/reimprimir/{pedido_id}")
def habilitar_reimpresion_pedido(
    pedido_id: int,
    tipo: Optional[str] = Query(default="CUENTA", description="Tipo de reimpresión: CUENTA (pre-cuenta mesa) o COCINA (comanda preparación)"),
    db: Session = Depends(get_db)
):
    """
    Restablece el flag de impresión según el tipo solicitado:
    - CUENTA: impreso_caja = False (para pre-cuenta de mesa o recibo)
    - COCINA: impreso_cocina = False (para comanda de preparación)
    """
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail=f"Pedido con ID #{pedido_id} no encontrado.")

    tipo_norm = (tipo or "CUENTA").upper().strip()
    if tipo_norm == "COCINA":
        pedido.impreso_cocina = False
    elif tipo_norm == "CUENTA":
        pedido.impreso_caja = False
    else:
        pedido.impreso_cocina = False
        pedido.impreso_caja = False

    db.commit()
    db.refresh(pedido)

    return {
        "success": True,
        "pedido_id": pedido.id,
        "codigo_pedido": pedido.codigo_pedido,
        "tipo": tipo_norm,
        "impreso_cocina": bool(pedido.impreso_cocina),
        "impreso_caja": bool(getattr(pedido, "impreso_caja", False)),
        "mensaje": f"Pedido #{pedido.codigo_pedido} encolado para reimpresión de {tipo_norm} en SAT Q22."
    }
