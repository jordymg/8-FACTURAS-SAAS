# ADR-0001 (app): Rediseño del formulario de revisión

**Date:** 2026-07-07
**Status:** ADOPTADA — no implementada todavía

## Contexto
El formulario de revisión pasó a ~20 campos por tarjeta con la estructura
v2 de la planilla (ver `docs/areas/planillas/decisions/0005-estructura-v2.md`).
Hoy es una lista larga, un campo por fila, sin agrupar — pendiente de
evaluar en el celular (ver `docs/STATUS.md` general). El founder definió
tres cambios concretos antes de esa evaluación.

## Decisión

### a. Ocultar por defecto los campos poco frecuentes
Campos que casi nunca tienen valor (ej. Perc. IVA, SIRTAC) no se muestran
por defecto si la factura no los tiene. **Garantía**: si la extracción
detectó un valor en uno de esos campos, ese campo **sí se muestra** — nunca
se puede perder un dato que la IA extrajo. La regla aplica campo por campo,
no por bloque.

### b. Layout responsivo en desktop
Hoy cada campo ocupa el ancho completo de la tarjeta, obligando a
scrollear mucho hasta llegar a "Guardar". En pantallas anchas, pasar a una
grilla de ~2 columnas (o similar) — un campo individual no necesita más de
~1/3 del ancho disponible.

### c. Procesamiento automático, sin botón manual
Al cargar la foto, la extracción arranca sola — se saca el botón "Procesar
con IA" como paso manual intermedio.

**Ojo con la carga múltiple**: el botón existía en parte para juntar varios
archivos antes de mandarlos a procesar en batch. Al sacarlo, hay que
resolver que subir varias fotos juntas siga funcionando (ej. procesando
cada una automáticamente a medida que se agrega, o disparando el
procesamiento del lote completo apenas se sueltan/seleccionan todas las
fotos — a definir en la implementación, no en este ADR).

## Consecuencias
- Afecta `templates/app.html`, `static/js/app.js`, `static/css/app.css`.
- (a) requiere que el frontend sepa, por campo, si vino con valor o vacío
  desde la extracción, para decidir mostrar/ocultar — ya se recibe así
  (`r.fields`), no requiere cambios en el backend.
- (c) requiere resolver el flujo de carga múltiple sin el botón manual
  antes de sacarlo — no es opcional, el ADR original de captura multi-archivo
  depende de ese paso hoy.
- No implementado todavía — junto con la prueba en celular pendiente
  (`docs/STATUS.md` general, Next).
