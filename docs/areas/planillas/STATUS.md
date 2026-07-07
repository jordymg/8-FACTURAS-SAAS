# STATUS — Área Planillas

## Estado actual
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

**UX de duplicados implementada (ADR-0009)**: criterio de match ajustado a
3 campos (`cuit`+`numero`+`fecha`, no solo 2 como decía el ADR-0002
originalmente), normalizado para que ceros a la izquierda no rompan el
match (ej. "0017367" y "17367" se tratan igual). `sheets.find_duplicate()`
recibe las facturas ya leídas (una sola lectura del Sheet por lote, no por
archivo) y devuelve la fecha de carga de la coincidencia. `/api/extract` la
manda al frontend, que muestra un aviso amarillo ("Esta factura ya la
subiste el...") arriba de la tarjeta — no bloquea el guardado. Probado con
match exacto, match con cero a la izquierda distinto, y no-match por fecha
distinta.

## Next
1. **Probar el flujo completo en producción** con una foto real: confirmar
   que el prompt nuevo de Gemini extrae bien los ~20 campos (sobre todo el
   IVA discriminado por alícuota y la regla de duda de Tipo Factura), y que
   el formulario de revisión (ahora ~20 campos por tarjeta) es usable — hoy
   es una lista larga sin agrupar por secciones, podría valer la pena
   repensarlo si se siente incómodo de usar en el celular.
2. **Armar el set de casos de prueba del prompt** que piden el ADR-0007/0008
   (factura electrónica A/B/C, ticket consumidor final, tique-factura A,
   comprobante con CAI, presupuesto sin autorización) para validar la regla
   de CAE/duda en cada cambio futuro del prompt — todavía no existe.
3. Retomar el ADR-0003 (pestañas por período) cuando se discuta: cómo se
   pasa de un período a otro, y qué pasa con el filtro por mes y las
   fórmulas de total anual (ADR-0002) si los datos quedan repartidos en
   varias pestañas.
4. Decidir migración de planillas v1 ya conectadas por clientes reales (si
   las hay) a la estructura v2.
