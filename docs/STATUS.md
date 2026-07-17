# STATUS

## Configuración rápida (constantes que se tocan seguido)
- **Tope de facturas mensual**: `LIMITE_MENSUAL` y `UMBRAL_AVISO` en
  `app/services/limites.py`. Detalle completo en
  `docs/decisions/0008-tope-facturas-mensual.md`.
- **Extracción de Gemini**: modelo y `temperature` en
  `app/services/gemini.py`. Detalle en
  `docs/decisions/0010-extraccion-determinista-temperature-cero.md`.
- **Duración de la sesión**: `SESSION_LIFETIME_DIAS` (90 días de
  inactividad, renovable) en `app/__init__.py`. Detalle en
  `docs/decisions/0012-sesion-90-dias-oauth-sin-reconsentimiento.md`.
- **Reintentos ante 503 de Gemini**: `MAX_REINTENTOS_503` y
  `BACKOFF_SEG` en `app/services/gemini.py`. Detalle en
  `docs/decisions/0005-pantalla-espera-cold-start.md`.
- **Server local: puerto 5050, no 5000** — el redirect_uri de OAuth
  registrado en Google Cloud Console es `http://localhost:5050/oauth2callback`
  (descubierto el 2026-07-12 tras un rato de debug). Levantar con
  `python -m flask --app wsgi run --debug --port 5050`, y entrar por
  `http://localhost:5050` (con `localhost`, no `127.0.0.1` — Google los
  trata como hosts distintos).

**Rediseño del flujo de guardado (ADR-0006 área App, 2026-07-14)**: botón
único "Guardar en Sheets" para toda la tanda (se sacan los botones por
tarjeta), cruz "✕ Descartar factura" más visible por tarjeta, y cuenta
regresiva de 3 segundos que redirige sola a la home (se saca el botón
"Volver") — **sin pantalla nueva**: la cuenta regresiva reemplaza al botón
único en su mismo lugar, las tarjetas guardadas siguen visibles arriba
(corregido el mismo día a pedido del CEO, la primera versión sí usaba una
pantalla de éxito separada). Falla parcial al guardar: lo guardado queda
guardado, lo fallido se puede reintentar o descartar. Probado con una
simulación de DOM real (jsdom) cubriendo los 6 casos pedidos — no
confirmado todavía en navegador real (falta acceso a Chromium/Playwright
en este entorno y login real de Google). Detalle completo en
`docs/areas/app/STATUS.md` y el ADR. De paso, se aclaró la Regla 2 del
ADR-0009 (repo general): no prohíbe el ":" en todo texto, aplica a
párrafos/textos corridos, queda como criterio y no como regla mecánica.

**Sesión persistente de 90 días + OAuth sin re-consentimiento (ADR-0012
repo general, handoff del CEO, 2026-07-15)**: reportado desde el celular —
la app pedía login de nuevo Y mostraba la pantalla de permisos de Google
de nuevo Y llegaba un mail de Google de "autorizaste la aplicación", en
cada visita. Dos causas, ambas corregidas:
- La sesión de Flask no era permanente (`session.permanent` nunca se
  seteaba) → cookie "de navegador" sin vencimiento propio, se perdía al
  cerrar el navegador del todo. Ahora `session.permanent = True` al
  loguear (`app/blueprints/auth.py`) + `PERMANENT_SESSION_LIFETIME` = 90
  días en una sola constante (`SESSION_LIFETIME_DIAS`,
  `app/__init__.py`) + `SESSION_REFRESH_EACH_REQUEST = True` (el plazo
  corre desde el último uso, no desde el login) + cookie con
  `HttpOnly`, `SameSite=Lax`, y `Secure` solo en producción (detectado
  con la env var `RENDER=true` que pone Render sola).
- El login forzaba `prompt="consent"` en cada intento, generando un grant
  nuevo (de ahí el mail) cada vez — se saca. Además, la librería
  `google-auth-oauthlib` pone `access_type="offline"` **por default** si
  no se indica lo contrario (no alcanzaba con simplemente no
  mencionarlo) — se pasa `access_type="online"` explícito para
  desactivarlo.
- `SECRET_KEY` ya se leía de variable de entorno (no se generaba en el
  proceso) y en Render usa `generateValue: true`, que — confirmado contra
  la documentación de Render — genera el valor una sola vez al crear el
  servicio y lo persiste; no se regenera en cada deploy. No hizo falta
  cambiar nada ahí, solo confirmarlo.
- **Probado en este entorno** (sin browser real ni cuenta de Google
  disponible): la cookie de sesión emitida tiene vencimiento propio (no es
  "de navegador"), sobrevive un restart del proceso simulado (misma
  `SECRET_KEY`, dos instancias de la app arrancadas por separado), una
  sesión vencida obliga a re-loguear, y la URL de autorización generada
  ya no lleva `prompt` ni `access_type=offline`.
- **No probado, pendiente de confirmación real por el CEO** (mismo tipo de
  límite que el rediseño de guardado, no hay Chromium/Playwright ni login
  real de Google en este entorno): que Google efectivamente omite la
  pantalla de permisos y el mail en un segundo login real con una cuenta
  que ya autorizó antes, comportamiento en producción (Render) tras un
  redeploy real, y la PWA instalada en el celular real (el escenario
  original del reporte). Detalle completo en
  `docs/decisions/0012-sesion-90-dias-oauth-sin-reconsentimiento.md`.

**Rediseño visual del tip rotativo de la home (ADR-0004 área App, Decisión
E, handoff del CEO, 2026-07-15)**: el tip se veía muy chico y pasaba
desapercibido. Cambio solo visual (CSS/HTML) — tarjeta con fondo celeste
suave (distinto del amarillo de avisos), bordes redondeados, texto más
grande y con más contraste, ícono de lamparita a la izquierda. Rotación,
textos y posición sin cambios (`static/js/app.js` no se tocó, confirmado
por diff vacío). Probado con Playwright/Chromium (instalado para esta
sesión) contra el HTML real de `/app` en desktop y mobile — tarjeta
visible, ícono presente, rotación funcionando, sin overflow horizontal,
fondo distinguible del aviso de límite mensual, buen contraste. Pendiente
de confirmación en celular real. Detalle completo en
`docs/areas/app/decisions/0004-tips-y-textos-de-bienvenida-home.md` y
`docs/areas/app/STATUS.md`.

