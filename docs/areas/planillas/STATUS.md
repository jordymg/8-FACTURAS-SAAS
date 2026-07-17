# STATUS — Área Planillas

## Estado actual
**Estructura v3 implementada (ADR-0011, 2026-07-17)** — 18 columnas,
reemplaza la v2. Motivada por la instrumentación de tiempos (ADR-0014
repo general): con datos reales, la llamada a Gemini resultó el
componente dominante del tiempo de extracción (~9s medidos) — el CEO
decidió recortar campos por doble motivo (simplificar producto + acortar
prompt/respuesta). Se sacan 6 columnas (Perc. IVA, Perc. IIBB ARBA, IIBB
CABA, Ret. Ganancias, Ret. IVA, SIRTAC) y entra una sola columna nueva,
**"Otros impuestos"** — suma de cualquier percepción/retención/impuesto
no discriminado, con texto rojo en la columna de datos (no el
encabezado) + nota fija en el encabezado avisando que hay que revisar la
factura original con el contador. `imp_internos` se sigue extrayendo
aparte (no entra en la suma). Sin clientes reales conectados, sin
migración — la pestaña del año en curso de la planilla de referencia se
renombró a `"2026-v2"` (datos intactos, sin uso) y la app crea `"2026"`
de nuevo con v3 en el próximo uso.

Bug encontrado y corregido en el camino: `_formatear_encabezado()`
(reformatea `sheet1`/"Hoja 1" en cada reconexión) no limpiaba columnas
que sobraban cuando la estructura se achica (23→18) — quedaban etiquetas
viejas pegadas a la derecha. Nunca se había manifestado antes porque
v1→v2 solo agregó columnas. Corregido con un `batch_clear` de las
columnas sobrantes, verificado contra la API real.

Probado contra la API real de Sheets (ambas cuentas de prueba): 18
columnas en el orden correcto, formato/ancho/protección/fila congelada,
rojo solo en datos (no encabezado) y nota exacta en "Otros impuestos",
guardado con y sin `otros_impuestos`, ceros a la izquierda y duplicados
sin regresión. **No probado**: extracción real de Gemini con una foto que
tenga percepciones reales (no hay fotos de muestra en este entorno) — el
CEO lo confirma con una foto real en producción, y ahí mismo se puede
comparar el tiempo real de extracción contra los ~9s previos (ADR-0014).
Detalle completo en
[`decisions/0011-estructura-v3.md`](decisions/0011-estructura-v3.md).

## Historia — Estructura v2 (reemplazada por v3, ver arriba)
**Estructura v2 implementada** (ADR-0005 + ADR-0006, 23 columnas — IVA por
alícuota, percepciones, retenciones, Cód. Proveedor, Categoría clasificada
libremente por la IA, CUENTA en blanco). Reemplaza la v1 (9 columnas
simples). Probado con datos realistas en una pestaña de prueba antes de dar
por buena la implementación.

**Regla de CAE corregida por Issue #002 / ADR-0007, mecanismo de duda
ajustado por ADR-0008**: el uso real detectó un falso positivo (Ticket A
válido marcado como comprobante en negro) el mismo día del despliegue de la
v2. El CAE no es la única evidencia de autorización — también cuentan CAEA,
CAI y controlador fiscal homologado. "Tipo Factura" = "X" solo si no se
detecta NINGUNA de las 4 (sin cambios). El mecanismo de duda se revisó una
vez implementado: en vez de dejar el campo vacío y bloquear el guardado
(ADR-0007), la IA **completa el campo con su mejor valor** y lo marca "baja
certeza" — el formulario lo resalta en rojo (clase `campo-en-duda`) pero
**no bloquea el guardado**; avanzar/guardar se toma como confirmación
implícita de que el usuario lo revisó. Implementado en el prompt de Gemini
y en `static/js/app.js` / `static/css/app.css`.

Bugs encontrados y corregidos durante la implementación de la v2:
- **Ceros a la izquierda perdidos** en Punto de Venta y N° de Factura (ej.
  "0014" → 14): Sheets los interpretaba como número bajo `USER_ENTERED`. Se
  fuerzan a texto (truco del apóstrofe inicial) para `cuit`, `punto_venta` y
  `numero`.
- **Montos guardados como texto, no como número**: la planilla de prueba
  tiene configuración regional en español (coma decimal); mandar "13192.36"
  (punto decimal) bajo `USER_ENTERED` no se reconocía como número ahí, y
  quedaba como texto (rompía el formato de moneda y las fórmulas del
  ADR-0002). Se manda como `float` de Python en vez de string, para no
  depender de la configuración regional de la planilla del cliente.
- **Falso positivo de CAE** (Issue #002): ver arriba.

Lo ya implementado de la v1 sigue vigente sin cambios: metodología de
cálculo (ADR-0002), encabezado protegido y reescrito siempre con textos
canónicos, formato visual (ADR-0004: fecha AAAA-MM-DD mostrada DD/MM/AAAA,
moneda con formato `$`, fila congelada), Issue #001 (facturas desalineadas,
resuelto). El ancho de columna pasó de auto-resize a **anchos fijos por
columna** (`_COLUMN_WIDTHS` en `sheets.py`) — ajustables a mano en Sheets
después si algo queda muy angosto/ancho.

**UX de duplicados implementada (ADR-0009), criterio final `proveedor` +
`numero` + `fecha`**: probando la primera versión (`cuit`+`numero`+`fecha`)
aparecieron dos casos reales que no se detectaban — Issue #003. `cuit` se
reemplazó por `proveedor` (las facturas en negro casi nunca tienen CUIT
visible, y son justo las que más necesitan este aviso), y `norm_id()` ahora
saca cualquier carácter no numérico (no solo ceros a la izquierda), así un
CUIT o número con guiones matchea igual. `proveedor` se compara sin
importar mayúsculas/espacios extra. También se agregó chequeo contra otras
fotos de la **misma tanda** (antes solo comparaba contra lo ya guardado en
el Sheet). `/api/extract` manda el resultado al frontend, que muestra un
aviso amarillo no bloqueante arriba de la tarjeta.

## Next
1. **Confirmar en producción con una foto real que tenga impuestos
   discriminados** (IVA a alguna alícuota, o algo que caiga en "Otros
   impuestos" — percepción, retención, SIRTAC) — CAE, duda y duplicados
   ya se probaron en producción (Issues #002 y #003), falta
   específicamente ese caso. Con la v3 (ADR-0011), además hay que
   confirmar que "Otros impuestos" suma bien cuando hay más de un
   concepto no discriminado en la misma factura. El formulario de
   revisión ya tiene rediseño decidido (ver
   `docs/areas/app/decisions/0001-*.md`), sin implementar todavía.
2. **Armar el set de casos de prueba del prompt** que piden el ADR-0007/0008
   (factura electrónica A/B/C, ticket consumidor final, tique-factura A,
   comprobante con CAI, presupuesto sin autorización) para validar la regla
   de CAE/duda en cada cambio futuro del prompt — todavía no existe.
3. Retomar el ADR-0003 (pestañas por período) cuando se discuta: ya tiene
   registrada la idea del founder de creación automática de pestaña por
   período, pero siguen sin resolver el filtro por mes y las fórmulas de
   total anual (ADR-0002) si los datos quedan repartidos en varias
   pestañas.
4. **ADR-0010 (pregunta abierta, no decidir todavía)**: qué hacer cuando un
   cliente pida una columna extra propia que no forma parte de la
   estructura estándar — se registra la pregunta, se retoma cuando aparezca
   el primer pedido real.
