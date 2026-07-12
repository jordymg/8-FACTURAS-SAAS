# ISSUES

Log de problemas que cumplieron el criterio para quedar registrados (no todo
bug entra acá — ver criterio abajo). Objetivo: no repetir el mismo error dos
veces, y que cualquier IA que entre a una sesión nueva vea de un vistazo qué
problemas ya se pisaron.

## Cuándo un problema pasa a ser issue
Se loguea acá si cumple **al menos una**:
1. Tocó datos reales de un usuario (no solo un entorno de prueba).
2. No lo agarramos nosotros primero — lo encontró el uso real de la app, no
   una revisión de código nuestra.
3. La causa es una rareza de un sistema externo que puede volver a morder en
   otro lado si no queda escrito.
4. Si es un bug común arreglado en el momento, sin sorpresas ni datos reales
   pisados, **no** se loguea — sería ruido.

Cada entrada: número secuencial, área, fecha, síntoma, causa raíz, fix, estado.

---

## #001 — Facturas se cargan desencolumnadas en Sheets
**Área:** [planillas](areas/planillas/)
**Fecha:** 2026-07-06
**Síntoma:** al conectar una planilla NUEVA y vacía (simulando un cliente
nuevo) y cargar varias facturas seguidas, la primera se guarda bien (columnas
A→K), pero la segunda arranca en la columna K (justo debajo de donde cayó el
timestamp `cargada_el` de la primera) y la tercera arranca en la columna U
(debajo del `cargada_el` de la segunda) — cada factura nueva se corre más a
la derecha que la anterior, en vez de agregarse en una fila nueva empezando
en la columna A.

**Causa raíz (confirmada por debug, dos bugs encadenados):**
1. `sheet.get_all_values()` en una planilla recién creada y realmente vacía
   devuelve `[[]]` (una fila "vacía"), no `[]` — y `[[]]` es *truthy* en
   Python. El chequeo `if not sheet.get_all_values():` en
   `connect_spreadsheet()` nunca detectaba la planilla como vacía, así que
   **el encabezado nunca se escribía** para una planilla nueva.
2. Sin encabezado, la primera factura terminaba en la fila 1 (vía
   `append_row` sin rango explícito, que al no encontrar ninguna tabla
   escribe ahí mismo) — pareciendo correcta a simple vista. Pero para la
   segunda factura, la API de Sheets, al tener que "adivinar" dónde termina
   la tabla sin un encabezado ni rango explícito que la ancle, interpretaba
   mal el límite y empezaba a escribir donde terminó la última columna de la
   fila anterior, en vez de en una fila nueva desde la columna A. Confirmado
   con un script de reproducción controlada (pestaña de prueba vacía +
   `connect_spreadsheet` completo + 3 facturas con pausas realistas) que
   reprodujo el síntoma exacto, y luego dejó de reproducirse con el fix.

**Fix:** en `app/services/sheets.py`:
- Nueva función `_real_row_count()` que cuenta filas con contenido real
  (filtra las filas "fantasma" que `get_all_values()` puede devolver),
  usada tanto en `connect_spreadsheet()` (para detectar vacío) como en
  `append_invoice()` (para calcular la próxima fila).
- Se dejó de usar `append_row` (que le pide a Sheets que adivine dónde
  escribir) tanto para el encabezado como para cada factura — ahora se
  calcula la fila exacta y se escribe con `sheet.update(...)` a un rango de
  celdas explícito (`A{fila}:K{fila}`), sin ambigüedad posible.

**Estado:** ✅ resuelto y verificado con reproducción controlada (commit
pendiente de push). Datos reales desencolumnados en la planilla de
producción del founder: pendiente que el founder pase la URL/ID para
corregir esas filas puntuales (no se tocó ninguna planilla de producción).

---

## #002 — Ticket A válido catalogado como comprobante en negro
**Área:** [planillas](areas/planillas/)
**Fecha:** 2026-07-06
**Síntoma:** en producción, un Ticket A perfectamente válido (autorizado por
un controlador fiscal homologado, sin CAE) se guardó con "Tipo Factura" =
"X" — la letra que el sistema usa para marcar un comprobante no autorizado
(en negro).

