# ADR-0006: Modelo de organización por roles

**Date:** 2026-07-07
**Status:** ADOPTADA

## Contexto
El proyecto se piensa como una empresa tradicional, con roles clásicos
(CEO, CPO, etc.), independientemente de que algunos los ocupe una IA en vez
de una persona. A medida que crecen las áreas de I+D (`docs/areas/`),
faltaba definir quién es el encargado de cada una.

## Decisión
- **Organigrama vivo** en [`docs/ORGANIGRAMA.md`](../ORGANIGRAMA.md).
- **Los roles se crean con cada área nueva** — no se nombran todos los
  cargos de entrada, solo los que ya tienen un área real que dirigir.
- **CEO dirige sin ejecutar**: define visión, prioridades, y aprueba toda
  decisión (los ADRs son sus firmas). No escribe código ni documentación
  operativa.
- **CPO es el encargado de las áreas App y Planillas** — son el mismo
  producto visto de dos lados (medio y entregable), el cliente lo vive como
  una sola experiencia.

## Alternativas consideradas
- Nombrar todos los roles C-level de entrada (CTO, CFO, etc.): descartada
  — roles sin un área real que dirigir son ruido documental.
- Planillas bajo un rol fiscal propio (ej. "responsable de compliance"):
  descartada por ahora — es una decisión de producto con conocimiento de
  dominio fiscal de apoyo, no una dirección fiscal formal. Puede revisarse
  cuando haya clientes reales y volumen de decisiones de dominio fiscal
  (ver nota en `docs/ORGANIGRAMA.md`).

## Consecuencias
- Cada área nueva en `docs/areas/` debe declarar su encargado en su propio
  `README.md` y sumarse al organigrama.
- `docs/ORGANIGRAMA.md` se actualiza cada vez que cambia un encargado o
  nace un rol nuevo — es documento vivo, no una foto fija.
