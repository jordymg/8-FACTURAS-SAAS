"""Tope de facturas mensual — diseño funcional en
docs/decisions/0008-tope-facturas-mensual.md. Versión soft del MVP (ver
ADR-0007): solo contador + aviso, sin corte de servicio todavía.

El ciclo mensual se ancla al día de alta del usuario (ej. alta el 10 -> el
ciclo va del 10 al 9 del mes siguiente), no al mes calendario — un cliente
que se suma el 28 no puede quedarse con 2-3 días de margen antes del reset."""

import calendar
import datetime

from app.models import User

LIMITE_MENSUAL = 200
UMBRAL_AVISO = 160  # 80% del límite, misma proporción que antes (200 de 250)


def _inicio_ciclo(fecha_alta: datetime.date, hoy: datetime.date) -> datetime.date:
    """Fecha de inicio del ciclo mensual vigente hoy, para un usuario dado
    de alta en `fecha_alta`. Si el mes no tiene el día exacto de alta (ej.
    alta el 31, mes de 30 días), se usa el último día de ese mes — mismo
    comportamiento estándar que un ciclo de facturación real."""
    dia = fecha_alta.day
    ultimo_dia_mes_actual = calendar.monthrange(hoy.year, hoy.month)[1]
    candidato = hoy.replace(day=min(dia, ultimo_dia_mes_actual))
    if candidato > hoy:
        anio, mes = hoy.year, hoy.month - 1
        if mes == 0:
            anio, mes = anio - 1, 12
        ultimo_dia_mes_anterior = calendar.monthrange(anio, mes)[1]
        candidato = datetime.date(anio, mes, min(dia, ultimo_dia_mes_anterior))
    return candidato


def facturas_del_mes(user: User) -> int:
    """Conteo de facturas cargadas en el ciclo mensual vigente. No escribe
    en la DB — si el ciclo guardado no es el vigente, el conteo real es 0
    (el reset real y persistido pasa recién en registrar_factura_cargada,
    la próxima vez que guarde una factura)."""
    if not user.created_at:
        # Usuario sin fecha de alta guardada (no debería pasar tras el
        # backfill de _ensure_schema) — mejor mostrar el conteo crudo que
        # romper la home.
        return user.invoices_this_month or 0
    inicio = _inicio_ciclo(user.created_at, datetime.date.today())
    if user.invoices_cycle_start != inicio:
        return 0
    return user.invoices_this_month or 0


def registrar_factura_cargada(user: User) -> None:
    """Suma 1 al contador del ciclo vigente — resetea a 0 primero si el
    usuario todavía tenía guardado un ciclo anterior. No hace commit, eso
    lo decide el caller (junto con el resto de cambios de esa request)."""
    hoy = datetime.date.today()
    if not user.created_at:
        user.created_at = hoy
    inicio = _inicio_ciclo(user.created_at, hoy)
    if user.invoices_cycle_start != inicio:
        user.invoices_cycle_start = inicio
        user.invoices_this_month = 0
    user.invoices_this_month += 1
