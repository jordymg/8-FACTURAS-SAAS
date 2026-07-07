# STATUS — Área App (diseño/UX)

## Estado actual
Ya tiene su primera decisión propia:
**ADR-0001** — rediseño del formulario de revisión (ocultar campos poco
frecuentes salvo que tengan valor extraído, grilla responsiva en desktop,
procesamiento automático sin botón manual). No implementada todavía.

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
1. **Prioridad alta pre-lanzamiento**: implementar la pantalla de espera
   (ADR-0005 repo general) con el enmascaramiento de reintentos de Gemini.
2. Implementar el rediseño del formulario de revisión (ADR-0001 de esta
   área), junto con probarlo en el celular (pendiente también en
   `docs/STATUS.md` general).
3. Diseñar el onboarding de configuración de planilla (ver `PRODUCTO.md`) —
   necesita una conversación de diseño dedicada.
4. Conversación de diseño dedicada más amplia, para completar el resto de
   `PRODUCTO.md`: pantallas, flujos, identidad visual.
