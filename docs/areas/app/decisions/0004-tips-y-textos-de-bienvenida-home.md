# ADR-0004 (app): Tips gestionables + textos de bienvenida y feedback en la home

**Date:** 2026-07-11 (adenda visual: 2026-07-15)
**Status:** ADOPTADA e IMPLEMENTADA — origen: sesión de diseño CEO (Jordi) + CPO (Claude), APROBADO por CEO.
Confirmada funcionando por el founder en navegador el mismo día, tras dos
rondas de ajustes visuales chicos (ver nota en Decisión C). Ver Decisión E
para el rediseño visual del tip (tarjeta + ícono) del 2026-07-15.

## Contexto
El [ADR-0005 general](../../decisions/0005-pantalla-espera-cold-start.md)
(pantalla de espera / carrusel) dejó los textos del carrusel "a definir al
implementar". El CEO resolvió esto con un mecanismo único: un archivo de
tips editable por él mismo, que alimenta la home ahora y (a futuro) el
carrusel de espera cuando se implemente. Se suman además textos de
bienvenida y feedback a la home, y se ajusta la jerarquía tipográfica del
texto de entrada del [ADR-0002](0002-rediseno-pantalla-inicio.md) (Decisión 3).

## Decisión A — Archivo de tips único y editable
- `strings/tips.txt`: un tip por línea, texto plano. Encabezado con
  instrucciones de edición para el CEO. Líneas vacías o que empiecen con
  `#` se ignoran (permite comentarios). Si el archivo falta o queda vacío,
  la app no muestra tips — no rompe nada.
- **Única fuente de tips del producto**: la lee `app/services/tips.py`
  (función `get_tips()`), pensada para que la pantalla de espera del
  ADR-0005 general la reuse directamente cuando se implemente — no hay
  nada específico de la home en esa función.
- Contenido inicial: los 6 tips exactos que definió el CEO (ver el archivo).

## Decisión B — Tips en la home: uno por vez, rotando
- Ubicación: debajo de la dropzone, arriba de "Últimas facturas".
- Un tip por vez, rotación automática cada 9 segundos con fade suave
  (CSS transition de opacidad). Arranca en un índice aleatorio.
- Estilo discreto, prefijo "Tip — ", visible en mobile y desktop.

## Decisión C — Textos de entrada: saludo + cuerpo agrandado + feedback
Orden arriba de la dropzone:
1. Saludo: "Gracias por probar nuestro servicio." — permanente para todos
   los usuarios, no solo nuevos.
2. Texto de entrada existente (ADR-0002), **sin cambiar la redacción**
   (incluye un ":" aprobado antes de la Decisión D — no se toca, la regla
   de sin-dos-puntos aplica a textos nuevos), con jerarquía visual mayor:
   más grande y con más peso que un párrafo común, pero por debajo del
   título "Facturas" del header.
3. Feedback: "Tu opinión nos importa. Cualquier mejora o cambio que se te
   ocurra, contanos y lo tomamos en cuenta." — tamaño chico, el que tenía
   el texto de entrada antes de este ajuste.

**Ajuste del founder tras probar en navegador (mismo día)**: el bloque
completo (saludo, entrada, feedback) queda centrado (`text-align: center`),
y el saludo pasa a tener la misma tipografía que el texto de entrada
(antes era más chico y gris) — quedan iguales entre sí, el feedback sigue
chico y gris como estaba.

**De paso, mismo pedido**: se subió el contraste del borde punteado de la
dropzone (`.zona`), de `var(--gray-200)` (gris muy pálido, poco visible) a
`var(--gray-500)` (gris medio) — no forma parte de ningún ADR previo, es
un ajuste de legibilidad puntual.

Jerarquía tipográfica final: título del header > texto de entrada > saludo
y feedback (mismo tamaño discreto que antes tenía el texto de entrada).

