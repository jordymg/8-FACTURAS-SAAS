# STATUS — Área Planillas

## Estado actual
Planilla v1 en producción (deploy en Render), creada manualmente por cada
usuario y conectada vía Service Account. Probada end-to-end con datos reales.
Bug conocido detectado 2026-07-06: filas de facturas consecutivas pueden caer
desalineadas de columna (ver STATUS.md general del repo / issue en curso).

## Next
Entrevistar al founder para cerrar los puntos ABIERTOS de `PRODUCTO.md`:
- Punto 3: metodología de cálculo (fórmulas en el Sheet vs. Python).
- Punto 5: reglas de integridad (encabezados protegidos, ediciones/borrados).
- Punto 6: formato visual (moneda, fechas, legibilidad para el contador).
