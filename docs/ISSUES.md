# ISSUES

Log de problemas que cumplieron el criterio para quedar registrados (no todo
bug entra acá — ver criterio abajo). Objetivo: no repetir el mismo error dos
veces, y que cualquier IA que entre a una sesión nueva vea de un vistazo qué
problemas ya se pisaron.

## Cuándo un problema pasa a ser issue
Se loguea acá si cumple **al menos una**:
1. Tocó datos reales de un usuario (no solo un entorno de prueba).
2. No lo agarramos nosotros primero — lo encontró el uso real de la app, no
   una revisión de código nuestra.
3. La causa es una rareza de un sistema externo que puede volver a morder en
   otro lado si no queda escrito.
4. Si es un bug común arreglado en el momento, sin sorpresas ni datos reales
   pisados, **no** se loguea — sería ruido.

Cada entrada: número secuencial, área, fecha, síntoma, causa raíz, fix, estado.

---

## #001 — Facturas se cargan desencolumnadas en Sheets
**Área:** [planillas](areas/planillas/)
**Fecha:** 2026-07-06
**Síntoma:** al conectar una planilla y cargar varias facturas seguidas, la
primera se guarda bien (columnas A→K), pero la segunda arranca en la columna
K (justo debajo de donde cayó el timestamp `cargada_el` de la primera) y la
tercera arranca en la columna U (debajo del `cargada_el` de la segunda) — cada
factura nueva se corre más a la derecha que la anterior, en vez de agregarse
en una fila nueva empezando en la columna A.
**Causa raíz:** `app/services/sheets.py` usa `sheet.append_row(...)` sin
especificar el rango de la tabla. La API de Google Sheets, cuando no le decís
explícitamente dónde arranca la tabla, adivina el punto de inserción — y en
vez de anclarse siempre a la columna A, a veces interpreta que la tabla nueva
empieza donde terminó la última columna con datos de la fila anterior.
Comportamiento documentado y 100% reproducible de la API, no algo al azar.
**Fix:** agregar `table_range="A1"` a los `append_row` de `connect_spreadsheet`
y `append_invoice` en `app/services/sheets.py`, para que la API nunca tenga
que adivinar dónde arranca la tabla.
**Estado:** abierto — diagnosticado, fix acordado pero no aplicado todavía
(a pedido del founder, pendiente de charlar más). Datos reales ya
desencolumnados en la planilla de prueba: no corregidos todavía, decisión
del founder si se arreglan a mano o se limpian por código.
