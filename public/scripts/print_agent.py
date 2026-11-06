#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
   RESTAURANTE SAN PARRILLA - AGENTE DE IMPRESIÓN AUTOMÁTICA EN SEGUNDO PLANO
==============================================================================
Este script se ejecuta localmente en el PC de caja de Windows conectado a la
impresora térmica SAT Q22 (80mm).

Funcionamiento:
1. Consulta cada 2 segundos los pedidos pendientes en /api/impresion/pendientes.
2. Si detecta nuevos pedidos (de meseros, cajero, admin o web):
   a) Formatea la comanda térmica en comandos ESC/POS estándar (80mm).
   b) Envía el trabajo RAW al spooler de la impresora de Windows.
   c) Envía el comando de corte automático de papel.
   d) Notifica a /api/impresion/marcar-impreso/{id} para evitar reimpresiones.
==============================================================================
"""

import os
import sys
import time
import unicodedata
from datetime import datetime

try:
    import requests
except ImportError:
    print("[!] Error: 'requests' no está instalado. Ejecuta: pip install requests")
    sys.exit(1)

# Intentar importar win32print (específico de Windows)
try:
    import win32print
    HAS_WIN32PRINT = True
except ImportError:
    HAS_WIN32PRINT = False

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
# URL del backend o dominio web de San Parrilla
API_BASE_URL = os.environ.get("SP_API_URL", "https://www.sanparrilla.com").rstrip("/")

# Nombre de la impresora térmica en Windows.
# Si se deja en "SAT Q22", buscará una impresora con ese nombre o similar.
# Si se deja vacío ("") o no se encuentra, usará la impresora PREDETERMINADA de Windows.
PRINTER_NAME = os.environ.get("SP_PRINTER_NAME", "SAT Q22").strip()

# Intervalo de sondeo en segundos (2 segundos según especificación)
POLL_INTERVAL = float(os.environ.get("SP_POLL_INTERVAL", "2.0"))

# Ancho de caracteres en papel térmico de 80mm (fuente estándar A = 42-48 cols)
LINE_WIDTH = 42

# Comandos ESC/POS estándar
ESC = b"\x1b"
GS = b"\x1d"

CMD_INIT = ESC + b"@"                  # Inicializar impresora
CMD_ALIGN_LEFT = ESC + b"a\x00"        # Alinear a la izquierda
CMD_ALIGN_CENTER = ESC + b"a\x01"      # Centrar
CMD_ALIGN_RIGHT = ESC + b"a\x02"       # Alinear a la derecha
CMD_BOLD_ON = ESC + b"E\x01"           # Negrita activada
CMD_BOLD_OFF = ESC + b"E\x00"          # Negrita desactivada
CMD_TEXT_NORMAL = GS + b"!\x00"        # Tamaño de texto normal
CMD_TEXT_DOUBLE = GS + b"!\x11"        # Doble ancho y doble alto (título)
CMD_TEXT_DOUBLE_H = GS + b"!\x01"      # Doble alto
CMD_FEED_5 = ESC + b"d\x05"            # Avanzar 5 líneas de papel
CMD_CUT_PAPER = GS + b"V\x41\x00"      # Corte de papel parcial / total
CMD_CUT_FALLBACK = ESC + b"i"          # Comando alternativo de corte


def normalizar_texto(texto: str) -> str:
    """
    Limpia tildes o caracteres especiales para garantizar compatibilidad
    con cualquier juego de caracteres de la memoria interna de la impresora.
    """
    if not texto:
        return ""
    # Mantiene la 'ñ' y reemplaza acentos comunes si es necesario
    t = texto.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    t = t.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
    t = t.replace("ñ", "n").replace("Ñ", "N")
    return t


def detectar_impresora() -> str:
    """
    Detecta la impresora SAT Q22 o la predeterminada en Windows.
    """
    if not HAS_WIN32PRINT:
        print("[AVISO] Entorno sin win32print (no-Windows o sin pywin32). Modo depuración consola.")
        return "DEBUG_PRINTER"

    try:
        printers = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
        print(f"[i] Impresoras instaladas en Windows ({len(printers)}):")
        for p in printers:
            print(f"    - {p}")

        default_printer = win32print.GetDefaultPrinter()
        print(f"[i] Impresora predeterminada actual: '{default_printer}'")

        if PRINTER_NAME:
            # Búsqueda exacta o coincidencia parcial sensible / insensible
            for p in printers:
                if PRINTER_NAME.lower() in p.lower():
                    print(f"[+] Coincidencia encontrada para '{PRINTER_NAME}': Usando '{p}'")
                    return p
            print(f"[!] No se encontró exactamente '{PRINTER_NAME}'. Usando predeterminada: '{default_printer}'")

        return default_printer
    except Exception as e:
        print(f"[!] Error al listar impresoras: {e}")
        try:
            return win32print.GetDefaultPrinter()
        except Exception:
            return "DEFAULT"


def enviar_raw_a_impresora(printer_name: str, raw_bytes: bytes, doc_name: str = "Comanda San Parrilla"):
    """
    Envía bytes RAW directamente al spooler de la impresora de Windows.
    """
    if not HAS_WIN32PRINT or printer_name == "DEBUG_PRINTER":
        # Simulación en consola para diagnóstico
        print(f"\n--- [IMPRESIÓN SIMULADA: {doc_name}] ---")
        try:
            print(raw_bytes.decode("cp850", errors="ignore"))
        except Exception:
            print(raw_bytes)
        print("--- [FIN IMPRESIÓN SIMULADA] ---\n")
        return True

    hprinter = win32print.OpenPrinter(printer_name)
    try:
        hjob = win32print.StartDocPrinter(hprinter, 1, (doc_name, None, "RAW"))
        try:
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(hprinter, raw_bytes)
            win32print.EndPagePrinter(hprinter)
        finally:
            win32print.EndDocPrinter(hprinter)
        return True
    finally:
        win32print.ClosePrinter(hprinter)


def construir_comanda_escpos(pedido: dict) -> bytes:
    """
    Construye la comanda de cocina con comandos ESC/POS para SAT Q22 (80mm).
    """
    codigo = pedido.get("codigo_pedido", f"ID-{pedido.get('id')}")
    ped_id = pedido.get("id", 0)
    tipo_label = pedido.get("tipo_label", pedido.get("tipo", "GENERAL")).upper()
    mesa = pedido.get("mesa")
    cliente = pedido.get("cliente_nombre") or "Cliente"
    telefono = pedido.get("cliente_telefono")
    creado_por = pedido.get("creado_por") or "Personal"
    notas = pedido.get("notas") or ""
    items = pedido.get("items") or []

    # Fecha y hora local
    fecha_raw = pedido.get("fecha_hora")
    try:
        if fecha_raw:
            dt = datetime.fromisoformat(fecha_raw.replace("Z", "+00:00"))
            fecha_str = dt.strftime("%d/%m/%Y %I:%M %p")
        else:
            fecha_str = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    except Exception:
        fecha_str = datetime.now().strftime("%d/%m/%Y %I:%M %p")

    b = bytearray()

    # 1. Inicialización
    b.extend(CMD_INIT)

    # 2. Encabezado Centrado
    b.extend(CMD_ALIGN_CENTER)
    b.extend(CMD_BOLD_ON)
    b.extend(CMD_TEXT_DOUBLE)
    b.extend(b"SAN PARRILLA\n")
    b.extend(CMD_TEXT_NORMAL)
    b.extend(b"*** COMANDA DE COCINA ***\n")
    b.extend(CMD_BOLD_OFF)
    b.extend(b"=" * LINE_WIDTH + b"\n")

    # 3. Tipo y Mesa en GRANDE y destacado
    b.extend(CMD_ALIGN_CENTER)
    b.extend(CMD_BOLD_ON)
    b.extend(CMD_TEXT_DOUBLE)
    if mesa:
        b.extend(f"MESA: {mesa}\n".encode("cp850", errors="ignore"))
    else:
        b.extend(f"{tipo_label}\n".encode("cp850", errors="ignore"))
    b.extend(CMD_TEXT_NORMAL)
    b.extend(CMD_BOLD_OFF)
    b.extend(b"=" * LINE_WIDTH + b"\n")

    # 4. Datos del Pedido
    b.extend(CMD_ALIGN_LEFT)
    b.extend(f"Pedido: #{codigo} (ID: #{ped_id})\n".encode("cp850", errors="ignore"))
    b.extend(f"Fecha : {fecha_str}\n".encode("cp850", errors="ignore"))
    b.extend(f"Atiende: {creado_por}\n".encode("cp850", errors="ignore"))

    if cliente and cliente.lower() != "cliente":
        cli_info = f"Cliente: {cliente}"
        if telefono:
            cli_info += f" (Tel: {telefono})"
        b.extend(f"{cli_info}\n".encode("cp850", errors="ignore"))

    b.extend(b"-" * LINE_WIDTH + b"\n")

    # 5. Lista de Platos y Especificaciones
    b.extend(CMD_BOLD_ON)
    b.extend(b"CANT  DESCRIPCION / ESPECIFICACION\n")
    b.extend(CMD_BOLD_OFF)
    b.extend(b"-" * LINE_WIDTH + b"\n")

    for it in items:
        cant = it.get("cantidad", 1)
        plato_nom = it.get("plato_nombre", "Plato").upper()
        sopa = it.get("sopa")
        principio = it.get("principio")
        acomp = it.get("acompanamiento")
        notas_item = it.get("notas_item")

        # Nombre del plato en Negrita
        b.extend(CMD_BOLD_ON)
        b.extend(f"{cant}x  {plato_nom}\n".encode("cp850", errors="ignore"))
        b.extend(CMD_BOLD_OFF)

        # Detalles secundarios
        if sopa:
            b.extend(f"     > SOPA: {sopa}\n".encode("cp850", errors="ignore"))
        if principio:
            b.extend(f"     > PRINCIPIO: {principio}\n".encode("cp850", errors="ignore"))
        if acomp:
            b.extend(f"     > ACOMP: {acomp}\n".encode("cp850", errors="ignore"))
        if notas_item:
            b.extend(CMD_BOLD_ON)
            if any(k in notas_item.upper() for k in ["TORRE A", "TORRE B", "URGENCIAS"]):
                b.extend(CMD_TEXT_DOUBLE_H)
                b.extend(f"     >>> {notas_item} <<<\n".encode("cp850", errors="ignore"))
                b.extend(CMD_TEXT_NORMAL)
            else:
                b.extend(f"     * NOTA: {notas_item}\n".encode("cp850", errors="ignore"))
            b.extend(CMD_BOLD_OFF)

        b.extend(b"\n")

    b.extend(b"-" * LINE_WIDTH + b"\n")

    # 6. Observaciones Generales del Pedido
    if notas and notas.strip():
        b.extend(CMD_BOLD_ON)
        b.extend(b"OBSERVACIONES GENERALES:\n")
        b.extend(CMD_BOLD_OFF)
        b.extend(f"  {notas.strip()}\n".encode("cp850", errors="ignore"))
        b.extend(b"-" * LINE_WIDTH + b"\n")

    # 7. Total comanda y pie
    total = pedido.get("total", 0)
    b.extend(CMD_ALIGN_RIGHT)
    b.extend(CMD_BOLD_ON)
    b.extend(f"TOTAL: ${total:,.0f}\n".encode("cp850", errors="ignore"))
    b.extend(CMD_BOLD_OFF)

    b.extend(CMD_ALIGN_CENTER)
    b.extend(b"\n*** LISTO PARA PREPARACION ***\n")

    # 8. Avance de papel y corte
    b.extend(CMD_FEED_5)
    b.extend(CMD_CUT_PAPER)
    b.extend(CMD_CUT_FALLBACK)

    return bytes(b)


def ciclo_impresion(printer_target: str):
    """
    Bucle principal de consulta y despacho de impresión.
    """
    print(f"\n=======================================================")
    print(f"  SAN PARRILLA POS - SERVICIO DE IMPRESIÓN ACTIVO")
    print(f"  Backend: {API_BASE_URL}")
    print(f"  Impresora Windows: '{printer_target}'")
    print(f"  Intervalo de chequeo: cada {POLL_INTERVAL} segundos")
    print(f"=======================================================\n")
    print("[*] Esperando pedidos entrantes... (Presiona Ctrl + C para detener)\n")

    consecutive_errors = 0

    while True:
        try:
            url_pendientes = f"{API_BASE_URL}/api/impresion/pendientes"
            resp = requests.get(url_pendientes, timeout=8)

            if resp.status_code == 200:
                consecutive_errors = 0
                pedidos = resp.json()

                if pedidos and len(pedidos) > 0:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Se encontraron {len(pedidos)} comanda(s) pendiente(s) por imprimir.")

                    for ped in pedidos:
                        ped_id = ped.get("id")
                        codigo = ped.get("codigo_pedido", ped_id)
                        mesa = ped.get("mesa", "")
                        tipo = ped.get("tipo_label", ped.get("tipo", ""))

                        print(f"  --> Imprimiendo Comanda #{codigo} ({tipo}{' - Mesa ' + mesa if mesa else ''})...")

                        # Generar bytes ESC/POS
                        raw_data = construir_comanda_escpos(ped)

                        # Enviar a la impresora
                        ok = enviar_raw_a_impresora(printer_target, raw_data, f"Comanda_{codigo}")

                        if ok:
                            # Notificar al servidor que ya fue impreso
                            url_marcar = f"{API_BASE_URL}/api/impresion/marcar-impreso/{ped_id}"
                            try:
                                r_marcar = requests.post(url_marcar, timeout=8)
                                if r_marcar.status_code == 200:
                                    print(f"      [OK] Comanda #{codigo} impresa y confirmada en el servidor.")
                                else:
                                    print(f"      [!] Impreso localmente, pero el servidor devolvió {r_marcar.status_code} al marcar.")
                            except Exception as em:
                                print(f"      [!] Error notificando confirmación a servidor: {em}")
                        else:
                            print(f"      [X] Falló el envío al spooler de la impresora para el pedido #{codigo}.")

            elif resp.status_code == 404:
                # Si el endpoint en el backend está iniciando o no responde
                consecutive_errors += 1
                if consecutive_errors == 1:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Aviso: Endpoint /api/impresion/pendientes no respondió (404). Reintentando...")
            else:
                consecutive_errors += 1
                if consecutive_errors % 10 == 1:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Respuesta inesperada del servidor: HTTP {resp.status_code}")

        except requests.exceptions.RequestException as e:
            consecutive_errors += 1
            if consecutive_errors % 15 == 1:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Conexión con servidor en espera ({e.__class__.__name__}). Reintentando...")
        except KeyboardInterrupt:
            print("\n[!] Servicio de impresión detenido por el usuario.")
            break
        except Exception as e:
            print(f"[!] Error inesperado en el ciclo: {e}")

        time.sleep(POLL_INTERVAL)


def main():
    print("=" * 60)
    print("  Iniciando Agente de Impresión Térmica San Parrilla (SAT Q22)")
    print("=" * 60)

    # Detectar impresora
    printer_target = detectar_impresora()
    ciclo_impresion(printer_target)


if __name__ == "__main__":
    main()
