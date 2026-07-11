# STATUS — Área App (diseño/UX)

## Estado actual
**ADR-0001** — rediseño del formulario de revisión (ocultar campos poco
frecuentes salvo que tengan valor extraído — con Neto e IVA 21% siempre
visibles pero no bloqueantes, grilla responsiva en desktop, procesamiento
automático sin botón manual). Implementado en código desde el 2026-07-07.

**ADR-0002** — rediseño de la pantalla de inicio (sesión de diseño CEO+CPO,
2026-07-11): auto-procesamiento también en la pantalla de inicio (aplica el
mismo mecanismo de ADR-0001), texto de bienvenida sobre la dropzone,
contenido con ancho máximo en desktop, botón "Ver planilla de Facturas" en
un header de 3 zonas. Implementado en código el mismo día. De paso se
agregó **cache-busting a `app.css`/`app.js`** (query param con el mtime del
archivo) — resuelve de raíz el problema de la sesión anterior (cambios de
código que no se veían reflejados en el navegador).

**Ambos ADRs (0001 y 0002) están implementados en código pero NO
confirmados funcionando en navegador todavía** — se verificaron por render
de servidor (`test_client`) y chequeos estáticos (grep, sintaxis, boot),
pero no hay herramienta de navegador en este entorno para confirmar
visualmente, y la sesión se cerró antes de que el founder llegara a probar
el rediseño de la pantalla de inicio en su navegador. **Primer paso de la
próxima sesión: abrir `http://localhost:5000` y confirmar los 5 criterios
de aceptación de `decisions/0002-rediseno-pantalla-inicio.md`.**

Además, `docs/decisions/0009-comunicacion-nunca-mencionar-ia.md` (repo
general, transversal): ningún texto visible menciona IA/Gemini — auditoría
hecha y corregida en 3 lugares (2 de ellos fuera del área App).

Además, el founder definió el foco del onboarding (ver `PRODUCTO.md`): no
es un carrusel genérico, es el paso de **configurar la planilla** (crearla,
compartirla con la SA, pegar la URL) — tiene que ser "a prueba de tontos".
Diseño concreto pendiente de la conversación de diseño dedicada.

Decisiones de diseño adoptadas en **otras** áreas que esta tiene que
reflejar cuando se implementen:
- Pantalla de espera / cold start —
  [`docs/decisions/0005-pantalla-espera-cold-start.md`](../../decisions/0005-pantalla-espera-cold-start.md)
  (repo general). Ahora **prioridad alta pre-lanzamiento**: también
  enmascara los reintentos automáticos ante 503 de Gemini (ver
  `docs/ROADMAP.md`).
- Aviso de duplicado detectado —
  [`docs/areas/planillas/decisions/0009-ux-duplicados.md`](../planillas/decisions/0009-ux-duplicados.md)
  (área planillas) — **ya implementado y confirmado en producción**.

## Next
1. **Confirmar visualmente ADR-0001 + ADR-0002 en el navegador**
   (`http://localhost:5000`, con `localhost` no `127.0.0.1` por el tema de
   OAuth ya resuelto). Con el cache-busting nuevo no debería hacer falta
   recarga forzada — si el problema de "no veo cambios" de la sesión
   anterior persiste, ahí sí hay un bug real que diagnosticar, no caché.
   Recién después de confirmar: commitear y probar en el celular.
2. **Prioridad alta pre-lanzamiento**: implementar la pantalla de espera
   (ADR-0005 repo general) con el enmascaramiento de reintentos de Gemini.
3. Diseñar el onboarding de configuración de planilla (ver `PRODUCTO.md`) —
   necesita una conversación de diseño dedicada.
4. Conversación de diseño dedicada más amplia, para completar el resto de
   `PRODUCTO.md`: pantallas, flujos, identidad visual.
