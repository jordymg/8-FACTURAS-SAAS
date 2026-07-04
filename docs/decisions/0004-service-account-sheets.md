# ADR-0004: Service Account para Sheets, OAuth solo para login

**Date:** 2026-07-04
**Status:** Accepted — supersedes parte de ADR-0002 (mecanismo de acceso a Sheets)

## Contexto
El scaffold original pedía scopes `spreadsheets` + `drive.file` por usuario vía OAuth
para crear y escribir en su propio Sheet/Drive. En la práctica esto quedó bloqueado
por un `redirect_uri_mismatch` y por la fricción de verificación de Google para scopes
sensibles. El founder ya tenía un prototipo funcional (carpeta `inbox/`) validado con
usuarios reales que resuelve esto con otra estrategia: una Service Account (SA)
centralizada escribe en la planilla del usuario, que la comparte como Editor una sola vez.

## Decisión
- **Sheets**: la app escribe con una Service Account (`gspread` + credenciales de SA).
  El usuario comparte su planilla con el email de la SA; el `spreadsheet_id` se guarda
  en la tabla `User` (no en `user_data.json` como en el prototipo).
- **Login de Google**: solo pide `openid` + `email` (identidad), sin scopes sensibles.
  No requiere verificación de Google ni queda sujeto a `redirect_uri_mismatch` por
  cambios de scope.
- **Campos de la planilla**: se adoptan los 9 campos ya validados por el founder
  (`fecha, proveedor, cuit, tipo, numero, neto, iva, total, moneda`), definidos en un
  único lugar (`app/services/fields.py`) para poder agregarse/cambiarse o soportar
  múltiples plantillas de planilla más adelante sin tocar el resto del código.
- **Prompt de extracción**: se adopta el prompt validado por el founder (`gemini.py`),
  con `response_schema` estructurado en vez de parsear JSON a mano.

## Imagen del comprobante — abierto, no cerrado
A diferencia de ADR-0002 (imagen en el Drive del usuario), por ahora la imagen se
guarda en **disco local del servidor** (`app/services/storage.py`), una carpeta por
usuario con nombre de archivo único por comprobante. Esto es interino:
- En Render free el disco es efímero — se pierde en cada redeploy/restart.
- Antes de producción hay que decidir entre: (a) Drive del usuario vía OAuth con scope
  `drive.file` (reintroduce la necesidad de verificación de Google), o (b) storage
  propio tipo S3/Cloudflare R2 (sin depender de Drive ni de scopes adicionales).

## Alternativas consideradas
- Mantener OAuth por usuario para Sheets — descartado: es la causa raíz del bloqueo
  de hoy y agrega fricción de verificación de Google sin necesidad para el MVP.

## Consecuencias
- Login más simple y sin fricción de verificación.
- Un solo punto de escritura (SA) — más fácil de debuguear que credenciales por usuario.
- Riesgo: la SA es un punto único de acceso a todas las planillas de todos los usuarios;
  si se compromete la clave de la SA, se compromete el acceso de escritura a todas.
  Mitigar guardando la clave solo en variables de entorno (Render), nunca en el repo.
- Pendiente: decidir y migrar el storage de imágenes antes de vender el producto.
