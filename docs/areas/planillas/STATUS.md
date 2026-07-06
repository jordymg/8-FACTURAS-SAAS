# STATUS — Área Planillas

## Estado actual
Planilla v1 en producción (Render), creada manualmente por cada usuario y
conectada vía Service Account. Probada end-to-end con datos reales. Issue #001
(facturas desalineadas de columna) diagnosticado y resuelto — ver
`docs/ISSUES.md`. Metodología de cálculo decidida (ADR-0002). Reglas de
integridad parcialmente decididas (punto 5 de PRODUCTO.md): encabezado
protegido y edición manual libre ya confirmados; qué pasa si se borra/renombra
la pestaña quedó abierto como ADR-0003 (en discusión — posible esquema de una
pestaña por período).

## Next
1. Implementar la protección de rango del encabezado en
   `connect_spreadsheet()` (ya decidido, falta el código).
2. Entrevistar al founder sobre el punto 6 de `PRODUCTO.md` (formato visual):
   formato de fecha (guardar AAAA-MM-DD y mostrar dd/mm/aaaa, o convertir de
   verdad), formato de moneda, y qué tan prolija debe quedar la planilla para
   el contador (fila congelada, ancho de columnas, colores alternados). Se
   preguntó pero no hubo respuesta todavía.
3. Discutir el ADR-0003 (pestañas por período) cuando se retome: cómo se pasa
   de un período a otro, y qué pasa con el filtro por mes y las fórmulas de
   total anual (ADR-0002) si los datos quedan repartidos en varias pestañas.
