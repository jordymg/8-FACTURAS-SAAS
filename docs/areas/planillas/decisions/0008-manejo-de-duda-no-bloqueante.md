# ADR-0008 (planillas): Manejo de duda no bloqueante (corrige ADR-0007)

**Date:** 2026-07-06
**Status:** ADOPTADA — corrige el mecanismo de duda del ADR-0007

## Contexto
El ADR-0007 (a raíz del Issue #002 — un Ticket A válido catalogado como
comprobante en negro) estableció que ante la duda la IA debía dejar el
campo **vacío** y bloquear el guardado hasta que el usuario lo completara.
Revisando ese mecanismo, se decide cambiarlo antes de que llegue a un
usuario real: dejar el campo vacío no le da al usuario ninguna pista de qué
va ahí, y bloquear el guardado agrega fricción. La regla de fondo del
ADR-0007 sobre las 4 vías de autorización (CAE, CAEA, CAI, controlador
fiscal) **no cambia** — lo que cambia es qué hace la IA y la UI cuando hay
duda.

## Decisión
- **Tipo Factura = "X"** sigue siendo solo cuando la IA no detecta NINGUNA
  evidencia de autorización (CAE, CAEA, CAI, controlador fiscal) — sin
  cambios respecto al ADR-0007.
- **Ante la duda, la IA completa el campo igual**, con el valor que
  considera más probable — nunca lo deja vacío — pero lo marca como **"baja
  certeza"**.
- El formulario de revisión muestra ese campo **resaltado en rojo** para que
  el usuario lo corrobore.
- **No se bloquea el guardado.** Si el usuario avanza (botón "Guardar"), se
  toma como confirmación de que revisó el dato.
- Este mecanismo (**mejor valor + rojo + confirmación implícita al
  guardar**) es la regla general del formulario de revisión, aplicable a
  cualquier campo donde la extracción no tenga certeza — no solo Tipo
  Factura.

## Alternativas consideradas
- Duda → "X" igual (comportamiento del ADR-0005, antes del ADR-0007):
  descartada, genera falsos comprobantes en negro sobre documentos válidos.
- Duda → campo vacío + rojo + guardado bloqueado (ADR-0007, versión
  anterior de este mismo ADR): descartada — el usuario no tiene pista de qué
  va ahí; es mejor proponer un valor (que en la mayoría de los casos va a
  estar bien) y pedir corroboración, sin fricción de bloqueo.

## Consecuencias
- **Prompt de Gemini** (`app/services/gemini.py`): sigue reconociendo las 4
  vías de autorización (sin cambios ahí). Cambia qué se le pide hacer ante
  la duda: completar con el valor más probable de todas formas, y agregar la
  clave a `campos_inciertos` (se reusa el mismo campo del esquema, cambia su
  semántica: ya no significa "vacío por duda", significa "tiene valor pero
  con baja certeza").
- **Frontend** (`static/js/app.js`, `static/css/app.css`): el campo se sigue
  resaltando en rojo (clase `campo-en-duda`), pero **se saca el bloqueo de
  guardado** que había agregado el ADR-0007 — el usuario puede guardar con
  el campo en rojo tal cual, sin tener que tocarlo.
- `docs/ISSUES.md` #002 ya está logueado (ADR-0007) — no hace falta un
  issue nuevo, es una corrección del fix, no un bug nuevo encontrado por el
  uso.
- La prevención pendiente del ADR-0007 (set de casos de prueba del prompt)
  sigue vigente sin cambios.
