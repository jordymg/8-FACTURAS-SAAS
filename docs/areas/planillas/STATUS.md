# STATUS — Área Planillas

## Estado actual
Planilla v1 en producción (Render), creada manualmente por cada usuario y
conectada vía Service Account. Probada end-to-end con datos reales. Issue #001
(facturas desalineadas de columna) diagnosticado y resuelto — ver
`docs/ISSUES.md`. Los 3 puntos ABIERTOS de `PRODUCTO.md` ya tienen decisión:
metodología de cálculo (ADR-0002), integridad (parcial, ver abajo) y formato
visual (ADR-0004). Falta implementar en código lo ya decidido.

## Next
1. Implementar en `connect_spreadsheet()` (`app/services/sheets.py`) todo lo
   ya decidido y sin código todavía:
   - Protección de rango del encabezado (punto 5).
   - Formato de celda de fecha (columna A) y de moneda (columnas F/G/H).
   - Fila 1 congelada.
   - Ancho de columna ajustado al contenido.
2. Retomar el ADR-0003 (pestañas por período) cuando se discuta: cómo se
   pasa de un período a otro, y qué pasa con el filtro por mes y las
   fórmulas de total anual (ADR-0002) si los datos quedan repartidos en
   varias pestañas.
