# STATUS — Área Planillas

## Estado actual
Planilla v1 en producción (Render), creada manualmente por cada usuario y
conectada vía Service Account. Probada end-to-end con datos reales. Issue #001
(facturas desalineadas de columna) diagnosticado y resuelto — ver
`docs/ISSUES.md`. Metodología de cálculo ya decidida (ADR-0002, enfoque mixto
fórmulas/Python).

## Next
Entrevistar al founder para cerrar los puntos ABIERTOS restantes de
`PRODUCTO.md`:
- Punto 5 (integridad): encabezados protegidos, qué pasa si el usuario edita
  o borra filas/pestaña a mano.
- Punto 6 (formato visual): moneda, fechas, ancho de columnas, legibilidad
  para el contador.
