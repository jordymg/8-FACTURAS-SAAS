# STATUS

## Current phase
Phase 1 — en producción (`https://facturas-saas.onrender.com`). La planilla
pasó de v1 (9 columnas) a **v2 (23 columnas)**, alineada a categorías
impositivas reales de un libro de compras argentino. Falta confirmar la
extracción con una foto real usando el prompt nuevo.

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
  de autorización (CAE, CAEA, CAI, controlador fiscal), y se agrega un
  **principio de duda general**: si la IA no está segura de un campo, lo
  deja vacío en vez de arriesgar un valor, y el formulario lo resalta en
  rojo hasta que el usuario lo complete (nueva clase `campo-en-duda`).
  Probado con una imagen ambigua antes de dar por bueno. Ver
  `docs/ISSUES.md` #002.
- Reconectar una planilla ya creada (vía `/app/config`, pegando la misma
  URL/ID de nuevo) reescribe el encabezado a la estructura vigente — sirve
  para llevar una planilla vieja (v1) a la v2 sin tocar código. Las filas de
  datos ya cargadas con la v1 no se migran solas: quedan desalineadas contra
  el nuevo encabezado si las hay.
- README.md de la raíz reemplazado por una versión más completa (trae de
  `inbox/`) — explica el producto, cómo se trabaja el repo (ADRs, áreas de
  I+D, `docs/ISSUES.md`) y linkea toda la documentación. Todos los links
  relativos a `/docs` verificados.

## Next
1. **Probar la extracción v2 con una foto real en producción.**
   Qué: subir una factura real (con al menos un impuesto discriminado —
   IVA, percepción o retención) y confirmar que el prompt nuevo de Gemini la
   lee bien, incluida la regla corregida de CAE/duda (ADR-0007): "X" solo
   sin ninguna de las 4 vías de autorización, y campo vacío + rojo cuando
   la IA no está segura.
   Dónde: `https://facturas-saas.onrender.com`.
   Qué se necesita: nada más que probarlo — el código ya está pusheado.

2. **Armar el set de casos de prueba del prompt** que pide el ADR-0007
   (factura electrónica A/B/C, ticket consumidor final, tique-factura A,
   comprobante con CAI, presupuesto sin autorización).
   Qué: fotos o imágenes de referencia de cada caso, para validar la regla
   de CAE/duda cada vez que se cambie el prompt.
   Dónde: no existe todavía, a definir dónde guardarlo (¿`docs/areas/planillas/`?).
   Qué se necesita: conseguir/armar los comprobantes de ejemplo.

3. **Evaluar el formulario de revisión con ~20 campos por tarjeta.**
   Qué: hoy es una lista larga sin agrupar por secciones (todos los campos
   uno debajo del otro). Confirmar si es cómodo de usar en el celular o si
   conviene agruparlo (ej. datos generales / impuestos / totales).
   Dónde: `templates/app.html` + `static/js/app.js`.
   Qué se necesita: probarlo primero en el celular; si molesta, se rediseña.

4. **Retomar el ADR-0003 (pestañas por período)** del área Planillas: cómo
   se pasa de un período a otro, y qué pasa con el filtro por mes y las
   fórmulas de total anual (ADR-0002) si los datos quedan repartidos en
   varias pestañas.

## Post-MVP (no bloquea nada de lo de arriba)
- Guardar la imagen del comprobante en el Drive del cliente, en vez de
  descartarla. Carpeta y nombre ya definidos: `Facturas/{año}/{mes}/`,
  archivo `{fecha}_{proveedor}_{numero}.jpg`. Depende de: el resultado de un
  experimento aislado de OAuth con scope `drive.file` (fuera de este repo).
- Canal de WhatsApp del prototipo — decidido que NO va en el MVP.

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
  fiscal); nuevo principio de duda general para todo el formulario de
  revisión.
