# ADR-0002 (planillas): Metodología de cálculo

**Date:** 2026-07-06
**Status:** ADOPTADA

## Criterio
Enfoque **mixto**: cada cálculo se resuelve de la manera más sencilla y
adecuada. Fórmula en el Sheet si es simple y fija (no depende de lógica de
negocio ni de validación). Python si involucra lógica, validación o
transformación de datos antes de que la fila exista.

## Fórmulas en el Sheet
- Total mensual de compras (`SUMIFS` por mes)
- IVA acumulado del mes
- Neto acumulado del mes
- Cantidad de facturas del mes (`COUNTIFS`)
- Total por proveedor (`SUMIFS`)
- Total anual acumulado
- Columna de control: neto + iva = total
- Promedio de gasto mensual

## Python, antes de escribir la fila
- Normalización de fechas a dd/mm/aaaa
- Validación de CUIT (11 dígitos + dígito verificador)
- Normalización del nombre del proveedor
- Detección de duplicados (cuit + numero)
- Cálculo de neto/iva si Gemini solo extrajo el total
- Asignación de fila correcta (Issue #001, ver `docs/ISSUES.md`)
- Conversión de moneda USD (cotización: pendiente de definir)
- ID interno de cada registro

## Pendientes de clasificar
- Pestaña "Resumen" anual: ¿fórmulas vivas o Python la regenera?
- Resaltado de filas corregidas a mano: ¿formato condicional o no se hace?

## Por qué este criterio
Evita dos extremos: hacer todo en Python (perdiendo la ventaja de que el
contador pueda auditar/ajustar fórmulas directamente en su propio Sheet) o
hacer todo con fórmulas (imposible para validaciones como el dígito
verificador de CUIT o la detección de duplicados, que necesitan lógica).
