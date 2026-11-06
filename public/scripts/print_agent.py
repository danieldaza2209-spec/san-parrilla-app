#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
   RESTAURANTE SAN PARRILLA - AGENTE DE IMPRESIÓN REMOTA AUTOMÁTICA (SAT Q22)
==============================================================================
Ejecuta en segundo plano en el PC de caja (Windows) conectado a la impresora
térmica SAT Q22 (80mm).

Flujo:
1. Consulta cada POLL_INTERVAL (2.5s) a GET /api/impresion/pendientes.
2. Por cada pedido nuevo (creado desde celular, tablet o PC):
   a) Si IMPRIMIR_COCINA == True: imprime Tirilla de Cocina (80mm) y corta papel.
   b) Si IMPRIMIR_CAJA == True: imprime Tirilla de Cuenta / Domicilio (80mm) y corta papel.
   c) Notifica a POST /api/impresion/marcar-impreso/{pedido_id}.
==============================================================================
"""

import os
import sys
import time
from datetime import datetime

try:
    import requests
except ImportError:
    print("[!] Error: 'requests' no esta instalado. Ejecuta: pip install requests pywin32")
    sys.exit(1)

try:
    import win32print
    HAS_WIN32PRINT = True
except ImportError:
    HAS_WIN32PRINT = False

# ==============================================================================
# CONFIGURACIÓN PRINCIPAL DEL AGENTE
# ==============================================================================
BACKEND_URL = os.environ.get(
    "SP_BACKEND_URL",
    "https://san-parrilla-backend.onrender.com/api/impresion"
).rstrip("/")

FALLBACK_BACKEND_URL = os.environ.get(
    "SP_FALLBACK_URL",
    "https://www.sanparrilla.com/api/impresion"
).rstrip("/")

# Nombre de la impresora en Windows (busca automáticamente "SAT" o "Q22" o usa la predeterminada)
PRINTER_NAME = os.environ.get("SP_PRINTER_NAME", "SAT Q22").strip()

# Intervalo de consulta en segundos
POLL_INTERVAL = float(os.environ.get("SP_POLL_INTERVAL", "2.5"))

# Banderas de tirillas a imprimir por cada pedido
IMPRIMIR_COCINA = os.environ.get("SP_IMPRIMIR_COCINA", "true").lower() in ("true", "1", "yes", "si")
IMPRIMIR_CAJA = os.environ.get("SP_IMPRIMIR_CAJA", "true").lower() in ("true", "1", "yes", "si")

# Ancho estándar en papel térmico de 80mm (40-42 columnas)
LINE_WIDTH = 40

# ==============================================================================
# SECUENCIAS ESC/POS ESTÁNDAR EN BYTES (80mm - SAT Q22)
# ==============================================================================
ESC_RESET = b"\x1b\x40"             # Inicializar / Reset impresora
ESC_ALIGN_LEFT = b"\x1b\x61\x00"    # Alinear a la izquierda
ESC_ALIGN_CENTER = b"\x1b\x61\x01"  # Centrado
ESC_ALIGN_RIGHT = b"\x1b\x61\x02"   # Alinear a la derecha
ESC_BOLD_ON = b"\x1b\x45\x01"       # Negrita ON
ESC_BOLD_OFF = b"\x1b\x45\x00"      # Negrita OFF
GS_NORMAL = b"\x1d\x21\x00"         # Tamaño normal
GS_DOUBLE = b"\x1d\x21\x11"         # Doble ancho y doble alto (Mesa / Pedido)
GS_DOUBLE_H = b"\x1d\x21\x01"       # Doble alto
ESC_FEED_4 = b"\x1b\x64\x04"        # Avanzar 4 líneas antes del corte
GS_CUT_FULL = b"\x1d\x56\x41\x00"   # Corte total de papel


def limpiar_texto(texto) -> str:
    """Normaliza caracteres acentuados para compatibilidad con codificación térmica CP850/ASCII."""
    if texto is None:
        return ""
    s = str(texto)
    reemplazos = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
        "ñ": "n", "Ñ": "N", "ü": "u", "Ü": "U",
        "—": "-", "–": "-", "•": "*", "°": "o",
    }
    for k, v in reemplazos.items():
        s = s.replace(k, v)
    return s


def fmt_cop(valor) -> str:
    """Formatea un número en pesos colombianos ($XX.XXX)."""
    try:
        num = int(round(float(valor or 0)))
        return "$" + f"{num:,}".replace(",", ".")
    except Exception:
        return "$0"


def extraer_hora(fecha_raw) -> str:
    """Extrae la hora HH:MM del timestamp del pedido."""
    if not fecha_raw:
        return datetime.now().strftime("%H:%M")
    try:
        dt = datetime.fromisoformat(str(fecha_raw).replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except Exception:
        return datetime.now().strftime("%H:%M")


def detectar_impresora() -> str:
    """
    Busca automáticamente en Windows una impresora que contenga 'SAT' o 'Q22'
    (o PRINTER_NAME), o usa la impresora predeterminada del sistema.
    """
    if not HAS_WIN32PRINT:
        print("[AVISO] win32print no disponible. Ejecutando en modo simulacion de consola.")
        return "CONSOLA_DEBUG"

    try:
        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        impresoras = [p[2] for p in win32print.EnumPrinters(flags)]
        print(f"[i] Impresoras detectadas en Windows ({len(impresoras)}):")
        for imp in impresoras:
            print(f"    - {imp}")

        # 1. Buscar coincidencia con PRINTER_NAME configurado
        if PRINTER_NAME:
            for imp in impresoras:
                if PRINTER_NAME.lower() in imp.lower():
                    print(f"[+] Impresora seleccionada por nombre: '{imp}'")
                    return imp

        # 2. Buscar cualquier impresora que contenga 'SAT' o 'Q22' o 'POS-80'
        for imp in impresoras:
            low = imp.lower()
            if "sat" in low or "q22" in low or "pos-80" in low or "80mm" in low:
                print(f"[+] Impresora termica detectada automaticamente: '{imp}'")
                return imp

        # 3. Usar predeterminada de Windows
        default_imp = win32print.GetDefaultPrinter()
        print(f"[!] Usando impresora predeterminada de Windows: '{default_imp}'")
        return default_imp
    except Exception as e:
        print(f"[!] Error al enumerar impresoras ({e}). Intentando predeterminada...")
        try:
            return win32print.GetDefaultPrinter()
        except Exception:
            return "DEFAULT"


def enviar_raw_spooler(printer_name: str, data: bytes, job_title: str = "SanParrilla_POS") -> bool:
    """Envía la secuencia RAW ESC/POS directamente a la cola de impresión de Windows."""
    if not HAS_WIN32PRINT or printer_name == "CONSOLA_DEBUG":
        print(f"\n>>> [SIMULACION IMPRESION: {job_title}] <<<")
        try:
            print(data.decode("cp850", errors="ignore"))
        except Exception:
            print(data)
        print(f">>> [FIN {job_title}] <<<\n")
        return True

    hprinter = win32print.OpenPrinter(printer_name)
    try:
        win32print.StartDocPrinter(hprinter, 1, (job_title, None, "RAW"))
        try:
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(hprinter, data)
            win32print.EndPagePrinter(hprinter)
        finally:
            win32print.EndDocPrinter(hprinter)
        return True
    finally:
        win32print.ClosePrinter(hprinter)


def construir_tirilla_cocina(pedido: dict) -> bytes:
    """
    Construye la Tirilla de Cocina (80mm) sin precios, con notas y ubicación destacadas:
    ========================================
            SAN PARRILLA - COCINA          
    Pedido: #SP-XXXX | Tipo: MESA 3 / DOMI 
    Hora: HH:MM                             
    ----------------------------------------
    [CANT] PRODUCTO                        
      * Notas: Sin cebolla                  
      * Sopa: Fideos | Ppio: Lentejas      
      * Ubicación: Torre A                  
    ========================================
    """
    sep = ("=" * LINE_WIDTH + "\n").encode("cp850")
    subsep = ("-" * LINE_WIDTH + "\n").encode("cp850")

    raw_cod = str(pedido.get("codigo") or pedido.get("codigo_pedido") or f"SP-{pedido.get('id', 0)}")
    codigo = raw_cod if raw_cod.startswith("#") else f"#{raw_cod}"
    tipo = limpiar_texto(pedido.get("tipo_label") or pedido.get("tipo") or "MESA").upper()
    hora = extraer_hora(pedido.get("fecha_hora"))
    items = pedido.get("items") or []
    notas_generales = limpiar_texto(pedido.get("notas") or "")

    b = bytearray()
    b.extend(ESC_RESET)

    # Encabezado Cocina
    b.extend(ESC_ALIGN_CENTER)
    b.extend(sep)
    b.extend(ESC_BOLD_ON)
    b.extend(GS_DOUBLE_H)
    b.extend(b"SAN PARRILLA - COCINA\n")
    b.extend(GS_NORMAL)
    b.extend(ESC_BOLD_OFF)

    # Pedido y Tipo en tamaño grande destacado
    b.extend(ESC_ALIGN_LEFT)
    b.extend(ESC_BOLD_ON)
    b.extend(GS_DOUBLE)
    b.extend(limpiar_texto(f"{codigo} | {tipo}\n").encode("cp850", errors="ignore"))
    b.extend(GS_NORMAL)
    b.extend(limpiar_texto(f"Pedido: {codigo} | Tipo: {tipo}\n").encode("cp850", errors="ignore"))
    b.extend(ESC_BOLD_OFF)
    b.extend(limpiar_texto(f"Hora: {hora}\n").encode("cp850", errors="ignore"))
    b.extend(subsep)

    # Detalle de platos para cocina
    for it in items:
        cant = it.get("cantidad", 1)
        nombre = limpiar_texto(it.get("nombre") or it.get("plato_nombre") or "PRODUCTO").upper()
        notas_it = limpiar_texto(it.get("notas") or "")
        notas_raw = limpiar_texto(it.get("notas_item") or "")
        sopa = limpiar_texto(it.get("sopa") or "")
        ppio = limpiar_texto(it.get("principios") or it.get("principio") or "")
        acomp = limpiar_texto(it.get("acompanamiento") or "")
        ubicacion = limpiar_texto(it.get("ubicacion_hospitalaria") or "")
        empaque = limpiar_texto(it.get("empaque") or "")

        # Línea principal del producto en negrita y doble alto
        b.extend(ESC_BOLD_ON)
        b.extend(GS_DOUBLE_H)
        b.extend(f"[{cant}] {nombre}\n".encode("cp850", errors="ignore"))
        b.extend(GS_NORMAL)
        b.extend(ESC_BOLD_OFF)

        # Guarniciones (Sopa / Principio / Acompañamiento)
        partes_guarn = []
        if sopa:
            partes_guarn.append(f"Sopa: {sopa}")
        if ppio:
            partes_guarn.append(f"Ppio: {ppio}")
        if acomp:
            partes_guarn.append(f"Acomp: {acomp}")
        if partes_guarn:
            b.extend(f"  * {' | '.join(partes_guarn)}\n".encode("cp850", errors="ignore"))

        # Ubicación Hospitalaria (Torre A / Torre B / Urgencias) en negrita
        if ubicacion:
            b.extend(ESC_BOLD_ON)
            b.extend(GS_DOUBLE_H)
            b.extend(f"  * Ubicacion: {ubicacion}\n".encode("cp850", errors="ignore"))
            b.extend(GS_NORMAL)
            b.extend(ESC_BOLD_OFF)

        # Empaque
        if empaque:
            b.extend(f"  * Empaque: {empaque}\n".encode("cp850", errors="ignore"))

        # Notas de preparación del ítem
        if notas_it:
            b.extend(ESC_BOLD_ON)
            b.extend(f"  * Notas: {notas_it}\n".encode("cp850", errors="ignore"))
            b.extend(ESC_BOLD_OFF)
        elif notas_raw and not (sopa or ppio or acomp or ubicacion or empaque):
            b.extend(ESC_BOLD_ON)
            b.extend(f"  * Notas: {notas_raw}\n".encode("cp850", errors="ignore"))
            b.extend(ESC_BOLD_OFF)

    if notas_generales:
        b.extend(subsep)
        b.extend(ESC_BOLD_ON)
        b.extend(f"Obs: {notas_generales}\n".encode("cp850", errors="ignore"))
        b.extend(ESC_BOLD_OFF)

    b.extend(sep)
    b.extend(ESC_FEED_4)
    b.extend(GS_CUT_FULL)
    return bytes(b)


def alinear_linea(izquierda: str, derecha: str, ancho: int = LINE_WIDTH) -> str:
    """Alinea el texto izquierdo a la izquierda y el derecho a la derecha rellenando con espacios."""
    espacio_disp = ancho - len(derecha) - 1
    if len(izquierda) > espacio_disp:
        izquierda = izquierda[:espacio_disp]
    espacios = " " * max(1, ancho - len(izquierda) - len(derecha))
    return izquierda + espacios + derecha + "\n"


def construir_tirilla_caja(pedido: dict) -> bytes:
    """
    Construye la Tirilla de Cuenta / Pre-cuenta (80mm) con precios y totales.
    Si el pedido es de mesa, formatea como PRE-CUENTA MESA.
    Si el pedido es Domicilio o Para Llevar, formatea como Tirilla de Cuenta / Entrega.
    """
    sep = ("=" * LINE_WIDTH + "\n").encode("cp850")
    subsep = ("-" * LINE_WIDTH + "\n").encode("cp850")

    raw_cod = str(pedido.get("codigo") or pedido.get("codigo_pedido") or f"SP-{pedido.get('id', 0)}")
    codigo = raw_cod if raw_cod.startswith("#") else f"#{raw_cod}"
    tipo_str = limpiar_texto(pedido.get("tipo_label") or pedido.get("tipo") or "MESA").upper()
    mesa_val = limpiar_texto(pedido.get("mesa") or "")
    if mesa_val and not mesa_val.lower().startswith("mesa"):
        mesa_val = f"Mesa {mesa_val}"

    es_mesa = bool(mesa_val) or ("MESA" in tipo_str)
    hora = extraer_hora(pedido.get("fecha_hora"))
    creado_por = limpiar_texto(pedido.get("creado_por") or "Colaborador")
    subtotal = float(pedido.get("subtotal") or 0)
    packaging_fee = float(pedido.get("packaging_fee") or 0)
    delivery_fee = float(pedido.get("delivery_fee") or 0)
    total = float(pedido.get("total") or 0)
    items = pedido.get("items") or []

    b = bytearray()
    b.extend(ESC_RESET)

    if es_mesa:
        # ==============================================================
        # FORMATO TÉRMICO OFICIAL: PRE-CUENTA MESA (80mm)
        # ==============================================================
        mesa_nombre = mesa_val if mesa_val else tipo_str
        b.extend(ESC_ALIGN_CENTER)
        b.extend(sep)
        b.extend(ESC_BOLD_ON)
        b.extend(GS_DOUBLE_H)
        b.extend(b"RESTAURANTE SAN PARRILLA\n")
        b.extend(GS_NORMAL)
        b.extend(b"PRE-CUENTA MESA\n")
        b.extend(ESC_BOLD_OFF)
        b.extend(subsep)

        b.extend(ESC_ALIGN_LEFT)
        b.extend(ESC_BOLD_ON)
        b.extend(limpiar_texto(f"Mesa: {mesa_nombre} | Pedido: {codigo}\n").encode("cp850", errors="ignore"))
        b.extend(ESC_BOLD_OFF)
        b.extend(limpiar_texto(f"Hora: {hora} | Atendido por: {creado_por}\n").encode("cp850", errors="ignore"))
        b.extend(subsep)

        # Detalle de platos y precios
        for it in items:
            cant = int(it.get("cantidad") or 1)
            nombre = limpiar_texto(it.get("nombre") or it.get("plato_nombre") or "Plato").upper()
            unit = float(it.get("precio") or it.get("precio_unitario") or 0)
            sub_it = float(it.get("subtotal") or (unit * cant))
            linea_item = alinear_linea(f"[{cant}] {nombre}", fmt_cop(sub_it))
            b.extend(ESC_BOLD_ON)
            b.extend(linea_item.encode("cp850", errors="ignore"))
            b.extend(ESC_BOLD_OFF)
            if cant > 1:
                b.extend(f"   ({fmt_cop(unit)} c/u)\n".encode("cp850", errors="ignore"))

        b.extend(subsep)
        if subtotal > 0 and (packaging_fee > 0 or subtotal != total):
            b.extend(alinear_linea("SUBTOTAL:", fmt_cop(subtotal)).encode("cp850", errors="ignore"))
        else:
            b.extend(alinear_linea("SUBTOTAL:", fmt_cop(total)).encode("cp850", errors="ignore"))

        if packaging_fee > 0:
            b.extend(alinear_linea("EMPAQUES:", fmt_cop(packaging_fee)).encode("cp850", errors="ignore"))

        b.extend(ESC_BOLD_ON)
        b.extend(GS_DOUBLE_H)
        b.extend(alinear_linea("TOTAL A PAGAR:", fmt_cop(total)).encode("cp850", errors="ignore"))
        b.extend(GS_NORMAL)
        b.extend(ESC_BOLD_OFF)

        b.extend(sep)
        b.extend(ESC_ALIGN_CENTER)
        b.extend(b"   !Gracias por su visita a San Parrilla!\n")
        b.extend(ESC_FEED_4)
        b.extend(GS_CUT_FULL)
        return bytes(b)

    # ==============================================================
    # FORMATO: DOMICILIOS Y PARA LLEVAR (CUENTA / ENTREGA)
    # ==============================================================
    cliente = limpiar_texto(pedido.get("cliente_nombre") or "Cliente")
    telefono = limpiar_texto(pedido.get("cliente_telefono") or "")
    direccion = limpiar_texto(pedido.get("direccion") or "")
    barrio = limpiar_texto(pedido.get("barrio") or "")
    mensajero = limpiar_texto(pedido.get("courier_name") or "")
    metodo_pago = limpiar_texto(pedido.get("metodo_pago") or "EFECTIVO")

    b.extend(ESC_ALIGN_CENTER)
    b.extend(sep)
    b.extend(ESC_BOLD_ON)
    b.extend(GS_DOUBLE_H)
    b.extend(b"RESTAURANTE SAN PARRILLA\n")
    b.extend(GS_NORMAL)
    b.extend(ESC_BOLD_OFF)
    b.extend(b"Barrancabermeja - POS\n")
    b.extend(subsep)

    b.extend(ESC_ALIGN_LEFT)
    b.extend(ESC_BOLD_ON)
    b.extend(f"Pedido: {codigo} | Tipo: {tipo_str}\n".encode("cp850", errors="ignore"))
    b.extend(ESC_BOLD_OFF)
    b.extend(f"Hora: {hora}\n".encode("cp850", errors="ignore"))

    cli_line = f"Cliente: {cliente}"
    if telefono:
        cli_line += f" | Tel: {telefono}"
    b.extend(f"{cli_line}\n".encode("cp850", errors="ignore"))

    if direccion:
        dir_line = f"Direccion: {direccion}"
        if barrio:
            dir_line += f" ({barrio})"
        b.extend(ESC_BOLD_ON)
        b.extend(f"{dir_line}\n".encode("cp850", errors="ignore"))
        b.extend(ESC_BOLD_OFF)

    if mensajero:
        b.extend(f"Mensajero: {mensajero}\n".encode("cp850", errors="ignore"))

    b.extend(subsep)

    for it in items:
        cant = int(it.get("cantidad") or 1)
        nombre = limpiar_texto(it.get("nombre") or it.get("plato_nombre") or "Plato")
        unit = float(it.get("precio") or it.get("precio_unitario") or 0)
        sub_it = float(it.get("subtotal") or (unit * cant))
        ubicacion = limpiar_texto(it.get("ubicacion_hospitalaria") or "")

        titulo_it = f"{cant}x {nombre}"
        if ubicacion:
            titulo_it += f" [{ubicacion.upper()}]"

        linea_it = alinear_linea(titulo_it, fmt_cop(sub_it))
        b.extend(ESC_BOLD_ON)
        b.extend(linea_it.encode("cp850", errors="ignore"))
        b.extend(ESC_BOLD_OFF)
        if cant > 1:
            b.extend(f"   ({fmt_cop(unit)} c/u)\n".encode("cp850", errors="ignore"))

    b.extend(subsep)

    if packaging_fee > 0:
        b.extend(alinear_linea("Empaques:", fmt_cop(packaging_fee)).encode("cp850", errors="ignore"))
    if delivery_fee > 0:
        b.extend(alinear_linea("Domicilio:", fmt_cop(delivery_fee)).encode("cp850", errors="ignore"))

    b.extend(ESC_BOLD_ON)
    b.extend(GS_DOUBLE_H)
    b.extend(alinear_linea("TOTAL A PAGAR:", fmt_cop(total)).encode("cp850", errors="ignore"))
    b.extend(GS_NORMAL)
    b.extend(f"Metodo de Pago: {metodo_pago}\n".encode("cp850", errors="ignore"))
    b.extend(ESC_BOLD_OFF)

    b.extend(sep)
    b.extend(ESC_FEED_4)
    b.extend(GS_CUT_FULL)
    return bytes(b)


def obtener_url_base_impresion(url_config: str) -> str:
    """Garantiza que la URL apunte a /api/impresion."""
    u = url_config.rstrip("/")
    if not u.endswith("/api/impresion"):
        u = u + "/api/impresion"
    return u


def consultar_pendientes(session: requests.Session):
    """Consulta la lista de pedidos pendientes en Render (con fallback a www.sanparrilla.com)."""
    urls = [obtener_url_base_impresion(BACKEND_URL)]
    fb = obtener_url_base_impresion(FALLBACK_BACKEND_URL)
    if fb not in urls:
        urls.append(fb)

    last_exc = None
    for base in urls:
        try:
            r = session.get(f"{base}/pendientes", timeout=10)
            if r.status_code == 200:
                return r.json(), base
        except requests.RequestException as exc:
            last_exc = exc
            continue

    if last_exc:
        raise last_exc
    return [], urls[0]


def marcar_pedido_impreso(session: requests.Session, base_url: str, pedido_id: int) -> bool:
    """Notifica al backend que el pedido ya fue impreso en cocina y caja."""
    urls = [base_url, obtener_url_base_impresion(BACKEND_URL), obtener_url_base_impresion(FALLBACK_BACKEND_URL)]
    vistos = set()
    for b_url in urls:
        if b_url in vistos:
            continue
        vistos.add(b_url)
        try:
            r = session.post(f"{b_url}/marcar-impreso/{pedido_id}", timeout=10)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            continue
    return False


def iniciar_agente():
    print("=" * 60)
    print("  SAN PARRILLA OS - AGENTE DE IMPRESION AUTOMATICA SAT Q22")
    print("=" * 60)
    printer_target = detectar_impresora()
    print(f"[i] Backend Primario : {obtener_url_base_impresion(BACKEND_URL)}")
    print(f"[i] Impresora Destino: {printer_target}")
    print(f"[i] Intervalo Sondeo : {POLL_INTERVAL}s")
    print(f"[i] Tirilla Cocina   : {'ACTIVA' if IMPRIMIR_COCINA else 'DESACTIVADA'}")
    print(f"[i] Tirilla Caja/Dom : {'ACTIVA' if IMPRIMIR_CAJA else 'DESACTIVADA'}")
    print("=" * 60)
    print("[*] Escuchando pedidos nuevos en segundo plano (Ctrl+C para detener)...\n")

    http_session = requests.Session()
    http_session.headers.update({"Accept": "application/json", "User-Agent": "SanParrillaPrintAgent/2.0"})

    while True:
        try:
            pendientes, active_base = consultar_pendientes(http_session)
            if isinstance(pendientes, list) and len(pendientes) > 0:
                for ped in pendientes:
                    ped_id = ped.get("id")
                    cod = ped.get("codigo") or ped.get("codigo_pedido") or f"#{ped_id}"
                    tipo = ped.get("tipo_label") or ped.get("tipo") or "PEDIDO"
                    impreso_cocina_bd = bool(ped.get("impreso_cocina", False))
                    impreso_caja_bd = bool(ped.get("impreso_caja", False))
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Pedido pendiente detectado: {cod} ({tipo}) [Cocina: {impreso_cocina_bd}, Caja: {impreso_caja_bd}]")

                    exito_cocina = True
                    exito_caja = True

                    if IMPRIMIR_COCINA and not impreso_cocina_bd:
                        bytes_cocina = construir_tirilla_cocina(ped)
                        exito_cocina = enviar_raw_spooler(printer_target, bytes_cocina, f"Cocina_{cod}")
                        if exito_cocina:
                            print(f"    [+] Tirilla de COCINA enviada a '{printer_target}'.")

                    if IMPRIMIR_CAJA and not impreso_caja_bd:
                        if IMPRIMIR_COCINA and not impreso_cocina_bd:
                            time.sleep(0.4)
                        bytes_caja = construir_tirilla_caja(ped)
                        job_label = f"PreCuenta_{cod}" if ("MESA" in str(tipo).upper() or ped.get("mesa")) else f"Cuenta_{cod}"
                        exito_caja = enviar_raw_spooler(printer_target, bytes_caja, job_label)
                        if exito_caja:
                            print(f"    [+] Tirilla de CUENTA / PRE-CUENTA enviada a '{printer_target}'.")

                    if exito_cocina and exito_caja:
                        if marcar_pedido_impreso(http_session, active_base, ped_id):
                            print(f"    [OK] Pedido {cod} marcado como IMPRESO en Neon DB.\n")
                        else:
                            print(f"    [!] Aviso: Se imprimio {cod}, pero fallo la confirmacion HTTP. Se reintentara.\n")

            time.sleep(POLL_INTERVAL)

        except requests.RequestException as net_err:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [Red/Render] Conexion inestable ({net_err}). Reintentando en 3s...")
            time.sleep(3.0)
        except KeyboardInterrupt:
            print("\n[!] Agente detenido manualmente por el usuario.")
            break
        except Exception as err:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [Error] {err}. Continuando en 3s...")
            time.sleep(3.0)


if __name__ == "__main__":
    iniciar_agente()
