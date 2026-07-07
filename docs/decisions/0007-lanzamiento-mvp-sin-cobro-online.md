# ADR-0007: Lanzamiento del MVP sin cobro online, sin landing y sin dominio propio

**Date:** 2026-07-07
**Status:** ADOPTADA — re-prioriza parte de la Fase 3 del ROADMAP

## Contexto
El ROADMAP tenía Mercado Pago + lógica de bloqueo, landing page y dominio
propio como bloqueantes duros de la Fase 3 (Launch). El founder decidió el
canal de venta real para los primeros clientes: **persona a persona, a
clientes conocidos, con demo presencial y cobro manual (efectivo)** — no
necesita ninguno de esos tres elementos para arrancar a vender.

## Decisión
El MVP se lanza **sin cobro online, sin landing y sin dominio propio**.
Los tres puntos dejan de ser bloqueantes duros y pasan a **"necesarios
post-MVP — no olvidar"**, para cuando la venta deje de ser 1 a 1 con
conocidos y haya que escalar:

1. **Cobro (Mercado Pago + bloqueo)**: postergado. Cobro manual/presencial
   por ahora. Necesario para escalar más allá de clientes conocidos.
2. **Landing page**: postergada. La venta inicial es presencial con demo en
   vivo. Sigue considerándose esfuerzo bajo / impacto alto para cuando
   toque.
3. **Dominio propio**: postergado, misma categoría que 1 y 2.

Lo que sí se mantiene como **bloqueante inmediato** para poder vender ya:
**Términos de uso, versión mínima** (ver `docs/ROADMAP.md` — cubre el
acceso Editor de la Service Account, qué datos procesa la app, la
no-persistencia de imágenes, y límites de responsabilidad; no busca ser
exhaustivo legalmente todavía).

## Alternativas consideradas
- Esperar a tener Mercado Pago + landing + dominio antes de vender:
  descartada — agrega semanas de trabajo sin necesidad real, si los
  primeros clientes son conocidos y pagan en efectivo.

## Consecuencias
- `docs/ROADMAP.md` Fase 3 se reordena: 1-3 quedan marcados como
  postergados (no bloqueantes), TOS pasa a hacerse ya.
- Sin cobro online, el tope de 250 facturas/mes (ver
  `docs/decisions/0008-tope-facturas-mensual.md`) arranca en versión
  **soft** (solo contador + avisos, sin corte) — no hay forma de cobrar un
  plus todavía si alguien lo supera.
- Sin landing, la demo presencial y el propio founder son el "onboarding de
  ventas" — no reemplaza el onboarding de producto (ver punto de
  configuración de planilla en `docs/areas/app/`).
