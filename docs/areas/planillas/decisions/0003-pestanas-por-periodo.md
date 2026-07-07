# ADR-0003 (planillas): ¿Una pestaña por período?

**Date:** 2026-07-06
**Status:** EN DISCUSIÓN — no decidido, no implementar todavía

## Origen
Surgió al entrevistar al founder sobre reglas de integridad (PRODUCTO.md
punto 5, qué pasa si se borra/renombra "Hoja 1"). Propuesta del founder: en
vez de escribir siempre en la primera pestaña de la planilla, escribir en
una pestaña específica por período, nombrada con el período actual (ej.
`JUL-26`).

## La idea
- Cada mes (o período que se defina) tiene su propia pestaña, ya
  preparada de antemano con el encabezado.
- El nombre de la pestaña sigue una convención fija (ej. `JUL-26`,
  `AGO-26`).

## Idea registrada del founder (2026-07-07) — sigue sin resolver, no implementar
Cuando se retome: la app **crea la pestaña nueva automáticamente** al cargar
la primera factura cuyo período no tiene pestaña todavía. Ejemplo: llega la
primera factura con fecha 01/08 → se crea la pestaña "AGO-26" vacía, con el
mismo encabezado que las demás, y esa factura va ahí. No hay que crear las
pestañas de antemano ni de forma manual.

Esto resuelve el primer sub-punto del dilema de abajo, pero **no** los
demás (filtro por mes, fórmulas de total anual, uso de `sheet1`) — siguen
abiertos.

## El dilema abierto (por eso es un ticket, no un ADR resuelto)
¿Cómo se pasa de un período a otro?
- ~~¿La app crea la pestaña del mes nuevo automáticamente la primera vez que
  hay que escribir ahí, o hay que crearlas todas de antemano?~~ Resuelto
  arriba: se crea automáticamente.
- ¿Qué pasa con `list_invoices` y el filtro por mes que ya existe hoy (que
  asume UNA sola pestaña con todas las filas, filtrando por la columna
  `fecha`) — pasaría a leer una pestaña específica en vez de filtrar?
- ¿Qué pasa con las fórmulas de "total anual acumulado" (ADR-0002) si los
  datos quedan repartidos en varias pestañas en vez de una sola tabla larga?
- ¿Se sigue usando `sheet1` (primera pestaña) para algo, o deja de tener
  sentido con este esquema?
- Relacionado con el punto 8 de `PRODUCTO.md` (backlog): "pestaña
  resumen/dashboard" — ¿una pestaña resumen por año, agregando las
  mensuales?

## Por qué no se resuelve ahora
Cambia la forma en que `app/services/sheets.py` lee y escribe (hoy asume una
tabla única en `sheet1`), y afecta el cálculo de totales (ADR-0002). Requiere
diseño propio antes de tocar código — se trata en el área de Planillas
cuando se retome.