**Causa raíz:** de dominio fiscal, no de código. La regla original (ADR-0005:
"si la IA no detecta CAE → Tipo Factura = X") asumía que el CAE es la única
evidencia de autorización de un comprobante argentino. En realidad existen
al menos cuatro vías: CAE (factura electrónica), CAEA (autorización
anticipada), CAI (talonario impreso) y marcas de un controlador fiscal
homologado (tickets y tique-facturas, sin CAE). Un Ticket A autorizado por
controlador fiscal no tiene CAE, así que la regla original lo marcaba mal.

**Fix:** ver
[`docs/areas/planillas/decisions/0007-regla-validez-comprobante.md`](areas/planillas/decisions/0007-regla-validez-comprobante.md)
— corrige la regla de CAE del ADR-0005: "X" solo si no se detecta NINGUNA de
las 4 vías de autorización, y agrega un principio general de duda (si la IA
no está segura, el campo queda vacío y se resalta en rojo para que el
usuario lo revise, en vez de arriesgar un valor). Prompt de Gemini
actualizado (`app/services/gemini.py`) y nuevo estado visual "campo en duda"
en el formulario de revisión (`static/js/app.js`, `static/css/app.css`).

**Estado:** ✅ resuelto — regla corregida, mecanismo de duda implementado y
probado. Prevención pendiente (ver ADR-0007): armar un set de casos de
prueba del prompt (factura A/B/C electrónica, ticket consumidor final,
tique-factura A, comprobante con CAI, presupuesto sin autorización) para
validar la regla en cada cambio futuro.

---

## #003 — Duplicados no detectados: CUIT ausente y formato con guiones
**Área:** [planillas](areas/planillas/)
**Fecha:** 2026-07-07
**Síntoma:** probando la detección de duplicados (ADR-0009) recién
implementada, dos casos reales no se detectaron:
1. Una factura ya cargada previamente no se reconoció como duplicada al
   volver a subirla.
2. Una **factura en negro** (sin CUIT visible, común en tickets informales)
   subida dos veces no disparó ningún aviso — justo el tipo de comprobante
   que más necesita este aviso.

**Causa raíz:** dos bugs encadenados, ambos encontrados por el uso real (no
por revisión de código):
1. El criterio de match normalizaba ceros a la izquierda pero no separadores
   — un CUIT extraído con guiones (`"30-62926009-5"`) no matcheaba contra el
   mismo CUIT guardado sin guiones (`"30629260095"`).
2. `find_duplicate()` requería CUIT no vacío para siquiera buscar — como las
   facturas en negro casi nunca tienen CUIT impreso, la búsqueda ni se
   ejecutaba para ese caso.

**Fix:** en `app/services/sheets.py`:
- `norm_id()` ahora saca cualquier carácter no numérico (no solo ceros a la
  izquierda), así guiones/espacios no rompen el match.
- El criterio de match se cambió de `cuit`+`numero`+`fecha` a
  **`proveedor`+`numero`+`fecha`** (ADR-0009 actualizado) — `proveedor` casi
  siempre está presente, incluso en comprobantes informales.
- De paso se agregó chequeo contra otras fotos de la **misma tanda** (antes
  solo comparaba contra lo ya guardado en el Sheet).

**Estado:** ✅ resuelto y probado (match con CUIT/guiones, factura sin CUIT
repetida, y duplicado dentro de la misma tanda).

---

## #004 — Contador/aviso del tope mensual nunca se actualizaban en el navegador
**Área:** [app](areas/app/)
**Fecha:** 2026-07-11
**Síntoma:** el founder probó guardar facturas después de implementar el
ADR-0008 (tope mensual) y el contador del header se quedaba siempre en 0,
sin importar cuántas facturas guardara.

**Causa raíz:** el contador (`N/250`) y el aviso amarillo se renderizaban
del lado del servidor **una sola vez**, cuando `/app` cargaba por primera
vez. Guardar una factura y volver a la home no recarga la página (es
navegación 100% client-side, JS solo togglea qué `<section>` se muestra) —
así que esos dos elementos nunca se actualizaban, quedaban congelados en
el valor que tenían al abrir la app esa vez.

**Fix:** `GET /api/invoices` ahora también devuelve `facturas_mes`,
`limite_mensual` y `umbral_aviso`; `static/js/app.js::loadInvoices()`
(ya se llama cada vez que se vuelve a la home) actualiza el contador y el
aviso con esos datos. El aviso pasó de renderizarse condicionalmente con
Jinja (`{% if %}`) a existir siempre en el HTML, oculto por una clase
`hidden` que JS togglea — mismo patrón que el tip rotativo (ADR-0004).

