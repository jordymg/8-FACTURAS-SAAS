# ADR-0006 (app): Rediseño del flujo de guardado — botón único, descartar por tarjeta, cuenta regresiva sin cambiar de pantalla

**Date:** 2026-07-14
**Status:** ADOPTADA e IMPLEMENTADA (con una corrección del CEO sobre el
primer intento, ver punto c) — pendiente de confirmación en navegador por
el founder (ver Consecuencias)

## Contexto
El flujo de revisión (ADR-0001 de esta área) mostraba una tarjeta por
comprobante, cada una con su propio botón "Guardar en Sheets", y tras
guardar todas quedaba un botón "Volver" para regresar a la home a mano. El
CEO pidió rediseñar este flujo: guardado en lote con un solo botón, una
forma más visible de descartar una factura de la tanda, y una vuelta a la
home automática en vez de manual.

## Decisión

### a. Botón único de guardado
Se saca el botón "Guardar en Sheets" de cada tarjeta. Al final de las
tarjetas de la tanda hay un solo botón "Guardar en Sheets" que guarda
todas las tarjetas visibles (no descartadas). Cada factura se sigue
guardando con el flujo existente, una llamada a `POST /api/invoices` por
factura (incluido el incremento del contador mensual,
`app/services/limites.py`) — no hay endpoint de guardado en lote nuevo en
el backend, el lote es una orquestación del lado del cliente.

**No bloqueo vigente, sin cambios**: los campos en rojo por baja certeza
(ADR-0008 área Planillas) y los avisos amarillos de duplicado (ADR-0009
área Planillas) siguen sin bloquear el guardado — apretar el botón único
con tarjetas en ese estado es confirmación implícita de todas. La
validación de formato que ya existía (fecha `AAAA-MM-DD`, campos
numéricos, campos `required` vacíos) se mantiene igual que antes, ahora
evaluada por tarjeta dentro del guardado en lote: una tarjeta con un
problema de formato no se manda a guardar y queda pendiente, mostrando el
mismo mensaje de validación de siempre; el resto de la tanda sigue su
curso normal.

### b. Descartar factura por tarjeta
Cada tarjeta lleva una cruz roja bien visible en la esquina superior
derecha del header, con el texto "Descartar factura" al lado (antes era
solo una "✕" gris, visible recién al pasar el mouse). Al tocarla, la
tarjeta se elimina sin guardar nada y sin incrementar el contador. Si se
descartan todas las tarjetas de la tanda sin haber guardado ninguna, se
vuelve a la home directamente, sin pasar por la cuenta regresiva.

### c. Cuenta regresiva y redirección automática, sin pantalla nueva
Se saca el botón "Volver". Al terminar de guardar la tanda (cuando ya no
queda ninguna tarjeta pendiente de resolución), el botón único "Guardar en
Sheets" es reemplazado **en el mismo lugar, dentro del mismo
`screen-review`** por el texto de la cuenta regresiva — no hay pantalla
nueva ni transición: las tarjetas ya guardadas (con sus datos) siguen
visibles arriba mientras corre la cuenta regresiva, para que el usuario
pueda seguir viendo lo que acaba de cargar. El texto:
- Una factura: "Factura guardada. Volviendo al inicio en 3… 2… 1…"
- Más de una: "Facturas guardadas. Volviendo al inicio en 3… 2… 1…"

**Corrección del mismo día (primer intento vs. versión final)**: el primer
intento implementaba esto como una pantalla de éxito nueva y separada
(`screen-exito`), a pantalla completa, reemplazando la vista de las
tarjetas. El CEO pidió específicamente que **no** cambie de pantalla —
mientras corre la cuenta regresiva quiere seguir viendo los datos de la
factura recién cargada, no una pantalla en blanco con solo el mensaje. Se
sacó `screen-exito` por completo; la cuenta regresiva ahora vive como un
párrafo (`#exito-texto`) al lado del botón único, oculto por defecto, que
se muestra ocultando el botón cuando termina de guardar la tanda.

