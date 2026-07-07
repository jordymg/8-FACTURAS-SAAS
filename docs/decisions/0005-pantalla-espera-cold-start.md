# ADR-0005: Pantalla de espera propia para el cold start de Render

**Date:** 2026-07-07
**Status:** ADOPTADA — no implementada todavía

## Contexto
El plan free de Render duerme el servicio tras un rato sin uso (~30s de
arranque al despertar) — riesgo ya previsto en ADR-0001. Mientras el
servicio despierta, el usuario ve la pantalla de carga genérica de Render,
no algo propio de la marca.

## Decisión
La PWA cachea su app shell (vía service worker) y muestra una **pantalla de
espera propia** mientras el servidor despierta, con un **carrusel de
mensajes rotativos** (tips de uso, qué hace la app) en vez de una pantalla
en blanco o el mensaje genérico de Render.

Esto es **complementario, no reemplazo**, del upgrade a un plan pago de
Render al salir al mercado (esa decisión sigue en pie según ADR-0001) — la
pantalla de espera cubre el tiempo hasta que se justifique el upgrade, y
sigue siendo una buena práctica de UX aunque el servicio ya no duerma.

## Consecuencias
- Requiere que el service worker (`static/sw.js`) cachee el app shell
  (HTML/CSS/JS mínimo) para poder mostrar algo propio incluso antes de que
  el backend responda.
- **Textos del carrusel**: a definir al implementar (no forman parte de
  esta decisión).
- No implementado todavía — queda documentado para cuando se priorice.