**Estado:** ✅ resuelto y probado (guardar una factura vía la API real y
volver a consultar `/api/invoices`, tal como haría el navegador, muestra el
conteo actualizado).

---

## #005 — Misma foto de factura, datos distintos en la extracción
**Área:** [app](areas/app/) — extracción con Gemini (`app/services/gemini.py`)
**Fecha:** 2026-07-11
**Síntoma:** el founder probó subir la misma foto de una factura varias
veces y obtuvo valores levemente distintos entre una extracción y otra.

**Causa raíz:** `GenerateContentConfig` no fijaba ninguna `temperature` —
por defecto el modelo puede variar su respuesta entre llamadas para la
misma entrada (comportamiento esperado de un LLM sin restringir, pensado
para generación creativa, no para extracción de datos donde se necesita
la misma lectura siempre).

**Fix:** se agregó `temperature=0` a la config de Gemini — busca la
interpretación más probable del comprobante de forma consistente entre
llamadas.

**Estado:** ✅ resuelto — probado con 2 llamadas seguidas sobre la misma
imagen de prueba, resultado idéntico en ambas. `temperature=0` reduce
drásticamente la variación pero no es una garantía matemática absoluta de
determinismo total (limitación conocida de los LLMs a nivel de
infraestructura) — si vuelve a pasar con una foto real, reportarlo.

---

## #006 — Límite de cuota de la API de Sheets al crear las 12 pestañas del año
**Área:** [planillas](areas/planillas/) — descubierto implementando
[ADR-0003](areas/planillas/decisions/0003-pestanas-por-periodo.md)
**Fecha:** 2026-07-11
**Síntoma:** implementando la creación automática de las 12 pestañas del
año al conectar una planilla (una llamada `add_worksheet()` + ~6 llamadas
de formato por pestaña, mismo patrón que ya usaba `connect_spreadsheet()`
para `sheet1`), la prueba real contra la planilla de referencia falló a
partir de la pestaña #9 de 12.

**Causa raíz:** ~80 llamadas de escritura seguidas a la API de Sheets (12
pestañas × ~7 llamadas cada una) superan la cuota de Google
`Write requests per minute per user` — la API devuelve HTTP 429
("Quota exceeded"). No es un límite exclusivo de este proyecto, es la
cuota estándar de la API de Sheets — cualquier operación que dispare
muchas escrituras seguidas en poco tiempo puede volver a pegar contra
esto (ej. si en el futuro se agrega backfill masivo de pestañas para
clientes ya conectados, o migración de datos entre pestañas).

**Fix:** `app/services/sheets.py::crear_pestanas_del_anio()` arma TODOS
los requests (crear las 12 pestañas + todo su formato: negrita, fecha,
moneda, fila congelada, anchos de columna, protección) en una sola lista
y los manda juntos en un único `spreadsheet.batch_update(...)`, más un
segundo llamado `values_batch_update(...)` para el texto del encabezado
de las 12 pestañas a la vez. **2 llamadas a la API en total, no ~80.**

**Estado:** ✅ resuelto y probado — las 12 pestañas se crean en ~3.7
segundos sin errores, con encabezado/fila congelada/protección/anchos de
columna verificados uno por uno contra la API real (no un mock), y
probado que llamarlo dos veces no duplica ni rompe nada (idempotente).
**Prevención a futuro**: cualquier operación nueva que escriba en varias
pestañas/rangos a la vez debería armarse como un `batch_update` único
desde el principio, no como un loop de llamadas individuales — este
límite de cuota puede volver a aparecer.

**Nota (2026-07-12)**: el founder volvió sobre el diseño de fondo y pidió
crear las pestañas **de a una, en el momento en que hacen falta** (no las
12 de una) — ver la versión vigente del ADR-0003. Con eso, el riesgo de
esta cuota específica ya no aplica en la práctica (nunca se crea más de
una pestaña por llamada), pero el mecanismo en lotes se mantuvo en
`crear_pestanas()` por si hiciera falta en el futuro, y esta nota queda
como registro de que el límite existe y hay que tenerlo presente.
