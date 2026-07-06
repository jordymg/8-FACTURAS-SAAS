# ADR-0006 (planillas): Categoría, CUENTA y Cód. Proveedor en la estructura v2

**Date:** 2026-07-06
**Status:** ADOPTADA — destraba la implementación de la v2 (ADR-0005)

## Contexto
El ADR-0005 dejó abierto cómo se completan Categoría y CUENTA, bloqueando
el prompt de Gemini y el formulario de revisión. Además el founder pidió
una columna nueva de código de proveedor.

## Decisión
1. **Categoría**: la completa la IA, clasificando **libremente** (sin lista
   fija). Es un feature para validar con feedback del cliente. El usuario
   puede corregirla en la tarjeta de revisión.
2. **CUENTA**: queda **en blanco**. No la completa ni la IA ni el usuario;
   es del contador. Fuera del prompt y del formulario por ahora.
3. **Cód. Proveedor**: columna **nueva**, ubicada al lado de Proveedor (la
   v2 pasa de 22 a **23 columnas**). Queda **en blanco** por ahora — es un
   código interno de cada cliente (lo pondría él o nosotros); si se completa
   y cómo, se define más adelante según avance el proyecto.

## Alternativas consideradas
- Categoría con lista fija de opciones — descartada por ahora: se prefiere
  clasificación libre para ver qué devuelve la IA y ajustar con feedback
  real.
- CUENTA sugerida por IA o completada por el usuario — descartada: es
  lenguaje del plan de cuentas del estudio contable, no del cliente ni de la
  app.
- No agregar Cód. Proveedor hasta definir su fuente — descartada: se agrega
  ya la columna (vacía) para no cambiar la estructura dos veces.

## Consecuencias
- ADR-0005 queda desbloqueado: actualizar la tabla a 23 columnas (Cód.
  Proveedor como #3, corriendo las demás) y marcar resuelto el punto
  "Abierto".
- Prompt de Gemini: agrega `categoria` (clasificación libre del gasto); no
  extrae `cuenta` ni `cod_proveedor`.
- `fields.py` / `sheets.py::ROW_KEYS`: 23 columnas; `cuenta` y
  `cod_proveedor` se escriben vacías.
- Formulario de revisión: `categoria` editable; `cuenta` y `cod_proveedor`
  no aparecen (o solo lectura vacía, a definir en implementación).
- Riesgo aceptado: la clasificación libre puede dar categorías
  inconsistentes entre facturas (ej. "Combustible" vs "Nafta") — se evalúa
  con feedback antes de pasar a lista fija.
