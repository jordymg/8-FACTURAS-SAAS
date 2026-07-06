# STATUS — Área Planillas

## Estado actual
Planilla v1 en producción (Render), creada manualmente por cada usuario y
conectada vía Service Account. Probada end-to-end con datos reales. Issue #001
(facturas desalineadas de columna) diagnosticado y resuelto — ver
`docs/ISSUES.md`. Los 3 puntos ABIERTOS de `PRODUCTO.md` ya tienen decisión y
**ya están implementados**: metodología de cálculo (ADR-0002), integridad
parcial — encabezado protegido (ADR punto 5) — y formato visual (ADR-0004:
fecha AAAA-MM-DD mostrada DD/MM/AAAA, moneda con formato `$`, fila congelada,
ancho de columna ajustado). Todo se aplica una sola vez, al crear el
encabezado en `connect_spreadsheet()`.

Efecto colateral encontrado y arreglado: al pasar la fecha a un valor de
fecha real (para que el formato visual funcione), `list_invoices()` filtraba
mal por mes — se corrigió leyendo el valor sin formatear y convirtiéndolo de
vuelta a AAAA-MM-DD en Python.

Nota pendiente (no bloqueante): `cuit` y `numero` los guarda Sheets como
número, no como texto — comportamiento previo a hoy, sin impacto visible
todavía, pero a tener en cuenta si más adelante se necesita el CUIT exacto
como texto (ceros a la izquierda, etc.).

## Next
Retomar el ADR-0003 (pestañas por período) cuando se discuta: cómo se pasa
de un período a otro, y qué pasa con el filtro por mes y las fórmulas de
total anual (ADR-0002) si los datos quedan repartidos en varias pestañas.
