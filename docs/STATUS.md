# STATUS

## Current phase
Phase 1 — flujo completo probado en local, sin persistencia de imagen (decisión MVP).
Falta deploy a producción.

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

## Next
1. **Deployar la app a Render y probar el flujo ahí, no solo en local.**
   Qué: publicar el servicio usando el `render.yaml` que ya está en el repo, y cargar
   en el dashboard de Render las variables de entorno reales (`GEMINI_API_KEY`,
   `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, y la Service Account).
   Dónde: dashboard de Render (render.com), conectando el repo de GitHub.
   Qué se necesita: agregar la URL pública de Render como redirect URI autorizado en
   Google Cloud Console, para el mismo client OAuth que se usa hoy. Ya no depende de
   resolver el storage de imagen (se sacó de este alcance, ver Done).

2. **Decidir si se retoma el canal de WhatsApp del prototipo.**
   Qué: el archivo `app.py` original (webhook de Twilio) no se integró a este repo,
   quedó en pausa tal como estaba en el prototipo.
   Dónde: no existe en el repo actual — solo queda documentado acá y en el ADR-0004.
   Qué se necesita: una cuenta de Twilio (Account SID + Auth Token) y decidir si tiene
   sentido antes o después de tener los primeros clientes pagando por la interfaz web.

## Post-MVP (no bloquea nada de lo de arriba)
- Guardar la imagen del comprobante en el Drive del cliente, en vez de descartarla.
  Carpeta y nombre ya definidos: `Facturas/{año}/{mes}/`, archivo
  `{fecha}_{proveedor}_{numero}.jpg`. Depende de: el resultado de un experimento
  aislado de OAuth con scope `drive.file` que se está probando fuera de este repo
  (por la fricción de `redirect_uri_mismatch` que tuvimos hoy con OAuth). Cuando
  funcione ahí, se porta el código a `app/services/` (el módulo `storage.py` que
  hacía esto se borró — hay que recrearlo) + se agrega el scope en
  `app/blueprints/auth.py` + un campo nuevo en `app/models.py` para el token de Drive.

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
