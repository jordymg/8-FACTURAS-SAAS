# ADR-0003 (planillas): Pestañas por período

**Date:** 2026-07-06, redefinida 2026-07-11, ajustada 2026-07-12 (tres veces)
**Status:** IMPLEMENTADA — `append_invoice`/`list_invoices`/`find_duplicate`
ya leen y escriben la pestaña del año, `sheet1` ("Hoja 1") queda sin uso
para datos nuevos. Ver "Historia" punto 6 y "Consecuencias".

## Origen
Surgió al entrevistar al founder sobre reglas de integridad (PRODUCTO.md
punto 5, qué pasa si se borra/renombra "Hoja 1"). Propuesta original: en
vez de escribir siempre en la primera pestaña de la planilla, escribir en
una pestaña específica por período.

## Historia de la idea (para entender por qué cambió varias veces)
1. **2026-07-06** (origen): pestaña por período, sin definir cómo se crean.
2. **2026-07-07**: el founder propuso crear la pestaña **de forma
   perezosa** — recién cuando llega la primera factura de un período sin
   pestaña. Quedó registrado pero sin implementar.
3. **2026-07-11**: pidió crear **las 12 pestañas mensuales del ciclo anual
   todas de una**, al conectar. Se implementó y se probó — encontrando un
   límite real de cuota de la API de Sheets en el camino (ver nota técnica
   más abajo, Issue #006).
4. **2026-07-12, primer ajuste**: volvió sobre el punto 3 y pidió **una
   pestaña por mes, creada de a una, en el momento en que hace falta** —
   ej. conectar en julio crea solo `JUL-26`; agosto se crea recién cuando
   llega. Se implementó y se probó.
5. **2026-07-12, segundo ajuste**: simplificó todavía más — **una sola
   pestaña por AÑO calendario**, no por mes. Ej. conectar en cualquier
   momento de 2026 crea una pestaña llamada simplemente `"2026"`, que
   contiene todo el año. Recién se crea una pestaña nueva (`"2027"`)
   cuando cambia el año. Hasta acá, solo se creaban las pestañas — todavía
   no se usaban para guardar/leer nada.
6. **2026-07-12, tercer ajuste — ESTA es la versión vigente**: el founder
   probó cargar una factura real y notó que se seguía guardando en "Hoja
   1", no en la pestaña del año — señaló, con razón, que esto era un
   problema grande (el "alcance acotado" documentado en versiones
   anteriores de este ADR nunca se había cerrado). Se cerró: ahora
   `append_invoice`, `list_invoices` y `find_duplicate` usan de verdad la
   pestaña del año, no `sheet1`. El founder confirmó explícitamente no
   preocuparse por migrar los datos ya cargados en "Hoja 1" — estamos en
   etapa de desarrollo, no hace falta.

## Decisión vigente (2026-07-12, tercer ajuste)
- **Al conectar por primera vez**: se crea únicamente la pestaña del año
  calendario en curso, nombrada con el año tal cual (ej. `"2026"`, sin
  ceros ni abreviaturas).
- **`append_invoice()`**: guarda la factura en la pestaña del año de SU
  FECHA (no la fecha de hoy) — ej. si la factura es del 2025, va a la
  pestaña "2025" aunque se cargue en 2026. Si esa pestaña todavía no
  existe, se crea ahí mismo con el encabezado canónico.
- **`list_invoices()`**: lee de la pestaña del año pedido (por defecto, el
  año actual — usado tal cual por "Últimas facturas" y por la detección
  de duplicados). Si la pestaña de ese año no existe todavía, devuelve
  lista vacía sin error.
- **`find_duplicate()`**: sin cambios propios — hereda el comportamiento
  de `list_invoices()` (compara contra lo que le pasen).
- Nunca se crean pestañas de años futuros por adelantado.
- `app/services/sheets.py::asegurar_pestana_del_anio(spreadsheet_id, fecha)`
  sigue siendo la función que crea la pestaña si no existe; ahora la usan
  tanto `connect_spreadsheet()`/`api.py` (primera conexión) como
  `append_invoice()` (por cada factura, según su propia fecha).

## Limitación conocida y aceptada — no busca en años anteriores
`list_invoices()` (y por lo tanto `find_duplicate()` y "Últimas facturas")
**solo miran el año actual por defecto**. Si una factura recién cargada
"duplica" algo del año anterior, o si querés ver facturas viejas en
"Últimas facturas", no aparece — habría que pasar `anio` explícitamente a
`list_invoices()`. Se aceptó esta limitación a propósito (el founder
confirmó que estamos en desarrollo, no hace falta resolver casos límite de
cruce de año todavía).

## Qué pasa con "Hoja 1" (datos ya cargados antes de este cambio)
**No hay migración ni backfill.** Los datos que ya estaban en "Hoja 1"
(facturas reales de pruebas del founder de las últimas semanas) se quedan
ahí, intactos, pero **la app deja de leerlos**: no van a aparecer más en
"Últimas facturas" ni se van a detectar como duplicados si se vuelven a
cargar. Confirmado explícitamente con el founder — estamos en etapa de
desarrollo, así que no se resuelve todavía. Si en algún momento se necesita
recuperar esos datos, hay que migrarlos a mano (copiar filas de "Hoja 1" a
la pestaña del año que corresponda según su columna `fecha`).

## Lo que queda abierto para más adelante (menor, ya no bloquea nada)
- ¿Qué pasa con las fórmulas de "total anual acumulado" (ADR-0002)? Con
  pestañas por AÑO (no por mes), un total anual queda contenido en una
  sola pestaña — más simple que si fuera por mes, pero no está armado
  todavía.
- ¿Tiene sentido seguir manteniendo "Hoja 1" en la planilla, o convendría
  ocultarla/renombrarla en algún momento para no confundir al contador?
- Si en el futuro hace falta ver/buscar en años anteriores (no solo el
  actual), hay que decidir cómo se expone eso en la UI (¿selector de año
  en "Últimas facturas"?).

## Nota técnica — límite de la API de Sheets descubierto probando una versión anterior
La versión del 2026-07-11 (12 pestañas mensuales de una) creaba cada
pestaña con `add_worksheet()` + formato completo (~7 llamadas de escritura
por pestaña). Con 12 pestañas eso son ~80 llamadas de escritura seguidas —
**se probó de verdad contra la planilla de referencia y falló con HTTP
429 "Quota exceeded for quota metric 'Write requests' ... per minute per
user"** a partir de la pestaña #9. Se resolvió agrupando todo en 2
llamadas a la API (`batch_update` + `values_batch_update`) — ver Issue
#006 en `docs/ISSUES.md`.

**Con la versión vigente (una pestaña por año) este límite deja de ser un
riesgo real por partida doble** — nunca se crea más de una pestaña por
llamada, y encima el ritmo de creación es de una vez por año, no una vez
por mes. Aun así `crear_pestanas()` (la función interna que hace el
trabajo real) se dejó armada para poder recibir una lista de varios
nombres a la vez y seguir usando el mismo mecanismo en lotes, por si en el
futuro hace falta crear más de una pestaña junta (ej. un backfill).

## Consecuencias
- Afecta `app/services/sheets.py`: `asegurar_pestana_del_anio()` (crea la
  pestaña si falta), `append_invoice()` (ahora calcula el año de la
  propia factura y escribe ahí, en vez de `sheet1`), `list_invoices()`
  (nuevo parámetro `anio`, default año actual, en vez de `sheet1`;
  devuelve `[]` si esa pestaña no existe todavía en vez de fallar).
  `_formatear_encabezado()` queda usada solo por `connect_spreadsheet()`
  (para `sheet1`, que sigue existiendo pero ya no recibe facturas nuevas).
- `app/blueprints/api.py::save_invoice()` se simplificó — ya no necesita
  su propio chequeo de "¿existe la pestaña del año?" por separado, porque
  `append_invoice()` ahora lo hace internamente con la fecha real de la
  factura (más correcto: antes chequeaba con la fecha de HOY, no con la
  fecha de la factura, lo cual habría sido incorrecto para cargar
  facturas atrasadas).
- Probado de punta a punta contra la API real de Sheets: `append_invoice`
  escribe en la pestaña del año correcto (no en "Hoja 1"), `list_invoices`
  la lee de vuelta, `find_duplicate` detecta un duplicado real dentro de
  esa pestaña y no detecta uno falso, un año sin pestaña devuelve lista
  vacía sin error, y el flujo completo por `POST`/`GET /api/invoices`
  funciona de punta a punta. Se confirmó explícitamente que los datos
  preexistentes en "Hoja 1" (facturas reales de pruebas anteriores del
  founder) quedaron intactos y sin tocar. **Confirmado funcionando por el
  founder en navegador (2026-07-12)**, cargando una factura real —
  commiteado y desplegado a producción el mismo día.
