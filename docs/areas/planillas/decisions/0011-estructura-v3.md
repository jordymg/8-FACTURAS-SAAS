# ADR-0011 (planillas): Estructura v3 — 18 columnas, "Otros impuestos"

**Date:** 2026-07-17
**Status:** ADOPTADA e IMPLEMENTADA

## Contexto
Arco completo de esta decisión, contado de punta a punta porque motivó el
cambio:

1. El CEO quería atacar el tiempo de espera entre sacar la foto y ver los
   datos extraídos, pero antes de optimizar se decidió medir primero —
   [ADR-0014](../../decisions/0014-instrumentacion-tiempos-extraccion.md)
   (repo general) instrumentó tiempos por etapa en `/api/extract` y
   `/api/invoices`.
2. Con datos reales de producción, la instrumentación mostró que la
   llamada a Gemini es el componente dominante del tiempo de extracción
   (~9s medidos), muy por encima de recepción/duplicados/escritura.
3. El CEO decidió recortar los campos que se le piden a Gemini, por doble
   motivo: **simplificación de producto** (menos columnas que un cliente
   chico probablemente no necesita desglosadas una por una) y
   **reducción del tiempo de generación** (menos campos en el schema =
   prompt y respuesta más cortos).

Estamos en etapa de desarrollo, sin clientes reales con planilla
conectada — el cambio de estructura va directo, sin plan de migración.

## Decisión

### 18 columnas (reemplaza la v2 de 23 — [ADR-0005](0005-estructura-v2.md))
Salen: Perc. IVA (`perc_iva`), Perc. IIBB ARBA (`perc_iibb_arba`), IIBB
CABA (`iibb_caba`), Ret. Ganancias (`ret_ganancias`), Ret. IVA
(`ret_iva`), SIRTAC (`sirtac`) — 6 columnas.

Entra: **Otros impuestos** (`otros_impuestos`), 1 columna nueva, ubicada
antes de Imp. Internos.

| # | Columna | Clave interna |
|---|---|---|
| 1 | Emisión | `fecha` |
| 2 | Proveedor | `proveedor` |
| 3 | Cód. Proveedor | `cod_proveedor` |
| 4 | CUIT | `cuit` |
| 5 | Categoría | `categoria` |
| 6 | CUENTA | `cuenta` |
| 7 | Tipo Factura | `tipo` |
| 8 | Punto de Venta | `punto_venta` |
| 9 | N° de Factura | `numero` |
| 10 | NETO GRAVADO | `neto` |
| 11 | IVA - 10,5% | `iva_105` |
| 12 | IVA - 21% | `iva_21` |
| 13 | IVA - 27% | `iva_27` |
| 14 | **Otros impuestos** | **`otros_impuestos`** (nueva) |
| 15 | Imp. Internos | `imp_internos` |
| 16 | Total Compra | `total` |
| 17 | Moneda | `moneda` |
| 18 | Fecha de Carga | `cargada_el` |

Todo lo demás de la v2 sigue igual sin cambios: reglas de CAE/duda
([ADR-0007](0007-regla-validez-comprobante.md)/[0008](0008-manejo-de-duda-no-bloqueante.md)),
Categoría libre, CUENTA y Cód. Proveedor vacías, formatos de fecha/moneda
([ADR-0004](0004-formato-visual.md)), texto forzado para
cuit/punto_venta/numero (ceros a la izquierda), montos como número real.
`imp_internos` sigue extrayéndose (decisión explícita del CEO — no entra
en la suma de "Otros impuestos").

### "Otros impuestos" — comportamiento
- **Contenido**: suma (un solo número) de cualquier percepción, retención
  u otro impuesto detectado en el comprobante que no corresponda a IVA
  por alícuota ni a Impuestos Internos. Vacío si no hay ninguno
  (consistente con el resto de los montos ausentes — string vacío, no se
  fuerza "0").
- **Formato**: numérico con formato de moneda (como el resto de los
  montos) + **texto en rojo en toda la columna de datos** (no en el
  encabezado) — señal visual de que esa factura tiene impuestos que el
  sistema no desglosó y que el cliente/contador debe revisar.
- **Nota fija en la celda de encabezado** (texto exacto aprobado por el
  CEO, no se parafrasea):
  > "Suma de percepciones, retenciones u otros impuestos del comprobante
  > que el sistema no desglosa por separado. Si hay un valor acá, revisá
  > la factura original con tu contador."
- Se aplica al crear cada pestaña — mismo mecanismo/lote que el resto del
  formato de encabezado y columnas (`crear_pestanas()`), y también en el
  formato legado de `sheet1` (`_formatear_encabezado()`,
  `connect_spreadsheet()`).

### Prompt de Gemini (`app/services/gemini.py`)
Eliminados del prompt y del `response_schema` los 6 campos de arriba y
sus instrucciones asociadas. Agregado `otros_impuestos` con instrucción
de sumar cualquier percepción/retención/impuesto que no sea IVA
discriminado ni Imp. Internos. `campos_inciertos` (baja certeza,
ADR-0008) aplica también a `otros_impuestos` sin cambios — es un
mecanismo genérico, no depende de qué claves existan. No se tocó
`temperature` ni el modelo (`gemini-2.5-flash`).

