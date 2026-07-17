# Producto: PLANILLA FACTURAS COMPRAS

> Escrito para alguien que lo lee por primera vez.

## 1. Qué es
**PLANILLA FACTURAS COMPRAS** es el Google Sheet donde queda registrada cada
factura de compra que el usuario fotografía con la app. Es el **entregable
real** del servicio: la app (foto → IA → revisión) es el medio, la planilla es
lo que el cliente efectivamente usa día a día y le entrega a su contador a fin
de mes. Ver [`docs/PRD.md`](../../PRD.md).

## 2. Estructura
> **v3 vigente** (18 columnas) — ver
> [`decisions/0011-estructura-v3.md`](decisions/0011-estructura-v3.md).
> Reemplaza la v2 (23 columnas,
> [`decisions/0005-estructura-v2.md`](decisions/0005-estructura-v2.md) +
> [`decisions/0006-categoria-cuenta-cod-proveedor.md`](decisions/0006-categoria-cuenta-cod-proveedor.md)),
> que a su vez había reemplazado la v1 original de 9 columnas.

1 pestaña por año calendario (ej. `"2026"`, ver
[`decisions/0003-pestanas-por-periodo.md`](decisions/0003-pestanas-por-periodo.md)),
18 columnas de datos:

| Col | Campo | Tipo | Quién la escribe |
|---|---|---|---|
| A | fecha | fecha (AAAA-MM-DD) | La IA extrae, el usuario confirma/edita |
| B | proveedor | texto | La IA extrae, el usuario confirma/edita |
| C | cod_proveedor | texto | En blanco por ahora (ver ADR-0006) |
| D | cuit | texto (11 dígitos) | La IA extrae, el usuario confirma/edita |
| E | categoria | texto | La IA clasifica libremente, el usuario corrige (ver ADR-0006) |
| F | cuenta | texto | En blanco — es del contador (ver ADR-0006) |
| G | tipo | texto (A/B/C/X, etc.) | La IA extrae — regla de las 4 vías de autorización (ADR-0007) |
| H | punto_venta | texto (ceros a la izq.) | La IA extrae |
| I | numero | texto (ceros a la izq.) | La IA extrae |
| J | neto | número | La IA extrae |
| K | iva_105 | número | La IA extrae, IVA discriminado al 10,5% |
| L | iva_21 | número | La IA extrae, IVA discriminado al 21% |
| M | iva_27 | número | La IA extrae, IVA discriminado al 27% |
| N | **otros_impuestos** | número (texto rojo) | La IA suma percepciones/retenciones/otros no discriminados aparte (ADR-0011) |
| O | imp_internos | número | La IA extrae |
| P | total | número | La IA extrae |
| Q | moneda | texto (ARS/USD) | El usuario elige (selector) |
| R | cargada_el | fecha-hora | La app, automático (timestamp del guardado) |

Definido en código en `app/services/fields.py` (columnas A-Q salvo
cod_proveedor/cuenta) y `app/services/sheets.py::ROW_KEYS` (orden
completo, incluye cod_proveedor, cuenta y cargada_el).

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

## 6. Formato visual — ADOPTADA (ver ADR-0004 de esta área)
Detalle completo en
[`decisions/0004-formato-visual.md`](decisions/0004-formato-visual.md).

Resumen:
- **Fecha:** se guarda como `AAAA-MM-DD` (valor real, sin cambios), pero se
  formatea la celda para mostrarse `DD/MM/AAAA` — aclara/corrige la mención
  a "dd/mm/aaaa" del ADR-0002.
- **Moneda:** valor numérico real (`13192.36`), con formato de celda de
  moneda para mostrarse `$13.192,36`.
- **Legibilidad:** fila de encabezado congelada ✅, ancho de columna
  ajustado al contenido ✅, colores alternados por fila ❌ (descartado).
- Implementación pendiente en `connect_spreadsheet()`.

## 7. Versionado
**v1** (9 columnas + imagen + cargada_el, definida 2026-07-04 al integrar
el prototipo del founder — ver
[ADR-0004 del repo general](../../decisions/0004-service-account-sheets.md),
no confundir con el ADR-0004 de esta área) → **v2** (23 columnas, alineada
a categorías impositivas reales — IVA por alícuota, percepciones,
retenciones —
[`decisions/0005-estructura-v2.md`](decisions/0005-estructura-v2.md) +
[`decisions/0006-categoria-cuenta-cod-proveedor.md`](decisions/0006-categoria-cuenta-cod-proveedor.md))
→ **v3 vigente** (18 columnas, 2026-07-17 — se sacan 6 columnas de
percepciones/retenciones/SIRTAC y se reemplazan por una sola "Otros
impuestos" que suma todo lo no discriminado aparte, motivado por
simplificar el producto y acortar el tiempo de extracción con Gemini —
[`decisions/0011-estructura-v3.md`](decisions/0011-estructura-v3.md)).
Todo cambio de estructura (agregar/sacar/renombrar columnas, nueva
plantilla) se decide en esta área, con un ADR en `decisions/`.

## 8. Backlog de ideas
- Totales mensuales (fila o pestaña de resumen).
- Pestaña resumen/dashboard dentro de la misma planilla.
- Plantilla modelo para que el usuario cree su propia planilla desde cero
  con un click (hoy la crea a mano).
- Soporte multi-moneda más allá de ARS/USD si aparece la necesidad.
