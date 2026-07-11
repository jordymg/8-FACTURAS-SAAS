# ADR-0009: La app nunca dice "IA" en su comunicación

**Date:** 2026-07-11
**Status:** ADOPTADA — origen: sesión de diseño CEO (Jordi) + CPO (Claude)

## Por qué repo general y no área App
Esta decisión se originó en una sesión de diseño sobre la pantalla de
inicio (`/app`), pero es una regla **transversal a todo el producto**: se
aplica a textos ya existentes fuera del área App (mensajes de error del
backend, ver Consecuencias), y a superficies futuras que tampoco son de esa
área — el carrusel de la pantalla de espera
([`docs/decisions/0005-pantalla-espera-cold-start.md`](0005-pantalla-espera-cold-start.md)),
emails, onboarding. Por eso va en `docs/decisions/` (repo general) y no en
`docs/areas/app/decisions/`.

## Contexto
El founder definió una regla de producto permanente sobre cómo la app se
comunica con el cliente final.

## Decisión
Ningún texto visible al usuario final puede mencionar "IA", "inteligencia
artificial", "Gemini", "modelo", ni equivalentes. En su lugar: "nuestro
sistema", o directamente describir la acción ("leemos los datos de tu
factura", "extraemos los datos").

**Racional del CEO**: los clientes saben que hay IA detrás, pero la
comunicación del producto habla de "nuestro sistema", no de la tecnología.

Aplica:
- **Retroactivamente** a todo texto existente (auditado hoy, ver
  Consecuencias).
- **A futuro**: textos del carrusel de espera (ADR-0005 general, pendientes
  de redactar), onboarding, avisos, emails si los hubiera.

## Alternativas consideradas
- Mencionar la IA explícitamente por transparencia con el cliente:
  descartada — el founder prefiere que la comunicación de producto no hable
  de la tecnología subyacente, independientemente de que el cliente sepa
  que existe.

## Consecuencias — auditoría hecha el 2026-07-11
Se encontraron y corrigieron 3 textos visibles al usuario que violaban la
regla (ninguno en `docs/areas/app/decisions/0002-*.md`, que es donde se
originó el pedido — estaban en otras partes del código):
1. `templates/app.html` — "Extrayendo datos con IA, puede tardar unos
   segundos…" → reescrito sin mencionar IA.
2. `static/js/app.js` — botón "Reintentar con IA" (tarjeta de error de
   extracción) → reescrito sin mencionar IA.
3. `app/blueprints/api.py` — mensaje de error `"Gemini no está configurado
   (falta GEMINI_API_KEY)."` (se muestra si falta configurar la variable de
   entorno) → reescrito sin mencionar Gemini ni el nombre de la variable.

No se tocaron comentarios de código (no son visibles al usuario, y
documentan honestamente que la extracción usa Gemini — útil para quien
mantiene el código).

Toda superficie nueva de texto (carrusel ADR-0005, onboarding pendiente de
diseño en `docs/areas/app/PRODUCTO.md`) debe revisarse contra esta regla
antes de implementarse.
