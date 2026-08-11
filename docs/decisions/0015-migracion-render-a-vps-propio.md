# ADR-0015: Migración de Render a VPS propio

**Date:** 2026-08-11
**Status:** ADOPTADA — migración **planificada, no ejecutada todavía**. La
ejecución se documenta aparte en el runbook operativo
[`docs/ops/vps.md`](../ops/vps.md) (a crear) y se cierra en `docs/STATUS.md`
cuando el cutover esté hecho y verificado.

## Contexto
La app corre hoy en Render free tier
(`https://facturas-saas.onrender.com`, auto-deploy desde GitHub `master` —
ver [ADR-0001](0001-stack.md)). El free tier duerme el servicio tras ~15
minutos sin tráfico, con un arranque en frío (~30s) inaceptable para
clientes reales. Ese único problema obligó a una cadena de workarounds que
nunca terminó de cerrar: keep-alive por GitHub Actions descartado por
imprecisión, reemplazado por un monitor externo de UptimeRobot que vive
fuera del repo (ver [ADR-0013](0013-keep-alive-render-free.md) e
[Issue #007](../ISSUES.md)).

El CEO consiguió un **servidor propio** (Contabo, Ubuntu 24.04) y un
**dominio propio** (`mcfly.ar`). Migrar ahí elimina el cold start de raíz
(un VPS con un proceso bajo systemd no duerme), da dominio propio, da
control total sobre la plataforma, y deja una base para crecer sin estar
atado a las restricciones de un free tier. El costo es que pasamos a
operar nosotros lo que Render hacía administrado (TLS, gestión de proceso,
backups, deploy) — se contempla explícito abajo.

## Decisión
Migrar la app de Render a un VPS propio. Definiciones tomadas:

1. **Dominio.** La app se sirve en **`facturas.mcfly.ar`** (subdominio
   dedicado del dominio del CEO). TLS con Let's Encrypt (certbot).
2. **Topología del server.** `nginx` como reverse proxy delante de
   `gunicorn`, `gunicorn` gestionado por `systemd` (arranque automático,
   restart ante caída), firewall con `ufw`. `ProxyFix` en la app se
   mantiene sin cambios: nginx termina TLS y reenvía HTTP puertas adentro,
   igual que hacía el proxy de Render (sin `ProxyFix`, oauthlib rechaza el
   login por transporte inseguro).
3. **Base de datos: Postgres self-hosted en el VPS.** Se descarta SQLite.
   Aunque la DB de la app es diminuta hoy (solo identidad, planilla
   conectada, contador — los datos de facturas viven en el Sheet del
   cliente, no acá), se mantiene Postgres porque: (a) es el mismo motor que
   ya corre en producción, el código ya lo habla (`psycopg2`, el
   `postgres://`→`postgresql://` en `app/__init__.py`), así que no se
   re-testea nada; (b) contempla el crecimiento futuro de la DB sin un
   segundo cambio de motor; (c) migrar los datos actuales es un
   `pg_dump`/`pg_restore` limpio de Postgres a Postgres.
4. **Deploy manual.** No se reconstruye el auto-deploy de Render por ahora.
   El deploy es un `git pull` + restart del servicio (scriptcito en el
   runbook). El auto-deploy (webhook o similar) se agrega más adelante si
   el deploy manual llega a doler — una pieza menos que mantener durante la
   migración.
5. **Se retira el keep-alive.** El mecanismo de UptimeRobot
   ([ADR-0013](0013-keep-alive-render-free.md)) existía solo porque Render
   free duerme; un VPS no duerme, así que pierde su propósito. Al cerrar el
   cutover se apaga el monitor de UptimeRobot (vive en la cuenta del CEO,
   fuera del repo). El endpoint `GET /health` **se mantiene** — deja de ser
   un truco anti-sueño y pasa a ser un health check real para nginx y
   monitoreo. Ver la actualización correspondiente en el ADR-0013.
6. **La pantalla de espera se mantiene, reencuadrada.** El
   [ADR-0005](0005-pantalla-espera-cold-start.md) tenía dos justificaciones:
   el cold start de Render y la latencia propia de Gemini (~7-8s típicos,
   picos ocasionales, más los reintentos ante 503). La primera desaparece
   con el VPS; la segunda no. La pantalla sigue vigente **solo por la
   latencia de Gemini**. Ver la actualización correspondiente en el
   ADR-0005.
7. **Reemplazo del flag de producción.** Hoy la cookie de sesión se marca
   `Secure` detectando `RENDER=true` (env var que Render pone sola). En el
   VPS esa var no existe. Se reemplaza por una env var propia
   **`PRODUCTION=true`** que se setea en el server. Es un cambio de código
   chico (`app/__init__.py`) — sin él, la cookie no viaja `Secure` sobre
   HTTPS.
8. **Google OAuth.** Se agrega el redirect URI
   `https://facturas.mcfly.ar/oauth2callback` en Google Cloud Console (la
   ruta de callback de la app es `/oauth2callback`). El VPS pasa a ser la
   única producción (ver Consecuencias — el hosting anterior se decomisiona,
   sin rollback). Los scopes y el resto del flujo no cambian (login solo de
   identidad, ver
   [ADR-0004](0004-service-account-sheets.md) y
   [ADR-0012](0012-sesion-90-dias-oauth-sin-reconsentimiento.md)).

### División de trabajo (humano / Claudito / Claude Code)
El servidor tiene una instancia de Claude CLI instalada (apodada
**"Claudito"**). El reparto, para no romper el workflow multi-IA
(`docs/WORKFLOW.md`: Claude Code es la única puerta de escritura del repo):

- **Solo el CEO (humano):** el redirect URI en Google Cloud Console (es su
  cuenta Google), el DNS de `facturas.mcfly.ar` (su proveedor de dominio),
  poner los **valores** de los secretos (ni Claudito ni Claude Code tocan
  credenciales), el test de login real y la decisión de cutover.
- **Claudito (ejecuta en el server):** provisión del VPS siguiendo el
  runbook — Postgres, nginx, certbot, systemd, ufw, levantar la app, leer
  logs, iterar. Si necesita ajustar algo del repo, lo devuelve como
  handoff (`docs/handoffs/`), no commitea.
- **Claude Code (esta línea de trabajo):** escribe y commitea los ADRs, el
  runbook y las actualizaciones de docs; integra los handoffs de Claudito.
  Único escritor del repo.

## Alternativas consideradas
- **Quedarse en Render free con los workarounds actuales** — descartada:
  el cold start nunca se resolvió del todo (el keep-alive es un parche
  frágil, fuera del repo) y seguimos atados a las reglas de un free tier.
- **Render plan pago** — resuelve el sueño, pero mantiene la dependencia
  del proveedor, no da dominio propio ni control de la plataforma, y suma
  un costo mensual atado a Render. Con un VPS y dominio ya disponibles, no
  se justifica.
- **SQLite en el VPS** — descartada: sería cambiar un motor que hoy
  funciona (Postgres en producción) por otro, para tener que volver a
  cambiarlo cuando la DB crezca. Ver punto 3 de la Decisión.
- **Reconstruir el auto-deploy desde el arranque** — descartada por ahora:
  una pieza más de infraestructura que mantener justo durante la
  migración; el deploy manual alcanza para esta etapa. Ver punto 4.
- **Darle toda la migración a Claudito de punta a punta** — descartada:
  hay pasos que un server headless no puede ni debe hacer (login a la
  cuenta Google del CEO, DNS, valores de secretos, cutover con navegador
  real), y dos Claudes escribiendo el mismo repo se pisan. Ver la división
  de trabajo arriba.

## Consecuencias
- **Ganamos:** sin cold starts (se retira el keep-alive y su parche
  externo), dominio propio (`facturas.mcfly.ar`), control total del stack,
  y una base para crecer sin las restricciones del free tier.
- **Asumimos operar lo que Render hacía administrado:** TLS y su
  renovación (certbot), gestión del proceso (systemd), backups de Postgres,
  y el deploy. Todo esto se documenta como procedimiento en el runbook
  operativo [`docs/ops/vps.md`](../ops/vps.md) (a crear) — es la
  contrapartida real de la migración, no un detalle.
- **Cambios de código/config** (menores, a implementar): reemplazar
  `RENDER` por `PRODUCTION` en `app/__init__.py`, y actualizar
  `.env.example` (hoy desactualizado: lista `TOKENS_KEY` que no se usa y no
  menciona las vars de la Service Account ni `PRODUCTION`).
- **Docs a actualizar como parte de esta migración:**
  [ADR-0013](0013-keep-alive-render-free.md) (marcar UptimeRobot retirado
  post-migración), [ADR-0005](0005-pantalla-espera-cold-start.md)
  (reencuadrar la justificación solo a la latencia de Gemini),
  `docs/ARCHITECTURE.md` (fila Hosting: Render → VPS), y `docs/STATUS.md`
  al cerrar.
- **Sin red de rollback (decisión del CEO, 2026-08-11):** el hosting
  anterior se decomisiona **ya**, no se deja en standby. El VPS es la única
  producción desde el cutover, así que la prueba de login real + una carga
  de factura (runbook §7) es el go/no-go: si falla, se arregla sobre el VPS,
  no hay a dónde volver. Riesgo asumido a conciencia por la etapa actual
  (venta a conocidos, pocos usuarios logueados).
- **Pendiente de ejecución y verificación real:** todo. Este ADR fija la
  decisión y el plan; ninguna fase se ejecutó todavía. El estado de avance
  vive en `docs/STATUS.md` y el detalle operativo en el runbook.
