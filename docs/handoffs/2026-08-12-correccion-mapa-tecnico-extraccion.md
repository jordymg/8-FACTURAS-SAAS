# Mapa técnico del flujo de extracción — Facturas SaaS (corregido)

> Corrección de un documento previo generado por un Proyecto de Claude sin
> acceso al código ni al VPS (solo `README.md`, `docs/decisions/`,
> `docs/ISSUES.md`, `docs/areas/planillas/`). Esta versión se corrigió con
> acceso directo al repo real y al VPS de producción (`vmi3497965`,
> `facturas.mcfly.ar`), el 2026-08-12. Los cuatro puntos que el documento
> original marcaba como "no puedo confirmar" (sección 4 original) están
> resueltos abajo con evidencia del código/config real.

Diagnóstico de base para el síntoma reportado: la app tarda mucho en procesar la foto y termina mostrando "error de red" cuando la conexión del usuario está bien.

## 1. Stack (corregido — la app **ya no está en Render**)

| Capa | Tecnología |
|---|---|
| Frontend | PWA (HTML/JS estático) |
| Backend | Flask (Python), gunicorn detrás de nginx |
| Extracción | Gemini (Google), modelo `gemini-flash-latest` |
| Datos del usuario | Google Sheets, vía una Service Account centralizada |
| Hosting | **VPS propio** (`vmi3497965.contaboserver.net`, dominio `facturas.mcfly.ar`), `systemd` + gunicorn + nginx |

`docs/decisions/0001-stack.md` (Render) quedó **superado** por
[`docs/decisions/0015-migracion-render-a-vps-propio.md`](../decisions/0015-migracion-render-a-vps-propio.md).
Render fue dado de baja definitivamente el 2026-08-12
(`docs/handoffs/2026-08-12-render-dado-de-baja.md`) — no está en standby,
no hay vuelta atrás. El `render.yaml` que queda en el repo es vestigial,
ya no se usa para desplegar.

## 2. Paso a paso del flujo (una foto o una tanda, de punta a punta)

1. **Usuario abre la PWA.** ~~Cold start de Render (~30s)~~ **ya no aplica**: un proceso bajo `systemd` no se duerme. Esta justificación de ADR-0005 quedó explícitamente retirada en su "Reencuadre 2026-08-11" (ver más abajo) — el servicio en el VPS no tiene ese problema.

2. **Usuario saca/sube la foto (o varias) de la factura** desde la PWA (cámara del celular o archivo). El frontend sí soporta tandas: agrupa varios archivos en un mismo `POST` (`static/js/app.js`, campo `archivos`).

3. **El frontend envía la imagen al backend** vía `fetch("/api/extract", { method: "POST", body: form })` (`static/js/app.js:77`). Confirmado en el código:
   - **No hay `AbortController` ni timeout configurado en el fetch.** El navegador espera indefinidamente (hasta que el propio SO/browser corte, o hasta que el servidor cierre la conexión).
   - El único `catch` alrededor de ese fetch (`static/js/app.js:79-84`) hace `alert("Error de red. Revisá tu conexión.")` — y se dispara en **dos casos bien distintos**: (a) el `fetch` mismo falla (sin conexión, DNS, conexión reseteada), o (b) `resp.json()` no puede parsear la respuesta porque no es JSON válido (por ejemplo, si nginx o gunicorn cortan la conexión y devuelven una página de error HTML, o si la conexión se corta a mitad de respuesta). **Este mensaje genérico es la causa directa de que cualquier corte de conexión, sea cual sea el motivo real, se vea igual para el usuario.**

4. **El backend llama a Gemini** (`app/services/gemini.py::extract_invoice()`). `temperature=0`, `response_schema` estructurado, imagen solo en memoria (nunca se persiste) — esto seguía correctamente documentado en el original, sin cambios.

5. **Gemini responde, o falla con un 503 — y hoy SÍ reintenta.** Corrección importante: el documento original decía que el reintento automático "no está implementado todavía". **Está implementado desde el 2026-07-15** (`docs/decisions/0005-pantalla-espera-cold-start.md`, sección "Implementación"):
   - `MAX_REINTENTOS_503 = 3`, backoff `[2, 4, 8]` segundos (`app/services/gemini.py`).
   - Solo reintenta `ServerError` (5xx); un `ClientError` (4xx, ej. API key inválida) propaga directo, sin reintento.
   - Al agotar los 3 reintentos, se levanta `GeminiSobrecargadoError` con un mensaje amigable ya aprobado ("No pudimos procesar tu factura en este momento...").
   - **El frontend muestra la misma pantalla de espera con carrusel de tips durante todo el reintento** (`#overlay-espera`) — el usuario no ve "error, reintentando", ve la espera normal. Esto también está implementado, no pendiente.

