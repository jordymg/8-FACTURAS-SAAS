# ADR-0001 (app): Rediseño del formulario de revisión

**Date:** 2026-07-07
**Status:** ADOPTADA e IMPLEMENTADA — confirmada funcionando por el founder
en navegador el 2026-07-11 (ver nota de 2026-07-08 en Consecuencias para el
diagnóstico previo del problema de caché).

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

**Refinamiento acordado en la conversación de diseño (2026-07-07)**: los 4
campos `required` (Emisión, Proveedor, Total, Moneda) siempre se muestran, y
bloquean el guardado si están vacíos (sin cambios). Se suman `Neto Gravado`
e `IVA 21%` como **siempre visibles pero no bloqueantes**: en Factura A casi
siempre tienen valor, pero en Factura B/C es legítimo que vengan vacíos (el
IVA va incluido en el total, no discriminado) — se muestran igual para que
el usuario pueda juzgar si corresponde completarlos, sin impedir guardar una
Factura B válida. El resto (16 campos) se oculta si viene vacío. Debe existir
un botón "Mostrar campos ocultos" para completar a mano algo que la IA no
detectó.

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
- (c) resuelto sin cola de archivos: cada selección/drop se manda a
  `/api/extract` directamente como su propia tanda (se pierde la posibilidad
  de revisar/sacar un archivo antes de mandarlo, pero se sigue pudiendo
  descartar cada tarjeta ya procesada, como antes).

### Nota 2026-07-08 — implementado pero no confirmado funcionando
Los 3 cambios se implementaron en código el 2026-07-07 (`static/js/app.js`,
`static/css/app.css`, `templates/app.html` — sin commitear todavía) y se
verificaron por lectura, sintaxis (CSS balanceado, JS válido con `node`), y
una simulación de la lógica de ocultar/mostrar contra datos de una Factura B
realista (dio el resultado esperado). **No había herramienta de navegador
disponible para confirmar visualmente esta sesión.**

El founder probó en vivo (`localhost:5000`, tras resolver un
`redirect_uri_mismatch` de OAuth causado por entrar con `127.0.0.1` en vez
de `localhost` — mismatch de Google Cloud Console, no relacionado a este
ADR) y reportó: **"no anda bien, parece que no cambió nada"**. Causa sin
diagnosticar todavía. Hipótesis principal, sin confirmar: los archivos
estáticos (`app.js`/`app.css`) no tienen cache-busting
(`static/js/app.js` se sirve siempre con la misma URL) — el navegador podría
haber servido una copia cacheada de antes de los cambios. Otras hipótesis a
descartar: algún error de JS en consola que frene todo el script, o un bug
real en la lógica.

**Próximo paso**: repetir la prueba forzando recarga sin caché (Ctrl+Shift+R
o modo incógnito) antes de asumir que el código está mal.
