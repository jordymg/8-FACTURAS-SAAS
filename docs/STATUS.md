# STATUS

## Configuración rápida (constantes que se tocan seguido)
- **Tope de facturas mensual**: `LIMITE_MENSUAL` y `UMBRAL_AVISO` en
  `app/services/limites.py`. Detalle completo en
  `docs/decisions/0008-tope-facturas-mensual.md`.
- **Extracción de Gemini**: modelo y `temperature` en
  `app/services/gemini.py`. Detalle en
  `docs/decisions/0010-extraccion-determinista-temperature-cero.md`.
- **Server local: puerto 5050, no 5000** — el redirect_uri de OAuth
  registrado en Google Cloud Console es `http://localhost:5050/oauth2callback`
  (descubierto el 2026-07-12 tras un rato de debug). Levantar con
  `python -m flask --app wsgi run --debug --port 5050`, y entrar por
  `http://localhost:5050` (con `localhost`, no `127.0.0.1` — Google los
  trata como hosts distintos).

## Current phase
Phase 1 en producción (`https://facturas-saas.onrender.com`), planilla v2
(23 columnas) confirmada con datos reales. **Re-priorizado el camino a
vender** (ADR-0007 repo general): el MVP sale a la calle sin cobro online,
sin landing y sin dominio propio — venta persona a persona a conocidos, demo
presencial, cobro manual. Checklist real de "antes de vender" en
`docs/ROADMAP.md`.

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
- **Documentado, sin implementar** (queda para cuando se priorice):
  - `docs/decisions/0005-pantalla-espera-cold-start.md` (repo general, no
    confundir con el ADR-0005 del área Planillas): pantalla propia con
    carrusel de mensajes mientras Render despierta del cold start,
    complementaria al upgrade de plan pago (ADR-0001).
  - `docs/ROADMAP.md`: reintentos automáticos ante 503 de Gemini + mensaje
    de error amigable, marcado prioridad alta pre-lanzamiento (Fase 2); y
    política de acceso de soporte (la Service Account ya tiene acceso
    Editor a las planillas — reflejarlo en los términos de uso antes de
    lanzar, Fase 3), con la idea de una vista de solo-lectura como
    alternativa post-MVP anotada en el icebox.
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
  tips. Pasa a prioridad alta pre-lanzamiento. No implementado todavía.
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

2. **Reintentos automáticos ante 503 de Gemini, con espera invisible.**
   Qué: reintentar solo, mostrando la pantalla de espera con carrusel
   (ADR-0005 repo general) en vez de un mensaje de error — recién si se
   agotan los reintentos, error amigable.
   Dónde: `app/services/gemini.py` (backend) + `static/js/app.js`,
   `templates/app.html` (frontend, ver ADR-0005).
   Qué se necesita: implementar — documentado, no hecho.

3. **Onboarding de configuración de planilla.**
   Qué: guiar "a prueba de tontos" el paso de crear la planilla, compartirla
   con la SA, y pegar la URL.
   Dónde: `docs/areas/app/` — necesita antes una conversación de diseño
   dedicada para los textos/pasos concretos.
   Qué se necesita: esa conversación de diseño, después implementar.

4. **Tope de 250 facturas/mes, versión soft (sin corte).**
   Qué: contador en la DB + aviso al acercarse al límite (ej. 200).
   Dónde: `app/models.py::User.invoices_this_month` (ya existe el campo),
   diseño funcional completo en `docs/decisions/0008-tope-facturas-mensual.md`.
   Qué se necesita: implementar el aviso en la UI y definir el reset
   mensual del contador (no diseñado todavía).

5. **Probar en el celular** el rediseño del formulario y de la pantalla de
   inicio (ADR-0001, ADR-0002, ADR-0003 área App) — ya confirmado
   funcionando en navegador desktop, falta mobile real.
   Dónde: `templates/app.html`, `static/js/app.js`, `static/css/app.css`.
   Qué se necesita: probarlo en un celular real y ajustar si algo se ve mal.

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