Los números aparecen progresivamente, uno por segundo. A los 3 segundos
totales, redirige a la home vía navegación client-side (misma sección de
siempre + `loadInvoices()` para refrescar la lista y el contador; recién
ahí se limpian las tarjetas y se vuelve a mostrar el botón único, listo
para la próxima tanda). La cuenta regresiva no se puede cancelar ni
acelerar — no hay botón "Ir ahora" ni tap para saltarla. La duración vive
en una única constante, `DURACION_CUENTA_REGRESIVA_SEG` en
`static/js/app.js`, para poder bajarla fácil (el CEO mencionó 2 segundos
como posible ajuste futuro) sin tocar el resto de la lógica. Los textos no
mencionan IA y no llevan ":" en el texto corrido, cumpliendo el ADR-0009
general.

### d. Falla parcial al guardar
Si al guardar la tanda alguna factura falla (error de API/Sheets), las que
se guardaron bien quedan guardadas — no se revierte nada. Las tarjetas
fallidas quedan en pantalla con el mensaje de error devuelto por el
backend y dos salidas: descartarla (cruz), o corregirla si hace falta y
volver a apretar el botón único, que reintenta solo las tarjetas
pendientes (las ya guardadas no se vuelven a mandar). La cuenta regresiva
aparece recién cuando no queda ninguna tarjeta pendiente — si las
restantes se descartan tras una falla y al menos una se había guardado
antes, igual aparece la cuenta regresiva (singular/plural según cuántas
se guardaron efectivamente).

### e. Duplicados dentro de la tanda
El chequeo de duplicados contra otras fotos de la misma tanda (ADR-0009
área Planillas) sigue igual, sin cambios. Si se descarta una tarjeta que
otro aviso de duplicado referenciaba, ese aviso simplemente deja de
importar — no se recalcula en vivo, y no rompe nada (el aviso ya
mostrado en la tarjeta descartada desaparece con la tarjeta).

## Alternativas consideradas
- Mantener el botón "Volver" manual tras guardar: descartada — un paso
  extra que el CEO prefirió sacar a favor de una redirección automática.
- Cuenta regresiva cancelable o con botón "Ir ahora": descartada por el
  CEO — son solo 3 segundos, no vale la pena la complejidad de una salida
  anticipada.
- Mantener un botón de guardado por tarjeta (en vez de uno único):
  descartada — quedaba redundante con el botón único y complicaba definir
  cuándo disparar la redirección (¿al guardar la última? ¿con un botón
  aparte?). Un solo punto de guardado simplifica también cuándo mostrar la
  pantalla de éxito.

## Consecuencias
- Afecta `templates/app.html` (botón único + `#exito-texto` en el mismo
  lugar, ambos dentro de `screen-review`; se saca `btn-volver` y no se
  agrega ninguna pantalla nueva), `static/js/app.js` (`guardarTanda()`,
  `verificarFinTanda()`, `mostrarPantallaExito()` — ya no llama a
  `showScreen()`, solo alterna clases `hidden` entre el botón y el texto —,
  `crearBtnDescartar()` actualizado), `static/css/app.css`
  (`.btn-descartar` rediseñado, `.exito-texto` nueva, `.btn.hidden` para
  poder ocultar el botón único, se saca el CSS muerto de `.btn-guardar`).
- Las tarjetas con error de **extracción** (falla `/api/extract`, con su
  botón "Reintentar" ya existente) son un flujo aparte, sin cambios — no
  entran al guardado en lote (no tienen campos que guardar). Para que la
  cuenta regresiva no aparezca con una de estas tarjetas todavía sin
  resolver en pantalla, `verificarFinTanda()` también las tiene en cuenta:
  solo avanza cuando no queda ninguna tarjeta que no sea `.guardado` (lo
  que incluye tanto pendientes de guardado en lote como errores de
  extracción sin descartar ni reintentar).
- Probado con una simulación del DOM real (jsdom cargando el
  `app.html`/`app.js` reales, con `fetch` mockeado) cubriendo los 6 casos
  pedidos: tanda de 1, tanda de 3, descartar 1 de 3, descartar todas,
  falla simulada de 1 de 3 con reintento, y descartar la fallida tras una
  falla parcial — los 6 casos pasaron, incluyendo el contador del header
  (se confirma que `loadInvoices()` se vuelve a llamar al volver a la
  home). **No se pudo probar en un navegador real** (no hay Chromium ni
  Playwright/Selenium disponibles en este entorno, y el flujo requiere
  login real de Google) — pendiente de que el founder lo confirme en
  vivo, como ya pasó con ADR-0001 en su momento.
