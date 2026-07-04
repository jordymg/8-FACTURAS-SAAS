# STATUS

## Current phase
Phase 1 — flujo completo probado en local. Falta deploy a producción.

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
- Imagen del comprobante: se sigue guardando (no se sacó), pero interinamente en disco
  local del servidor (`app/services/storage.py`), una carpeta por usuario, nombre único
  por archivo. Pendiente decidir el storage definitivo antes de producción.
- **Probado end-to-end en local con cuenta real**: login → conectar planilla → subir foto
  → extracción con Gemini → revisar → guardar → fila aparece en el Google Sheet real.

## Next
1. **Decidir dónde se va a guardar la imagen de cada comprobante, antes de deployar.**
   Qué: elegir entre (a) subirla al Google Drive del propio usuario, o (b) guardarla en
   un storage propio (Cloudflare R2 o AWS S3).
   Dónde: la lógica vive en `app/services/storage.py` — hoy guarda en el disco del
   servidor, que en Render (plan free) se borra en cada redeploy o reinicio.
   Qué se necesita: si se elige Drive, hay que agregar de nuevo el scope OAuth
   `drive.file` en `app/blueprints/auth.py` (puede requerir verificación de Google —
   la misma fricción que motivó el pivot de hoy). Si se elige S3/R2, hay que crear una
   cuenta y conseguir las credenciales (Access Key/Secret) para ponerlas en `.env`.

2. **Deployar la app a Render y probar el flujo ahí, no solo en local.**
   Qué: publicar el servicio usando el `render.yaml` que ya está en el repo, y cargar
   en el dashboard de Render las variables de entorno reales (`GEMINI_API_KEY`,
   `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, y la Service Account).
   Dónde: dashboard de Render (render.com), conectando el repo de GitHub.
   Qué se necesita: (a) tener resuelto el punto 1, porque el disco free de Render es
   efímero; (b) agregar la URL pública de Render como redirect URI autorizado en
   Google Cloud Console, para el mismo client OAuth que se usa hoy.

3. **Decidir si se retoma el canal de WhatsApp del prototipo.**
   Qué: el archivo `app.py` original (webhook de Twilio) no se integró a este repo,
   quedó en pausa tal como estaba en el prototipo.
   Dónde: no existe en el repo actual — solo queda documentado acá y en el ADR-0004.
   Qué se necesita: una cuenta de Twilio (Account SID + Auth Token) y decidir si tiene
   sentido antes o después de tener los primeros clientes pagando por la interfaz web.

## Blocked
- Nada bloqueado en este momento — Gemini y Sheets funcionando con las credenciales del
  prototipo (créditos y permisos OK).

## Decisiones
- 2026-07-03: ADR-0001 stack, ADR-0002 user-owned storage, ADR-0003 price $1,999/250 facturas
- 2026-07-04: SDK google-generativeai deprecado → migrado a google-genai>=1.0
- 2026-07-04: ADR-0004 — pivot a Service Account para Sheets + OAuth solo de identidad,
  tras bloquearse el flujo anterior con `redirect_uri_mismatch`. Se integró el prototipo
  funcional del founder (prompt, campos, UI de tarjetas). Storage de imagen queda abierto.
