# ADR-0013: Keep-alive para Render free tier vía GitHub Actions

**Date:** 2026-07-16
**Status:** ADOPTADA e IMPLEMENTADA

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
