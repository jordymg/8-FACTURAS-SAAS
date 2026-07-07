# ADR-0008: Tope de facturas mensual — diseño funcional

**Date:** 2026-07-07
**Status:** ADOPTADA — versión soft (sin corte) para el MVP, ver Consecuencias

## Contexto
El plan tiene un tope de facturas por mes (ver
`docs/decisions/0003-pricing.md`). Faltaba definir el diseño funcional: cómo
se cuenta, cuándo se avisa, y qué pasa al llegar al límite.

## Decisión
- **Contador de facturas por usuario por mes**, llevado en la base de datos
  de la app (`app/models.py::User.invoices_this_month`, ya existe) — **no**
  leyendo el Sheet del usuario cada vez.
- **Advertencia al usuario al acercarse al límite** (ej. al llegar a 200:
  "estás por llegar al límite del mes").
- **Advertencia al acercarse el fin de mes**: "pagá el mes próximo o el
  servicio se corta" — aplicable recién cuando exista cobro (ver ADR-0007).
- **Al llegar a 250**: se corta el servicio del mes, salvo pago de un plus
  que sume facturas adicionales (upsell a definir en detalle cuando exista
  el cobro).
- **Mientras NO haya cobro online (MVP, ver ADR-0007)**: solo contador +
  avisos, **sin corte** — sirve para ver uso real de los primeros clientes
  antes de que el corte tenga sentido (no tendría con qué "destrabarse").

## Alternativas consideradas
- Contar leyendo el Sheet del usuario en cada request: descartada — más
  lento (una llamada a la API de Sheets por chequeo) y menos confiable que
  un contador propio en la app.
- Cortar el servicio directamente en el MVP sin cobro: descartada — sin
  forma de pagar el plus, cortarle el servicio a un cliente conocido sin
  vía de solución sería peor que no cortar.

## Consecuencias
- Implementación (no hecha todavía): mostrar el contador/aviso en la UI
  (área App) cuando `invoices_this_month` se acerque a 250; el corte real y
  el upsell quedan bloqueados hasta que exista cobro (ADR-0007).
- El reset mensual de `invoices_this_month` no está diseñado todavía —
  pendiente definir cuándo y cómo se reinicia el contador cada mes.
