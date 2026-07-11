# ADR-0009: Reglas de comunicación con el usuario — nunca decir "IA", sin dos puntos

**Date:** 2026-07-11 (Regla 2 agregada el mismo día, sesión de tips/home)
**Status:** ADOPTADA — origen: sesión de diseño CEO (Jordi) + CPO (Claude)

Este documento agrupa reglas transversales sobre **cómo la app le habla al
usuario** — se van sumando acá en vez de fragmentarse en un ADR por regla.

## Por qué repo general y no área App
Esta decisión se originó en una sesión de diseño sobre la pantalla de
inicio (`/app`), pero es una regla **transversal a todo el producto**: se
aplica a textos ya existentes fuera del área App (mensajes de error del
backend, ver Consecuencias), y a superficies futuras que tampoco son de esa
área — el carrusel de la pantalla de espera
([`docs/decisions/0005-pantalla-espera-cold-start.md`](0005-pantalla-espera-cold-start.md)),
emails, onboarding. Por eso va en `docs/decisions/` (repo general) y no en
`docs/areas/app/decisions/`.

## Regla 1 — nunca mencionar IA

### Contexto
El founder definió una regla de producto permanente sobre cómo la app se
comunica con el cliente final.

### Decisión
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

### Alternativas consideradas
- Mencionar la IA explícitamente por transparencia con el cliente:
  descartada — el founder prefiere que la comunicación de producto no hable
  de la tecnología subyacente, independientemente de que el cliente sepa
  que existe.

### Consecuencias — auditoría hecha el 2026-07-11
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

## Regla 2 — sin dos puntos en textos nuevos

### Contexto
Sesión de tips/textos de la home
([ADR-0004 área App](../areas/app/decisions/0004-tips-y-textos-de-bienvenida-home.md)):
el CEO prefiere que los textos visibles al usuario eviten el carácter ":".

### Decisión
Los textos visibles al usuario (tips, avisos, explicaciones) evitan el
carácter ":". **No es retroactiva** (a diferencia de la Regla 1): aplica a
textos nuevos de acá en adelante. El texto de entrada del ADR-0002 (área
App) ya tenía un ":" aprobado antes de esta regla y queda exento
explícitamente — no se reescribe salvo pedido futuro del CEO.

### Consecuencias
Los 3 textos nuevos del ADR-0004 (saludo, feedback, los 6 tips iniciales)
ya vienen redactados sin ":". Revisar contra esta regla cualquier texto
nuevo de acá en adelante (carrusel ADR-0005, onboarding).
