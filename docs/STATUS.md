# STATUS

## Current phase
Phase 1 — flujo completo probado en local. Storage de imagen definitiva en experimento
aparte. Falta deploy a producción.

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
  guardada en el encabezado, desordenando todo lo que seguía. También: aislamiento de
  imágenes pendientes por usuario, error claro si falta la key de Gemini, validación
  visual del campo moneda, y unificación de tipos MIME en `app/services/formats.py`.
- Decisión sobre la imagen del comprobante: se define guardarla en el **Drive del propio
  cliente** (no en disco local ni S3/R2), organizada en `Facturas/{año}/{mes}/` con
  nombre de archivo `{fecha}_{proveedor}_{numero}.jpg`. Como esto requiere volver a
  pedir un scope OAuth (`drive.file`) y el founder quiere evitar repetir la fricción de
  OAuth de hoy, se decidió probarlo primero en un experimento aislado, fuera de este
  repo, con otra IA — se le dio un prompt autocontenido con el contexto necesario
  (incluyendo los errores de `redirect_uri_mismatch` de hoy) para que lo pruebe sin
  arriesgar este proyecto. Mientras tanto sigue en disco local del servidor
  (`app/services/storage.py`), interino.

## Next
1. **Cuando el experimento aislado de Drive OAuth funcione, traerlo a este proyecto.**
   Qué: reemplazar el guardado en disco local por subida al Drive del cliente, con la
   estructura `Facturas/{año}/{mes}/` y el nombre `{fecha}_{proveedor}_{numero}.jpg`
   ya definidos — no hace falta redecidir esto, solo portar el código que funcione.
   Dónde: `app/services/storage.py` (la interfaz ya existe, solo cambia la
   implementación), `app/blueprints/auth.py` (agregar el scope `drive.file` al login),
   `app/models.py` (agregar de nuevo un campo para guardar el token de Drive del
   usuario, esta vez solo para Drive, no para Sheets).
   Qué se necesita: el resultado del experimento aislado (código + pasos exactos de
   Google Cloud Console que hayan funcionado ahí).

2. **Deployar la app a Render y probar el flujo ahí, no solo en local.**
   Qué: publicar el servicio usando el `render.yaml` que ya está en el repo, y cargar
   en el dashboard de Render las variables de entorno reales (`GEMINI_API_KEY`,
   `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, y la Service Account).
   Dónde: dashboard de Render (render.com), conectando el repo de GitHub.
   Qué se necesita: (a) tener resuelto el punto 1 (mientras la imagen se guarde en
   disco local, se pierde en cada redeploy del plan free de Render); (b) agregar la
   URL pública de Render como redirect URI autorizado en Google Cloud Console, para
   el mismo client OAuth que se usa hoy.

3. **Decidir si se retoma el canal de WhatsApp del prototipo.**
   Qué: el archivo `app.py` original (webhook de Twilio) no se integró a este repo,
   quedó en pausa tal como estaba en el prototipo.
   Dónde: no existe en el repo actual — solo queda documentado acá y en el ADR-0004.
   Qué se necesita: una cuenta de Twilio (Account SID + Auth Token) y decidir si tiene
   sentido antes o después de tener los primeros clientes pagando por la interfaz web.

## Blocked
- Nada bloqueado en este momento — Gemini y Sheets funcionando con las credenciales del
  prototipo (créditos y permisos OK). El único punto en pausa (imagen en Drive) está
  en experimento aparte, no bloquea seguir usando la app tal como está hoy.

## Decisiones
- 2026-07-03: ADR-0001 stack, ADR-0002 user-owned storage, ADR-0003 price $1,999/250 facturas
- 2026-07-04: SDK google-generativeai deprecado → migrado a google-genai>=1.0
- 2026-07-04: ADR-0004 — pivot a Service Account para Sheets + OAuth solo de identidad,
  tras bloquearse el flujo anterior con `redirect_uri_mismatch`. Se integró el prototipo
  funcional del founder (prompt, campos, UI de tarjetas).
- 2026-07-04: la imagen del comprobante va al Drive del cliente (estructura
  `Facturas/{año}/{mes}/`, nombre `{fecha}_{proveedor}_{numero}.jpg`), pero se prueba
  primero en un experimento aislado fuera de este repo por la fricción de OAuth de hoy.
- 2026-07-04: WORKFLOW.md — el bloque Next de STATUS.md debe escribirse para alguien
  que no conoce el proyecto: pasos numerados, QUÉ/DÓNDE/QUÉ SE NECESITA.
