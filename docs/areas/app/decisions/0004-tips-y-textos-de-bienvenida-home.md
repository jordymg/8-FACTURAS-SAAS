# ADR-0004 (app): Tips gestionables + textos de bienvenida y feedback en la home

**Date:** 2026-07-11
**Status:** ADOPTADA e IMPLEMENTADA — origen: sesión de diseño CEO (Jordi) + CPO (Claude), APROBADO por CEO.
Confirmada funcionando por el founder en navegador el mismo día, tras dos
rondas de ajustes visuales chicos (ver nota en Decisión C).

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
