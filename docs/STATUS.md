# STATUS

## Current phase
Phase 1 — deployado en Render (`https://facturas-saas.onrender.com`) y probado con
un usuario real. Se encontró y arregló un bug de datos (Issue #001, ver
`docs/ISSUES.md`) durante esa prueba.

## Done
- Pivot de arquitectura: se integró el prototipo funcional del founder (carpeta `inbox/`,
  ya limpiada) — ver ADR-0004. Sheets se escriben con una Service Account en vez de
  OAuth por usuario; el login de Google pasa a pedir solo identidad (openid + email).
- Campos de la planilla actualizados a los 9 validados por el founder: fecha, proveedor,
  cuit, tipo, numero, neto, iva, total, moneda — definidos en `app/services/fields.py`.
- Prompt de extracción y `response_schema` estructurado de Gemini adoptados del prototipo.
- Pantalla nueva `/app/config`: el usuario ve el email de la Service Account, comparte su
  planilla como Editor, pega la URL/ID y la app valida el acceso.
- UI de captura multi-archivo (drag&drop) + tarjetas de revisión editables por comprobante,
  con reintentar-con-IA y guardado individual — igual que el prototipo validado.
- **Probado end-to-end en local con cuenta real**: login → conectar planilla → subir foto
  → extracción con Gemini → revisar → guardar → fila aparece en el Google Sheet real.
- Revisión de código del pivot: 6 hallazgos corregidos (commit `12507eb`) — el más
  importante era que conectar una planilla nueva vacía convertía la primera factura
  guardada en el encabezado, desordenando todo lo que seguía. También: error claro si
  falta la key de Gemini, validación visual del campo moneda, y unificación de tipos
  MIME en `app/services/formats.py`.
- **Decisión MVP sin persistencia de imagen**: se saca el guardado de la imagen del
  comprobante de este alcance — ni disco local, ni Drive, ni S3/R2. La foto se usa
  solo en memoria para mandarla a Gemini y se descarta apenas vuelve la respuesta de
  extracción. Se eliminó `app/services/storage.py`, el mecanismo `img_token`/`_pending`
  que existía para eso, y las imágenes de prueba que habían quedado en disco. Motivo:
  destrabar el deploy a Render ya, sin esperar a resolver dónde va a vivir la imagen
  en producción. La columna `imagen` de la planilla queda siempre vacía por ahora.
  El diseño de la carpeta/nombre para cuando se resuelva (Drive del cliente, post-MVP)
  ya está definido: `Facturas/{año}/{mes}/`, archivo `{fecha}_{proveedor}_{numero}.jpg`.
- **Deploy a Render**: la app está publicada en `https://facturas-saas.onrender.com`.
  Se agregaron dos fixes necesarios para que funcionara ahí (no hacían falta en local):
  `psycopg2-binary` en `requirements.txt` (faltaba el driver de Postgres — en local
  siempre se usó SQLite) y `ProxyFix` en `app/__init__.py` (sin esto, el login de
  Google fallaba porque Flask veía el request como http, no https, detrás del proxy
  de Render).
