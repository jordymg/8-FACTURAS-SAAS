# ADR-0005: Pantalla de espera propia para el cold start de Render

**Date:** 2026-07-07
**Status:** ADOPTADA — no implementada todavía. Ampliada 2026-07-07: mismo
mecanismo se usa también para enmascarar reintentos de Gemini (ver abajo).

## Contexto
El plan free de Render duerme el servicio tras un rato sin uso (~30s de
arranque al despertar) — riesgo ya previsto en ADR-0001. Mientras el
servicio despierta, el usuario ve la pantalla de carga genérica de Render,
no algo propio de la marca.

**Segundo caso de uso, sumado al re-priorizar el pre-lanzamiento (ver
`docs/decisions/0007-lanzamiento-mvp-sin-cobro-online.md`)**: los
reintentos automáticos ante un 503 de Gemini (Fase 2 del ROADMAP, "hacer
antes de vender") necesitan una pantalla de espera — se decidió que sea
la MISMA pantalla/carrusel de este ADR, no una nueva.

## Decisión
La PWA cachea su app shell (vía service worker) y muestra una **pantalla de
espera propia** mientras el servidor despierta, con un **carrusel de
mensajes rotativos** (tips de uso, qué hace la app) en vez de una pantalla
en blanco o el mensaje genérico de Render.

Esto es **complementario, no reemplazo**, del upgrade a un plan pago de
Render al salir al mercado (esa decisión sigue en pie según ADR-0001) — la
pantalla de espera cubre el tiempo hasta que se justifique el upgrade, y
sigue siendo una buena práctica de UX aunque el servicio ya no duerma.

**Uso ampliado — reintentos de Gemini invisibles**: cuando Gemini devuelve
503 y la app reintenta automáticamente, el usuario **no ve** ningún mensaje
de "error, reintentando" — ve esta misma pantalla de espera con el
carrusel de tips, como si fuera simplemente parte del tiempo de
procesamiento normal. Solo si los reintentos se agotan (todos fallan) se
muestra recién ahí un mensaje de error amigable.

## Consecuencias
- Requiere que el service worker (`static/sw.js`) cachee el app shell
  (HTML/CSS/JS mínimo) para poder mostrar algo propio incluso antes de que
  el backend responda.
- Requiere que la lógica de reintentos de Gemini (backend,
  `app/services/gemini.py`) y la pantalla de espera (frontend) se activen
  con el mismo mecanismo/señal, para que el usuario vea una sola pantalla
  consistente sea cual sea la causa de la espera.
- **Textos del carrusel**: a definir al implementar (no forman parte de
  esta decisión).
- No implementado todavía — ahora prioridad alta pre-lanzamiento por el
  caso de uso de reintentos de Gemini (ver `docs/ROADMAP.md`), no solo el
  cold start de Render.
