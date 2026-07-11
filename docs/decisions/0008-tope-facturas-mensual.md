# ADR-0008: Tope de facturas mensual — diseño funcional

**Date:** 2026-07-07
**Status:** ADOPTADA e IMPLEMENTADA (versión soft, sin corte) — ver
Consecuencias para el detalle de implementación del 2026-07-11.

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
- El corte real y el upsell quedan bloqueados hasta que exista cobro
  (ADR-0007) — no implementados, es la parte que sigue pendiente.

### Implementación (2026-07-11)
- **Límite mensual: 200 facturas** (`LIMITE_MENSUAL`, cambiado desde 250 a
  pedido del founder), aviso al llegar a **160** (`UMBRAL_AVISO`, 80% del
  límite, misma proporción que antes). Ambas son constantes en
  `app/services/limites.py` — para volver a cambiarlas, se editan ahí,
  nada más.
- **Contador en el header**: `N/200`, discreto, a la izquierda de
  "Configuración" — siempre visible, no solo cerca del límite.
- **Aviso en la home**: banner (mismo lenguaje visual que el aviso de
  duplicados, ADR-0009 área Planillas) cuando el conteo del ciclo llega a
  160 — "Estás por llegar al límite de facturas de este mes (N de 200)".
  No bloquea nada, es solo informativo.

**Corrección del founder sobre el ciclo (mismo día)**: la primera versión
reseteaba por **mes calendario** (1° de cada mes, igual para todos). El
founder aclaró que el ciclo tiene que ser **por fecha de alta de cada
cliente** — ej. alta el 10, dura hasta el 9 del mes siguiente, no hasta
fin de mes calendario. Corregido:
- `User.created_at` (nuevo): fecha de alta, se completa sola al loguearse
  por primera vez (`app/blueprints/auth.py`). Usuarios de antes de este
  campo recibieron un backfill con la fecha del día en que se agregó la
  columna (mejor aproximación disponible, no hay dato histórico real).
- `User.invoices_cycle_start` (reemplaza el `invoices_month` de la primera
  versión, que queda como columna huérfana inofensiva en las bases que ya
  lo tenían): fecha de inicio del ciclo vigente.
- `app/services/limites.py::_inicio_ciclo()`: calcula el inicio del ciclo
  vigente a partir del día de alta.

**Aclaración sobre "meses de distinta duración"** (el founder pidió no
depender de eso): para cualquier alta entre el día 1 y el 28, la regla es
literal y sin excepciones — "alta el 10, dura hasta el 9 del mes
siguiente" vale igual todos los meses del año, porque todo mes tiene al
menos 28 días. La única situación donde un mes puede no tener el día exacto
es con altas el **29, 30 o 31** (ej. alguien que se suma un 31 de enero,
y llega febrero) — ahí, inevitablemente, hay que elegir algo, porque ese
día no existe. Se usa el último día de ese mes corto (mismo criterio que
cualquier suscripción real con ciclo por aniversario). No es una
complejidad agregada al caso general, es la única solución posible para
un caso de calendario que no se puede evitar. **Confirmado explícitamente
a pedido del founder** con el caso "alta 31 de enero": en un año NO
bisiesto (2026) el ciclo corta el 28/02; en un año bisiesto (2028) corta
el 29/02 — sin tocar código, ya se comportaba así.

**Por qué no hace falta más precisión que esto**: el founder aclaró que el
servicio se piensa como un **abono anual** — no es crítico que la duración
exacta de cada ciclo mensual sea idéntica mes a mes (28, 29, 30 o 31 días
según a cuál mes le toque el corte). Lo que importa es el aniversario de
alta como referencia, no una precisión de reloj mes a mes. Esto confirma
que el enfoque actual (clamping simple al último día del mes corto) es
suficiente — no hace falta una librería de cálculo de fechas más
sofisticada (ej. `dateutil.relativedelta`) ni un diseño más elaborado.
- `facturas_del_mes()` (solo lectura, no escribe) y
  `registrar_factura_cargada()` (resetea y persiste al guardar una factura,
  `POST /api/invoices`) — mismo patrón sin cron que la versión anterior.
- Ambas columnas nuevas con el mismo mecanismo de auto-migración liviana
  del ADR-0003 área App (`app/__init__.py::_ensure_schema`), sin Alembic.
- Probado: el ejemplo exacto del founder (alta el 10 → sigue en ese ciclo
  hasta el 9 del mes siguiente inclusive, resetea el 10), el caso de
  alta a fin de mes con meses de distinta duración, reset por ciclo viejo,
  incremento con persistencia, render real de `/app`.
- **Issue #004** (ver `docs/ISSUES.md`): el contador y el aviso no se
  actualizaban en el navegador tras guardar una factura — corregido.
