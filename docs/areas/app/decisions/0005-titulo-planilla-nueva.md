# ADR-0005 (app): Título de la planilla nueva, elegido por el usuario

**Date:** 2026-07-11, corregida el mismo día tras el primer intento
**Status:** ADOPTADA e IMPLEMENTADA (versión corregida) — ver "Corrección"
más abajo

## Contexto
El flujo de conexión (ADR-0003 de esta área) agregó un botón "Crear
planilla nueva" que abre `sheets.new` — un atajo de Google que crea una
hoja en blanco sin título. El founder preguntó si convenía ponerle un
nombre automáticamente, o dejárselo al usuario.

## Limitación técnica de partida
`sheets.new` es un link puro del lado del cliente — no acepta parámetros,
no hay forma de pre-cargarle un título al crear la planilla. Lo único
posible es **renombrarla después**, una vez que el usuario la compartió
con la Service Account (recién ahí tenemos permiso de Editor para
cambiarle el nombre vía la API de Sheets — `gspread.Spreadsheet.update_title()`).

## Decisión
- En el **Paso 3** (pegar el link), si es la **primera conexión** del
  usuario (`user.spreadsheet_id` todavía vacío), aparece un campo de texto
  **en blanco** (placeholder "Ej. Ferretería López") para que el cliente
  escriba el nombre que quiere darle a su planilla.
- **El año lo agrega el sistema, no el usuario**: al conectar, si el
  cliente escribió un nombre, el título final que se aplica es
  `f"{nombre escrito} {año actual}"` (ej. escribe "Ferretería López" →
  queda "Ferretería López 2026"). `app/services/sheets.py::rename_spreadsheet()`
  renombra la planilla en Google Drive a ese valor.
- **Solo la primera vez**: en reconexiones (`user.spreadsheet_id` ya
  tenía algo), el campo de título ni siquiera se muestra — no se le pisa
  a nadie un nombre que ya haya elegido a mano después de la primera
  conexión.
- Si el rename falla por lo que sea (permisos, error de red), no rompe el
  flujo de conexión — la planilla queda conectada igual, con el título que
  ya tenía.

## Corrección del mismo día (primer intento vs. versión final)
El **primer intento** (implementado y probado, pero corregido antes de
llegar al founder de forma definitiva) precargaba el campo con una
sugerencia automática basada en el email: `f"Facturas {parte local del
email} {año}"` (ej. "Facturas mcfly.ar 2026"), editable. El founder pidió
específicamente que **no** se sugiera nada a partir del email — quiere un
campo en blanco donde el cliente escriba el nombre que él elija (ej. el
nombre de su negocio), y que el sistema solo le agregue el año
automáticamente al final, sin que el cliente tenga que escribirlo. Eso es
lo que quedó implementado (ver Decisión arriba). El código de
`config_view()` que calculaba la sugerencia por email se sacó por
completo — ya no existe `titulo_sugerido`.

## Alternativas consideradas
- Título automático fijo, sin preguntarle nada al usuario: descartada por
  el founder — prefirió darle la opción de elegir, con una sugerencia
  precargada para no obligarlo a pensar un nombre desde cero.
- Usar el nombre de la empresa/usuario en vez del email: descartada por
  ahora — no existe ese campo en `User` todavía (solo `email`). Si se
  necesita en el futuro, es un campo nuevo con el mismo mecanismo de
  auto-migración liviana ya usado (`app/__init__.py::_ensure_schema`).
- Renombrar en cada reconexión, no solo la primera vez: descartada — el
  mismo riesgo que llevó a decidir "solo primera vez" para el encabezado
  en su momento (ADR-0002/0003): pisaría un nombre que el usuario ya haya
  elegido después de conectar.

## Consecuencias
- Afecta `app/services/sheets.py` (`rename_spreadsheet()`),
  `app/blueprints/api.py` (`connect_sheet()`, arma `f"{nombre} {año}"` y
  decide si renombrar), `templates/config.html` (campo condicional, en
  blanco), `strings/es.json` (`titulo_planilla_label`,
  `titulo_planilla_placeholder`). `app/blueprints/web.py::config_view()`
  ya no calcula nada relacionado al título (se sacó `titulo_sugerido` en
  la corrección).
- No requiere scopes nuevos de Google ni cambios de schema — la Service
  Account ya tenía permiso de Editor suficiente para renombrar, una vez
  compartida la planilla.
- Probado de punta a punta contra la API real de Sheets: conectar con
  nombre "Ferretería de prueba" dejó el título real en Google Drive como
  "Ferretería de prueba 2026", restaurado después a su valor original. No
  confirmado todavía en navegador por el founder.
