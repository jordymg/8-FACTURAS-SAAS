# STATUS — Área Planillas

## Estado actual
Planilla v1 en producción (Render), creada manualmente por cada usuario y
conectada vía Service Account. Probada end-to-end con datos reales. Issue #001
(facturas desalineadas de columna) diagnosticado y resuelto — ver
`docs/ISSUES.md`. Los 3 puntos ABIERTOS de `PRODUCTO.md` ya tienen decisión y
**ya están implementados**: metodología de cálculo (ADR-0002), integridad
parcial — encabezado protegido (ADR punto 5) — y formato visual (ADR-0004:
fecha AAAA-MM-DD mostrada DD/MM/AAAA, moneda con formato `$`, fila congelada,
ancho de columna ajustado). Se aplica en `connect_spreadsheet()` **cada vez**
que se conecta una planilla, no solo la primera vez — incluye planillas que
ya tenían datos y un encabezado propio (con otros nombres de columna): el
encabezado se reescribe con los textos canónicos (los datos no se tocan), y
el formato de fecha/moneda aplica retroactivamente a las filas viejas
también, siempre que se hayan guardado con la app (quedan como fecha/número
reales, no texto). Verificado en producción sobre una planilla real que ya
tenía facturas cargadas.

Efecto colateral encontrado y arreglado: al pasar la fecha a un valor de
fecha real (para que el formato visual funcione), `list_invoices()` filtraba
mal por mes — se corrigió leyendo el valor sin formatear y convirtiéndolo de
vuelta a AAAA-MM-DD en Python.

Nota pendiente (no bloqueante): `cuit` y `numero` los guarda Sheets como
número, no como texto — comportamiento previo a hoy, sin impacto visible
todavía, pero a tener en cuenta si más adelante se necesita el CUIT exacto
como texto (ceros a la izquierda, etc.).

## Next
1. **Implementar la estructura v2** (ADR-0005 + ADR-0006, 23 columnas — IVA
   por alícuota, percepciones, retenciones, Cód. Proveedor, Categoría
   clasificada libremente por la IA, CUENTA en blanco, y la regla CAE
   ausente → Tipo Factura = "X"). Sin puntos abiertos, lista para programar:
   reescribir el prompt de Gemini, `fields.py`, `sheets.py`
   (encabezado/formato/ancho de columna fijo por columna) y el formulario de
   revisión del frontend.
2. Retomar el ADR-0003 (pestañas por período) cuando se discuta: cómo se
   pasa de un período a otro, y qué pasa con el filtro por mes y las
   fórmulas de total anual (ADR-0002) si los datos quedan repartidos en
   varias pestañas.