**Carrusel "consejos de revisión" en la pantalla de revisión (ADR-0007
área App, handoff del CEO, 2026-07-15)**: segundo carrusel rotativo,
independiente del tip de la home, arriba de las tarjetas de facturas en
la pantalla de revisión. Réplica exacta del estilo visual del tip de home
(mismas clases CSS, cero líneas nuevas en `static/css/app.css`) y misma
mecánica de rotación, con contenido propio en un archivo nuevo
(`strings/consejos-revision.txt`, 6 textos exactos aprobados por el CEO).
`static/js/app.js` refactorizado en una función reutilizable para ambos
carruseles, sin cambiar timings ni comportamiento. Probado con
Playwright/Chromium contra el HTML real de `/app` con 1 y 3 tarjetas, en
desktop y mobile — sin overflow ni tarjeta empujada fuera de vista, ambos
carruseles rotan independiente, tip de home intacto. Pendiente
confirmación en celular real. Detalle completo en
`docs/areas/app/decisions/0007-carrusel-consejos-revision.md` y
`docs/areas/app/STATUS.md`.

**ADR-0005 implementado: pantalla de espera + reintentos ante 503 de
Gemini (handoff del CEO, 2026-07-15, tras sufrir un 503 real)**:
- Backend (`app/services/gemini.py`): 3 reintentos con backoff 2/4/8s
  ante `ServerError` (5xx) de Gemini, ~14s de sleep en el peor caso;
  otros errores (`ClientError` 4xx) no se reintentan. Al agotar los
  reintentos, mensaje de error EXACTO aprobado ("No pudimos procesar tu
  factura en este momento..."), sin cambios necesarios en `api.py`.
- Frontend: overlay de espera nuevo (`#overlay-espera`, spinner +
  tarjeta reutilizando `.tip-card`/`.tip-icono`/`.tip-rotativo` tal
  cual) reemplaza al viejo banner `#cargando`, visible durante toda la
  extracción — reintentos automáticos invisibles para el usuario.
  **Tercer carrusel independiente** (`strings/mensajes-espera.txt`, 6
  textos exactos) reutilizando `iniciarCarruselRotativo`. El botón de
  reintento manual ya existente (`.btn-reintentar-ia`) ya retenía la
  foto — no necesitó cambios.
- Service worker (`static/sw.js`): ahora cachea el app shell completo
  (`app.css`, `app.js`, `static/espera.html` nuevo) y sirve ese shell
  ante una navegación lenta/caída (carrera de 3s), para cubrir el cold
  start de Render.
- **Hallazgo reportado, no resuelto** (pedido explícito del handoff): el
  timeout default de gunicorn (30s, sin override en `render.yaml`) podría
  no alcanzar en el peor caso de una tanda con varios archivos golpeando
  503 a la vez — no se tocó la infraestructura, queda pendiente de
  decisión del CEO. Detalle completo, con lo probado y lo no probado, en
  `docs/decisions/0005-pantalla-espera-cold-start.md`.

**Keep-alive para Render free tier (ADR-0013 repo general, handoff del CEO,
2026-07-16)**: Render free duerme el servicio tras ~15 min sin tráfico
entrante (cold start ~30s, inaceptable para clientes). Se descarta el plan
pago de Render por ahora (decisión del CEO). Implementado:
- Endpoint `GET /health` (`app/blueprints/api.py`) — respuesta estática
  `{"status": "ok"}`, sin DB/Sheets/Gemini, sin auth, sin afectar el
  conteo de facturas.
- `.github/workflows/keep-alive.yml` — cron (más `workflow_dispatch` para
  probarlo a mano) que le pega a `/health` en producción.
- **Probado en este entorno**: `/health` responde 200 instantáneo en
  local (Flask test client).

**No cumplía su función — diagnosticado y ajustado el mismo día
(Issue #007, handoff del CEO)**: el CEO confirmó con un log de Render que
la app se durmió a las ~10:06 hora Argentina pese al keep-alive recién
implementado. Diagnóstico vía `gh` CLI contra la API de Actions: el
workflow estaba bien configurado (activo, rama default, sin errores),
pero **GitHub Actions no ejecuta el trigger `schedule` con precisión para
crons sub-horarios** — gaps reales observados de ~100 minutos con
`*/14 * * * *` (7 veces más lento que lo pedido), y el incidente reportado
cayó justo en uno de esos huecos. `/health` en sí respondía bien — no era
el endpoint. Causa raíz de la plataforma (GitHub), no de nuestra
configuración. Fix aplicado: cron bajado a `*/10 * * * *` (decisión del
CEO) + `--fail` agregado al `curl` (sin ese flag una respuesta HTTP de
error no hacía fallar el paso). **Riesgo señalado, no resuelto con
garantía**: como la causa de fondo es la imprecisión de GitHub para
crons frecuentes, `*/10` reduce el riesgo pero no lo elimina — si los
gaps reales siguen superando ~15 min, hace falta una alternativa
(servicio externo de pings, plan pago de Render), decisión del CEO.
Pendiente: verificar los gaps reales de las próximas horas. Detalle
completo en `docs/decisions/0013-keep-alive-render-free.md` e
[Issue #007](ISSUES.md).
Complementa, no reemplaza, al ADR-0005 (pantalla de espera).

**GitHub Actions descartado, reemplazado por UptimeRobot (Issue #007
cerrado, handoff del CEO, 2026-07-16)**: el fix de `*/10` de arriba **no
alcanzó** — el CEO verificó un cold start real posterior al ajuste, la
app se siguió durmiendo. Confirma que la causa nunca fue el valor del
intervalo, sino la imprecisión de GitHub Actions en sí para ejecutar
`schedule` con la frecuencia configurada. GitHub Actions queda
**descartado** como mecanismo de keep-alive:
- `.github/workflows/keep-alive.yml` **eliminado** del repo — no convive
  con el mecanismo nuevo, un cron que no cumple su frecuencia no sirve ni
  como respaldo.
- Mecanismo vigente: **UptimeRobot** (servicio externo gratuito), monitor
  HTTP cada 5 minutos contra `https://facturas-saas.onrender.com/health`
  en producción. Configurado a mano por el CEO **fuera del repo** (su
  propia cuenta) — **no hay rastro de esto en el código**, una sesión
  futura que busque el keep-alive tiene que revisar la cuenta de
  UptimeRobot del CEO, no el repo.
- Se mantiene sin cambios: el endpoint `GET /health`
  (`app/blueprints/api.py`, ahora consumido por UptimeRobot), el ADR-0005
  (pantalla de espera, cobertura de cold starts residuales), y el plan
  pago de Render como solución de fondo postergada hasta la salida a
  vender (ADR-0001) — UptimeRobot es un workaround del free tier, no lo
  reemplaza conceptualmente.
- **Pendiente de confirmación real**: que UptimeRobot mantenga la app
  despierta durante un período largo sin cold starts — la verifica el CEO
  desde su cuenta y el uso real. Detalle completo en la sección
  "Reemplazo 2026-07-16" de `docs/decisions/0013-keep-alive-render-free.md`.

**Instrumentación de tiempos por etapa (ADR-0014 repo general, handoff
del CEO, 2026-07-16)**: antes de optimizar el tiempo de espera entre
sacar la foto y ver los datos extraídos, se decidió medir primero. Sesión
de solo instrumentación, sin optimizaciones ni cambios de comportamiento
visible. Implementado:
- `POST /api/extract`: una línea de log por foto (`TIEMPOS extract
  [n/total] — imagen: …MB | recepción: …s | gemini: …s (reintentos: N,
  último intento: …s) | duplicados: …s | total: …s`) más una línea de
  resumen del lote (lectura de la planilla + total del request).
- `POST /api/invoices`: una línea con la duración de la escritura en el
  Sheet, marcando si disparó la creación de la pestaña del año, y la
  duración total.
- Interruptor `LOG_TIEMPOS` (env var), **default activado también en
  producción** (decisión del CEO — importan los tiempos reales).
- Logger propio (`app/services/tiempos.py`) que no propaga al root
  logger, para no arrastrar el nivel INFO de librerías de terceros
  (gspread, google-genai). Ninguna línea loguea datos sensibles del
  comprobante (solo tiempos, tamaños, contadores).
- **Modelo de Gemini configurado hoy**: `gemini-2.5-flash` (default de
  código y valor explícito en `render.yaml`, coinciden).
- **Probado en este entorno** con Flask test client + mocks de
  Gemini/Sheets (sin credenciales reales): tanda de 2 fotos genera 2
  líneas identificables + resumen de lote, guardado genera su línea
  marcando pestaña creada, `LOG_TIEMPOS=false` no loguea nada, respuestas
  HTTP sin cambios de contenido/formato. **No probado contra las APIs
  reales** — pendiente de confirmar en producción que las líneas
  aparecen en los logs de Render con datos reales.
- **Observación de optimización, no implementada** (para que decida el
  CEO con los datos en la mano): cada guardado llama a
  `asegurar_pestana_del_anio()`, que hace una llamada a la API de Sheets
  para confirmar que la pestaña ya existe (caso normal) antes de escribir
  — candidato a cachear si los tiempos muestran que pesa. Detalle
  completo en `docs/decisions/0014-instrumentacion-tiempos-extraccion.md`.

## Current phase
Phase 1 en producción (`https://facturas-saas.onrender.com`), planilla v2
(23 columnas) confirmada con datos reales. **Re-priorizado el camino a
vender** (ADR-0007 repo general): el MVP sale a la calle sin cobro online,
sin landing y sin dominio propio — venta persona a persona a conocidos, demo
presencial, cobro manual. Checklist real de "antes de vender" en
`docs/ROADMAP.md`.

**Nuevo documento**: `docs/FEATURES.md` — catálogo vivo e interno de
features del producto (ADR-0011 repo general). Primera entrada: la carga
de facturas por foto (todo lo online hoy). Segunda: "Reportes al
contador", registrada como idea sin especificar todavía. Mantenedor:
**Claude 1 (CPO)**, con aprobación del CEO para toda entrada y cambio.

**Modelo de nombres y roles formalizado** (`docs/ORGANIGRAMA.md`): los
integrantes IA de la empresa tienen nombre propio separado del rol que
ocupan — el Claude que hoy es CPO se llama **"Claude 1"**. Roles futuros
pueden ocuparlos Claudes nuevos ("Claude 2", etc.), cada uno su propio
espacio de trabajo. `README.md` también referencia esto en "Cómo
trabajamos" y en la tabla de documentación (fila nueva para
`docs/FEATURES.md`).

ADR-0001, ADR-0002, ADR-0003 y ADR-0004 (rediseño de formulario, pantalla
de inicio, header con nombre de planilla + email, y tips/textos de
bienvenida — los cuatro del área App) **ya confirmados funcionando por el
founder en navegador (2026-07-11)**. Ver `docs/areas/app/STATUS.md` y los
ADRs en `docs/areas/app/decisions/`.

**Onboarding de configuración de planilla implementado** (ADR-0005 área
App, mismo día): 3 pasos reordenados (copiar email → crear/compartir
planilla → pegar link). En la primera conexión, el cliente escribe un
título en blanco para su planilla (el sistema le agrega el año solo).

**Pestañas de período (ADR-0003 área Planillas), cuatro versiones en dos
días — ya cerrado**: primero se probó crear las 12 pestañas mensuales del
ciclo anual de una sola vez (2026-07-11) — encontrando **Issue #006**
(`docs/ISSUES.md`): crear 12 pestañas de a una con todo su formato
dispara ~80 llamadas seguidas a la API de Sheets y supera la cuota de
Google, confirmado fallando de verdad contra la planilla de referencia;
se resolvió agrupando todo en 2 llamadas (`batch_update` +
`values_batch_update`). El founder ajustó el diseño dos veces más
(2026-07-12): a una pestaña mensual por vez, y después a **una sola
pestaña por año calendario** (ej. `"2026"`). En las primeras tres
versiones el alcance quedaba acotado a "solo crear pestañas" — guardar y
leer facturas seguía usando `sheet1`. **El founder probó cargar una
factura real, vio que se seguía guardando en "Hoja 1", y marcó esto como
un problema real** — se cerró: `append_invoice`, `list_invoices` y
`find_duplicate` ahora usan de verdad la pestaña del año (por defecto, el
año actual). "Hoja 1" queda con los datos reales de pruebas anteriores
del founder, intacta pero sin uso — confirmado que no hace falta migrarla
por ahora (estamos en desarrollo). Detalle completo en
`docs/areas/planillas/decisions/0003-*.md`.

**Confirmado funcionando por el founder en navegador (2026-07-12)** —
cargó una factura real y quedó en la pestaña del año correcto. Commiteado
y desplegado a producción el mismo día.

**Pendiente, no bloquea nada de lo de arriba**:
- Decidir si "Últimas facturas"/duplicados deberían buscar también en años
  anteriores (hoy solo miran el año actual).
- Decidir qué hacer con los datos ya cargados en "Hoja 1" antes de este
  cambio (facturas reales de pruebas del founder) — hoy quedan intactos
  pero sin uso, la app no los lee más. ¿Migrarlos a mano a "2026" en algún
  momento, o dejarlos como quedaron?

De paso, esta sesión también se documentó y aplicó
`docs/decisions/0009-comunicacion-nunca-mencionar-ia.md` (repo general,
transversal, ahora con 2 reglas: nunca mencionar IA, y sin dos puntos en
textos nuevos): ningún texto visible de la app puede mencionar IA/Gemini —
auditoría hecha, 3 textos corregidos.

## Done
- Pivot de arquitectura: Sheets se escriben con una Service Account en vez de
  OAuth por usuario; el login de Google pide solo identidad (openid + email).
  Ver ADR-0004 del repo general.
- Decisión MVP sin persistencia de imagen: la foto se usa solo en memoria
  para la extracción y se descarta.
- Deploy a Render (`psycopg2-binary` + `ProxyFix`, necesarios solo en
  producción, no en local).
- Issue #001 (facturas desencolumnadas) diagnosticado por debug y resuelto —
  ver `docs/ISSUES.md`.
- Nueva convención `docs/areas/{nombre}/` (I+D por producto) y
  `docs/ISSUES.md` (log de problemas que tocaron datos reales o
  sorprendieron). Primera área: planillas.
- **Estructura v2 de la planilla implementada** (ADR-0005 + ADR-0006 del
  área Planillas): 23 columnas — IVA discriminado por alícuota (10,5/21/27%),
  percepciones (IVA, IIBB ARBA/CABA), retenciones (Ganancias, IVA), SIRTAC,
  Impuestos Internos, Categoría (clasificación libre por la IA), CUENTA y
  Cód. Proveedor (en blanco por ahora). Prompt de Gemini reescrito con reglas
  explícitas por cada impuesto (evita confundir uno con otro). Dos bugs
  encontrados y corregidos durante la implementación (ceros a la izquierda
  perdidos en Punto de Venta/N° de Factura; montos guardados como texto en
  vez de número por la configuración regional de la planilla) — ambos
  probados en una pestaña de prueba antes de aplicar. Detalle completo en
  `docs/areas/planillas/STATUS.md`.
- **Issue #002 resuelto**: el mismo día del despliegue de la v2, un Ticket A
  válido (autorizado por controlador fiscal, sin CAE) se guardó como "Tipo
  Factura" = "X" (comprobante en negro) — falso positivo. Corregido por
  ADR-0007 (área Planillas): "X" solo si no se detecta NINGUNA de las 4 vías
  de autorización (CAE, CAEA, CAI, controlador fiscal). Ver `docs/ISSUES.md` #002.
- **Mecanismo de duda ajustado (ADR-0008, corrige ADR-0007)**: en vez de
  dejar el campo vacío y bloquear el guardado, la IA completa el campo con
  su mejor valor y lo marca "baja certeza" — el formulario lo resalta en
  rojo (clase `campo-en-duda`) pero **no bloquea el guardado**; avanzar se
  toma como confirmación implícita. Se revisó el mismo día, antes de que el
  mecanismo anterior llegara a un usuario real.
- Reconectar una planilla ya creada (vía `/app/config`, pegando la misma
  URL/ID de nuevo) reescribe el encabezado a la estructura vigente — sirve
  para llevar una planilla vieja (v1) a la v2 sin tocar código. Las filas de
  datos ya cargadas con la v1 no se migran solas: quedan desalineadas contra
  el nuevo encabezado si las hay.
- README.md de la raíz reemplazado por una versión más completa (trae de
  `inbox/`) — explica el producto, cómo se trabaja el repo (ADRs, áreas de
  I+D, `docs/ISSUES.md`) y linkea toda la documentación. Todos los links
  relativos a `/docs` verificados.
- **Nueva área `docs/areas/app/`** (diseño/UX de la app): solo estructura y
  alcance por ahora (README + PRODUCTO.md stub + STATUS.md), sin decisiones
  propias — el contenido sale de una conversación de diseño dedicada,
  todavía pendiente.
- **UX de duplicados implementada (ADR-0009, área Planillas)**: criterio
  final `proveedor`+`numero`+`fecha` (se sacó `cuit` — Issue #003, ver
  `docs/ISSUES.md`). `sheets.find_duplicate()` + aviso amarillo no
  bloqueante en la tarjeta de revisión con la fecha de carga de la
  coincidencia, también contra otras fotos de la misma tanda. **Confirmado
  funcionando en producción por el founder** (factura en negro sin CUIT
  repetida, ya se detecta bien).
- **Pantalla de espera + reintentos ante 503 de Gemini — IMPLEMENTADO
  el 2026-07-15** (`docs/decisions/0005-pantalla-espera-cold-start.md`,
  repo general, no confundir con el ADR-0005 del área Planillas): ver
  "ADR-0005 implementado" más arriba, primer bloque de esta sesión, para
  el detalle completo. Sigue documentado pero sin implementar: política de
  acceso de soporte (la Service Account ya tiene acceso Editor a las
  planillas — reflejarlo en los términos de uso antes de lanzar, Fase 3),
  con la idea de una vista de solo-lectura como alternativa post-MVP
  anotada en el icebox.
- **Organigrama de la empresa** (`docs/ORGANIGRAMA.md`, ADR-0006 repo
  general): roles se crean con cada área nueva, no todos de entrada. CEO
  (Jordi) dirige sin ejecutar. CPO (Claude) es el encargado de las áreas App
  y Planillas — mismo producto visto de dos lados (medio y entregable).
  `docs/areas/app/README.md` completado con la definición del área (qué es,
  encargado, alcance, qué NO es). `docs/areas/planillas/README.md` también
  actualizado con su encargado, por consistencia con el ADR nuevo.
- **Re-priorización general del camino a vender (ADR-0007 repo general)**:
  el MVP se lanza sin Mercado Pago, sin landing y sin dominio propio — venta
  persona a persona, demo en vivo, cobro manual/efectivo. Esos 3 puntos
  pasan de bloqueantes duros a "postergados, no olvidar" en
  `docs/ROADMAP.md`. Lo único que sigue siendo bloqueante inmediato:
  términos de uso mínimos (hacer ahora).
- **Tope de 250 facturas/mes — diseño funcional completo** (ADR-0008 repo
  general, no implementado todavía): contador en la DB de la app, aviso al
  acercarse al límite, corte al llegar a 250 salvo pago de un plus (bloqueado
  hasta que exista cobro). Mientras no haya cobro (MVP): solo contador +
  avisos, sin corte.
- **Pantalla de espera (ADR-0005 repo general) ampliada**: además del cold
  start de Render, ahora también enmascara los reintentos automáticos ante
  un 503 de Gemini — el usuario nunca ve "reintentando", ve el carrusel de
  tips. **Implementado el 2026-07-15** (ver el bloque al principio de esta
  sesión).
- **Onboarding, foco redefinido** (`docs/areas/app/PRODUCTO.md`): no es un
  carrusel genérico, es el paso crítico de configurar la planilla (crearla,
  compartir con la SA, pegar la URL) — tiene que ser "a prueba de tontos".
- **ADR-0001 del área App** (primera decisión propia de esa área):
  rediseño del formulario de revisión — ocultar campos poco frecuentes
  salvo que tengan valor extraído, grilla responsiva en desktop,
  procesamiento automático sin botón manual (resolviendo que la carga
  múltiple siga funcionando). No implementado todavía.
- **ADR-0003 del área Planillas (pestañas por período) recibe la idea del
  founder**: la app crearía la pestaña nueva automáticamente al llegar la
  primera factura de un período sin pestaña — sigue sin resolver el resto
  (filtro por mes, fórmulas de total anual).
- **Backlog "migración v1→v2" reencuadrado como ADR-0010 del área
  Planillas (pregunta abierta, no decidir todavía)**: no es migrar
  planillas viejas, es qué hacer cuando un cliente pida una columna extra
  propia — postura del founder es estar abiertos sin modificar la planilla
  cliente por cliente, pero el cómo queda sin resolver.

## Next — checklist antes de vender (ver ADR-0007, detalle en `docs/ROADMAP.md`)
1. **Términos de uso, versión mínima.**
   Qué: cubrir acceso Editor de la SA (incluye soporte), qué datos procesa
   la app, no-persistencia de imágenes, límites de responsabilidad. No
   exhaustivo legalmente todavía.
   Dónde: documento nuevo, ubicación a definir (¿raíz del repo, tipo
   `TERMINOS.md`?).
   Qué se necesita: redactarlo — es el único punto 100% pendiente de
   arrancar.

2. **Onboarding de configuración de planilla.**
   Qué: guiar "a prueba de tontos" el paso de crear la planilla, compartirla
   con la SA, y pegar la URL.
   Dónde: `docs/areas/app/` — necesita antes una conversación de diseño
   dedicada para los textos/pasos concretos.
   Qué se necesita: esa conversación de diseño, después implementar.

3. **Tope de 250 facturas/mes, versión soft (sin corte).**
   Qué: contador en la DB + aviso al acercarse al límite (ej. 200).
   Dónde: `app/models.py::User.invoices_this_month` (ya existe el campo),
   diseño funcional completo en `docs/decisions/0008-tope-facturas-mensual.md`.
   Qué se necesita: implementar el aviso en la UI y definir el reset
   mensual del contador (no diseñado todavía).

4. **Probar en el celular real** todo lo que quedó confirmado solo en
   Chromium/Playwright o navegador desktop hasta ahora: el rediseño del
   formulario y la pantalla de inicio (ADR-0001, ADR-0002, ADR-0003 área
   App), la sesión de 90 días + login sin re-consentimiento (ADR-0012),
   las tarjetas de tips/consejos/espera y sus tres carruseles (ADR-0004
   Decisión E, ADR-0007 área App, ADR-0005 repo general), y el fallback
   del service worker en un cold start real de Render.
   Dónde: toda la PWA — `templates/app.html`, `static/js/app.js`,
   `static/css/app.css`, `static/sw.js`, `app/blueprints/auth.py`.
   Qué se necesita: probarlo en un celular real (instalado como PWA) y
   ajustar si algo se ve o se comporta distinto que en desktop.

5. **Decidir el timeout de gunicorn en Render** (hallazgo de la sesión del
   2026-07-15, sin resolver a propósito).
   Qué: el default de gunicorn (30s, sin override en `render.yaml`) podría
   no alcanzar si varios archivos de una misma tanda pegan 503 de Gemini a
   la vez (el backoff aprobado ya suma ~14s de sleep por archivo, sin
   contar la duración real de las llamadas).
   Dónde: `render.yaml` (`startCommand`), detalle completo en
   `docs/decisions/0005-pantalla-espera-cold-start.md`.
   Qué se necesita: que el CEO decida si subir `--timeout` (ej. a 60s) o
   dejarlo así hasta ver si el caso se repite en uso real — no se tocó
   sin esa decisión.

## Deuda técnica / discusiones abiertas (no bloquean vender)
- Armar el set de casos de prueba del prompt (ADR-0007/0008 área Planillas)
  — necesita fotos/imágenes de referencia, no existe todavía.
- ADR-0003 área Planillas (pestañas por período) — sigue sin resolver el
  filtro por mes y las fórmulas de total anual.
- ADR-0010 área Planillas (columnas custom por cliente) — pregunta abierta,
  no decidir todavía.
- Confirmar en producción una foto real con impuestos discriminados (IVA,
  percepción o retención) — CAE, duda y duplicados ya confirmados.

## Post-MVP (no bloquea nada de lo de arriba)
- Guardar la imagen del comprobante en el Drive del cliente, en vez de
  descartarla. Carpeta y nombre ya definidos: `Facturas/{año}/{mes}/`,
  archivo `{fecha}_{proveedor}_{numero}.jpg`. Depende de: el resultado de un
  experimento aislado de OAuth con scope `drive.file` (fuera de este repo).
- Canal de WhatsApp del prototipo — decidido que NO va en el MVP.
- Mercado Pago suscripciones + landing page + dominio propio — postergados
  (ADR-0007), necesarios para escalar más allá de clientes conocidos.
- Upsell de facturas adicionales al superar el tope mensual — depende de
  que exista cobro online (ADR-0008).

## Blocked
- Nada bloqueado en este momento.

## Decisiones
- 2026-07-03: ADR-0001 stack, ADR-0002 user-owned storage, ADR-0003 price $1,999/250 facturas
- 2026-07-04: ADR-0004 — pivot a Service Account para Sheets + OAuth solo de identidad.
- 2026-07-04: WORKFLOW.md — el bloque Next de STATUS.md debe escribirse para alguien
  que no conoce el proyecto: pasos numerados, QUÉ/DÓNDE/QUÉ SE NECESITA.
- 2026-07-04: MVP sin persistencia de imagen.
- 2026-07-05: el canal de WhatsApp del prototipo NO va en el MVP — queda como post-MVP.
- 2026-07-06: deploy a Render (`facturas-saas.onrender.com`).
- 2026-07-06: Issue #001 diagnosticado por debug y resuelto — ver `docs/ISSUES.md`.
- 2026-07-06: nueva convención `docs/areas/{nombre}/` + `docs/ISSUES.md`. Primera área: planillas.
- 2026-07-06: ADR-0005 + ADR-0006 (área Planillas) — estructura v2 de la
  planilla (23 columnas), reemplaza la v1. Implementada el mismo día.
- 2026-07-06: README.md de la raíz reemplazado (contenido traído de `inbox/`).
- 2026-07-06: ADR-0007 (área Planillas) — corrige la regla de CAE del
  ADR-0005 tras el Issue #002 (falso positivo real en producción). "X" solo
  sin ninguna de las 4 vías de autorización (CAE, CAEA, CAI, controlador
  fiscal).
- 2026-07-06: ADR-0008 (área Planillas) — corrige el mecanismo de duda del
  ADR-0007: en vez de campo vacío + guardado bloqueado, la IA completa el
  campo con su mejor valor + lo marca "baja certeza" (rojo, sin bloqueo);
  avanzar/guardar es la confirmación implícita. Regla general para todo el
  formulario de revisión.
- 2026-07-07: documentado (no implementado): pantalla de espera propia para
  el cold start de Render con carrusel de mensajes (ADR-0005 repo general),
  UX de duplicados detectados sin bloquear el guardado (ADR-0009 área
  Planillas), reintentos ante 503 de Gemini (prioridad alta pre-lanzamiento)
  y política de acceso de soporte vía la Service Account (reflejar en
  términos de uso antes de lanzar) — ambos anotados en `docs/ROADMAP.md`.
- 2026-07-07: nueva área `docs/areas/app/` (diseño/UX de la app) — solo
  estructura y alcance, sin decisiones propias todavía.
- 2026-07-07: ADR-0009 (área Planillas) implementado — criterio de match de
  duplicados, versión final: `proveedor`+`numero`+`fecha` (no `cuit`+`numero`
  como decía el ADR-0002 originalmente). Se pasó primero por una versión
  intermedia con `cuit` en vez de `proveedor`, mal por Issue #003 (facturas
  en negro casi nunca tienen CUIT visible) — corregida el mismo día. Aviso
  no bloqueante en la tarjeta de revisión, también contra duplicados dentro
  de la misma tanda. Confirmado funcionando en producción.
- 2026-07-07: ADR-0006 (repo general) — modelo de organización por roles.
  Organigrama vivo en `docs/ORGANIGRAMA.md`, roles se crean con cada área
  nueva. CEO (Jordi) dirige sin ejecutar; CPO (Claude) encargado de las
  áreas App y Planillas.
- 2026-07-07: ADR-0007 (repo general) — MVP se lanza sin cobro online, sin
  landing y sin dominio propio (venta persona a persona, demo presencial,
  cobro manual). Esos 3 puntos pasan a postergados, no bloqueantes.
  Términos de uso mínimos pasan a ser el único bloqueante inmediato.
- 2026-07-07: ADR-0008 (repo general) — diseño funcional del tope de 250
  facturas/mes: contador en la DB de la app, avisos al acercarse al límite,
  corte al llegar al tope salvo pago de un plus (bloqueado hasta que exista
  cobro). MVP: solo contador + avisos, sin corte.
- 2026-07-07: ADR-0005 (repo general) ampliado — la pantalla de espera del
  cold start de Render también enmascara los reintentos automáticos ante
  503 de Gemini; pasa a prioridad alta pre-lanzamiento.
- 2026-07-07: ADR-0001 (área App, primera decisión propia) — rediseño del
  formulario de revisión: ocultar campos poco frecuentes salvo que tengan
  valor, grilla responsiva en desktop, procesamiento automático sin botón
  manual.
- 2026-07-07: foco del onboarding redefinido (`docs/areas/app/PRODUCTO.md`):
  no es un carrusel genérico, es el paso de configurar la planilla.
- 2026-07-07: ADR-0003 (área Planillas) recibe la idea de creación
  automática de pestaña por período — sigue sin resolver el resto.
- 2026-07-07: ADR-0010 (área Planillas, pregunta abierta) — qué hacer
  cuando un cliente pida una columna custom propia; reencuadra el punto de
  backlog que antes decía "migración v1→v2".
- 2026-07-11: ADR-0009 (repo general) — ningún texto visible de la app
  menciona IA/Gemini/modelo; se usa "nuestro sistema" o se describe la
  acción. Retroactivo (3 textos corregidos) y a futuro (carrusel, onboarding,
  emails).
- 2026-07-11: ADR-0002 (área App) — rediseño de la pantalla de inicio,
  sesión de diseño CEO+CPO: auto-procesamiento también ahí, texto de
  bienvenida sobre la dropzone, ancho máximo del contenido en desktop.
  Confirmado funcionando en navegador el mismo día.
- 2026-07-11: ADR-0003 (área App) — corrige la Decisión 4 del ADR-0002: el
  centro del header muestra el nombre real de la planilla conectada (link,
  leído una vez al conectar, no en cada visita) o "Conectá tu planilla" sin
  conexión, más el email de la cuenta logueada. Nuevo campo
  `User.spreadsheet_title` con auto-migración liviana (sin Alembic).
  Confirmado funcionando en navegador el mismo día.
- 2026-07-11: ADR-0004 (área App) — archivo de tips editable
  (`strings/tips.txt`) sin tocar código, uno rotando en la home cada 9s;
  saludo + texto de entrada agrandado + pedido de feedback arriba de la
  dropzone. Regla 2 del ADR-0009 general: sin dos puntos en textos nuevos
  (no retroactiva). Confirmado funcionando en navegador el mismo día, tras
  ajustar el bloque de texto a centrado con tipografía uniforme entre
  saludo y entrada, y subir el contraste del borde de la dropzone.
- 2026-07-11: texto de entrada reescrito de nuevo ("Gracias por probar
  nuestra aplicación" + objetivo de la app) reemplazando el saludo por
  separado; se agregó un contador `N/200` discreto en el header, siempre
  visible (no solo el aviso al acercarse al límite).
- 2026-07-11: ADR-0008 corregido dos veces más el mismo día — límite bajado
  de 250 a 200 (aviso a 160, ambas constantes en
  `app/services/limites.py`), y confirmado que el ciclo por fecha de alta
  ya manejaba bien los meses cortos (alta 31/01 corta el 28/02 en año no
  bisiesto, 29/02 en bisiesto) sin necesitar cambios de código.
- 2026-07-11: Issue #004 (`docs/ISSUES.md`) — el contador y el aviso del
  tope mensual no se actualizaban en el navegador tras guardar una factura
  (se renderizaban una sola vez del lado del servidor). Corregido:
  `GET /api/invoices` ahora también devuelve el conteo, y el frontend lo
  actualiza cada vez que se vuelve a la home.
- 2026-07-11: Issue #005 (`docs/ISSUES.md`) + ADR-0010 (repo general) — la
  misma foto de factura podía dar datos distintos entre extracciones
  porque Gemini no tenía fijada la `temperature`. Se fija en 0
  (`app/services/gemini.py`) para una lectura consistente.
- 2026-07-11: onboarding de conexión de planilla reordenado a 3 pasos
  (copiar email → crear/compartir → pegar link), con textos explicados a
  pedido del founder (ADR-0005 área App, ver `docs/areas/app/decisions/`).
- 2026-07-11: ADR-0005 (área App) corregido el mismo día — el título de la
  planilla nueva ya no se sugiere por email; el cliente escribe un nombre
  en blanco y el sistema le agrega el año automáticamente.
- 2026-07-11: ADR-0003 (área Planillas) redefinido — en vez de crear
  pestañas de forma perezosa (idea de 2026-07-07), ahora se crean las 12
  pestañas del ciclo anual todas juntas al conectar por primera vez.
  Alcance acotado: solo crea las pestañas, no cambia dónde se guardan/leen
  las facturas (sigue siendo `sheet1`).
- 2026-07-11: Issue #006 (`docs/ISSUES.md`) — crear las 12 pestañas de a
  una (con todo su formato) superaba la cuota de escritura por minuto de
  la API de Sheets, confirmado fallando contra la planilla de referencia.
  Resuelto agrupando todo en 2 llamadas a la API en vez de ~80
  (`batch_update` + `values_batch_update`).
- 2026-07-12: ADR-0003 (área Planillas) ajustado varias veces — de "12
  pestañas mensuales de una" (2026-07-11) a "una mensual por vez", a "una
  sola pestaña por año calendario" (ej. "2026"). `meses_del_ciclo_anual()`
  y `nombre_pestana()` se sacaron del código por quedar sin uso.
- 2026-07-12: ADR-0003 (área Planillas) — **cerrado el alcance acotado**:
  `append_invoice`/`list_invoices`/`find_duplicate` pasan de usar
  `sheet1` ("Hoja 1") a usar la pestaña del año real (por defecto, el año
  actual). El founder encontró esto probando una factura real y lo marcó
  como problema — quedó resuelto y probado contra la API real de Sheets.
  Los datos ya cargados en "Hoja 1" quedan intactos pero sin uso, sin
  migración (confirmado que no hace falta en etapa de desarrollo).
- 2026-07-12: ADR-0011 (repo general) — se crea `docs/FEATURES.md`,
  catálogo vivo e interno de features del producto (no lo lee el
  cliente), del que se derivan pitches de venta y estrategia de
  marketing. Cada feature tiene una ficha de tags (online, estado, área,
  ADRs, precio posible, costo, plan, origen, fechas, dependencias,
  métrica de éxito) más explicación llana y detalle técnico. Primera
  entrada: carga de facturas por foto (online). Segunda: "Reportes al
  contador" (idea, sin especificar). Mantenedor: Claude 1 (CPO), con
  aprobación del CEO.
- 2026-07-12: modelo de nombres y roles formalizado en
  `docs/ORGANIGRAMA.md` — los integrantes IA tienen nombre propio
  separado del rol (el Claude que ocupa el cargo de CPO se llama "Claude
  1"). Roles futuros pueden ocuparlos Claudes nuevos ("Claude 2", etc.),
  cada uno su propio espacio de trabajo/contexto. `README.md` actualizado
  con la misma referencia y una fila nueva para `docs/FEATURES.md` en la
  tabla de documentación.
- 2026-07-14: ADR-0006 (área App) — rediseño del flujo de guardado: botón
  único para toda la tanda, cruz de descartar más visible por tarjeta,
  cuenta regresiva de 3s con redirección automática a la home (se saca
  "Volver"), manejo de falla parcial (reintentar o descartar la tarjeta
  fallida). Corregido el mismo día: la cuenta regresiva no cambia de
  pantalla, reemplaza al botón único en su lugar (las tarjetas guardadas
  siguen visibles). Implementado y probado con simulación de DOM real;
  pendiente confirmación en navegador real por el founder.
- 2026-07-14: ADR-0009 (repo general) — Regla 2 aclarada: no prohíbe el
  ":" en todo texto visible, aplica a párrafos/textos corridos; queda como
  criterio, no como regla mecánica. Ante la duda, consultar al CEO.
- 2026-07-15: ADR-0004 área App, Decisión E (handoff del CEO) — rediseño
  visual del tip rotativo de la home: tarjeta con fondo celeste, bordes
  redondeados, texto más grande/oscuro e ícono de lamparita. Solo
  CSS/HTML, `static/js/app.js` sin tocar. Probado con Playwright/Chromium
  contra el HTML real de `/app`, desktop y mobile. Pendiente confirmación
  en celular real.
- 2026-07-15: ADR-0007 área App (handoff del CEO) — carrusel "consejos de
  revisión" en la pantalla de revisión de facturas, arriba de las
  tarjetas, réplica del estilo del tip de home (mismas clases CSS, sin
  tocar `static/css/app.css`) y misma mecánica de rotación
  (`static/js/app.js` refactorizado en una función reutilizable, sin
  cambiar timings). Textos propios en `strings/consejos-revision.txt` (6
  exactos del handoff). Probado con Playwright/Chromium con 1 y 3
  tarjetas, desktop y mobile: sin overflow, ambos carruseles rotan
  independiente, tip de home intacto. Pendiente confirmación en celular
  real.
- 2026-07-15: ADR-0005 (repo general, handoff del CEO tras un 503 real)
  — implementado de punta a punta: reintentos 3×2/4/8s ante 503 de Gemini
  (`app/services/gemini.py`, `GeminiSobrecargadoError` con el mensaje
  final exacto), overlay de espera con spinner + tercer carrusel
  (`strings/mensajes-espera.txt`) reemplazando `#cargando`, service
  worker cacheando el app shell completo (`static/espera.html` nuevo)
  para el cold start. Probado contra un servidor Flask real con
  Playwright: reintentos mockeados, overlay, mensaje de error exacto,
  reintento manual, 3 carruseles independientes, y el fallback del
  service worker ante una navegación lenta. **Hallazgo reportado sin
  resolver**: el timeout default de gunicorn (30s) podría no alcanzar en
  el peor caso de una tanda con varios 503 — pendiente de decisión del
  CEO, no se tocó `render.yaml`.
- 2026-07-15: ADR-0012 (repo general, handoff del CEO) — sesión de Flask
  permanente (90 días de inactividad, renovable) +
  `SESSION_REFRESH_EACH_REQUEST` + cookie con `HttpOnly`/`SameSite=Lax`/
  `Secure` en producción; se saca `prompt="consent"` del login de Google y
  se fuerza `access_type="online"` explícito (la librería lo ponía en
  "offline" por default). Resuelve el reporte del CEO desde el celular:
  re-login, pantalla de permisos y mail de Google repetidos en cada
  visita. `SECRET_KEY` en Render confirmado estable entre deploys (no
  hizo falta cambiarlo). Pendiente de confirmación real (Google, Render,
  celular con PWA instalada) — ver detalle en el ADR.
- 2026-07-16: ADR-0013 (repo general, handoff del CEO) — keep-alive para
  Render free tier: endpoint `GET /health` estático +
  `.github/workflows/keep-alive.yml` con cron cada 14 minutos 24/7.
  Complementa (no reemplaza) el ADR-0005. Probado `/health` en local;
  pendiente de confirmación real en producción y GitHub Actions.
- 2026-07-16: Issue #007 (handoff del CEO, diagnóstico) — el keep-alive
  no cumplía su función: GitHub Actions no ejecuta `schedule` con
  precisión para crons sub-horarios (gaps reales de ~100 min con `*/14`,
  confirmado vía `gh run list`). Causa de la plataforma, no de
  configuración. Fix: cron a `*/10` (decisión del CEO) + `--fail` al
  curl. Riesgo señalado sin resolver con garantía — si los gaps siguen
  superando ~15 min, hace falta una alternativa (decisión del CEO).
- 2026-07-16: Issue #007 cerrado (handoff del CEO) — el fix de `*/10` no
  alcanzó, cold start real confirmado después del ajuste. GitHub Actions
  descartado como mecanismo de keep-alive; `.github/workflows/keep-alive.yml`
  eliminado. Reemplazado por UptimeRobot (monitor HTTP cada 5 min contra
  `/health`), configurado por el CEO fuera del repo, sin rastro en el
  código. El endpoint `/health` y el ADR-0005 (pantalla de espera) se
  mantienen sin cambios.
- 2026-07-16: ADR-0014 (repo general, handoff del CEO) — instrumentación
  de tiempos por etapa en `/api/extract` y `/api/invoices` (recepción,
  llamada a Gemini con reintentos, chequeo de duplicados, escritura en
  Sheets), sesión de solo medición, sin optimizar nada. Flag
  `LOG_TIEMPOS` default activado incluso en producción (decisión del
  CEO). Logger propio sin propagar al root logger, sin datos sensibles
  del comprobante. Probado con mocks (Flask test client); pendiente
  confirmar en logs reales de Render. Modelo de Gemini configurado hoy:
  `gemini-2.5-flash`. Observación de optimización sin implementar:
  `asegurar_pestana_del_anio()` pega a la API de Sheets en cada guardado
  incluso cuando la pestaña ya existe.
  mantienen sin cambios.
