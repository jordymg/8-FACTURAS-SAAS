# Producto: PLANILLA FACTURAS COMPRAS

> Escrito para alguien que lo lee por primera vez.

## 1. Qué es
**PLANILLA FACTURAS COMPRAS** es el Google Sheet donde queda registrada cada
factura de compra que el usuario fotografía con la app. Es el **entregable
real** del servicio: la app (foto → IA → revisión) es el medio, la planilla es
lo que el cliente efectivamente usa día a día y le entrega a su contador a fin
de mes. Ver [`docs/PRD.md`](../../PRD.md).

## 2. Estructura
1 pestaña (`sheet1`, la primera hoja de la planilla), 9 columnas de datos +
2 columnas de metadata que escribe la app:

| Col | Campo | Tipo | Quién la escribe |
|---|---|---|---|
| A | fecha | fecha (AAAA-MM-DD) | La IA extrae, el usuario confirma/edita |
| B | proveedor | texto | La IA extrae, el usuario confirma/edita |
| C | cuit | texto (11 dígitos) | La IA extrae, el usuario confirma/edita |
| D | tipo | texto (Factura A/B/C, Presupuesto, etc.) | La IA extrae, el usuario confirma/edita |
| E | numero | texto | La IA extrae, el usuario confirma/edita |
| F | neto | número | La IA extrae, el usuario confirma/edita |
| G | iva | número | La IA extrae, el usuario confirma/edita |
| H | total | número | La IA extrae, el usuario confirma/edita |
| I | moneda | texto (ARS/USD) | El usuario elige (selector) |
| J | imagen | texto | La app (hoy siempre vacío — MVP sin persistencia de imagen) |
| K | cargada_el | fecha-hora | La app, automático (timestamp del guardado) |

Definido en código en `app/services/fields.py` (columnas A-I) y
`app/services/sheets.py::ROW_KEYS` (agrega imagen + cargada_el).

**Qué no se toca a mano:** el encabezado (fila 1) — lo escribe la app la
primera vez que se conecta una planilla vacía. Las columnas J y K son
metadata de la app, no datos que el usuario deba completar.

## 3. Metodología de cálculo — ADOPTADA (ver ADR-0002)
Enfoque mixto: fórmula en el Sheet si es simple y fija, Python si involucra
lógica, validación o transformación. Detalle completo en
[`decisions/0002-metodologia-calculo.md`](decisions/0002-metodologia-calculo.md).

Resumen:
- **Fórmulas en el Sheet**: total mensual, IVA acumulado, neto acumulado,
  cantidad de facturas del mes, total por proveedor, total anual, columna de
  control neto+iva=total, promedio de gasto mensual.
- **Python antes de escribir**: normalización de fecha (dd/mm/aaaa) y de
  proveedor, validación de CUIT (dígito verificador), detección de
  duplicados (cuit+numero), cálculo de neto/iva si falta, asignación de fila
  correcta (Issue #001), conversión USD (cotización pendiente de definir),
  ID interno.
- **Pendiente de clasificar**: pestaña "Resumen" anual (¿fórmulas vivas o
  regenerada por Python?), resaltado de filas corregidas a mano.

## 4. Ciclo de vida
1. **Creación**: hoy, manual — el usuario crea la planilla en Google Sheets a
   mano (o usa una que ya tenía) y la conecta desde `/app/config`. Automatizar
   la creación (que la app la cree por vos) queda a definir.
2. **Conexión**: vía Service Account — el usuario comparte la planilla con el
   mail de la SA como Editor, pega la URL/ID en `/app/config`, la app valida
   el acceso y guarda el `spreadsheet_id` en su cuenta.
3. **Uso mensual**: cada factura cargada agrega una fila.
4. **Cierre de mes**: sin proceso automático hoy (Fase 2, no arrancado).
5. **Entrega al contador**: sin export a .xlsx propio — se comparte
   directamente el Google Sheet (o se descarga como .xlsx desde el propio
   Sheets, función nativa de Google). Decisión del founder: no vale la pena
   construir un export propio cuando Sheets ya lo resuelve gratis.

## 5. Reglas de integridad — PARCIALMENTE DECIDIDA
- **Encabezado (fila 1):** protegido con protección de rango de Google
  Sheets — nadie debería poder editarlo/borrarlo sin permiso explícito.
  Implementación pendiente en `connect_spreadsheet()`.
- **Edición manual de filas de datos:** permitida libremente. El usuario es
  dueño de su planilla; no se bloquea ni se valida. Nota: si edita un campo
  a mano de forma que quede en un formato raro (ej. CUIT sin dígitos), la
  detección de duplicados por cuit+numero (ADR-0002) podría no funcionar
  bien para esa fila puntual — comportamiento aceptado, no se resuelve.
- **Pestaña borrada/renombrada:** ABIERTO — el founder propuso pasar a un
  esquema de una pestaña por período (ej. `JUL-26`) en vez de una sola tabla
  en `sheet1`, lo que cambia la pregunta de fondo. Ver
  [`decisions/0003-pestanas-por-periodo.md`](decisions/0003-pestanas-por-periodo.md)
  (en discusión, no implementar todavía).

## 6. Formato visual — ABIERTO
Formato de moneda, de fechas, ancho de columnas, legibilidad para el
contador (que no usa la app, solo recibe el Sheet). A decidir con el founder.

## 7. Versionado
La estructura actual es **v1** (9 columnas + imagen + cargada_el, definida
2026-07-04 al integrar el prototipo del founder — ver ADR-0004 del repo
general). Todo cambio de estructura (agregar/sacar/renombrar columnas, nueva
plantilla) se decide en esta área, con un ADR en `decisions/`.

## 8. Backlog de ideas
- Totales mensuales (fila o pestaña de resumen).
- Pestaña resumen/dashboard dentro de la misma planilla.
- Plantilla modelo para que el usuario cree su propia planilla desde cero
  con un click (hoy la crea a mano).
- Soporte multi-moneda más allá de ARS/USD si aparece la necesidad.
