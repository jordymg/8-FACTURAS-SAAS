# ADR-0002 (app): Rediseño de la pantalla de inicio (/app)

**Date:** 2026-07-11
**Status:** ADOPTADA — origen: sesión de diseño CEO (Jordi) + CPO (Claude), APROBADO por CEO.
Implementado en código el mismo día, verificado por render de servidor
(`test_client`, ver Consecuencias) — **pendiente de confirmación visual del
founder en navegador**, la sesión se cerró antes de esa prueba.

## Contexto
Sesión de diseño dedicada sobre la pantalla de inicio de la app
(`templates/app.html`), la primera pantalla que ve el usuario tras
loguearse y tener una planilla conectada. Cuatro problemas concretos
identificados y resueltos en la misma sesión.

## Decisión

### 1. Auto-procesamiento en la pantalla de inicio
Se elimina el botón "Procesar con IA": seleccionar archivos (click/cámara)
o soltarlos en la dropzone dispara `/api/extract` automáticamente, sin
click intermedio. Soporta selección múltiple igual que antes (una tanda =
lo que se seleccionó/soltó junto); la detección de duplicados intra-tanda
(ADR-0009 del área Planillas) no se toca.

**Esta decisión no es nueva**: es la aplicación en la pantalla de inicio
del mismo auto-procesamiento ya decidido para el formulario de revisión en
[`0001-rediseno-formulario-revision.md`](0001-rediseno-formulario-revision.md)
(punto c de ese ADR). No se duplica el racional de fondo acá.

### 2. Texto de bienvenida sobre la dropzone
Texto fijo, discreto (no es un título ni compite visualmente con la
dropzone), visible siempre en mobile y desktop:

> "Esta aplicación está pensada para ahorrarte trabajo: cargar facturas más
> rápido y más simple. Subís la foto, revisás los datos y se cargan a tu
> planilla."

### 3. Ancho máximo del contenido en desktop
El contenido de la pantalla de inicio (texto de bienvenida + dropzone +
"Últimas facturas") se envuelve en un contenedor de ancho máximo ~760px,
centrado (`margin: 0 auto`). Antes se estiraba de borde a borde en
pantallas anchas, dejando un vacío enorme en el listado entre el proveedor
(izquierda) y el monto (derecha). En mobile no cambia nada — el max-width
no tiene efecto por debajo de ese ancho, así que no hace falta un media
query para "revertirlo".

El header (`.app-header`) queda fuera de este contenedor — sigue siendo una
barra completa de borde a borde, como es convención para una barra
superior sticky.

### 4. Botón "Ver planilla de Facturas" en el header
Texto exacto del botón: **"Ver planilla de Facturas"**. Header pasa de 2
zonas (título izquierda, controles derecha) a 3 zonas
(izquierda/centro/derecha):
- **Con planilla conectada** (`user.spreadsheet_id` presente): abre
  `https://docs.google.com/spreadsheets/d/{spreadsheet_id}` en pestaña
  nueva.
- **Sin planilla conectada**: el botón se muestra igual (no se oculta ni
  deshabilita) y navega a `/app/config` en la misma pestaña — empuja al
  usuario nuevo hacia el paso crítico del onboarding (conectar la planilla
  es el punto de mayor abandono identificado).

  **Nota de implementación**: hoy `web.app_view()` redirige a
  `/app/config` ANTES de renderizar `app.html` si el usuario no tiene
  `spreadsheet_id` — o sea, esta segunda rama del botón es inalcanzable
  con el routing actual (nadie sin planilla llega a ver este header
  todavía). Se implementa igual en la plantilla porque no cuesta nada y
  deja la plantilla correcta si ese redirect cambia a futuro — no se tocó
  el redirect en sí, está fuera de alcance de este ADR (ver Fuera de
  alcance).

En mobile, el header pasa a 2 filas: título + controles arriba (como hoy),
el botón "Ver planilla de Facturas" centrado en una fila propia debajo —
el ancho no alcanza para las 3 zonas en una sola fila con los 4 elementos
de texto (título, botón, Configuración, Salir).

No se creó ningún campo, endpoint ni migración nueva — `User.spreadsheet_id`
ya existía en `app/models.py`, solo se expone al template.

## Fuera de alcance (explícito en el handoff de origen)
- Tips/carrusel de la pantalla de espera (ADR-0005 general) — pendiente de
  decisión y redacción, próxima sesión.
- Formulario de revisión — tiene su propio ADR
  ([0001](0001-rediseno-formulario-revision.md)), no se adelanta acá.
- Cualquier cambio de flujo de backend más allá de disparar
  `/api/extract` automáticamente — en particular, el redirect de
  `web.app_view()` cuando no hay planilla conectada NO se tocó (ver nota en
  la Decisión 4).

## Consecuencias
- Afecta `templates/app.html`, `templates/base.html`, `static/css/app.css`,
  `app/__init__.py` (nuevo context processor `asset_version`).
  `app/blueprints/web.py` ya exponía `user` al template, sin cambios ahí.
- De paso, se agregó cache-busting a los assets estáticos (`app.css`,
  `app.js`) vía un query param con el mtime del archivo — la sesión
  anterior había un cambio de código que no se veía reflejar en el
  navegador, con caché de estáticos como hipótesis principal sin confirmar.
  Se resuelve de raíz acá en vez de pedir hard-refresh cada vez.

### Verificación hecha (2026-07-11)
- Grep de "IA"/"Gemini" en texto visible: limpio (solo quedan 2 comentarios
  de código, no visibles al usuario).
- CSS con llaves balanceadas, JS válido (`node -e "new Function(...)"`,).
- Boot de Flask OK.
- Render real de `/app` vía `test_client` (no un mock): status 200,
  aparece "Ver planilla de Facturas", aparece el texto de bienvenida exacto,
  aparece `contenido-centrado`, cache-busting presente en ambos assets, NO
  aparece "Procesar con IA", y el link generado apunta al spreadsheet_id
  correcto del usuario de prueba.
- **No verificado**: cómo se ve/comporta realmente en un navegador (grilla
  centrada, header en 2 filas en mobile, click en "Ver planilla" abriendo
  pestaña nueva, auto-procesamiento end-to-end con una foto real). No hay
  herramienta de navegador disponible en el entorno de Claude Code para
  esto — necesita que el founder lo pruebe y confirme.

## Criterios de aceptación
1. El botón "Procesar con IA" no existe más; seleccionar o soltar archivos
   dispara la extracción sin ningún click adicional (click/cámara y
   drag&drop, uno o varios archivos).
2. El texto de bienvenida aparece sobre la dropzone con la redacción
   exacta de la Decisión 2.
3. En desktop el contenido queda centrado con ancho limitado; el listado
   ya no se estira de borde a borde. En mobile no hay regresión visual.
4. "Ver planilla de Facturas" centrado en el header; con planilla conectada
   abre el Sheet correcto en pestaña nueva; sin planilla lleva a
   `/app/config`.
5. Ningún texto visible de la app menciona IA/Gemini — ver
   [`docs/decisions/0009-comunicacion-nunca-mencionar-ia.md`](../../decisions/0009-comunicacion-nunca-mencionar-ia.md)
   para la auditoría completa (no se limitó a esta pantalla).
