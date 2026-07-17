# ADR-0005 (planillas): Estructura v2 de la planilla

**Date:** 2026-07-06
**Status:** ADOPTADA e IMPLEMENTADA (2026-07-06) — ver `docs/areas/planillas/STATUS.md` para detalle de la implementación y bugs encontrados en el camino

> ⚠️ **Reemplazada por [ADR-0011](0011-estructura-v3.md) (2026-07-17):**
> la v2 de 23 columnas pasa a v3 de 18 — se sacan 6 columnas de
> percepciones/retenciones/SIRTAC y se reemplazan por una sola columna
> "Otros impuestos" (suma de todo lo que no se desglosa aparte). Esta
> página queda como historia de la v2, no como estructura vigente.

## Contexto
La v1 (9 campos + imagen + cargada_el, ADR-0004 del repo general) era una
versión simple para validar el flujo. El founder pidió repensar toda la
estructura desde cero, alineada a las categorías impositivas reales que usa
un contador argentino para el libro de compras (IVA discriminado por
alícuota, percepciones, retenciones), y agregar campos de uso interno del
cliente (Categoría, CUENTA).

## Decisión — 23 columnas
(Actualizada por ADR-0006: se agregó Cód. Proveedor como columna #3 y se
resolvió cómo se completan Categoría y CUENTA.)

| # | Columna | Clave interna | Quién la completa |
|---|---|---|---|
| 1 | Emisión | `fecha` | La IA extrae (fecha del comprobante) |
| 2 | Proveedor | `proveedor` | La IA extrae |
| 3 | Cód. Proveedor | `cod_proveedor` | En blanco por ahora (ver ADR-0006) |
| 4 | CUIT | `cuit` | La IA extrae |
| 5 | Categoría | `categoria` | La IA clasifica libremente, el usuario puede corregir (ver ADR-0006) |
| 6 | CUENTA | `cuenta` | En blanco — es del contador (ver ADR-0006) |
| 7 | Tipo Factura | `tipo` | La IA extrae — **regla especial**: si no detecta CAE en el comprobante, se completa con `"X"` (letra de comprobante en negro), sin importar qué letra esté impresa |
| 8 | Punto de Venta | `punto_venta` | La IA extrae |
| 9 | N° de Factura | `numero` | La IA extrae |
| 10 | NETO GRAVADO | `neto` | La IA extrae |
| 11 | IVA - 10,5% | `iva_105` | La IA extrae, discriminado por alícuota |
| 12 | IVA - 21% | `iva_21` | La IA extrae, discriminado por alícuota |
| 13 | IVA - 27% | `iva_27` | La IA extrae, discriminado por alícuota |
| 14 | Perc. IVA | `perc_iva` | La IA extrae |
| 15 | Perc. IIBB ARBA | `perc_iibb_arba` | La IA extrae |
| 16 | IIBB CABA | `iibb_caba` | La IA extrae |
| 17 | RET GANANCIAS | `ret_ganancias` | La IA extrae |
| 18 | RET IVA | `ret_iva` | La IA extrae |
| 19 | SIRTAC | `sirtac` | La IA extrae |
| 20 | Imp. Internos | `imp_internos` | La IA extrae |
| 21 | Total Compra | `total` | La IA extrae |
| 22 | Moneda | `moneda` | El usuario elige (selector ARS/USD, como en v1) |
| 23 | Fecha de Carga | `cargada_el` | La app, automático (timestamp del guardado, como en v1) |

## CAE — cómo se usa (sin ser columna)
El número de CAE **no se guarda** en ninguna columna. Se usa únicamente para
que la IA determine si el comprobante está autorizado (CAE presente → letra
real A/B/C/etc.) o no (CAE ausente → `"X"` en la columna Tipo Factura).

> ⚠️ **Corregido por [ADR-0007](0007-regla-validez-comprobante.md):** el CAE
> no es la única evidencia de autorización — también cuentan CAEA, CAI y
> controlador fiscal homologado. "X" solo si no se detecta NINGUNA de las 4.
> Además, si la IA no está segura, el campo queda vacío (no elige un valor)
> y se resalta para revisión manual — ver ese ADR para el detalle completo.

## Resuelto (ADR-0006)
Categoría, CUENTA y Cód. Proveedor ya tienen decisión — ver
[`decisions/0006-categoria-cuenta-cod-proveedor.md`](0006-categoria-cuenta-cod-proveedor.md).
No quedan puntos abiertos en la estructura.

## Consecuencias / implicancias para implementar (no hecho todavía)
- **Prompt de Gemini** (`app/services/gemini.py`): hay que reescribirlo
  entero — pasa de 9 campos simples a extraer ~20 campos (incluye
  `categoria`, clasificación libre del gasto), con reglas explícitas por
  cada impuesto/percepción/retención (evita la ambigüedad de confundir un
  impuesto con otro, ver discusión que motivó este ADR) y la regla de CAE →
  Tipo Factura = "X". No extrae `cuenta` ni `cod_proveedor` (quedan vacías).
- **`app/services/fields.py`**: reemplazar la lista `FIELDS` completa.
- **`app/services/sheets.py`**: `ROW_KEYS` cambia de 11 a 23 columnas — el
  encabezado, los formatos (fecha/moneda) y el ancho de columnas (ver
  conversación sobre volver a ancho fijo, columna por columna) se actualizan
  ahí.
- **Frontend** (`templates/app.html`, `static/js/app.js`): el formulario de
  revisión pasa de 9 a ~20 campos editables por tarjeta (`cuenta` y
  `cod_proveedor` no aparecen, o solo lectura vacía — a definir en
  implementación) — repensar el layout, no solo agregar inputs.
- **Planillas ya conectadas (v1)**: esto es un cambio de estructura, no
  aditivo — decidir migración cuando se implemente (¿se migran las filas
  viejas, quedan como están, se avisa al cliente?).
- Ancho de columna fijo por columna (en vez de auto-resize): a definir
  valores concretos al implementar.
