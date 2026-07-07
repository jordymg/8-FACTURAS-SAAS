# STATUS — Área App (diseño/UX)

## Estado actual
Área recién creada (2026-07-07) — solo estructura y alcance, sin decisiones
propias todavía. La interfaz actual existe y funciona en producción, pero
se construyó de forma incremental sin pasar por un diseño formal en esta
área.

Hay dos decisiones de diseño ya adoptadas en **otras** áreas que esta área
tiene que reflejar cuando se implementen:
- Pantalla de espera / cold start —
  [`docs/decisions/0005-pantalla-espera-cold-start.md`](../../decisions/0005-pantalla-espera-cold-start.md)
  (repo general).
- Aviso de duplicado detectado —
  [`docs/areas/planillas/decisions/0009-ux-duplicados.md`](../planillas/decisions/0009-ux-duplicados.md)
  (área planillas).

## Next
1. Conversación de diseño dedicada para completar `PRODUCTO.md` de esta
   área: pantallas, flujos, y sobre todo el formulario de revisión con ~20
   campos (evaluar si conviene agruparlo por secciones — pendiente también
   en `docs/STATUS.md` general).
2. Cuando se prioricen, implementar la pantalla de espera (ADR-0005 repo
   general) y el aviso de duplicados (ADR-0009 área planillas) — ninguna de
   las dos tiene código todavía.