- **Issue #001 resuelto**: al probar con un usuario nuevo real en producción, las
  facturas 2 y 3 se guardaron desencolumnadas en el Sheet. Diagnosticado por debug
  (no se aplicó ningún fix a ciegas) y confirmado con reproducción controlada: eran
  dos bugs encadenados en `app/services/sheets.py` (ver detalle completo en
  `docs/ISSUES.md` #001). Ya arreglado y verificado.

## Next
1. **Confirmar el fix del Issue #001 en producción.**
   Qué: repetir la prueba real (usuario nuevo, planilla nueva, 3+ facturas seguidas)
   contra `https://facturas-saas.onrender.com` para confirmar que ya no se
   desencolumnan.
   Dónde: la app pública de Render, una vez que este fix esté pusheado y Render haya
   redeployado solo.
   Qué se necesita: nada más que probarlo — el fix ya está commiteado.

2. **Corregir las filas ya desencolumnadas en la planilla real de producción.**
   Qué: la planilla nueva que se usó para probar el deploy tiene ahora mismo 2 filas
   mal encolumnadas (facturas 2 y 3 de esa prueba).
   Dónde: esa planilla de Google Sheets (no la vieja `Facturas Proveedores - bot` que
   se usó como referencia para diagnosticar el bug).
   Qué se necesita: que el founder pase la URL/ID de esa planilla puntual para
   corregir las filas (a mano o por script) — no se tocó ninguna planilla de
   producción sin permiso.

## Post-MVP (no bloquea nada de lo de arriba)
- Guardar la imagen del comprobante en el Drive del cliente, en vez de descartarla.
  Carpeta y nombre ya definidos: `Facturas/{año}/{mes}/`, archivo
  `{fecha}_{proveedor}_{numero}.jpg`. Depende de: el resultado de un experimento
  aislado de OAuth con scope `drive.file` que se está probando fuera de este repo
  (por la fricción de `redirect_uri_mismatch` que tuvimos con OAuth). Cuando
  funcione ahí, se porta el código a `app/services/` (el módulo `storage.py` que
  hacía esto se borró — hay que recrearlo) + se agrega el scope en
  `app/blueprints/auth.py` + un campo nuevo en `app/models.py` para el token de Drive.
- Canal de WhatsApp (`app.py` del prototipo, webhook de Twilio). Decidido que NO va
  en el MVP. No se integró a este repo, queda solo documentado acá y en el ADR-0004.
  Si se retoma más adelante, necesita una cuenta de Twilio (Account SID + Auth Token).

## Blocked
- Nada bloqueado en este momento — Gemini y Sheets funcionando con las credenciales del
  prototipo (créditos y permisos OK).

## Decisiones
- 2026-07-03: ADR-0001 stack, ADR-0002 user-owned storage, ADR-0003 price $1,999/250 facturas
- 2026-07-04: SDK google-generativeai deprecado → migrado a google-genai>=1.0
- 2026-07-04: ADR-0004 — pivot a Service Account para Sheets + OAuth solo de identidad,
  tras bloquearse el flujo anterior con `redirect_uri_mismatch`. Se integró el prototipo
  funcional del founder (prompt, campos, UI de tarjetas).
- 2026-07-04: WORKFLOW.md — el bloque Next de STATUS.md debe escribirse para alguien
  que no conoce el proyecto: pasos numerados, QUÉ/DÓNDE/QUÉ SE NECESITA.
- 2026-07-04: MVP sin persistencia de imagen — se saca del alcance guardar la foto
  (ni disco, ni Drive, ni S3), para destrabar el deploy a Render sin depender de esa
  decisión. Guardarla en el Drive del cliente queda como post-MVP.
- 2026-07-05: el canal de WhatsApp del prototipo NO va en el MVP — queda como post-MVP.
- 2026-07-06: deploy a Render (`facturas-saas.onrender.com`), con fixes de
  `psycopg2-binary` y `ProxyFix` necesarios solo en producción.
- 2026-07-06: Issue #001 diagnosticado por debug (no a ciegas) y resuelto — ver
  `docs/ISSUES.md`. Causa: `get_all_values()` devuelve `[[]]` (truthy) en una
  planilla vacía, lo que saltaba la escritura del encabezado; sin encabezado, la
  API de Sheets adivinaba mal dónde escribir la fila siguiente. Se dejó de usar
  `append_row` (que le pide a Sheets adivinar) por escritura a rango explícito.
- 2026-07-06: nueva convención en `docs/areas/{nombre}/` para unidades de I+D por
  producto (README + PRODUCTO.md + STATUS.md + decisions/), y `docs/ISSUES.md` como
  log de problemas que tocaron datos reales o sorprendieron (criterio documentado
  ahí). Primera área: planillas.
