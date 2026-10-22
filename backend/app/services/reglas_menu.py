"""
Modulo de Servicio: Reglas de Negocio para el Menú del Día San Parrilla.
Responsabilidad única: Definir y validar las reglas de preparación diaria de sopas, principios y acompañamientos.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app import models, crud

# --- REGLAS DE NEGOCIO SAN PARRILLA ---
MAX_SOPAS_POR_DIA = 1
MAX_PRINCIPIOS_POR_DIA = 3
MAX_ACOMPANAMIENTOS_POR_DIA = 3

NOMBRE_PRINCIPIO_OBLIGATORIO = "Frijoles Caseros"
NOMBRE_ACOMPANAMIENTO_OBLIGATORIO = "Tajadas Maduras"

STOCK_DEFECTO_PREPARADO = 50  # Porciones por defecto por ítem


def validar_reglas_menu(
    sopa_id: int,
    principios_ids: List[int],
    acompanamientos_ids: List[int],
    db: Session
) -> Dict[str, Any]:
    """
    Valida si una selección de ítems cumple con las reglas del restaurante:
    - 1 sola sopa.
    - Exactamente 3 principios (debe incluir Frijoles Caseros).
    - Exactamente 3 acompañamientos (debe incluir Tajadas Maduras).
    """
    errores = []

    # 1. Validar Sopa
    if not sopa_id:
        errores.append("Debe seleccionarse exactamente 1 Sopa del Día.")

    # 2. Validar Principios
    if len(principios_ids) != MAX_PRINCIPIOS_POR_DIA:
        errores.append(f"El menú debe contener exactamente {MAX_PRINCIPIOS_POR_DIA} principios.")
    
    principios_db = db.query(models.Principio).filter(models.Principio.id.in_(principios_ids)).all()
    nombres_principios = [p.nombre for p in principios_db]
    if NOMBRE_PRINCIPIO_OBLIGATORIO not in nombres_principios:
        errores.append(f"El principio '{NOMBRE_PRINCIPIO_OBLIGATORIO}' debe ser incluido obligatoriamente todos los días.")

    # 3. Validar Acompañamientos
    if len(acompanamientos_ids) != MAX_ACOMPANAMIENTOS_POR_DIA:
        errores.append(f"El menú debe contener exactamente {MAX_ACOMPANAMIENTOS_POR_DIA} acompañamientos.")
    
    acomp_db = db.query(models.Acompanamiento).filter(models.Acompanamiento.id.in_(acompanamientos_ids)).all()
    nombres_acomp = [a.nombre for a in acomp_db]
    if NOMBRE_ACOMPANAMIENTO_OBLIGATORIO not in nombres_acomp:
        errores.append(f"El acompañamiento '{NOMBRE_ACOMPANAMIENTO_OBLIGATORIO}' debe ser incluido obligatoriamente todos los días.")

    return {
        "valido": len(errores) == 0,
        "errores": errores
    }


def auto_generar_menu_dia_segun_reglas(
    db: Session,
    fecha_str: str,
    sopa_id: int,
    principios_ids: List[int],
    acompanamientos_ids: List[int],
    stock_preparado: int = STOCK_DEFECTO_PREPARADO
) -> models.MenuDia:
    """
    Valida y genera un Menú del Día aplicando las reglas de negocio de San Parrilla.
    """
    validacion = validar_reglas_menu(sopa_id, principios_ids, acompanamientos_ids, db)
    if not validacion["valido"]:
        raise ValueError(" | ".join(validacion["errores"]))

    # Verificar si ya existe menú para esa fecha
    menu_existente = crud.get_menu_dia_by_fecha(db, fecha_str)
    if menu_existente:
        # Re-poblar los ítems con las nuevas reglas
        db.query(models.MenuDiaItem).filter(models.MenuDiaItem.menu_dia_id == menu_existente.id).delete()
        menu = menu_existente
    else:
        menu = models.MenuDia(fecha=fecha_str)
        db.add(menu)
        db.commit()
        db.refresh(menu)

    # 1. Agregar Sopa (1 por día)
    item_sopa = models.MenuDiaItem(
        menu_dia_id=menu.id,
        tipo_item=models.TipoItemStock.SOPA,
        sopa_id=sopa_id,
        cantidad_preparada=stock_preparado,
        cantidad_vendida=0
    )
    db.add(item_sopa)

    # 2. Agregar Principios (3 por día)
    for p_id in principios_ids:
        item_p = models.MenuDiaItem(
            menu_dia_id=menu.id,
            tipo_item=models.TipoItemStock.PRINCIPIO,
            principio_id=p_id,
            cantidad_preparada=stock_preparado,
            cantidad_vendida=0
        )
        db.add(item_p)

    # 3. Agregar Acompañamientos (3 por día)
    for a_id in acompanamientos_ids:
        item_a = models.MenuDiaItem(
            menu_dia_id=menu.id,
            tipo_item=models.TipoItemStock.ACOMPANAMIENTO,
            acompanamiento_id=a_id,
            cantidad_preparada=stock_preparado,
            cantidad_vendida=0
        )
        db.add(item_a)

    db.commit()
    db.refresh(menu)
    return menu
