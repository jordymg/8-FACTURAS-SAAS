# ADR-0007 (app): Carrusel "consejos de revisión" en la pantalla de revisión

**Date:** 2026-07-15
**Status:** ADOPTADA e IMPLEMENTADA — origen: handoff aprobado por el CEO.

## Contexto
La home ya tiene un tip rotativo (ADR-0004 área App), recién rediseñado
como tarjeta con ícono de lamparita (misma ADR, Decisión E). El CEO pidió
un segundo carrusel, independiente, en la pantalla de revisión de
facturas — donde el usuario ve las tarjetas editables extraídas y el
botón único "Guardar en Sheets" (ADR-0006 área App) — con el mismo
lenguaje visual, pero contenido propio orientado a esa pantalla.

## Decisión
- **Ubicación**: arriba de las tarjetas de facturas, primer elemento
  dentro de `#screen-review` — lo primero que se ve al entrar a revisar.
- **Estilo visual**: réplica exacta de la tarjeta del tip de home —
  reutiliza las clases CSS existentes (`.tip-card`, `.tip-icono`,
  `.tip-rotativo`) tal cual, sin duplicar reglas nuevas. Mismo fondo
  celeste, bordes redondeados, padding, ícono de lamparita, tamaño de
  texto.
- **Mecánica de rotación**: idéntica al tip de home (arranca en un índice
  aleatorio, rota cada 9s, fade de 300ms, prefijo "Tip — "). Se
  refactorizó el bloque de rotación de `static/js/app.js` en una función
  reutilizable (`iniciarCarruselRotativo(elId, textos)`) sin cambiar el
  comportamiento — se llama una vez para el tip de home
  (`#tip-rotativo` + `strings/tips.txt`) y otra para el carrusel nuevo
  (`#consejo-revision-rotativo` + `strings/consejos-revision.txt`). Cada
  llamado arma su propio índice y `setInterval` — son dos carruseles
  independientes, no comparten estado ni timer.
- **Archivo de textos propio**: `strings/consejos-revision.txt`, misma
  convención que `strings/tips.txt` (un texto por línea, `#` para
  comentarios, líneas vacías se ignoran, archivo ausente/vacío no rompe
  nada — solo no se muestra el carrusel). Leído por
  `app/services/consejos_revision.py::get_consejos_revision()`, mismo
  patrón que `app/services/tips.py::get_tips()` pero en un módulo propio.
  El propósito del archivo incluye tanto consejos de uso de la pantalla
  de revisión como novedades/mejoras pedidas por clientes a medida que se
  implementan — se espera que se edite con el tiempo.
- **Contenido inicial**: los 6 textos exactos aprobados por el CEO (ver el
  archivo), sin modificar ni un carácter — cumplen ADR-0009 general (no
  mencionan IA).

## Alternativas consideradas
- Reutilizar el mismo archivo `strings/tips.txt` de la home — descartada:
  el contenido es de otro contexto (consejos específicos de la pantalla
  de revisión + novedades de producto, no tips generales de la app), y
  `tips.py` ya documenta que su fuente se piensa compartir a futuro con la
  pantalla de espera (ADR-0005 general) — mezclar ahí contenido de otro
  origen habría roto esa intención.
- Ubicarlo debajo del botón de guardar, o entre las tarjetas y el botón —
  descartadas: el CEO eligió arriba de las tarjetas, para que sea lo
  primero que se vea al entrar a revisar.

## Consecuencias
- Segundo uso de `.tip-card`/`.tip-icono`/`.tip-rotativo` en el proyecto,
  confirmando que esas clases quedaron bien desacopladas del contenido
  (funcionan igual con id y textos distintos) — no hizo falta tocar
  `static/css/app.css`.
- `static/js/app.js` gana una función reutilizable en vez de dos bloques
  copiados — si se necesitara un tercer carrusel del mismo tipo a futuro,
  es una línea más.
- Dos `setInterval` corriendo en simultáneo en la pantalla de revisión
  (uno por carrusel, si ambos llegaran a estar visibles a la vez en algún
  escenario futuro) — hoy no es un problema real porque `screen-review` y
  `screen-capture` son excluyentes (una sola `.screen.active` a la vez),
  pero technically ambos timers corren en background igual estén
  visibles o no (el `setInterval` no se pausa al ocultar la pantalla) —
  mismo comportamiento que ya tenía el tip de home antes de este cambio,
  no es una regresión nueva.

## Criterios de aceptación
1. El carrusel de consejos aparece arriba de la primera tarjeta al entrar
   a revisar, con el mismo estilo visual que el tip de home.
2. Rota cada ~9s con fade, arrancando en un texto aleatorio distinto en
   cada carga — igual que el tip de home.
3. En mobile, la tarjeta no empuja la primera tarjeta de factura fuera de
   vista ni genera scroll horizontal.
4. El tip de la home sigue intacto: mismos textos de `strings/tips.txt`,
   sigue rotando con su propio timer, sin interferencia del carrusel
   nuevo.
5. Ambos carruseles pueden rotar "a la vez" (estados/timers
   independientes) sin pisarse ni compartir índice.
6. `docs/areas/app/STATUS.md` y `docs/STATUS.md` actualizados.

### Pruebas hechas (2026-07-15)
Mismo enfoque que la Decisión E de ADR-0004 (Playwright + Chromium, ya
instalado en el entorno en la sesión anterior): se generó el HTML real de
`/app` (Flask + Jinja reales) contra un usuario de prueba en una base
SQLite temporal — sin tocar la base de desarrollo real — forzando la
screen de revisión visible con 1 y con 3 tarjetas de prueba para
comprobar que el carrusel no empuja la primera tarjeta fuera de vista en
mobile. Verificado por código y con capturas de pantalla en desktop y
mobile (375×812):
- El carrusel de consejos se ve arriba de las tarjetas, mismo estilo
  visual que el tip de home (ícono, fondo, bordes, tamaño de texto).
- Rotación de ambos carruseles funciona de forma independiente (el texto
  de cada uno cambia solo tras esperar >9s, sin afectarse entre sí).
- El tip de la home sigue rotando sus propios textos sin cambios.
- Sin overflow horizontal en mobile con 1 y con 3 tarjetas.

**No probado**: celular real (mismo tipo de limitación que sesiones
anteriores de esta área — solo emulación de viewport en Chromium
headless).
