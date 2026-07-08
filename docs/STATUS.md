# STATUS

## Current phase
Phase 1 en producción (`https://facturas-saas.onrender.com`), planilla v2
(23 columnas) confirmada con datos reales. **Re-priorizado el camino a
vender** (ADR-0007 repo general): el MVP sale a la calle sin cobro online,
sin landing y sin dominio propio — venta persona a persona a conocidos, demo
presencial, cobro manual. Checklist real de "antes de vender" en
`docs/ROADMAP.md`.

**Arrancar la próxima sesión por acá**: ADR-0001 (área App, rediseño del
formulario) está implementado en código (2026-07-07, sin commitear) pero el
founder probó en local y no vio ningún cambio — sin diagnosticar todavía,
hipótesis principal caché del navegador. Ver
`docs/areas/app/decisions/0001-rediseno-formulario-revision.md` (nota
2026-07-08) y `docs/areas/app/STATUS.md`.

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

5. **Rediseño del formulario de revisión** (ADR-0001 área App): ocultar
   campos poco frecuentes salvo que tengan valor, grilla responsiva en
   desktop, procesamiento automático sin botón manual.
   Dónde: `templates/app.html`, `static/js/app.js`, `static/css/app.css`.
   Qué se necesita: implementar — probarlo en el celular junto con esto.

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
