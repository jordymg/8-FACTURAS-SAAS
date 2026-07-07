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
