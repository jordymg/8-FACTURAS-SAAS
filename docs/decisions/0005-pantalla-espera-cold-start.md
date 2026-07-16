# ADR-0005: Pantalla de espera propia para el cold start de Render

**Date:** 2026-07-07
**Status:** ADOPTADA e IMPLEMENTADA (2026-07-15, handoff del CEO tras un
503 real de Gemini en uso real). Ampliada 2026-07-07: mismo mecanismo se
usa también para enmascarar reintentos de Gemini (ver abajo).

## Contexto
El plan free de Render duerme el servicio tras un rato sin uso (~30s de
arranque al despertar) — riesgo ya previsto en ADR-0001. Mientras el
servicio despierta, el usuario ve la pantalla de carga genérica de Render,
no algo propio de la marca.

**Segundo caso de uso, sumado al re-priorizar el pre-lanzamiento (ver
`docs/decisions/0007-lanzamiento-mvp-sin-cobro-online.md`)**: los
reintentos automáticos ante un 503 de Gemini (Fase 2 del ROADMAP, "hacer
antes de vender") necesitan una pantalla de espera — se decidió que sea
la MISMA pantalla/carrusel de este ADR, no una nueva.

## Decisión
La PWA cachea su app shell (vía service worker) y muestra una **pantalla de
espera propia** mientras el servidor despierta, con un **carrusel de
mensajes rotativos** (tips de uso, qué hace la app) en vez de una pantalla
en blanco o el mensaje genérico de Render.

Esto es **complementario, no reemplazo**, del upgrade a un plan pago de
Render al salir al mercado (esa decisión sigue en pie según ADR-0001) — la
pantalla de espera cubre el tiempo hasta que se justifique el upgrade, y
sigue siendo una buena práctica de UX aunque el servicio ya no duerma.

**Uso ampliado — reintentos de Gemini invisibles**: cuando Gemini devuelve
503 y la app reintenta automáticamente, el usuario **no ve** ningún mensaje
de "error, reintentando" — ve esta misma pantalla de espera con el
carrusel de tips, como si fuera simplemente parte del tiempo de
procesamiento normal. Solo si los reintentos se agotan (todos fallan) se
muestra recién ahí un mensaje de error amigable.

## Consecuencias
- Requiere que el service worker (`static/sw.js`) cachee el app shell
  (HTML/CSS/JS mínimo) para poder mostrar algo propio incluso antes de que
  el backend responda.
- Requiere que la lógica de reintentos de Gemini (backend,
  `app/services/gemini.py`) y la pantalla de espera (frontend) se activen
  con el mismo mecanismo/señal, para que el usuario vea una sola pantalla
  consistente sea cual sea la causa de la espera.
- **Textos del carrusel**: a definir al implementar (no forman parte de
  esta decisión).

## Implementación (2026-07-15, handoff del CEO)

### Reintentos ante 503 (backend)
`app/services/gemini.py`: `MAX_REINTENTOS_503 = 3`, `BACKOFF_SEG = [2, 4, 8]`
(espera creciente entre intentos, ~14s de sleep en el peor caso, 4
llamadas totales). Envuelve **solo** la llamada a
`client.models.generate_content(...)` — no el `json.loads` posterior, que
no es un fallo transitorio de red. Distingue por tipo de excepción del
SDK `google-genai` (`google.genai.errors.ServerError` = 5xx, se
reintenta; `ClientError` = 4xx, como imagen inválida o API key mala, NO
se reintenta, propaga directo). Al agotar los 3 reintentos, se levanta
`GeminiSobrecargadoError` con el mensaje EXACTO aprobado:

> "No pudimos procesar tu factura en este momento. Esperá unos minutos y
> volvé a intentar. La foto no se perdió, solo tocá reintentar."

`app/blueprints/api.py` no necesitó ningún cambio: su
`except Exception as e: ... "error": str(e)` ya mostraba lo que sea que
levante `gemini.py`, así que alcanzó con que el mensaje de la excepción
ya sea el texto final.

### Pantalla de espera con carrusel (frontend)
Overlay nuevo (`#overlay-espera`, `templates/app.html`) — fixed, cubre
cualquier `.screen`, con spinner (`.spinner`, `@keyframes girar`, nuevo)
+ tarjeta reutilizando **tal cual** `.tip-card`/`.tip-icono`/`.tip-rotativo`
(mismas clases que el tip de home y el carrusel de consejos de revisión,
sin una línea de CSS nueva para el mensaje en sí). Reemplaza al viejo
banner `#cargando` — `static/js/app.js::procesar()` ahora muestra/oculta
`#overlay-espera` durante toda la llamada a `/api/extract`, reintentos
automáticos incluidos: el usuario ve exactamente la misma pantalla sea
una extracción rápida o una con reintentos, cumpliendo "invisible".

**Tercer carrusel independiente**: `strings/mensajes-espera.txt` (6
textos exactos aprobados) + `app/services/mensajes_espera.py::get_mensajes_espera()`,
mismo patrón que `tips.py`/`consejos_revision.py`. El bloque de rotación
de `static/js/app.js` ya era una función reutilizable
(`iniciarCarruselRotativo`, del handoff anterior) — se sumó un tercer
llamado, `("mensaje-espera-rotativo", window.__MENSAJES_ESPERA__)`, con
su propio índice/timer independiente de los otros dos. Mantiene el
prefijo "Tip — " por consistencia visual con los otros dos carruseles
(decisión confirmada con el CEO — el mensaje 1 lee un poco raro con el
prefijo, pero se priorizó la consistencia).

**Botón de reintento manual**: ya existía (`crearCardError`,
`.btn-reintentar-ia`) y ya reenviaba el mismo `File` capturado en el
closure — cumplía el requisito de "la foto no se pierde" sin necesitar
ningún cambio.

### Cache del app shell para cold start (service worker)
`static/sw.js` pasa de cachear solo `app.css`/`app.js` a sumar
`static/espera.html` — una página **estática** (sin Jinja) con la misma
tarjeta/spinner/carrusel, los 6 textos de `mensajes-espera` duplicados a
mano como array JS (no puede leer el `.txt` en tiempo de carga) y un
polling liviano que reintenta cargar la página real cada ~2.5s hasta que
el backend responda. El `fetch` handler del SW, para navegaciones (no
`/api/*`, no assets), corre una carrera (`Promise.race`) entre la red
real y un timeout de 3s (`TIMEOUT_NAVEGACION_MS`) — si pierde la red,
sirve `espera.html` cacheado.

**Limitación inherente, no un bug**: la primera visita de un usuario
nuevo (service worker recién instalándose) no tiene nada cacheado
todavía — esa primera vez el cold start se ve como antes de este cambio.
Mejora recién desde la segunda visita en adelante.

### ⚠️ Hallazgo reportado, no resuelto (pedido explícito del handoff)
El handoff pidió verificar si el timeout del worker de gunicorn en Render
es un riesgo real para tolerar los reintentos, y señalarlo en vez de
resolverlo por mi cuenta. Verificado: `render.yaml` no fija `--timeout`
en ningún lado (ni `Procfile` ni `gunicorn.conf.py` existen) — rige el
default de gunicorn, **30 segundos**. `/api/extract` procesa los archivos
de una tanda en un loop serial dentro de la misma request. El backoff
aprobado ya suma ~14s de sleep por archivo en el peor caso (el propio
handoff estimaba "~15 segundos"), sin contar la duración real de las 4
llamadas a Gemini que fallan/reintentan (más lentas justo en el escenario
de alta demanda que dispara el 503). Con un solo archivo agotando los 3
reintentos, el total ya puede acercarse al límite de 30s; con más de un
archivo en la misma tanda golpeando 503, el riesgo de superar el timeout
deja de ser hipotético. **No se tocó `render.yaml`** — queda pendiente de
que el CEO decida (la opción más simple sería subir `--timeout` a, por
ejemplo, 60s en el `startCommand`, pero es un cambio de infraestructura
de producción que no correspondía decidir unilateralmente).

### Pruebas hechas
- **Backend** (mocks, sin pegarle a la API real de Gemini): éxito
  directo (1 llamada), 503 que se recupera en el 2° intento (2 llamadas,
  ~2s), 503 persistente en los 3 reintentos (4 llamadas, ~14s,
  `GeminiSobrecargadoError` con el mensaje exacto confirmado carácter por
  carácter), `ClientError` (400) sin reintento.
- **Frontend + service worker**, contra un servidor Flask real (no la
  simulación estática de sesiones anteriores) con un usuario de prueba en
  una base SQLite temporal, vía Playwright/Chromium: el service worker
  instala y cachea los 3 archivos del shell; el overlay aparece con
  spinner y carrusel durante una extracción mockeada (`page.route` sobre
  `/api/extract`, sin pegarle a Gemini real) y desaparece al terminar,
  pasando a la pantalla de revisión; el mensaje de error final coincide
  exacto cuando se simula agotar los reintentos, con el botón de
  reintento manual funcionando; los tres carruseles (home, revisión,
  espera) rotan de forma independiente.
- **Cold start**: simulado como navegación lenta (delay de red > 3s vía
  `page.route`, más fiel a cómo Render realmente se comporta — la
  conexión queda colgada mientras el contenedor arranca, no falla de
  inmediato) — confirmado que se sirve `espera.html` cacheado. La
  variante de "red completamente caída" (`context.setOffline`) no pudo
  probarse en este entorno: Chromium/Playwright cortan la red antes de
  que el service worker llegue a interceptar el evento `fetch`,
  limitación de la herramienta de testing, no del código (la rama de
  `.catch()` que atiende ambos casos es la misma).
- **No probado**: celular real (mismo límite que sesiones anteriores).

No implementado todavía: nada — el alcance del handoff quedó completo.
Lo único pendiente es la decisión del CEO sobre el timeout de gunicorn
(arriba).