## Decisión D — Regla de estilo: sin dos puntos en textos nuevos
Los textos visibles al usuario evitan el carácter ":" — preferencia
explícita del CEO. **Se agrega como una segunda regla dentro del
[ADR-0009 general](../../decisions/0009-comunicacion-nunca-mencionar-ia.md)**
(mismo documento, no uno nuevo) — decisión del implementador: ambas reglas
son sobre "cómo la app le habla al usuario", transversales al producto, y
tiene más sentido tenerlas juntas que fragmentadas en ADRs de una sola
regla cada uno. **No es retroactiva** (a diferencia de la regla de "nunca
decir IA"): aplica a textos nuevos de acá en adelante; el texto de entrada
existente con ":" queda exento explícitamente (ver Decisión C, punto 2).

## Decisión E — Rediseño visual: tarjeta con ícono (2026-07-15)
El CEO reportó que el tip se veía muy chico y pasaba desapercibido.
Handoff aprobado por el CEO, cambio **solo visual** — no toca la Decisión
B (rotación cada 9s, índice aleatorio inicial, fade) ni los textos de los
tips (siguen viniendo de `strings/tips.txt`).

- El tip pasa a renderizarse como **tarjeta**: fondo celeste suave
  (`#eef4ff`, el mismo tono que ya usaba el foco de los inputs del
  formulario — no un color nuevo en la paleta), bordes redondeados
  (`var(--radius)`, igual que el resto de tarjetas/recuadros de la app), y
  padding generoso.
- Tamaño de letra: sube un escalón, de `.82rem` a `.92rem` — por debajo de
  `.entrada` (`1rem`) y del título del header (`1.1rem`), como pidió el
  handoff ("sin llegar al tamaño de títulos/encabezados").
- Color de texto: pasa de `var(--gray-500)` (gris pálido, parte del
  problema de "pasa desapercibido") a `var(--gray-900)`, para buen
  contraste sobre el fondo celeste.
- **Ícono de lamparita** a la izquierda del texto, alineado verticalmente
  — SVG inline (`<svg class="tip-icono">`, stroke `currentColor` en
  `var(--blue)`), sin agregar ninguna librería de íconos nueva (no había
  ninguna en el proyecto).
- **Color deliberadamente distinto del amarillo** de `.aviso-limite` /
  `.aviso-duplicado` (`#fff8e6`) — para que el tip no se lea como una
  advertencia.
- Posición sin cambios: sigue debajo de la dropzone, arriba de "Últimas
  facturas".

**Decisión técnica de implementación** (no estaba en el handoff, surgió al
implementar): el JS de rotación (`static/js/app.js`) manipula
`textContent` de `#tip-rotativo` directamente en cada tip nuevo — si el
ícono viviera adentro de ese mismo elemento, cada rotación lo borraría.
Se resolvió sin tocar `app.js` en absoluto: el ícono queda como hermano
de `#tip-rotativo` dentro de un `.tip-card` contenedor, y el show/hide +
fade de la tarjeta completa (ícono incluido) se controla con CSS
`:has()` apuntando al estado de `#tip-rotativo` (que sigue siendo el
único elemento que el JS toca, exactamente igual que antes). Las reglas
viejas de `.tip-rotativo` quedan como resguardo por si algún navegador no
soportara `:has()` (soportado en navegadores mobile desde 2023, no es un
riesgo real para el público de la app).

### Alternativas consideradas
- Mover el tip arriba de la dropzone — descartada, la posición actual
  está bien para el CEO.
- Animar la transición entre tips (más allá del fade que ya existía) —
  descartada por ahora, podría retomarse a futuro.
- Convertir el espacio en una tarjeta de novedades/avisos más genérica
  (no solo tips) — descartada por ahora, podría discutirse a futuro.

### Consecuencias
- El tip gana jerarquía visual sin cambiar su comportamiento ni su
  posición — riesgo bajo, cambio acotado a `templates/app.html` y
  `static/css/app.css` únicamente (`static/js/app.js` sin tocar,
  confirmado por diff vacío).
- Introduce el primer uso de `:has()` en el CSS del proyecto — si algún
  navegador viejo no lo soporta, el único efecto es que la tarjeta no se
  oculta/atenúa via CSS (se apoya en el resguardo de `.tip-rotativo`), no
  rompe nada.

## Implementación
- `strings/tips.txt` (nuevo).
- `app/services/tips.py` (nuevo): `get_tips() -> list[str]`, tolera archivo
  ausente/vacío/con solo comentarios sin romper.
- `app/blueprints/web.py::app_view()`: pasa `tips_json` al template.
- `templates/app.html`: bloque saludo/entrada/feedback reordenado,
  contenedor del tip rotativo, `window.__TIPS__`.
- `static/js/app.js`: rotación del tip (índice aleatorio inicial, interval
  9s, fade).
- `static/css/app.css`: jerarquía tipográfica nueva (`.saludo`, `.entrada`,
  `.feedback`, ya no se usa el nombre `.bienvenida`), estilos del tip
  rotativo. Respeta el `max-width` de `.contenido-centrado` (ADR-0002).

**Adenda 2026-07-15 (Decisión E, tarjeta + ícono)**:
- `templates/app.html`: `#tip-rotativo` pasa de `<p>` suelto a estar
  envuelto en `<div class="tip-card">` junto al SVG del ícono (hermano,
  no hijo).
- `static/css/app.css`: `.tip-card` (fondo, radio, padding, flex),
  `.tip-icono`, `.tip-rotativo` actualizado (tamaño de letra, color,
  `flex:1; min-width:0` para que el texto haga wrap en mobile sin
  desbordar). `static/js/app.js` **sin cambios**.

## Fuera de alcance
1. Implementar la pantalla de espera / carrusel del ADR-0005 general — el
   mecanismo de tips se diseñó para que ese consumo futuro sea directo
   (`get_tips()` reusable), pero la pantalla en sí no se implementa acá.
   **Nota**: el handoff de origen se cortó en este punto de la sección
   "Fuera de alcance" — se infiere este ítem por ser el único mencionado
   explícitamente como fuera de alcance en el resto del texto (Decisión A,
   punto 2). Si había más ítems fuera de alcance en el handoff original,
   no llegaron a esta sesión.

## Criterios de aceptación
1. Editar `strings/tips.txt` (agregar/sacar/cambiar una línea) sin tocar
   código, y el cambio se refleja en la home.
2. Si `strings/tips.txt` no existe o queda vacío, la home no muestra
   ningún tip y no rompe.
3. En la home aparecen, en orden: saludo, texto de entrada (más grande),
   feedback, dropzone, tip rotativo, Últimas facturas.
4. El tip rotativo cambia solo cada ~9s, con transición suave, arrancando
   en un tip aleatorio distinto en cada carga.
5. Ninguno de los textos nuevos (saludo, feedback, tips) usa ":".
6. `docs/areas/app/STATUS.md` y `docs/STATUS.md` actualizados.

**Criterios de aceptación de la adenda (Decisión E, 2026-07-15)**:
7. El tip se ve como tarjeta (fondo, bordes redondeados, padding) con
   ícono de lamparita a la izquierda del texto.
8. La posición no cambia (sigue debajo de la dropzone, arriba de "Últimas
   facturas") y la rotación (9s, fade, orden, arranque aleatorio) sigue
   funcionando igual que antes.
9. El color de fondo de la tarjeta del tip es distinguible a simple vista
   del amarillo de `.aviso-limite`/`.aviso-duplicado` (no se confunde con
   una advertencia).
10. En mobile (viewport angosto) la tarjeta no genera scroll horizontal ni
    empuja el resto del contenido fuera de pantalla.
11. El texto es legible sobre el nuevo fondo (contraste suficiente).

### Pruebas hechas (2026-07-15)
Sin Chromium/Playwright instalado de entrada en este entorno — se instaló
para esta sesión (`npx playwright install chromium`) y se armó una prueba
real (no simulada):
1. Se generó el HTML **real** de `/app` (Flask + Jinja reales, no HTML
   escrito a mano) contra un usuario de prueba en una base SQLite temporal
   en el scratchpad — la base de desarrollo real (`app.db`) no se tocó.
   El usuario de prueba se configuró con 165 facturas del ciclo (arriba
   del umbral de 160) para forzar que `.aviso-limite` (amarillo) y la
   tarjeta del tip (celeste) aparezcan juntos en pantalla y se pueda
   verificar que no se confunden.
2. Ese HTML se sirvió con los assets reales (`static/css/app.css`,
   `static/js/app.js` sin modificar) y se abrió con Playwright/Chromium en
   dos viewports: desktop (1280×900) y mobile (375×812, tamaño iPhone).
3. Verificado por código (no solo visual): la tarjeta es visible, contiene
   el ícono SVG, el texto cambia solo tras esperar >9s (la rotación sigue
   funcionando), no hay overflow horizontal en mobile, el fondo de la
   tarjeta (`rgb(238,244,255)` = `#eef4ff`) es distinto del fondo de
   `.aviso-limite` (`rgb(255,248,230)` = `#fff8e6`) y del fondo general
   (`rgb(249,250,251)`), y el texto usa `var(--gray-900)` sobre ese fondo
   (contraste alto).
4. Verificado visualmente con capturas de pantalla en ambos viewports —
   tarjeta con ícono, bien diferenciada del aviso amarillo, sin romper el
   layout en mobile.
5. Confirmado por diff que `static/js/app.js` no se tocó (0 líneas
   cambiadas) — la lógica de rotación es exactamente la misma.

**No probado**: el celular real (el entorno de pruebas es Chromium
headless emulando un viewport mobile, no un dispositivo real) — mismo
tipo de limitación que otras sesiones de esta área (ADR-0006). Pendiente
de que el CEO lo confirme en su teléfono.
