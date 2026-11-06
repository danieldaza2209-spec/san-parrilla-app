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
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
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
BACKEND_URL = (
    os.environ.get("SP_BACKEND_URL")
    or os.environ.get("SP_API_URL")
    or "https://san-parrilla-backend.onrender.com/api/impresion"
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


def es_pedido_clinica(pedido: dict) -> bool:
    """Detecta si un pedido corresponde al convenio hospitalario Clínica Primero de Mayo."""
    cli = str(pedido.get("cliente_nombre") or pedido.get("customer_name") or "").lower()
    if "clínica" in cli or "clinica" in cli or "hospital" in cli:
        return True

    notas_ped = str(pedido.get("notas") or "").lower()
    if "clínica" in notas_ped or "clinica" in notas_ped or "domicilios_clinica" in notas_ped:
        return True

    items = pedido.get("items") or []
    for it in items:
        nom = str(it.get("nombre") or it.get("plato_nombre") or "").lower()
        ubic = str(it.get("ubicacion_hospitalaria") or "").strip()
        notas_it = str(it.get("notas") or it.get("notas_item") or "").lower()
        if ubic:
            return True
        if "torre a" in notas_it or "torre b" in notas_it or "urgencias" in notas_it:
            return True
        if "dieta" in nom or "clínica" in nom or "clinica" in nom:
            return True
    return False


def normalizar_ubicacion_clinica(ubic_raw: str, notas_raw: str = "") -> str:
    """Estandariza la ubicación a TORRE A, TORRE B, URGENCIAS u otra."""
    texto = f"{ubic_raw} {notas_raw}".upper()
    if "TORRE B" in texto or "TORRE_B" in texto:
        return "TORRE B"
    elif "URGENCIAS" in texto or "URGENCIA" in texto:
        return "URGENCIAS"
    elif "TORRE A" in texto or "TORRE_A" in texto:
        return "TORRE A"
    elif ubic_raw and ubic_raw.strip():
        return ubic_raw.strip().upper()
    return "TORRE A"


def extraer_tipo_dieta(nombre_plato: str) -> str:
    """Extrae el tipo de dieta en mayúsculas (ej. 'NORMAL', 'HIPOSÓDICA', 'LÍQUIDA', 'HIPERPROTEICA', 'BLANDA')."""
    nom = str(nombre_plato or "").strip()
    if "Dieta" in nom:
        return nom.split("Dieta", 1)[1].strip().upper()
    elif "dieta" in nom.lower():
        idx = nom.lower().find("dieta")
        return nom[idx + 5:].strip(" -:").upper()
    clean = re.sub(r"^(Desayuno|Almuerzo|Cena)\s+Cl[íi]nica\s*-\s*", "", nom, flags=re.IGNORECASE)
    clean = re.sub(r"^Cl[íi]nica\s*-\s*", "", clean, flags=re.IGNORECASE)
    return clean.strip().upper() or "NORMAL"


def es_item_agua_auto(nombre_plato: str) -> bool:
    """Detecta si el ítem es una botella de agua automática del convenio."""
    nom = str(nombre_plato or "").lower()
    return "botella con agua" in nom or "agua (dieta hipo" in nom or "agua clinica" in nom


def es_dieta_hipo(nombre_plato: str) -> bool:
    """Detecta si la dieta es hiposódica o hipoglúcida y por ende amerita agua automática."""
    nom = str(nombre_plato or "").lower()
    if es_item_agua_auto(nom):
        return False
    return "hiposódica" in nom or "hiposodica" in nom or "hipoglúcida" in nom or "hipoglucida" in nom


def extraer_cantidad_domicilios_clinica(pedido: dict) -> int:
    """Extrae la cantidad de domicilios / carreras registradas para el servicio."""
    cant = pedido.get("cantidad_domicilios")
    if cant is not None and int(cant) > 0:
        return int(cant)
    notas = str(pedido.get("notas") or "")
    m = re.search(r"\[DOMICILIOS_CLINICA:(\d+)\]", notas, flags=re.IGNORECASE)
    if m:
        return int(m.group(1))
    df = float(pedido.get("delivery_fee") or 0)
    if df > 0:
        return max(1, int(round(df / 3000.0)))
    tipo = str(pedido.get("tipo") or pedido.get("tipo_label") or "").upper()
    if "DOMICILIO" in tipo:
        return 1
    return 0


def procesar_estructura_clinica(pedido: dict):
    """
    Agrupa los ítems de un pedido de clínica:
    1. Por Ubicación (TORRE A, TORRE B, URGENCIAS, etc.)
    2. Dentro de cada ubicación, por Tipo de Dieta (NORMAL, LÍQUIDA, BLANDA, etc.)
    Calcula totales:
    - total_raciones: suma de raciones de comida
    - total_agua_auto: botellas de agua automáticas
    - total_domicilios: carreras registradas
    """
    items = pedido.get("items") or []
    agrupado = {}
    orden_ubicaciones = ["TORRE A", "TORRE B", "URGENCIAS"]
    total_raciones = 0
    total_agua_items = 0
    total_dietas_hipo = 0

    for it in items:
        cant = int(it.get("cantidad") or 1)
        nombre = str(it.get("nombre") or it.get("plato_nombre") or "").strip()
        unit = float(it.get("precio") or it.get("precio_unitario") or 0)
        sub_it = float(it.get("subtotal") or (unit * cant))
        ubic_raw = str(it.get("ubicacion_hospitalaria") or "")
        notas_it = str(it.get("notas") or it.get("notas_item") or "")

        if es_item_agua_auto(nombre):
            total_agua_items += cant
            continue

        total_raciones += cant
        if es_dieta_hipo(nombre):
            total_dietas_hipo += cant

        ubic = normalizar_ubicacion_clinica(ubic_raw, notas_it)
        dieta = extraer_tipo_dieta(nombre)

        if ubic not in agrupado:
            agrupado[ubic] = {}

        if dieta not in agrupado[ubic]:
            agrupado[ubic][dieta] = {
                "cantidad": 0,
                "precio_total": 0.0,
                "precio_unit": unit,
                "notas": [],
            }

        agrupado[ubic][dieta]["cantidad"] += cant
        agrupado[ubic][dieta]["precio_total"] += sub_it
        if notas_it:
            clean_n = re.sub(r"\[.*?(TORRE\s*A|TORRE\s*B|URGENCIAS).*?\]", "", notas_it, flags=re.IGNORECASE).strip(" |")
            if clean_n and clean_n not in agrupado[ubic][dieta]["notas"]:
                agrupado[ubic][dieta]["notas"].append(clean_n)

    total_agua_final = max(total_agua_items, total_dietas_hipo)
    total_domicilios = extraer_cantidad_domicilios_clinica(pedido)

    ubicaciones_ordenadas = [u for u in orden_ubicaciones if u in agrupado] + [u for u in sorted(agrupado.keys()) if u not in orden_ubicaciones]
    return agrupado, ubicaciones_ordenadas, total_raciones, total_agua_final, total_domicilios


def construir_tirilla_cocina(pedido: dict) -> bytes:
    """
    Construye la Comanda de Cocina (80mm) con diseno visual exacto:
    ========================================
            SAN PARRILLA - COCINA          
    ========================================
    *** >>> ADICIÓN A MESA <<< *** (si aplica)
    PEDIDO: #SP-XXXX
    TIPO: [DOMICILIO / PARA LLEVAR / MESA X]
    HORA: HH:MM
    ATENDIDO POR: [colaborador_nombre]
    UBICACIÓN: MESA [X] (si es Mesa, en grande)
    CLIENTE: [cliente_nombre / Mostrador / General / Mesa X]
    ----------------------------------------
    [CANT] NOMBRE DEL PLATO
      [TORRE A / TORRE B / URGENCIAS]
      > Sopa: [Nombre] | Ppio: [Nombre]
      > Acomp: [Nombre]
      * NOTA: [Observaciones]
      [Empaque: Icopor / Caja]
    ========================================
    """
    sep = ("=" * LINE_WIDTH + "\n").encode("cp850")
    subsep = ("-" * LINE_WIDTH + "\n").encode("cp850")

    raw_cod = str(pedido.get("codigo") or pedido.get("codigo_pedido") or f"SP-{pedido.get('id', 0)}")
    codigo = raw_cod if raw_cod.startswith("#") else f"#{raw_cod}"
    tipo = limpiar_texto(pedido.get("tipo_label") or pedido.get("tipo") or "MESA").upper()
    hora = extraer_hora(pedido.get("fecha_hora"))
    creado_por = limpiar_texto(pedido.get("creado_por") or "Colaborador")
    items = pedido.get("items") or []
    notas_generales = limpiar_texto(pedido.get("notas") or "")
    es_adicion = bool(pedido.get("es_adicion") or "ADICION" in tipo)

    b = bytearray()
    b.extend(ESC_RESET)

    # 0. MANEJO ESPECIAL AGRUPADO PARA CONVENIO CLÍNICA
    if es_pedido_clinica(pedido):
        agrupado, ubicaciones, tot_raciones, tot_agua, tot_dom = procesar_estructura_clinica(pedido)

        b.extend(ESC_ALIGN_CENTER)
        b.extend(sep)
        b.extend(ESC_BOLD_ON)
        b.extend(b"        SAN PARRILLA - COCINA          \n")
        b.extend(b"   CONVENIO CLINICA PRIMERO DE MAYO    \n")
        b.extend(ESC_BOLD_OFF)
        b.extend(sep)

        b.extend(ESC_ALIGN_LEFT)
        b.extend(ESC_BOLD_ON)
        b.extend(limpiar_texto(f"PEDIDO: {codigo}\n").encode("cp850", errors="ignore"))
        b.extend(limpiar_texto(f"TIPO: {tipo} (PACIENTES)\n").encode("cp850", errors="ignore"))
        b.extend(ESC_BOLD_OFF)
        b.extend(limpiar_texto(f"HORA: {hora}\n").encode("cp850", errors="ignore"))
        b.extend(limpiar_texto(f"ATENDIDO POR: {creado_por}\n").encode("cp850", errors="ignore"))

        area_torre = " / ".join(ubicaciones) if ubicaciones else "TORRE A"
        b.extend(ESC_BOLD_ON)
        b.extend(b"CONVENIO: CLINICA PRIMERO DE MAYO\n")
        b.extend(limpiar_texto(f"AREA / TORRE: {area_torre}\n").encode("cp850", errors="ignore"))
        b.extend(ESC_BOLD_OFF)
        b.extend(subsep)

        b.extend(ESC_ALIGN_CENTER)
        b.extend(ESC_BOLD_ON)
        b.extend(b">>> DISTRIBUCION POR PABELLON Y DIETA <<<\n")
        b.extend(ESC_BOLD_OFF)
        b.extend(subsep)
        b.extend(ESC_ALIGN_LEFT)

        for ubic in ubicaciones:
            b.extend(ESC_BOLD_ON)
            b.extend(GS_DOUBLE_H)
            b.extend(f"[UBICACION: {ubic}]\n".encode("cp850", errors="ignore"))
            b.extend(GS_NORMAL)
            b.extend(ESC_BOLD_OFF)

            dietas_map = agrupado[ubic]
            for dieta_nom, data_d in sorted(dietas_map.items()):
                cant_d = data_d["cantidad"]
                b.extend(ESC_BOLD_ON)
                b.extend(f"  {cant_d:2d}X {limpiar_texto(dieta_nom)}\n".encode("cp850", errors="ignore"))
                b.extend(ESC_BOLD_OFF)
                for nota in data_d["notas"]:
                    b.extend(f"     * {limpiar_texto(nota)}\n".encode("cp850", errors="ignore"))
            b.extend(b"\n")

        b.extend(subsep)
        b.extend(ESC_ALIGN_CENTER)
        b.extend(ESC_BOLD_ON)
        b.extend(b"CONSOLIDADO GENERAL DEL SERVICIO\n")
        b.extend(ESC_BOLD_OFF)
        b.extend(ESC_ALIGN_LEFT)
        b.extend(ESC_BOLD_ON)
        b.extend(limpiar_texto(f"  TOTAL RACIONES ENTREGADAS   : {tot_raciones}\n").encode("cp850", errors="ignore"))
        b.extend(limpiar_texto(f"  TOTAL BOTELLAS AGUA AUTO    : {tot_agua}\n").encode("cp850", errors="ignore"))
        b.extend(limpiar_texto(f"  CANTIDAD DOMICILIOS/CARRERAS: {tot_dom}\n").encode("cp850", errors="ignore"))
        b.extend(ESC_BOLD_OFF)

        if notas_generales:
            b.extend(subsep)
            b.extend(limpiar_texto(f"  * NOTA PEDIDO: {notas_generales}\n").encode("cp850", errors="ignore"))

        b.extend(sep)
        b.extend(ESC_FEED_4)
        b.extend(GS_CUT_FULL)
        return bytes(b)

    # 1. ENCABEZADO CENTRADO OFICIAL
    b.extend(ESC_ALIGN_CENTER)
    b.extend(sep)
    b.extend(ESC_BOLD_ON)
    b.extend(b"        SAN PARRILLA - COCINA          \n")
    b.extend(ESC_BOLD_OFF)
    b.extend(sep)

    # Si es adicion a mesa ocupada, banner intermedio destacado
    if es_adicion:
        b.extend(ESC_BOLD_ON)
        b.extend(GS_DOUBLE_H)
        b.extend(b"*** >>> ADICION A MESA <<< ***\n")
        b.extend(GS_NORMAL)
        b.extend(ESC_BOLD_OFF)

    # 2. METADATOS EN TEXTO NORMAL / DESTACADO
    b.extend(ESC_ALIGN_LEFT)
    b.extend(ESC_BOLD_ON)
    b.extend(limpiar_texto(f"PEDIDO: {codigo}\n").encode("cp850", errors="ignore"))
    b.extend(limpiar_texto(f"TIPO: {tipo}\n").encode("cp850", errors="ignore"))
    b.extend(ESC_BOLD_OFF)
    b.extend(limpiar_texto(f"HORA: {hora}\n").encode("cp850", errors="ignore"))
    b.extend(limpiar_texto(f"ATENDIDO POR: {creado_por}\n").encode("cp850", errors="ignore"))

    mesa_val = limpiar_texto(pedido.get("mesa") or "")
    es_mesa = ("MESA" in tipo) or bool(mesa_val)
    cli_val = pedido.get("cliente_nombre") or pedido.get("customer_name") or ""
    cli_raw = limpiar_texto(cli_val).strip()

    if es_mesa:
        num_mesa = re.sub(r"(?i)^mesa\s*", "", mesa_val).strip()
        if not num_mesa:
            m = re.search(r"MESA\s*(\S+)", tipo, flags=re.IGNORECASE)
            num_mesa = m.group(1).strip() if m else "1"

        if not cli_raw or cli_raw.lower() in ("cliente", "none", "null"):
            cli_mesa = f"Mesa {num_mesa}"
        else:
            cli_mesa = cli_raw

        b.extend(ESC_BOLD_ON)
        b.extend(GS_DOUBLE_H)
        b.extend(limpiar_texto(f"UBICACION: MESA {num_mesa}\n").encode("cp850", errors="ignore"))
        b.extend(GS_NORMAL)
        b.extend(limpiar_texto(f"CLIENTE: {cli_mesa}\n").encode("cp850", errors="ignore"))
        b.extend(ESC_BOLD_OFF)
    else:
        is_mostrador = ("LLEVAR" in tipo) or ("MOSTRADOR" in tipo)
        if cli_raw and cli_raw.lower() not in ("cliente", "none", "null", "mostrador", "general"):
            cliente_str = cli_raw.upper()
        elif is_mostrador:
            cliente_str = "Mostrador"
        else:
            cliente_str = "Cliente General"

        b.extend(ESC_BOLD_ON)
        b.extend(limpiar_texto(f"CLIENTE: {cliente_str}\n").encode("cp850", errors="ignore"))
        b.extend(ESC_BOLD_OFF)

    b.extend(subsep)

    # 3. BLOQUE DE PLATOS (SIN PRECIOS, LECTURA LIMPIA)
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

        # Cantidad y nombre en negrilla / doble altura
        b.extend(ESC_BOLD_ON)
        b.extend(GS_DOUBLE_H)
        b.extend(f"[{cant}] {nombre}\n".encode("cp850", errors="ignore"))
        b.extend(GS_NORMAL)
        b.extend(ESC_BOLD_OFF)

        # Indicacion clinica si aplica (Torre A / Torre B / Urgencias)
        if ubicacion:
            b.extend(ESC_BOLD_ON)
            b.extend(limpiar_texto(f"  [{ubicacion.upper()}]\n").encode("cp850", errors="ignore"))
            b.extend(ESC_BOLD_OFF)

        # Sopa y principio
        partes_guarn = []
        if sopa:
            partes_guarn.append(f"Sopa: {sopa}")
        if ppio:
            partes_guarn.append(f"Ppio: {ppio}")
        if partes_guarn:
            b.extend(limpiar_texto(f"  > {' | '.join(partes_guarn)}\n").encode("cp850", errors="ignore"))

        # Acompanamiento
        if acomp:
            b.extend(limpiar_texto(f"  > Acomp: {acomp}\n").encode("cp850", errors="ignore"))

        # Notas y observaciones destacadas
        if notas_it:
            b.extend(ESC_BOLD_ON)
            b.extend(limpiar_texto(f"  * NOTA: {notas_it}\n").encode("cp850", errors="ignore"))
            b.extend(ESC_BOLD_OFF)
        elif notas_raw and not (sopa or ppio or acomp or ubicacion or empaque):
            b.extend(ESC_BOLD_ON)
            b.extend(limpiar_texto(f"  * NOTA: {notas_raw}\n").encode("cp850", errors="ignore"))
            b.extend(ESC_BOLD_OFF)

        # Empaque si es para llevar o domicilio
        if empaque:
            b.extend(limpiar_texto(f"  [Empaque: {empaque}]\n").encode("cp850", errors="ignore"))

    # Observaciones generales del pedido
    if notas_generales:
        b.extend(subsep)
        b.extend(ESC_BOLD_ON)
        b.extend(limpiar_texto(f"  * NOTA PEDIDO: {notas_generales}\n").encode("cp850", errors="ignore"))
        b.extend(ESC_BOLD_OFF)

    # 4. PIE CON SEPARADOR Y CORTE TOTAL
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

    # 0. MANEJO ESPECIAL AGRUPADO PARA CONVENIO CLÍNICA
    if es_pedido_clinica(pedido):
        agrupado, ubicaciones, tot_raciones, tot_agua, tot_dom = procesar_estructura_clinica(pedido)

        cliente = limpiar_texto(pedido.get("cliente_nombre") or pedido.get("customer_name") or "Clinica Primero de Mayo (Pacientes)")
        direccion = limpiar_texto(pedido.get("direccion") or "Clinica Primero de Mayo - Hospitalizacion")
        metodo_pago = limpiar_texto(pedido.get("metodo_pago") or "FIADO / CARTERA")

        b.extend(ESC_ALIGN_CENTER)
        b.extend(sep)
        b.extend(ESC_BOLD_ON)
        b.extend(GS_DOUBLE_H)
        b.extend(b"RESTAURANTE SAN PARRILLA\n")
        b.extend(GS_NORMAL)
        b.extend(ESC_BOLD_OFF)
        b.extend(b"TICKET ENTREGA / CUENTA CONVENIO\n")
        b.extend(subsep)

        b.extend(ESC_ALIGN_LEFT)
        b.extend(ESC_BOLD_ON)
        b.extend(limpiar_texto(f"Pedido: {codigo} | Tipo: {tipo_str}\n").encode("cp850", errors="ignore"))
        b.extend(ESC_BOLD_OFF)
        b.extend(limpiar_texto(f"Hora: {hora} | Atendido: {creado_por}\n").encode("cp850", errors="ignore"))
        b.extend(limpiar_texto(f"Cliente: {cliente}\n").encode("cp850", errors="ignore"))
        if direccion:
            b.extend(limpiar_texto(f"Entrega: {direccion}\n").encode("cp850", errors="ignore"))
        b.extend(subsep)

        b.extend(ESC_ALIGN_CENTER)
        b.extend(ESC_BOLD_ON)
        b.extend(b">>> DISTRIBUCION POR PABELLON Y DIETA <<<\n")
        b.extend(ESC_BOLD_OFF)
        b.extend(subsep)
        b.extend(ESC_ALIGN_LEFT)

        for ubic in ubicaciones:
            b.extend(ESC_BOLD_ON)
            b.extend(f"[UBICACION: {ubic}]\n".encode("cp850", errors="ignore"))
            b.extend(ESC_BOLD_OFF)

            dietas_map = agrupado[ubic]
            for dieta_nom, data_d in sorted(dietas_map.items()):
                cant_d = data_d["cantidad"]
                sub_d = data_d["precio_total"]
                linea = alinear_linea(f"  {cant_d:2d}X {limpiar_texto(dieta_nom)}", fmt_cop(sub_d))
                b.extend(linea.encode("cp850", errors="ignore"))
            b.extend(b"\n")

        # CONSOLIDADO GENERAL AL PIE
        b.extend(subsep)
        b.extend(ESC_ALIGN_CENTER)
        b.extend(ESC_BOLD_ON)
        b.extend(b"CONSOLIDADO GENERAL DEL SERVICIO\n")
        b.extend(ESC_BOLD_OFF)
        b.extend(ESC_ALIGN_LEFT)
        b.extend(ESC_BOLD_ON)
        b.extend(limpiar_texto(f"  TOTAL RACIONES ENTREGADAS   : {tot_raciones}\n").encode("cp850", errors="ignore"))
        b.extend(limpiar_texto(f"  TOTAL BOTELLAS AGUA AUTO    : {tot_agua} ($0)\n").encode("cp850", errors="ignore"))
        b.extend(limpiar_texto(f"  CANTIDAD DOMICILIOS/CARRERAS: {tot_dom}\n").encode("cp850", errors="ignore"))
        b.extend(ESC_BOLD_OFF)
        b.extend(subsep)

        # Totales financieros
        if packaging_fee > 0:
            b.extend(alinear_linea("Empaques:", fmt_cop(packaging_fee)).encode("cp850", errors="ignore"))
        if delivery_fee > 0:
            b.extend(alinear_linea(f"Domicilios ({tot_dom} carreras):", fmt_cop(delivery_fee)).encode("cp850", errors="ignore"))

        b.extend(ESC_BOLD_ON)
        b.extend(GS_DOUBLE_H)
        b.extend(alinear_linea("TOTAL A PAGAR:", fmt_cop(total)).encode("cp850", errors="ignore"))
        b.extend(GS_NORMAL)
        b.extend(limpiar_texto(f"Metodo de Pago: {metodo_pago}\n").encode("cp850", errors="ignore"))
        b.extend(ESC_BOLD_OFF)

        b.extend(sep)
        b.extend(ESC_FEED_4)
        b.extend(GS_CUT_FULL)
        return bytes(b)

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
    cliente = limpiar_texto(pedido.get("cliente_nombre") or pedido.get("customer_name") or "Cliente")
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


def marcar_pedido_impreso(session: requests.Session, base_url: str, pedido_id: int, tipo: str = "COCINA") -> bool:
    """Notifica al backend que el trabajo (COCINA o CUENTA) ya fue impreso."""
    urls = [base_url, obtener_url_base_impresion(BACKEND_URL), obtener_url_base_impresion(FALLBACK_BACKEND_URL)]
    vistos = set()
    for b_url in urls:
        if b_url in vistos:
            continue
        vistos.add(b_url)
        try:
            r = session.post(f"{b_url}/marcar-impreso/{pedido_id}?tipo={tipo}", timeout=10)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            continue
    return False


def iniciar_servidor_estado_local(printer_target: str):
    """Expone http://127.0.0.1:8765/status para que el navegador detecte que el agente Python ESC/POS esta activo."""
    class StatusHandler(BaseHTTPRequestHandler):
        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.end_headers()

        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            payload = f'{{"ok": true, "agent": "python-escpos", "printer": "{limpiar_texto(printer_target)}"}}'
            self.wfile.write(payload.encode("utf-8"))

        def log_message(self, format, *args):
            return

    def _serve():
        try:
            srv = HTTPServer(("127.0.0.1", 8765), StatusHandler)
            srv.serve_forever()
        except Exception:
            pass

    t = threading.Thread(target=_serve, daemon=True)
    t.start()


def iniciar_agente():
    print("=" * 60)
    print("  SAN PARRILLA OS - AGENTE DE IMPRESION AUTOMATICA SAT Q22")
    print("=" * 60)
    printer_target = detectar_impresora()
    iniciar_servidor_estado_local(printer_target)
    print(f"[i] Backend Primario : {obtener_url_base_impresion(BACKEND_URL)}")
    print(f"[i] Impresora Destino: {printer_target}")
    print(f"[i] Intervalo Sondeo : {POLL_INTERVAL}s")
    print(f"[i] Modo Operativo   : AUTOMATICO (SOLO COCINA) | CUENTAS Y TESTS (BAJO DEMANDA)")
    print("=" * 60)
    print("[*] Escuchando comandas nuevas en segundo plano (Ctrl+C para detener)...\n")

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
                    tipo_trabajo = str(ped.get("tipo_trabajo") or ("CUENTA" if ped.get("impreso_cocina") and not ped.get("impreso_caja") else "COCINA")).upper()

                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Trabajo pendiente: {cod} ({tipo}) -> [{tipo_trabajo}]")

                    if tipo_trabajo == "COCINA":
                        bytes_cocina = construir_tirilla_cocina(ped)
                        exito = enviar_raw_spooler(printer_target, bytes_cocina, f"Cocina_{cod}")
                        if exito:
                            print(f"    [+] Comanda de COCINA impresa en '{printer_target}'.")
                            if marcar_pedido_impreso(http_session, active_base, ped_id, tipo="COCINA"):
                                print(f"    [OK] Pedido {cod} confirmado en Neon DB como impreso en Cocina.\n")
                            else:
                                print(f"    [!] Aviso: Se imprimio Cocina {cod}, pero fallo confirmacion HTTP.\n")

                    elif tipo_trabajo in ("CUENTA", "TEST"):
                        bytes_caja = construir_tirilla_caja(ped)
                        job_label = f"Test_{cod}" if tipo_trabajo == "TEST" else (f"PreCuenta_{cod}" if ("MESA" in str(tipo).upper() or ped.get("mesa")) else f"Cuenta_{cod}")
                        exito = enviar_raw_spooler(printer_target, bytes_caja, job_label)
                        if exito:
                            print(f"    [+] Tirilla de {tipo_trabajo} impresa en '{printer_target}'.")
                            if marcar_pedido_impreso(http_session, active_base, ped_id, tipo=tipo_trabajo):
                                print(f"    [OK] Trabajo {cod} ({tipo_trabajo}) confirmado como impreso.\n")
                            else:
                                print(f"    [!] Aviso: Se imprimio {tipo_trabajo} {cod}, pero fallo confirmacion HTTP.\n")

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
