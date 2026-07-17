# ADR-0014: Instrumentación de tiempos por etapa del procesamiento de facturas

**Date:** 2026-07-16
**Status:** ADOPTADA e IMPLEMENTADA

## Contexto
El CEO quiere atacar el tiempo de espera entre que el usuario carga/saca la
foto y ve los datos extraídos — pero antes de optimizar nada, se decidió
medir: instrumentar el backend para saber con datos reales en qué se va el
tiempo (recepción de la imagen, llamada a Gemini, chequeo de duplicados,
escritura en Sheets), en vez de optimizar por intuición. Esta sesión es
solo instrumentación — cero cambios de comportamiento visible, cero
optimizaciones.

## Decisión
- **Flujo de extracción** (`POST /api/extract`, `app/blueprints/api.py`):
  una línea de log por foto (identificada con índice `[n/total]` en
  tandas de varias fotos) con tamaño de la imagen (MB), duración de
  recepción/preparación (lectura del archivo hasta que la llamada a
  Gemini está lista para salir), duración de la llamada a Gemini
  (total, incluyendo reintentos, más la duración del último intento por
  separado y la cantidad de reintentos — ver cambios en
  `app/services/gemini.py`), duración del chequeo de duplicados de esa
  foto, y duración total de esa foto. Además, una línea de resumen del
  lote con la duración de la lectura de la planilla (`list_invoices()`,
  que se hace una sola vez por lote, no por foto — ver ADR-0009) y la
  duración total del request completo.
- **Flujo de guardado** (`POST /api/invoices`): una línea con la
  duración de `sheets.append_invoice()` (marcando explícitamente si ese
  guardado disparó la creación de la pestaña del año — infla ese
  guardado puntual, ver ADR-0003 área Planillas) y la duración total del
  request.
- **Interruptor**: `LOG_TIEMPOS` (env var), **default activado, también
  en producción** — decisión del CEO, los tiempos que importan son los
  de condiciones reales (Render free, red real, Gemini real), no los de
  un entorno de desarrollo. Con el flag en `false`/`0`, no se loguea nada
  y no hay overhead apreciable (los `time.monotonic()` en sí son
  despreciables; lo único que se evita es armar el string y llamar al
  logger).
- **Logger propio** (`app/services/tiempos.py`, logger `"tiempos"`, sin
  `propagate` al root logger): evita que, al habilitar el nivel INFO para
  poder ver estas líneas, también se vuelvan visibles los logs INFO de
  librerías de terceros (gspread, google-genai) que comparten el logging
  estándar de Python — estas seguirían en su nivel default (WARNING) sin
  ensuciar los logs de Render.
- **Sin datos sensibles**: las líneas solo llevan tiempos, tamaños y
  contadores — nunca proveedor, CUIT, montos ni ningún otro dato del
  comprobante.
- No se miden dimensiones en píxeles de la imagen — requeriría decodificar
  la imagen (no hay `Pillow` ni ninguna librería de imágenes en
  `requirements.txt` hoy) o agregar una dependencia nueva solo para esto,
  lo que no es "barato" en el sentido que pedía el handoff y contradice
  la restricción de cero overhead apreciable. Se mide solo el tamaño en
  bytes/MB, que es gratis (`len(image_bytes)`).

## Alternativas consideradas
- **Medir solo en desarrollo** — descartada: los tiempos que importan
  para decidir qué optimizar son los de producción real (Render free
  tier, con su latencia/cold start propios, y la API real de Gemini bajo
  carga real) — un entorno de desarrollo no los reproduce.
- **No medir y optimizar por intuición** — descartada: es exactamente lo
  que esta sesión evita a propósito, por pedido explícito del CEO. Sin
  datos reales, cualquier optimización (compresión de imagen, cambio de
  modelo, etc.) sería una apuesta, no una decisión informada.

## Consecuencias
- Próximo paso: juntar unos días de datos reales de estas líneas en los
  logs de Render y decidir con evidencia qué optimizar. Candidatas ya
  identificadas en la reunión CEO-CPO (no implementadas, no evaluadas
  todavía): compresión de imagen en el cliente antes de subir, y
  revisión de la variante de modelo de Gemini configurada.
- **Modelo de Gemini configurado hoy** (informativo, sin cambios en esta
  sesión): `gemini-2.5-flash` — default de código en
  `app/services/gemini.py` (`os.getenv("GEMINI_MODEL", "gemini-2.5-flash")`)
  y coincide con el valor explícito en `render.yaml`
  (`GEMINI_MODEL: value: gemini-2.5-flash`), así que es el que corre en
  producción.
- Cambios de contrato interno (no visibles desde afuera): `extract_invoice()`
  en `app/services/gemini.py` ahora devuelve `(campos, tiempos_gemini)` en
  vez de solo `campos`; `sheets.append_invoice()` ahora devuelve `bool`
  (si disparó la creación de la pestaña del año) en vez de `None`;
  `sheets.crear_pestanas()` devuelve la sublista de nombres efectivamente
  creados (antes devolvía siempre la lista completa pedida, ya existieran
  o no) y `sheets.asegurar_pestana_del_anio()` devuelve `bool` en vez del
  nombre de la pestaña — verificado que ningún llamador usaba esos
  valores de retorno previos, así que el cambio es seguro.
- **Probado en este entorno** (Flask test client + mocks de Gemini y
  Sheets, sin credenciales reales): una tanda de 2 fotos genera 2 líneas
  por foto identificables (`[1/2]`, `[2/2]`) más una línea de resumen del
  lote, con reintentos reflejados correctamente; un guardado genera su
  línea marcando la pestaña creada; con `LOG_TIEMPOS=false` no se loguea
  ninguna línea; el contenido y formato de las respuestas HTTP no
  cambiaron. **No probado contra las APIs reales de Gemini/Sheets en este
  entorno** (sin credenciales) — pendiente de que el uso real en
  producción confirme que las líneas aparecen en los logs de Render con
  datos reales.

## Observación de optimización (informativa, no implementada)
Dentro del flujo de guardado, cada `append_invoice()` llama a
`asegurar_pestana_del_anio()` — que en el caso normal (la pestaña del año
ya existe, que es casi siempre) igual hace una llamada a la API de Sheets
(`spreadsheet.worksheets()` en `crear_pestanas()`) solo para confirmar
que ya existe, antes de la escritura real. Es candidato a cachear (la
pestaña del año no cambia dentro de la misma sesión de uso) si los datos
de tiempos muestran que pesa. No se tocó — queda para que el CEO decida
con los números en la mano.