6. **El backend responde al frontend** con los resultados. Confirmado en `app/blueprints/api.py::extract()` (línea 70): el `try/except Exception as e: resultados.append({..., "error": str(e)})` envuelve la llamada a Gemini **por archivo**, dentro de un loop serial sobre la tanda — un error de Gemini en una foto no aborta las demás, y se devuelve como parte del JSON con `ok: false`, no como fallo de la request HTTP completa. Esto significa que **un 503 de Gemini, incluso agotando los 3 reintentos, NO dispara el "Error de red"** del frontend — dispara `crearCardError()`, una tarjeta de error específica por foto. El "Error de red" genérico solo aparece cuando la conexión HTTP en sí se corta.

7. **Usuario revisa/corrige los datos** en una tarjeta editable en pantalla. (sin cambios)

8. **Al guardar, el backend valida** CUIT, fechas, y duplicados. `app/services/sheets.py::find_duplicate()` compara `proveedor` + `numero` + `fecha` (normalizados con `norm_text`/`norm_id`), tanto contra el Sheet como contra otras fotos de la misma tanda — confirmado, coincide con el original (`docs/areas/planillas/decisions/0009-ux-duplicados.md`).

9. **El backend escribe la fila en el Google Sheet del usuario** vía la Service Account (`gspread`). Sin cambios respecto al original.

10. **El frontend actualiza el contador/lista** con `GET /api/invoices`. Sin cambios.

## 3. El sospechoso más probable del síntoma reportado (corregido)

Los dos sospechosos originales (cold start de Render, falta de reintento ante 503) **ya no aplican**: Render no existe más y el reintento está implementado desde julio. El síntoma reportado —tarda mucho y termina en "error de red"— tiene hoy una explicación más específica y verificable en el código:

**Timeout del servidor en tandas de varias fotos.** El VPS corre gunicorn con `--timeout 60` y nginx con `proxy_read_timeout 90s` (mayor a propósito, ver comentario en la config: "cubre extracciones lentas"). Pero `/api/extract` procesa **todas las fotos de una tanda en un loop serial dentro de la misma request** (paso 6). Si el usuario sube varias fotos juntas y alguna pega un 503 que agota los 3 reintentos (~14s de solo sleep, más la duración real de 4 llamadas a Gemini, más lenta justo bajo alta demanda), el tiempo total de la request puede superar los 60s del `--timeout` de gunicorn. Cuando eso pasa, gunicorn mata el worker a mitad de la request, la conexión se corta, y el `fetch` del frontend cae en el `catch` genérico → "Error de red" — aunque la causa real fue un timeout del servidor procesando la tanda, no un problema de conexión del usuario.

Esto es consistente con: la app "tarda mucho" (varias fotos, varios reintentos posibles) y termina en "error de red" (corte de conexión por timeout del worker, no error de red real).

**Nota:** esto es la explicación más plausible dado el código y la config actuales, pero no está confirmado contra logs de producción de ese incidente puntual — sigue siendo razonable revisar los logs de `systemd` (`journalctl -u facturas`) del momento exacto en que le pasó al usuario para confirmarlo con certeza.

## 4. Los cuatro puntos que el documento original no podía confirmar — ahora confirmados

1. **Texto y condición exacta del "error de red"**: `static/js/app.js:82`, `alert("Error de red. Revisá tu conexión.")`, dentro del único `catch` que envuelve el `fetch` a `/api/extract` (línea 79-84).
2. **Timeout en el fetch del frontend**: no hay ninguno. Sin `AbortController`, sin límite explícito — depende enteramente de que el servidor responda o corte la conexión.
3. **Distinción "Gemini no respondió" vs. "problema de red real" en el backend**: el backend SÍ distingue por archivo (errores de Gemini se devuelven como JSON `ok:false` con HTTP 200, ver punto 6 arriba) — pero **no hay nada que distinga, del lado del backend, un timeout del propio worker de gunicorn** (que corta la conexión entera) de un corte de red real; ambos se ven idénticos para el frontend.
4. **Logs de producción**: ya no aplica Render (dado de baja). En el VPS, los logs del servicio están en `journalctl -u facturas` — no revisados todavía para el incidente puntual reportado por el usuario, sección 3 arriba.

## Siguiente paso sugerido

Dado que la causa más probable es el timeout de gunicorn en tandas de varias fotos con reintentos, dos caminos concretos (no implementados todavía, a decidir):
- Subir `--timeout` de gunicorn (con su correspondiente margen en `proxy_read_timeout` de nginx), si se prioriza simplicidad sobre tiempo de espera del usuario.
- Procesar cada foto de la tanda como una request independiente desde el frontend (en vez de una sola request con todas), para que un timeout afecte solo a una foto y no tire abajo la tanda entera — cambio más grande, pero resuelve el problema de raíz en vez de correr el límite.

Antes de elegir, confirmar con `journalctl -u facturas` si el incidente reportado coincide en el tiempo con una tanda de varias fotos y/o con reintentos de Gemini.
