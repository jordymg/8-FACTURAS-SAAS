# ADR-0013: Keep-alive para Render free tier

**Date:** 2026-07-16
**Status:** ADOPTADA e IMPLEMENTADA — mecanismo **reemplazado** el mismo
día tras dos intentos fallidos con GitHub Actions (ver "Corrección
2026-07-16" y "Reemplazo 2026-07-16" al final). Mecanismo vigente:
**UptimeRobot**, configurado fuera del repo. Ver también
[Issue #007](../ISSUES.md).

## Contexto
Render free tier duerme el servicio tras ~15 minutos sin tráfico entrante;
el arranque en frío (~30s) es inaceptable para clientes reales — riesgo ya
previsto en [ADR-0001](0001-stack.md). El CEO descartó por ahora el plan
pago de Render, prefiere mantener costo cero y evaluar más adelante
independencia de proveedor (tema aparte, no resuelto en este ADR).

## Decisión
- Endpoint `GET /health` estático en `app/blueprints/api.py`: responde
  `200` con `{"status": "ok"}` al instante, sin tocar la DB, sin llamar a
  la API de Sheets ni a Gemini, sin autenticación ni sesión, y sin afectar
  el conteo de facturas mensual ni ninguna métrica de uso existente. Su
  único propósito es generar tráfico entrante que Render registre.
- `.github/workflows/keep-alive.yml`: cron cada 14 minutos, 24/7
  (`*/14 * * * *`), más `workflow_dispatch` para poder dispararlo a mano.
  Un solo `curl` a `https://facturas-saas.onrender.com/health` con timeout
  de 60s (el primer request tras el sueño tarda ~30s en despertar). El job
  no falla si el request falla (`|| true`) — no queremos workflows rojos
  por un timeout puntual, el próximo ping en 14 minutos lo corrige.
- El free tier da 750 horas de instancia por mes; un mes tiene como máximo
  744 horas, así que mantenerlo despierto 24/7 no supera el límite.
- Nota conocida: los crons de GitHub Actions no son exactos al minuto
  (pueden demorarse bajo carga de GitHub) — con margen de 15 vs 14 minutos
  es un riesgo menor aceptado. Si en la práctica la app igual se duerme a
  veces, bajar el cron a `*/10`.

## Alternativas consideradas
- **Plan pago de Render** — descartado por ahora, decisión del CEO de no
  pagar Render.
- **Servicio externo de pings (tipo UptimeRobot)** — descartado, agrega un
  tercero nuevo cuando GitHub Actions ya está en nuestra infraestructura y
  queda versionado en el repo.
- **Antesala estática en GitHub Pages que despierte a Render y
  redirija** — descartada, duplica origen/dominio (problemas con la PWA
  instalada y el redirect de OAuth) y no acorta la espera, solo la
  enmascara — que es justo lo que ya hace el [ADR-0005](0005-pantalla-espera-cold-start.md).
- **Migrar de proveedor** — fuera del alcance de este ADR, queda como tema
  abierto de independencia de proveedor.

## Consecuencias
- Es un workaround no soportado oficialmente por Render (la vía soportada
  es el plan pago) — si Render cambia las reglas o lo bloquea, se retoma
  la discusión (plan pago o migración).
- El [ADR-0005](0005-pantalla-espera-cold-start.md) (pantalla de espera)
  sigue vigente como complemento, sin cambios: cubre deploys, reinicios y
  reintentos de Gemini, casos que el keep-alive no elimina.
- Si el cron de GitHub se demora y la app se duerme igual en algún caso
  puntual, ajustar el cron a `*/10`.
- Reversible borrando `.github/workflows/keep-alive.yml`.
- Probado en este entorno: `GET /health` responde `200` instantáneo en
  local. **Pendiente de confirmación real**: `/health` en producción, el
  workflow disparado a mano contra producción, y que tras ~1 hora con el
  cron activo la app responda rápido a un request real sin cold start —
  requiere acceso a producción y a Actions del repo en GitHub, fuera de
  este entorno.

## Corrección 2026-07-16: el keep-alive no cumplía su función

El CEO confirmó con un log de Render que la app estaba dormida a las
~10:06 hora Argentina (13:06 UTC) y despertó por un request manual suyo —
el keep-alive no la mantuvo despierta. Diagnóstico (vía `gh` CLI contra la
API de Actions del repo):

- El workflow estaba activo, en la rama default (`master`), sin errores —
  no era un problema de configuración/deshabilitado/rama equivocada.
- Solo tenía 2 ejecuciones desde que se pusheó esa misma mañana. Horarios
  reales: push a las 10:16:50 UTC, Run 1 a las 11:56:49 UTC (**99
  minutos** después, no ~14), Run 2 a las 13:40:23 UTC (**103 minutos**
  después del Run 1).
- El incidente reportado (13:06 UTC) cae exactamente en ese hueco de 103
  minutos entre Run 1 y Run 2.
- `/health` respondía 200 correctamente al probarlo a mano — el endpoint
  en sí nunca fue el problema.

**Causa raíz confirmada:** el trigger `schedule` de GitHub Actions no
ejecuta con la precisión configurada para crons sub-horarios — es un
comportamiento conocido/documentado de la plataforma (los runs
programados pueden demorarse, sobre todo en horarios de carga, y más
todavía en repos con poca actividad de Actions), no un error de nuestra
configuración. El intervalo real observado (~100 min) fue ~7 veces más
lento que el `*/14` pedido.

**Fix aplicado:**
- Cron bajado a `*/10 * * * *` — decisión del CEO, ya tomada de antemano
  como parte de este fix independientemente del diagnóstico (el repo es
  público, minutos de Actions ilimitados y gratis, sin costo por bajar el
  intervalo). **Importante:** dado que la causa raíz es la imprecisión de
  GitHub para crons sub-horarios (no el valor del intervalo en sí), `*/10`
  reduce el riesgo pero **no lo elimina** — si GitHub sigue demorando
  ejecuciones por encima del margen de sueño de Render (~15 min), este
  ajuste solo no alcanza.
- Se agrega `--fail` al `curl` — sin este flag, una respuesta HTTP de
  error (4xx/5xx) no hace fallar el paso (curl solo falla por defecto ante
  errores de transporte, no de protocolo), y combinado con el `|| true` ya
  existente el workflow quedaría en verde igual. No fue la causa de este
  incidente puntual (los pings sí devolvieron 200), pero es un hueco real
  que se cierra de paso.

**Pendiente de verificación real:** los gaps efectivos entre pings de las
próximas horas (vía `gh run list --workflow keep-alive.yml`), y si la app
deja de aparecer dormida en los logs de Render. **Riesgo señalado, no
resuelto:** si tras este ajuste los gaps siguen superando ~15 minutos en
algún momento, la causa de fondo (crons sub-horarios de GitHub Actions no
son confiables) sigue vigente y hay que evaluar una alternativa distinta
(servicio externo de pings, plan pago de Render) — decisión del CEO, no
implementada acá.

## Reemplazo 2026-07-16: GitHub Actions descartado, mecanismo pasa a UptimeRobot

El riesgo señalado en la corrección anterior se confirmó: el CEO verificó
un cold start real **posterior** al fix de `*/10` — la app se siguió
durmiendo. El ajuste de intervalo no alcanzó, porque la causa de fondo
nunca fue el valor del cron, fue la imprecisión de GitHub Actions para
ejecutar `schedule` con la frecuencia configurada (gaps reales medidos de
99 y 103 minutos contra los 14 configurados originalmente — ver
"Corrección" arriba). **GitHub Actions queda descartado como mecanismo de
keep-alive**, no solo ajustado.

**Decisión del CEO:** reemplazar por **UptimeRobot** (uptimerobot.com),
servicio externo gratuito dedicado a monitoreo — la puntualidad del ping
es su producto (a diferencia de GitHub Actions, donde el `schedule` es
una feature secundaria de una plataforma de CI/CD). Monitor HTTP(s) cada
5 minutos contra la URL pública de producción
(`https://facturas-saas.onrender.com/health`). Suma como beneficio extra
alertas por mail si la app deja de responder de verdad (no solo
keep-alive, también monitoreo básico de disponibilidad).

**Importante — este mecanismo vive FUERA del repo:** la cuenta y el
monitor de UptimeRobot los configura el CEO a mano en
uptimerobot.com, no hay ningún archivo de config ni credencial en este
código. **Una sesión futura que busque el keep-alive en el repo no va a
encontrar rastro de él** — si `/health` deja de recibir tráfico regular y
la app se vuelve a dormir, lo primero a revisar es el estado del monitor
en la cuenta de UptimeRobot del CEO, no el código.

**Qué se elimina:** `.github/workflows/keep-alive.yml` (borrado del
repo). No convive con UptimeRobot — un cron que no cumple su frecuencia
no sirve ni como respaldo, y dejarlo activo solo generaría ruido en
Actions.

**Qué se mantiene sin cambios:**
- El endpoint `GET /health` en `app/blueprints/api.py` — sigue siendo la
  URL que se pinguea, ahora consumida por UptimeRobot en vez del
  workflow.
- El [ADR-0005](0005-pantalla-espera-cold-start.md) (pantalla de espera)
  — sigue como cobertura de los cold starts residuales que un keep-alive
  externo no puede eliminar del todo (deploys, reinicios, el propio
  margen entre pings).
- El plan pago de Render como solución definitiva de fondo, postergada
  hasta la salida a vender ([ADR-0001](0001-stack.md)) — UptimeRobot es
  un workaround del free tier, no la reemplaza conceptualmente.

**Alternativas consideradas (revisadas contra la decisión anterior):** la
entrada "Servicio externo de pings (tipo UptimeRobot)" en "Alternativas
consideradas" arriba quedó obsoleta — se había descartado por agregar un
tercero cuando GitHub Actions parecía alcanzar. Con GitHub Actions
descartado por imprecisión real y medida, ese argumento ya no aplica: la
alternativa que quedaba en pie es justamente la que se adopta acá.

**Pendiente de verificación real:** que UptimeRobot efectivamente
mantenga la app despierta durante un período largo (horas/días) sin cold
starts — pendiente de que el CEO lo confirme desde su cuenta y desde el
uso real de la app.