### Frontend
`app/services/fields.py::FIELDS` es la única fuente de verdad que
consumen tanto el prompt/schema de Gemini como el render de la tarjeta de
revisión (`static/js/app.js`, loop genérico sobre `CAMPOS`) — sacar/subir
un campo ahí alcanza para ambos lados. El único lugar hardcodeado fuera
de `fields.py` era `camposNumericos` en `static/js/app.js` (validación de
formato numérico en el frontend), actualizado igual. Los 6 campos viejos
desaparecen de la tarjeta, "Otros impuestos" aparece como campo editable
normal, participa del resaltado rojo de baja certeza si vino en
`campos_inciertos`. `templates/app.html` y `static/css/app.css` no
tienen código específico por campo — sin cambios.

### Bug encontrado y corregido en el camino
Probando el cambio contra la API real (planilla de referencia,
`connect_spreadsheet()` → reformatea `sheet1`/"Hoja 1"), se detectó que
`_formatear_encabezado()` solo escribía el encabezado nuevo en el rango
`A1:{última_col}1` sin limpiar columnas que quedaban de más cuando la
estructura se **achica** (23→18) — quedaban etiquetas viejas pegadas
("SIRTAC", "Imp. Internos", "Total Compra", "Moneda", "Fecha de Carga"
repetidas en las columnas S-W). Nunca se había manifestado antes porque
v1→v2 solo agregó columnas, nunca las sacó. Corregido: si
`sheet.col_count` supera la cantidad de columnas actuales, se limpian
(`batch_clear`) las celdas de encabezado que sobran a la derecha.
Verificado contra la API real (antes: 23 valores con restos v2 en fila 1;
después: exactamente 18).

## Alternativas consideradas
- **Comprimir la imagen antes de subir** (para bajar tiempo de
  extracción) — descartada por decisión del CEO: no comprometer la
  fidelidad de la lectura de Gemini a cambio de velocidad.
- **Mantener las 6 columnas ocultas en vez de eliminarlas** — descartada,
  el CEO decidió sacarlas del todo (simplificación real de producto, no
  solo cosmética).
- **Benchmark previo de variantes de prompt** antes de implementar —
  descartado: se implementa directo y se verifica el efecto real con la
  instrumentación de ADR-0014 ya en producción, en vez de medir en un
  entorno aparte.
- **Enviar los datos de tiempos a un Sheet interno** — descartada, no
  tiene ningún efecto sobre el tiempo de extracción en sí, solo movería
  dónde se ven los números.

## Consecuencias
- v3 reemplaza a v2 (`docs/areas/planillas/decisions/0005-estructura-v2.md`
  queda marcada como reemplazada, se conserva como historia).
- Sin clientes conectados, no hace falta migración — la pestaña del año
  en curso de la planilla de referencia se renombró a `"2026-v2"` (datos
  v2 intactos, sin uso) y la app crea `"2026"` de nuevo con v3 en el
  próximo guardado/conexión.
- La mejora de tiempo se verifica comparando las líneas `TIEMPOS` de los
  logs de antes (~9s de Gemini, documentado en ADR-0014) contra las de
  después, con uso real en producción — no se puede medir en este
  entorno (no hay foto de factura real disponible para probar contra la
  API real de Gemini).
- Si una factura trae percepciones/retenciones, el desglose fino deja de
  ser automático — pasa a ser trabajo del cliente/contador a partir de la
  señal en rojo + la nota del encabezado.
- **Probado contra la API real de Sheets** (planilla de referencia,
  ambas cuentas de prueba — `jordy.chatarra@gmail.com` y
  `mcfly.ar@gmail.com`): pestaña nueva con 18 columnas en el orden
  correcto, ancho de columnas, fila congelada, protección de encabezado,
  texto rojo solo en la columna de datos de "Otros impuestos" (no en el
  encabezado), nota exacta en la celda de encabezado, guardado sin
  `otros_impuestos` (queda vacío) y con `otros_impuestos` (se guarda como
  número con formato moneda), ceros a la izquierda y detección de
  duplicados sin regresión. **Probado con mocks** (Flask test client,
  sin llamar a Gemini real): la tarjeta de revisión ya no pide los 6
  campos viejos, sí pide "Otros impuestos", y el resaltado por baja
  certeza (`campos_inciertos`) sigue funcionando para el campo nuevo.
- **No probado, pendiente de confirmación real por el CEO**: extracción
  real de Gemini con una foto que tenga percepciones/retenciones de
  verdad (no hay fotos de muestra en este entorno) — falta confirmar que
  el modelo efectivamente detecta y suma bien esos montos en
  `otros_impuestos`, y medir el tiempo real de extracción con la v3 para
  compararlo contra los ~9s previos.
