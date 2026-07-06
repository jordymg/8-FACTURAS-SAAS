# ADR-0004 (planillas): Formato visual

**Date:** 2026-07-06
**Status:** ADOPTADA

## Fecha — aclara/corrige ADR-0002
El ADR-0002 (metodología de cálculo) decía "normalización de fechas a
dd/mm/aaaa" del lado de Python, lo cual entraba en conflicto con
`app/services/fields.py`, que le pide a Gemini el formato `AAAA-MM-DD`. Se
resuelve así:
- **Valor real guardado en la celda:** `AAAA-MM-DD` (sin cambios respecto a
  `fields.py`) — Sheets lo reconoce como fecha real (no texto), sin
  ambigüedad de región (día/mes vs mes/día), y las fórmulas de fecha del
  ADR-0002 (`SUMIFS` por mes, total anual, etc.) funcionan sobre ese valor.
- **Formato de visualización de la celda:** `DD/MM/AAAA`, aplicado como
  formato de número/fecha de Google Sheets (`Formato → Número → Fecha`), no
  como conversión del dato. El contador ve `04/07/2026`, el valor interno
  sigue siendo `2026-07-04`.
- La frase "normalización a dd/mm/aaaa" del ADR-0002 se refiere a esto (a la
  visualización), no a una conversión real del string — queda aclarado acá.

## Moneda
Los montos (neto, iva, total) mantienen su **valor numérico real** (ej.
`13192.36`), con un **formato de celda de moneda** aplicado (`Formato →
Número → Moneda`) para que se vean como `$13.192,36`. No se convierte el
dato a texto — las fórmulas del ADR-0002 (`SUMIFS`, promedios) siguen
funcionando sobre el número real.

## Legibilidad para el contador
- **Fila de encabezado congelada** (`Ver → Congelar → 1 fila`): sí — se
  aplica al crear la planilla, junto con la protección de rango y el
  negrita ya decididos en el punto 5.
- **Ancho de columna ajustado al contenido**: sí — se ajusta automáticamente
  una vez, al crear la planilla (para que nombres largos de proveedor no
  queden cortados visualmente).
- **Colores alternados por fila**: no — descartado, no vale la pena la
  complejidad/mantenimiento para el beneficio cosmético.

## Implementación pendiente
Todo esto se aplica en `connect_spreadsheet()` (`app/services/sheets.py`),
en el mismo lugar donde ya se escribe el encabezado y se le pone negrita —
agregar: formato de fecha en la columna A, formato de moneda en las columnas
F/G/H (neto/iva/total), congelar fila 1, y ajuste de ancho de columnas.
