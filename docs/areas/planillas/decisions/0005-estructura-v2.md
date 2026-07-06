# ADR-0005 (planillas): Estructura v2 de la planilla

**Date:** 2026-07-06
**Status:** ADOPTADA (lista de columnas) — implementación pendiente, ver sección final

## Contexto
La v1 (9 campos + imagen + cargada_el, ADR-0004 del repo general) era una
versión simple para validar el flujo. El founder pidió repensar toda la
estructura desde cero, alineada a las categorías impositivas reales que usa
un contador argentino para el libro de compras (IVA discriminado por
alícuota, percepciones, retenciones), y agregar campos de uso interno del
cliente (Categoría, CUENTA).

## Decisión — 22 columnas

| # | Columna | Clave interna | Quién la completa |
|---|---|---|---|
| 1 | Emisión | `fecha` | La IA extrae (fecha del comprobante) |
| 2 | Proveedor | `proveedor` | La IA extrae |
| 3 | CUIT | `cuit` | La IA extrae |
| 4 | Categoría | `categoria` | **ABIERTO** — ver más abajo |
| 5 | CUENTA | `cuenta` | **ABIERTO** — ver más abajo |
| 6 | Tipo Factura | `tipo` | La IA extrae — **regla especial**: si no detecta CAE en el comprobante, se completa con `"X"` (letra de comprobante en negro), sin importar qué letra esté impresa |
| 7 | Punto de Venta | `punto_venta` | La IA extrae |
| 8 | N° de Factura | `numero` | La IA extrae |
| 9 | NETO GRAVADO | `neto` | La IA extrae |
| 10 | IVA - 10,5% | `iva_105` | La IA extrae, discriminado por alícuota |
| 11 | IVA - 21% | `iva_21` | La IA extrae, discriminado por alícuota |
| 12 | IVA - 27% | `iva_27` | La IA extrae, discriminado por alícuota |
| 13 | Perc. IVA | `perc_iva` | La IA extrae |
| 14 | Perc. IIBB ARBA | `perc_iibb_arba` | La IA extrae |
| 15 | IIBB CABA | `iibb_caba` | La IA extrae |
| 16 | RET GANANCIAS | `ret_ganancias` | La IA extrae |
| 17 | RET IVA | `ret_iva` | La IA extrae |
| 18 | SIRTAC | `sirtac` | La IA extrae |
| 19 | Imp. Internos | `imp_internos` | La IA extrae |
| 20 | Total Compra | `total` | La IA extrae |
| 21 | Moneda | `moneda` | El usuario elige (selector ARS/USD, como en v1) |
| 22 | Fecha de Carga | `cargada_el` | La app, automático (timestamp del guardado, como en v1) |

## CAE — cómo se usa (sin ser columna)
El número de CAE **no se guarda** en ninguna columna. Se usa únicamente para
que la IA determine si el comprobante está autorizado (CAE presente → letra
real A/B/C/etc.) o no (CAE ausente → `"X"` en la columna Tipo Factura).

## Abierto — antes de implementar
**Categoría (4) y CUENTA (5)**: no está definido si la IA intenta
sugerirlas, si las completa el usuario a mano al revisar la tarjeta, o si
quedan vacías para que el contador las complete después. Sin esto definido,
no se puede implementar el formulario de revisión ni el prompt para estas
dos columnas.

## Consecuencias / implicancias para implementar (no hecho todavía)
- **Prompt de Gemini** (`app/services/gemini.py`): hay que reescribirlo
  entero — pasa de 9 campos simples a extraer ~19 campos, con reglas
  explícitas por cada impuesto/percepción/retención (evita la ambigüedad de
  confundir un impuesto con otro, ver discusión que motivó este ADR) y la
  regla de CAE → Tipo Factura = "X".
- **`app/services/fields.py`**: reemplazar la lista `FIELDS` completa.
- **`app/services/sheets.py`**: `ROW_KEYS` cambia de 11 a 22 columnas — el
  encabezado, los formatos (fecha/moneda) y el ancho de columnas (ver
  conversación sobre volver a ancho fijo, columna por columna) se actualizan
  ahí.
- **Frontend** (`templates/app.html`, `static/js/app.js`): el formulario de
  revisión pasa de 9 a ~20 campos editables por tarjeta — repensar el layout,
  no solo agregar inputs.
- **Planillas ya conectadas (v1)**: esto es un cambio de estructura, no
  aditivo — decidir migración cuando se implemente (¿se migran las filas
  viejas, quedan como están, se avisa al cliente?).
- Ancho de columna fijo por columna (en vez de auto-resize): a definir
  valores concretos al implementar.
